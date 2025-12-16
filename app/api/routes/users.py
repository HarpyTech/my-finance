from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/me")
def read_profile(user: str = Depends(get_current_user)):
    return {"user": user, "role": "admin"}
