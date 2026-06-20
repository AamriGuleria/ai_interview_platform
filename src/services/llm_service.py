from google import genai
from schemas.interview_schema import EvaluationResult, PersonalizedQuestionBatch, QuestionMetadataBatch, ResumeContext, QuestionMetadata
from core.config import config
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
            prompt = f"""You are an interview metadata classifier.
            Return ONLY valid JSON, no explanation.

            Questions:
            {questions_text}

            Output format:
            {{
                "questions": [
                    {{
                        "id": <same id as input>,
                        "category": "<topic>",
                        "difficulty": "<Beginner|Intermediate|Advanced>",
                        "skills": ["skill1"],
                        "question_type": "<Technical|Behavioral|Project|System Design|Scenario Based>"
                    }}
                ]
            }}

            Return JSON only."""

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
            prompt = f"""You are an experienced technical interviewer.
Candidate Context:
{json.dumps(resume_context, indent=2)}

Questions:
{question_block}

Rewrite each question to be specific to the candidate's experience.
Rules:
1. Preserve the original intent and difficulty.
2. Reference candidate projects/technologies when relevant.
3. Do not invent fake experience.
4. Return one personalized question per id.

Return ONLY valid JSON:
{{
    "questions": [
        {{
            "id": <same id>,
            "personalized_question": "...",
            "personalized_expected_answer": "..."
        }}
    ]
}}"""
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
        user_answer: str
    ):
        # interview_question_id: int
        # user_answer: str
        # expected_answer: str
        # score: float
        # feedback: str
        try:
            prompt = f"""
            You are an expert technical interviewer evaluating candidate responses.
            Candidate Context:
            {json.dumps(interview_context, indent=2)}

            Question Asked:
            {question}

            Candidate's Answer:
            {user_answer}

            Evaluation Task:

            Score the answer from 0-100 based on:

            1. **Correctness** (40%): How accurate and complete is the answer?
            - 90-100: Completely correct, all key points covered
            - 70-89: Mostly correct, minor gaps
            - 50-69: Partially correct, some misunderstandings
            - 30-49: Limited correctness, significant gaps
            - 0-29: Mostly incorrect or irrelevant

            2. **Relevance** (30%): How well does it address the question?
            - Directly addresses the asked question
            - Uses candidate's experience/projects when applicable
            - Avoids tangential information

            3. **Depth** (20%): Does it show understanding?
            - Surface-level answers: Lower score
            - Demonstrates reasoning and trade-offs: Higher score
            - Shows awareness of context/constraints: Higher score

            4. **Communication** (10%): Is it clear and well-structured?
            - Clear explanation: Higher score
            - Organized thoughts: Higher score
            - Appropriate technical terminology: Higher score

            Scoring Guide:
            - 85-100: Excellent - Hire signal, strong technical knowledge
            - 70-84: Good - Meets expectations, acceptable
            - 50-69: Average - Some gaps, needs improvement
            - 30-49: Poor - Significant gaps, concerning
            - 0-29: Very Poor - Does not meet baseline

            Context Awareness:
            - Consider the candidate's experience level (from context)
            - Adjust expectations based on their background
            - Give credit for partially correct answers that show understanding
            - Consider if they're applying concepts from their own experience

            Return JSON only:

            {{
                "score": <float between 0-100>,
                "feedback": "<constructive feedback addressing: what was good, what was missing, suggestions for improvement>",
                "strengths": ["<key strength>"],
                "gaps": ["<area of improvement>"]
            }}

            Be fair but honest. Score should reflect true understanding, not just effort.
            """
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