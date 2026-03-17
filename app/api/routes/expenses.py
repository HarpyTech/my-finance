from datetime import date
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
import logging

from app.api.deps import get_current_user
from app.models.expense import ExpenseCreate, ExpenseInputType
from app.services.expense_service import (
    add_expense,
    category_summary,
    list_expenses,
    monthly_summary,
    yearly_summary,
)
from app.services.expense_extraction_service import extract_expense_payload

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", status_code=201)
def create_expense(
    payload: ExpenseCreate,
    user: str = Depends(get_current_user),
):
    """Create a new expense"""
    logger.info("Create expense request received")
    try:
        result = add_expense(
            username=user,
            amount=payload.amount,
            category=payload.category,
            bill_type=payload.bill_type,
            input_type=payload.input_type,
            invoice_number=payload.invoice_number,
            vendor=payload.vendor,
            description=payload.description,
            expense_date=payload.expense_date,
            tax_details=payload.tax_details.model_dump(),
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


_MAX_IMAGE_BYTES = 6 * 1024 * 1024  # 6 MB


@router.post("/extract-and-create", status_code=201)
async def extract_and_create_expense(
    text_input: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    input_type: ExpenseInputType | None = Form(default=None),
    user: str = Depends(get_current_user),
):
    """Extract expense details with Gemini and insert into DB."""
    logger.info("Extract-and-create expense request received")
    try:
        image_bytes: bytes | None = None
        if image is not None:
            image_bytes = await image.read(_MAX_IMAGE_BYTES + 1)
            if len(image_bytes) > _MAX_IMAGE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image exceeds the {_MAX_IMAGE_BYTES // (1024 * 1024)} MB limit",
                )

        extracted = extract_expense_payload(
            text_input=text_input,
            image_bytes=image_bytes,
            image_mime_type=image.content_type if image else None,
        )

        result = add_expense(
            username=user,
            amount=extracted["amount"],
            category=extracted["category"],
            bill_type=extracted["bill_type"],
            input_type=input_type or _infer_input_type(text_input, image is not None),
            invoice_number=extracted["invoice_number"],
            vendor=extracted["vendor"],
            description=extracted["description"],
            expense_date=date.fromisoformat(extracted["expense_date"]),
            tax_details=extracted["tax_details"],
            line_items=extracted["line_items"],
        )

        logger.info("Expense extracted and created successfully")
        return {
            "expense": result,
            "extracted": extracted,
        }
    except ValueError as exc:
        logger.warning(f"Invalid extract-and-create request: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.error(f"Service error in extract-and-create: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error in extract-and-create: {str(exc)}",
            exc_info=True,
        )
        raise
    finally:
        if image is not None:
            await image.close()


def _infer_input_type(
    text_input: str | None,
    has_image: bool,
) -> ExpenseInputType:
    if text_input and has_image:
        return "mixed"
    if has_image:
        return "image"
    return "text"


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
