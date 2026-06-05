from fastapi import APIRouter
from apis.v1.auth import router as auth_router
from apis.v1.user import router as user_router
from apis.v1.interview import router as interview_router
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(interview_router)