from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
import logging

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
logger = logging.getLogger(__name__)


@router.post("", status_code=201)
def create_expense(payload: ExpenseCreate, user: str = Depends(get_current_user)):
    """Create a new expense"""
    logger.info("Create expense request received")
    try:
        result = add_expense(
            username=user,
            amount=payload.amount,
            category=payload.category,
            bill_type=payload.bill_type,
            vendor=payload.vendor,
            description=payload.description,
            expense_date=payload.expense_date,
            line_items=[item.model_dump() for item in payload.line_items],
        )
        logger.info("Expense created successfully")
        return result
    except RuntimeError as exc:
        logger.error(f"Service error creating expense: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error creating expense: {str(exc)}",
            exc_info=True,
        )
        raise


@router.get("")
def get_expenses(user: str = Depends(get_current_user)):
    """Get all expenses for the current user"""
    logger.info("Get expenses request received")
    try:
        result = {"items": list_expenses(user)}
        logger.info(f"Retrieved {len(result['items'])} expenses")
        return result
    except RuntimeError as exc:
        logger.error(f"Service error fetching expenses: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error fetching expenses: {str(exc)}",
            exc_info=True,
        )
        raise


@router.get("/summary/monthly")
def get_monthly_summary(
    year: int = Query(default=date.today().year, ge=2000, le=2100),
    user: str = Depends(get_current_user),
):
    """Get monthly expense summary"""
    logger.info(f"Monthly summary request for year: {year}")
    try:
        result = {"items": monthly_summary(user, year)}
        logger.info(f"Monthly summary retrieved for year {year}")
        return result
    except RuntimeError as exc:
        logger.error(f"Service error fetching monthly summary: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error fetching monthly summary: {str(exc)}",
            exc_info=True,
        )
        raise


@router.get("/summary/yearly")
def get_yearly_summary(user: str = Depends(get_current_user)):
    """Get yearly expense summary"""
    logger.info("Yearly summary request received")
    try:
        result = {"items": yearly_summary(user)}
        logger.info("Yearly summary retrieved")
        return result
    except RuntimeError as exc:
        logger.error(f"Service error fetching yearly summary: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error fetching yearly summary: {str(exc)}",
            exc_info=True,
        )
        raise


@router.get("/summary/categories")
def get_category_summary(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    user: str = Depends(get_current_user),
):
    """Get category-wise expense summary"""
    logger.info(f"Category summary request (year={year}, month={month})")
    try:
        result = {"items": category_summary(user, year=year, month=month)}
        logger.info(f"Category summary retrieved (year={year}, month={month})")
        return result
    except RuntimeError as exc:
        logger.error(f"Service error fetching category summary: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error fetching category summary: {str(exc)}",
            exc_info=True,
        )
        raise
