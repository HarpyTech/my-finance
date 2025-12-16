from fastapi import APIRouter, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token

# from fastapi import APIRouter,  Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    # # Replace with DB validation
    # if form.username != "admin" or form.password != "admin":
    #     return {"error": "Invalid credentials"}

    # token = create_access_token(form.username)
    # return {"access_token": token, "token_type": "bearer"}
    # 🔐 Replace with real auth later
    if form.username == "admin" and form.password == "admin":
        return RedirectResponse(url="/home", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": "Invalid username or password"
        }
    )
