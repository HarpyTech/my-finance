from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --------------------
# Root → Login page
# --------------------
@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

# --------------------
# Handle Login
# --------------------
@router.post("/login")
def web_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    # Call API login internally
    response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={"username": username, "password": password}
    )

    if response.status_code != 200:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"}
        )

    token = response.json()["access_token"]

    redirect = RedirectResponse("/home", status_code=302)
    redirect.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax"
    )
    return redirect
# --------------------
# Home Page
# --------------------
@router.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": "admin"}
    )
