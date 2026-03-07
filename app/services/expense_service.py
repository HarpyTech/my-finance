from datetime import date
from pymongo.errors import PyMongoError
import logging

from app.db.mongo import get_expenses_collection

logger = logging.getLogger(__name__)


def add_expense(
    username: str,
    amount: float,
    category: str,
    bill_type: str,
    vendor: str,
    description: str,
    expense_date: date,
    line_items: list[dict] | None = None,
):
    """Add a new expense for a user"""
    logger.info(
        f"Adding expense for user {username}: "
        f"${amount} - {category} - {vendor} on {expense_date}"
    )
    try:
        expenses = get_expenses_collection()
        doc = {
            "username": username,
            "amount": round(float(amount), 2),
            "category": category.strip().lower(),
            "bill_type": bill_type.strip().lower(),
            "vendor": vendor.strip(),
            "description": description.strip(),
            "expense_date": expense_date,
            "line_items": line_items or [],
        }
        result = expenses.insert_one(doc)

        expense_id = str(result.inserted_id)
        logger.info(f"Expense added successfully with ID: {expense_id}")

        return {
            "id": expense_id,
            "amount": doc["amount"],
            "category": doc["category"],
            "bill_type": doc["bill_type"],
            "vendor": doc["vendor"],
            "description": doc["description"],
            "expense_date": expense_date.isoformat(),
            "line_items": doc["line_items"],
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error while adding expense for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to store expense due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while adding expense for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise


def list_expenses(username: str):
    """List all expenses for a user"""
    logger.debug("Fetching all expenses for user")
    try:
        expenses = get_expenses_collection()
        docs = expenses.find({"username": username}).sort("expense_date", -1)

        result = [
            {
                "id": str(doc["_id"]),
                "amount": round(float(doc.get("amount", 0)), 2),
                "category": doc.get("category", "other"),
                "bill_type": doc.get("bill_type", "other"),
                "vendor": doc.get("vendor", ""),
                "description": doc.get("description", ""),
                "expense_date": doc["expense_date"].isoformat(),
                "line_items": doc.get("line_items", []),
            }
            for doc in docs
        ]
        logger.info(f"Retrieved {len(result)} expenses")
        return result
    except PyMongoError as exc:
        logger.error(
            f"Database error while fetching expenses: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to fetch expenses due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while fetching expenses for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise


def monthly_summary(username: str, year: int):
    """Get monthly expense summary for a user for a specific year"""
    logger.debug(f"Fetching monthly summary for year {year}")
    try:
        expenses = get_expenses_collection()
        start = date(year, 1, 1)
        end = date(year + 1, 1, 1)
        pipeline = [
            {
                "$match": {
                    "username": username,
                    "expense_date": {"$gte": start, "$lt": end},
                }
            },
            {
                "$group": {
                    "_id": {"month": {"$month": "$expense_date"}},
                    "total": {"$sum": "$amount"},
                }
            },
        ]
        result = list(expenses.aggregate(pipeline))
        totals = {row["_id"]["month"]: round(float(row["total"]), 2) for row in result}

        summary = [{"month": m, "total": totals.get(m, 0.0)} for m in range(1, 13)]
        total_year = sum(totals.values())
        logger.info(
            f"Monthly summary for year {year}: "
            f"Total ${total_year:.2f} across {len(totals)} months"
        )
        return summary
    except PyMongoError as exc:
        logger.error(
            f"Database error while fetching monthly summary "
            f"for user {username}, year {year}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            "Failed to fetch monthly summary due to database error"
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while fetching monthly summary "
            f"for user {username}, year {year}: {str(exc)}",
            exc_info=True,
        )
        raise


def yearly_summary(username: str):
    """Get yearly expense summary for a user"""
    logger.debug("Fetching yearly summary for user")
    try:
        expenses = get_expenses_collection()
        pipeline = [
            {"$match": {"username": username}},
            {
                "$group": {
                    "_id": {"year": {"$year": "$expense_date"}},
                    "total": {"$sum": "$amount"},
                }
            },
            {"$sort": {"_id.year": 1}},
        ]
        result = list(expenses.aggregate(pipeline))
        summary = [
            {
                "year": row["_id"]["year"],
                "total": round(float(row["total"]), 2),
            }
            for row in result
        ]
        logger.info(f"Yearly summary: {len(summary)} years of data")
        return summary
    except PyMongoError as exc:
        logger.error(
            f"Database error while fetching yearly summary "
            f"for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            "Failed to fetch yearly summary due to database error"
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while fetching yearly summary "
            f"for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise


def category_summary(username: str, year: int | None = None, month: int | None = None):
    """Get category-wise expense summary for a user"""
    period = f"year={year}, month={month}" if year else "all time"
    logger.debug(f"Fetching category summary for period: {period}")
    try:
        expenses = get_expenses_collection()
        match: dict = {"username": username}
        if year is not None:
            start_month = month if month is not None else 1
            end_month = month if month is not None else 12
            start = date(year, start_month, 1)
            if month is None:
                end = date(year + 1, 1, 1)
            else:
                end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
            match["expense_date"] = {"$gte": start, "$lt": end}

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {"category": "$category"},
                    "total": {"$sum": "$amount"},
                }
            },
            {"$sort": {"total": -1}},
        ]
        result = list(expenses.aggregate(pipeline))
        summary = [
            {
                "category": row["_id"]["category"],
                "total": round(float(row["total"]), 2),
            }
            for row in result
        ]
        logger.info(f"Category summary ({period}): " f"{len(summary)} categories")
        return summary
    except PyMongoError as exc:
        logger.error(
            f"Database error while fetching category summary "
            f"for user {username} ({period}): {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            "Failed to fetch category summary due to database error"
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while fetching category summary "
            f"for user {username} ({period}): {str(exc)}",
            exc_info=True,
        )
        raise
