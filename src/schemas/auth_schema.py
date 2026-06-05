from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    
class RegiserUser(BaseModel):
    email: str
    password: str
    role: Optional[UserRole]
    phone_number: Optional[str]
    # resume_url: Optional[str]
    skills: Optional[List[str]]
    experience: Optional[float]
class LoginUser(BaseModel):
    email: str
    password: str
    role: Optional[UserRole]
    ip_address: str
    device: str
      