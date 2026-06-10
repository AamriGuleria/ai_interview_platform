from google import genai
from schemas.interview_schema import QuestionMetadataBatch, ResumeContext
from core.config import config
from schemas.interview_schema import QuestionMetadata
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
        self.MODEL = "qwen2.5:3b"

    def generate(
        self,
        prompt: str
    ) -> str:

        response = chat(
            model=self.MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]
    def _fix_json_response(self, response: str) -> str:
        """Fix common JSON issues in LLM responses"""
        # Fix em dashes and en dashes with regular hyphens
        response = response.replace('–', '-').replace('—', '-')
        # Fix smart quotes with regular quotes
        response = response.replace('"', '"').replace('"', '"')
        response = response.replace(''', "'").replace(''', "'")
        # Remove percentage signs and other non-JSON characters
        response = re.sub(r'(\d+(?:\.\d+)?)%', r'"\1%"', response)
        # Fix unquoted values like "Not specified"
        response = re.sub(r': (Not specified)', r': "\1"', response)
        return response

    def generate_resume_context(
        self,
        prompt: str
    ) -> ResumeContext:

        try:
            response = self.generate(prompt)
            logger.info(f"Raw LLM response: '{response}'")
            
            if not response or not response.strip():
                raise ValueError("Empty response from LLM")
            
            # Try to extract JSON from response if it contains extra text
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # Fix common JSON issues
            response = self._fix_json_response(response)
            logger.info(f"Fixed JSON response: '{response}'")
            
            json_data = json.loads(response)
            logger.info(f"Data returned by llm is {json_data}")
            return ResumeContext.model_validate(
                json_data
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error. Response was: '{response}'. Error: {e}")
            raise RuntimeError(
                f"Failed to generate resume context: Invalid JSON response from LLM"
            )
        except Exception as e:
            logger.error(f"General error in generate_resume_context: {e}")
            raise RuntimeError(
                f"Failed to generate resume context: {e}"
            )
        
    def enrich_questions_metadata(
        self,
        questions: list[dict]
    ) -> QuestionMetadataBatch:
        try:
            questions_text = "\n\n".join(
                f"""
                ID: {q['id']}
                Question: {q['question_text']}
                Expected Answer: {q['expected_answer']}
                """
                for q in questions
            )
            prompt = f"""
            You are an interview metadata classifier.

            Return ONLY VALID JSON.

            Questions:

            {questions_text}

            Output format:

            {{
                "questions": [
                    {{
                        "id": 1,
                        "category": "Python",
                        "difficulty": "Intermediate",
                        "skills": ["Python"],
                        "question_type": "Technical"
                    }}
                ]
            }}

            Rules:

            difficulty:
            - Beginner
            - Intermediate
            - Advanced

            question_type:
            - Technical
            - Behavioral
            - Project
            - System Design
            - Scenario Based

            Return JSON only.
            """

            response = self.generate(prompt)
            logger.info(f"Raw metadata response: '{response}'")
            
            if not response or not response.strip():
                raise ValueError("Empty response from LLM")
            
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # Fix common JSON issues
            response = self._fix_json_response(response)

            json_data = json.loads(response)

            return (
                QuestionMetadataBatch
                .model_validate(
                    json_data
                )
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in metadata. Response: '{response}'. Error: {e}")
            raise RuntimeError(
                f"Failed to enrich metadata: Invalid JSON response from LLM"
            )
        except Exception as e:
            logger.error(f"General error in enrich_questions_metadata: {e}")
            raise RuntimeError(
                f"Failed to enrich metadata: {e}"
            )
