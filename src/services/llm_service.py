from google import genai
from schemas.interview_schema import ResumeContext
from core.config import config

class GeminiService:

    def __init__(self):
        self.client = genai.Client(
            api_key=config.gemini_api_key
        )

    def generate_resume_context(
        self,
        prompt: str
    ) -> ResumeContext:

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ResumeContext
            }
        )

        return response.parsed