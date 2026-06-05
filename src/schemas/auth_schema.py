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
    role: Optional[UserRole] = None
    phone_number: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[float] = None
class LoginUser(BaseModel):
    email: str
    password: str
    ip_address: str
    device: str
      