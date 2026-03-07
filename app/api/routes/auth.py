from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.security import create_access_token
from app.services.auth_service import authenticate_user, register_user

router = APIRouter()


class RegisterRequest(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    username: EmailStr
    password: str


COOKIE_NAME = "access_token"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def api_register(payload: RegisterRequest):
    user = register_user(payload.username, payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    return {
        "message": "User registered successfully",
        "user": user,
    }

@router.post("/login")
async def api_login(request: Request, response: Response):
    """
    API login endpoint
    - Used by UI or API clients
    - Supports form and JSON requests
    - Returns JWT and sets session cookie
    """
    content_type = request.headers.get("content-type", "")
    username = ""
    password = ""

    if "application/json" in content_type:
        body = await request.json()
        payload = LoginRequest(**body)
        username = payload.username
        password = payload.password
    else:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username and password are required",
        )

    user = authenticate_user(username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "username": user["username"],
        "role": user["role"]
    })

    _set_session_cookie(response, token)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"]
    }


@router.post("/logout")
def api_logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out"}


@router.get("/session")
def api_session(request: Request):
    user = getattr(request.state, "user", None)
    role = getattr(request.state, "role", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return {
        "authenticated": True,
        "user": user,
        "role": role,
    }


@router.get("/csrf")
def get_csrf_token(request: Request):
    token = request.cookies.get("csrf_token")
    return {"csrf_token": token}
