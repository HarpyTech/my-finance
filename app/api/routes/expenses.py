from datetime import date
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.services.expense_service import (
    add_expense,
    category_summary,
    list_expenses,
    monthly_summary,
    yearly_summary,
)

router = APIRouter()


class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str = Field(min_length=2, max_length=64)
    description: str = Field(default="", max_length=255)
    expense_date: date


@router.post("", status_code=201)
def create_expense(payload: ExpenseCreate, user: str = Depends(get_current_user)):
    return add_expense(
        username=user,
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        expense_date=payload.expense_date,
    )


@router.get("")
def get_expenses(user: str = Depends(get_current_user)):
    return {"items": list_expenses(user)}


@router.get("/summary/monthly")
def get_monthly_summary(
    year: int = Query(default=date.today().year, ge=2000, le=2100),
    user: str = Depends(get_current_user),
):
    return {"items": monthly_summary(user, year)}


@router.get("/summary/yearly")
def get_yearly_summary(user: str = Depends(get_current_user)):
    return {"items": yearly_summary(user)}


@router.get("/summary/categories")
def get_category_summary(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    user: str = Depends(get_current_user),
):
    return {"items": category_summary(user, year=year, month=month)}
