from datetime import date
from threading import Lock


_EXPENSES_BY_USER: dict[str, list[dict]] = {}
_COUNTER_BY_USER: dict[str, int] = {}
_LOCK = Lock()


def add_expense(username: str, amount: float, category: str, description: str, expense_date: date):
    with _LOCK:
        if username not in _EXPENSES_BY_USER:
            _EXPENSES_BY_USER[username] = []
            _COUNTER_BY_USER[username] = 1

        expense_id = _COUNTER_BY_USER[username]
        _COUNTER_BY_USER[username] += 1

        item = {
            "id": expense_id,
            "amount": round(float(amount), 2),
            "category": category.strip(),
            "description": description.strip(),
            "expense_date": expense_date.isoformat(),
        }
        _EXPENSES_BY_USER[username].append(item)
        return item


def list_expenses(username: str):
    return list(_EXPENSES_BY_USER.get(username, []))


def monthly_summary(username: str, year: int):
    summary: dict[int, float] = {m: 0.0 for m in range(1, 13)}
    for item in _EXPENSES_BY_USER.get(username, []):
        d = date.fromisoformat(item["expense_date"])
        if d.year == year:
            summary[d.month] += float(item["amount"])

    return [
        {"month": month, "total": round(total, 2)}
        for month, total in sorted(summary.items())
    ]


def yearly_summary(username: str):
    summary: dict[int, float] = {}
    for item in _EXPENSES_BY_USER.get(username, []):
        d = date.fromisoformat(item["expense_date"])
        summary[d.year] = summary.get(d.year, 0.0) + float(item["amount"])

    return [
        {"year": year, "total": round(total, 2)}
        for year, total in sorted(summary.items())
    ]


def category_summary(username: str, year: int | None = None, month: int | None = None):
    summary: dict[str, float] = {}
    for item in _EXPENSES_BY_USER.get(username, []):
        d = date.fromisoformat(item["expense_date"])
        if year is not None and d.year != year:
            continue
        if month is not None and d.month != month:
            continue
        summary[item["category"]] = summary.get(item["category"], 0.0) + float(item["amount"])

    return [
        {"category": category, "total": round(total, 2)}
        for category, total in sorted(summary.items(), key=lambda x: x[1], reverse=True)
    ]
