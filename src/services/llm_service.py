from google import genai
from schemas.interview_schema import QuestionMetadataBatch, ResumeContext
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

    def enrich_questions_metadata(
        self,
        questions: list[dict]
    ) -> QuestionMetadataBatch:
        try:
            questions_text = "\n\n".join(
                f"ID: {q['id']}\nQuestion: {q['question_text']}\nExpected Answer: {q['expected_answer']}"
                for q in questions
            )
            prompt = f"""
                Analyze the following interview questions and return metadata for each.

                {questions_text}

                Rules:
                difficulty must be one of: Beginner, Intermediate, Advanced
                question_type must be one of: Technical, Behavioral, Project, System Design, Scenario Based

                Return a JSON object with a 'questions' array where each item contains:
                id, category, difficulty, skills (list), question_type
                """
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": QuestionMetadataBatch
                }
            )
            return response.parsed
        except Exception as e:
            raise RuntimeError(
                f"Failed to enrich question metadata: {e}"
            )