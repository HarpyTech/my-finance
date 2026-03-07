from fastapi import APIRouter, Depends, Request
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/me")
def read_profile(request: Request, user: str = Depends(get_current_user)):
    role = getattr(request.state, "role", None)
    return {"user": user, "role": role}
