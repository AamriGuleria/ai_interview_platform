from google import genai
from schemas.interview_schema import QuestionMetadataBatch, ResumeContext, QuestionMetadata
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
        return json.loads(response)

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
        except Exception as e:
            logger.error(f"Error in enrich_questions_metadata: {e}")
            raise RuntimeError(f"Failed to enrich metadata: {e}")
        
    def get_personalized_questions(self, questions: list[dict], resume_context: json):
        #  id
        # question_text
        # expected_answer
        # category
        # difficulty
        # skills
        # question_type
        # source
        pass