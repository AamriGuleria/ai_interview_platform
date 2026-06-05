from fastapi import Depends, HTTPException
from passlib.context import CryptContext

from schemas.auth_schema import UserRole


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str)-> str:
    return pwd_context.hash(password)

def verify_password(raw_password: str, hashed_password: str)-> bool:
    return pwd_context.verify(raw_password, hashed_password)


# RBAC constraint
# def get_current_user():
#     pass
# def require_admin(current_user=Depends(get_current_user)):
#     if current_user != UserRole.ADMIN:
#         raise HTTPException(
#             status_code=403,
#             detail="Admin access required"
#         )
#     return current_user