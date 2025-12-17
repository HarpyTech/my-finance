from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.services.auth_service import authenticate_user

router = APIRouter()

@router.post("/login")
def api_login(form: OAuth2PasswordRequestForm = Depends()):
    """
    API login endpoint
    - Used by UI or API clients
    - Returns JWT only (NO redirects, NO HTML)
    """
    user = authenticate_user(form.username, form.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "username": user["username"],
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"]
    }
