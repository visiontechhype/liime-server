from fastapi import APIRouter
from schemas import UserResponse, ChatResponse, MessageResponse

router = APIRouter()

@router.get("/api/status", response_model=dict)
async def get_status():
    return {"status": "online", "version": "1.0.0"}

@router.get("/api/test")
async def test_endpoint():
    return {"message": "Server is working!", "status": "ok"}
