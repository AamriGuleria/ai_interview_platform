from google import genai
from schemas.interview_schema import ResumeContext
from core.config import config
from schemas.interview_schema import QuestionMetadata

class GeminiService:

    def __init__(self):
        self.client = genai.Client(
            api_key=config.gemini_api_key
        )

    def generate_resume_context(
        self,
        prompt: str
    ) -> ResumeContext:
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
            raise RuntimeError(
                f"Failed to generate resume context: {e}"
            )

    async def enrich_question(
        self,
        question_id: int
    ):
        try:
            pass
        except Exception as e:
            raise RuntimeError(
                f"Failed to perform metadata enrichment: {e}"
            )
        
    def enrich_question_metadata(
        self,
        question_text: str,
        expected_answer: str
    ) -> QuestionMetadata:
        try:
            prompt = f"""
                Analyze this interview question.

                Question:
                {question_text}

                Expected Answer:
                {expected_answer}

                Return JSON only.

                Rules:

                difficulty must be one of:
                - Beginner
                - Intermediate
                - Advanced

                question_type must be one of:
                - Technical
                - Behavioral
                - Project
                - System Design
                - Scenario Based

                Return:

                {{
                "category": "",
                "difficulty": "",
                "skills": [],
                "question_type": ""
                }}
                """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": QuestionMetadata
                }
            )

            return response.parsed

        except Exception as e:
            raise RuntimeError(
                f"Failed to enrich question metadata: {e}"
            )