from google import genai
from schemas.interview_schema import EvaluationResult, InterviewResponse, PersonalizedQuestionBatch, QuestionMetadataBatch, ResumeContext, QuestionMetadata
from core.config import config
from core.constants import INTERVIEW_RESULT_PROMPT, KNOWLEDGE_EVALUATION_PROMPT, METADATA_ENRICHMENT_PROMPT, PERSONALIZATION_PROMPT, EVALUATION_PROMPT
from ollama import chat
import json
import re
from logging import getLogger

logger = getLogger(__name__)
class GeminiService:
    def __init__(self):
        self.client = genai.Client(
            api_key=config.gemini_api_key
        )
        self.OLLAMA_MODEL = "qwen2.5:3b"

    def generate_resume_context(self, prompt: str) -> ResumeContext:
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ResumeContext
                }
            )
            return response.parsed
        except Exception as e:
            raise RuntimeError(f"Failed to generate resume context: {e}")

    def _parse_ollama_json(self, response: str) -> dict:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        response = response.replace('\u201c', '"').replace('\u201d', '"')
        response = response.replace('\u2018', "'").replace('\u2019', "'")
        response = response.replace('\u2013', '-').replace('\u2014', '-')
        
        try:
            # First attempt: direct parsing
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed on first attempt: {e}")
            logger.debug(f"Response length: {len(response)}, First 500 chars: {response[:500]}")
            
            # Strategy 1: Process character by character, escaping control chars in strings
            result = []
            in_string = False
            escape_next = False
            
            for char in response:
                if escape_next:
                    result.append(char)
                    escape_next = False
                    continue
                
                if char == '\\':
                    result.append(char)
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    result.append(char)
                    continue
                
                # If we're in a string and encounter a control character, escape it
                if in_string:
                    if char == '\n':
                        result.append('\\n')
                    elif char == '\r':
                        result.append('\\r')
                    elif char == '\t':
                        result.append('\\t')
                    elif ord(char) < 32:  # Other control characters
                        result.append(f'\\u{ord(char):04x}')
                    else:
                        result.append(char)
                else:
                    result.append(char)
            
            fixed_response = ''.join(result)
            
            try:
                logger.debug("Attempting parse after control char fix")
                return json.loads(fixed_response)
            except json.JSONDecodeError as e2:
                logger.warning(f"Control char fix didn't work: {e2}")
                
                # Strategy 2: Try to fix common JSON formatting issues
                # Extract just the JSON object/array
                start_idx = max(fixed_response.find('{'), fixed_response.find('['))
                end_idx = max(fixed_response.rfind('}'), fixed_response.rfind(']'))
                
                if start_idx >= 0 and end_idx > start_idx:
                    fixed_response = fixed_response[start_idx:end_idx+1]
                    logger.debug("Extracted JSON content, attempting parse")
                    
                    try:
                        return json.loads(fixed_response)
                    except json.JSONDecodeError as e3:
                        logger.warning(f"JSON extraction didn't work: {e3}")
                        logger.debug(f"Extracted response: {fixed_response[:500]}")
                        raise RuntimeError(f"Failed to parse JSON from LLM after multiple attempts: {e3}")

    def enrich_questions_metadata(self, questions: list[dict]) -> QuestionMetadataBatch:
        try:
            questions_text = "\n\n".join(
                f"ID: {q['id']}\nQuestion: {q['question_text']}\nExpected Answer: {q['expected_answer']}"
                for q in questions
            )
            prompt = METADATA_ENRICHMENT_PROMPT.format(questions_text=questions_text)

            response = chat(
                model=self.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response["message"]["content"]
            logger.info(f"Raw ollama response: {raw[:200]}")
            json_data = self._parse_ollama_json(raw)
            return QuestionMetadataBatch.model_validate(json_data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in metadata enrichment: {e}")
            raise RuntimeError(f"Failed to enrich metadata: Invalid JSON from LLM")
        except RuntimeError as e:
            logger.error(f"Runtime error in metadata enrichment: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in enrich_questions_metadata: {e}")
            raise RuntimeError(f"Failed to enrich metadata: {e}")
        
    def get_personalized_questions(
        self,
        questions: list[dict],
        resume_context: dict
    ) -> PersonalizedQuestionBatch:
        try:
            question_block = "\n\n".join(
                f"ID: {q['id']}\nQuestion: {q['question_text']}\nExpected Answer: {q['expected_answer']}"
                for q in questions
            )
            prompt = PERSONALIZATION_PROMPT.format(
                resume_context=json.dumps(resume_context, indent=2),
                question_block=question_block
            )
            response = chat(
                model=self.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response["message"]["content"]
            logger.info(f"Personalization raw response: {raw[:200]}")
            json_data = self._parse_ollama_json(raw)
            return PersonalizedQuestionBatch.model_validate(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in personalization: {e}")
            raise RuntimeError(f"Failed to personalize questions: Invalid JSON from LLM")
        except RuntimeError as e:
            logger.error(f"Runtime error in personalization: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_personalized_questions: {e}")
            raise RuntimeError(f"Failed to personalize questions: {e}")
    
    def get_question_evaluation(
        self,
        interview_question_id: int,
        interview_context: dict,
        question: str,
        user_answer: str,
        is_personalized: bool,
        expected_answer: str,
    ):
        # interview_question_id: int
        # user_answer: str
        # expected_answer: str
        # score: float
        # feedback: str
        try:
            if is_personalized:
                prompt = EVALUATION_PROMPT.format(
                    interview_context=json.dumps(interview_context, indent=2),
                    question=question,
                    user_answer=user_answer
                )
            else:
                prompt = KNOWLEDGE_EVALUATION_PROMPT.format(
                    question=question,
                    expected_answer=expected_answer,
                    user_answer=user_answer
                )
            response = chat(
                model=self.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response["message"]["content"]
            logger.info(f"Raw ollama response: {raw[:200]}")
            json_data = self._parse_ollama_json(raw)
            return EvaluationResult.model_validate(json_data)

        except Exception as e:
            raise RuntimeError(f"Failed to evaluate answer: {e}")
        

    def get_interview_evaluation(
        self,
        interview_id: int,
        interview_context: dict,
        evaluation_results: list[EvaluationResult]
    ):
        try:
            serialized_results = []
            for result in evaluation_results:
                if hasattr(result, "model_dump"):
                    serialized_results.append(result.model_dump())
                elif isinstance(result, dict):
                    serialized_results.append(result)
                elif hasattr(result, "dict"):
                    serialized_results.append(result.dict())
                else:
                    serialized_results.append(result)

            prompt = INTERVIEW_RESULT_PROMPT.format(
                interview_context=json.dumps(interview_context, indent=2),
                evaluation_data=json.dumps(serialized_results, indent=2)
            )
            response = chat(
                model=self.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response["message"]["content"]
            logger.info(f"Raw ollama response: {raw[:200]}")
            json_data = self._parse_ollama_json(raw)
            return InterviewResponse.model_validate(json_data)
        except Exception as e:
            raise RuntimeError(f"Failed to evaluate interview: {e}")
