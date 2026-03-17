from datetime import date, datetime, time
from pymongo.errors import PyMongoError
import logging

from app.db.mongo import (
    get_expense_line_items_collection,
    get_expenses_collection,
)

logger = logging.getLogger(__name__)


def _as_mongo_datetime(value: date) -> datetime:
    """Convert a date to a MongoDB-storable datetime at start of day."""
    return datetime.combine(value, time.min)


def add_expense(
    username: str,
    amount: float,
    category: str,
    bill_type: str,
    input_type: str,
    vendor: str,
    description: str,
    expense_date: date,
    tax_details: dict | None = None,
    line_items: list[dict] | None = None,
):
    """Add a new expense for a user"""
    logger.info(
        f"Adding expense for user {username}: "
        f"${amount} - {category} - {vendor} on {expense_date}"
    )
    try:
        expenses = get_expenses_collection()
        expense_line_items = get_expense_line_items_collection()

        normalized_tax = _normalize_tax_details(tax_details)
        normalized_items = line_items or []

        doc = {
            "username": username,
            "amount": round(float(amount), 2),
            "category": category.strip().lower(),
            "bill_type": bill_type.strip().lower(),
            "input_type": input_type.strip().lower(),
            "vendor": vendor.strip(),
            "description": description.strip(),
            "expense_date": _as_mongo_datetime(expense_date),
            "tax_details": normalized_tax,
            "line_items_count": len(normalized_items),
        }
        result = expenses.insert_one(doc)

        expense_id = str(result.inserted_id)

        if normalized_items:
            line_item_docs = [
                {
                    "expense_id": expense_id,
                    "username": username,
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total": item["total"],
                    "created_at": datetime.utcnow(),
                }
                for item in normalized_items
            ]
            expense_line_items.insert_many(line_item_docs)

        logger.info(f"Expense added successfully with ID: {expense_id}")

        return {
            "id": expense_id,
            "amount": doc["amount"],
            "category": doc["category"],
            "bill_type": doc["bill_type"],
            "input_type": doc["input_type"],
            "vendor": doc["vendor"],
            "description": doc["description"],
            "expense_date": expense_date.isoformat(),
            "tax_details": doc["tax_details"],
            "line_items": normalized_items,
        }
    except PyMongoError as exc:
        logger.error(
            ("Database error while adding expense for user " f"{username}: {str(exc)}"),
            exc_info=True,
        )
        raise RuntimeError("Failed to store expense due to database error") from exc
    except Exception as exc:
        logger.error(
            (
                "Unexpected error while adding expense for user "
                f"{username}: {str(exc)}"
            ),
            exc_info=True,
        )
        raise


def list_expenses(username: str):
    """List all expenses for a user"""
    logger.debug("Fetching all expenses for user")
    try:
        expenses = get_expenses_collection()
        expense_line_items = get_expense_line_items_collection()
        docs = list(expenses.find({"username": username}).sort("expense_date", -1))

        expense_ids = [str(doc["_id"]) for doc in docs]
        line_items_map: dict[str, list[dict]] = {
            expense_id: [] for expense_id in expense_ids
        }

        if expense_ids:
            cursor = expense_line_items.find(
                {
                    "username": username,
                    "expense_id": {"$in": expense_ids},
                },
                {
                    "_id": 0,
                    "expense_id": 1,
                    "name": 1,
                    "quantity": 1,
                    "unit_price": 1,
                    "total": 1,
                },
            )
            for item_doc in cursor:
                expense_id = item_doc.get("expense_id")
                if expense_id in line_items_map:
                    line_items_map[expense_id].append(
                        {
                            "name": item_doc.get("name", "item"),
                            "quantity": float(item_doc.get("quantity", 1)),
                            "unit_price": round(
                                float(item_doc.get("unit_price", 0)), 2
                            ),
                            "total": round(float(item_doc.get("total", 0)), 2),
                        }
                    )

        result = [
            {
                "id": str(doc["_id"]),
                "amount": round(float(doc.get("amount", 0)), 2),
                "category": doc.get("category", "other"),
                "bill_type": doc.get("bill_type", "other"),
                "input_type": doc.get("input_type", "manual"),
                "vendor": doc.get("vendor", ""),
                "description": doc.get("description", ""),
                "expense_date": doc["expense_date"].isoformat(),
                "tax_details": _normalize_tax_details(doc.get("tax_details")),
                "line_items": line_items_map.get(str(doc["_id"]), []),
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
            (
                "Unexpected error while fetching expenses for user "
                f"{username}: {str(exc)}"
            ),
            exc_info=True,
        )
        raise


def _normalize_tax_details(raw_tax_details: dict | None) -> dict:
    """Ensure all tax attributes are stored as explicit numeric fields."""
    raw = raw_tax_details or {}
    normalized = {
        "subtotal": _float_or_zero(raw.get("subtotal")),
        "tax": _float_or_zero(raw.get("tax")),
        "cgst": _float_or_zero(raw.get("cgst")),
        "sgst": _float_or_zero(raw.get("sgst")),
        "igst": _float_or_zero(raw.get("igst")),
        "vat": _float_or_zero(raw.get("vat")),
        "service_tax": _float_or_zero(raw.get("service_tax")),
        "cess": _float_or_zero(raw.get("cess")),
        "tip": _float_or_zero(raw.get("tip")),
        "discount": _float_or_zero(raw.get("discount")),
        "total_tax": _float_or_zero(raw.get("total_tax")),
    }

    computed_total_tax = (
        normalized["cgst"]
        + normalized["sgst"]
        + normalized["igst"]
        + normalized["vat"]
        + normalized["service_tax"]
        + normalized["cess"]
    )

    if normalized["total_tax"] <= 0 and computed_total_tax > 0:
        normalized["total_tax"] = round(computed_total_tax, 2)

    if normalized["tax"] <= 0 and normalized["total_tax"] > 0:
        normalized["tax"] = normalized["total_tax"]

    return {key: round(value, 2) for key, value in normalized.items()}


def _float_or_zero(value) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def monthly_summary(username: str, year: int):
    """Get monthly expense summary for a user for a specific year"""
    logger.debug(f"Fetching monthly summary for year {year}")
    try:
        expenses = get_expenses_collection()
        start = _as_mongo_datetime(date(year, 1, 1))
        end = _as_mongo_datetime(date(year + 1, 1, 1))
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


def category_summary(
    username: str,
    year: int | None = None,
    month: int | None = None,
):
    """Get category-wise expense summary for a user"""
    period = f"year={year}, month={month}" if year else "all time"
    logger.debug(f"Fetching category summary for period: {period}")
    try:
        expenses = get_expenses_collection()
        match: dict = {"username": username}
        if year is not None:
            start_month = month if month is not None else 1
            start = _as_mongo_datetime(date(year, start_month, 1))
            if month is None:
                end = _as_mongo_datetime(date(year + 1, 1, 1))
            else:
                end_date = (
                    date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
                )
                end = _as_mongo_datetime(end_date)
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
