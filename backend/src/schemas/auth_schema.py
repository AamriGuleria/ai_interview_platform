from enum import Enum
from typing import Optional
from pydantic import BaseModel

class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    
class RegiserUser(BaseModel):
    email: str
    password: str
    role: Optional[UserRole]

class LoginUser(BaseModel):
    email: str
    password: str
    role: Optional[UserRole]
    ip_address: str
    device: str
      