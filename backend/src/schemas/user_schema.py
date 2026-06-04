from typing import List, Optional
from pydantic import BaseModel


class UpdateProfile(BaseModel):
    phone_number: Optional[str]
    resume_url: Optional[str]
    skills: Optional[List[str]]
    experience: Optional[float]