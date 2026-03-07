from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.expense import ExpenseCreate
from app.services.expense_service import (
    add_expense,
    category_summary,
    list_expenses,
    monthly_summary,
    yearly_summary,
)

router = APIRouter()


@router.post("", status_code=201)
def create_expense(payload: ExpenseCreate, user: str = Depends(get_current_user)):
    try:
        return add_expense(
            username=user,
            amount=payload.amount,
            category=payload.category,
            bill_type=payload.bill_type,
            vendor=payload.vendor,
            description=payload.description,
            expense_date=payload.expense_date,
            line_items=[item.model_dump() for item in payload.line_items],
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("")
def get_expenses(user: str = Depends(get_current_user)):
    try:
        return {"items": list_expenses(user)}
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/summary/monthly")
def get_monthly_summary(
    year: int = Query(default=date.today().year, ge=2000, le=2100),
    user: str = Depends(get_current_user),
):
    try:
        return {"items": monthly_summary(user, year)}
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/summary/yearly")
def get_yearly_summary(user: str = Depends(get_current_user)):
    try:
        return {"items": yearly_summary(user)}
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/summary/categories")
def get_category_summary(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    user: str = Depends(get_current_user),
):
    try:
        return {"items": category_summary(user, year=year, month=month)}
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
