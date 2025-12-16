from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

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
# @router.post("/login")
# def login(
#     request: Request,
#     username: str = Form(...),
#     password: str = Form(...)
# ):
#     # 🔐 Replace with real auth later
#     if username == "admin" and password == "admin":
#         return RedirectResponse(url="/home", status_code=302)

#     return templates.TemplateResponse(
#         "login.html",
#         {
#             "request": request,
#             "error": "Invalid username or password"
#         }
#     )

# --------------------
# Home Page
# --------------------
@router.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": "admin"}
    )
