from datetime import date
from pymongo.errors import PyMongoError

from app.db.mongo import get_expenses_collection


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

        return {
            "id": str(result.inserted_id),
            "amount": doc["amount"],
            "category": doc["category"],
            "bill_type": doc["bill_type"],
            "vendor": doc["vendor"],
            "description": doc["description"],
            "expense_date": expense_date.isoformat(),
            "line_items": doc["line_items"],
        }
    except PyMongoError as exc:
        raise RuntimeError("Failed to store expense due to database error") from exc


def list_expenses(username: str):
    try:
        expenses = get_expenses_collection()
        docs = expenses.find({"username": username}).sort("expense_date", -1)

        return [
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
    except PyMongoError as exc:
        raise RuntimeError("Failed to fetch expenses due to database error") from exc


def monthly_summary(username: str, year: int):
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

        return [{"month": m, "total": totals.get(m, 0.0)} for m in range(1, 13)]
    except PyMongoError as exc:
        raise RuntimeError("Failed to fetch monthly summary due to database error") from exc


def yearly_summary(username: str):
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
        return [
            {
                "year": row["_id"]["year"],
                "total": round(float(row["total"]), 2),
            }
            for row in result
        ]
    except PyMongoError as exc:
        raise RuntimeError("Failed to fetch yearly summary due to database error") from exc


def category_summary(username: str, year: int | None = None, month: int | None = None):
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
        return [
            {
                "category": row["_id"]["category"],
                "total": round(float(row["total"]), 2),
            }
            for row in result
        ]
    except PyMongoError as exc:
        raise RuntimeError("Failed to fetch category summary due to database error") from exc
