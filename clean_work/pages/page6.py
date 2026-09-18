"""Spending analysis page for Student Survival."""
from datetime import date
import storage
from models import StudentBudget

TITLE = "วิเคราะห์"
CATEGORIES = ["อาหาร", "เดินทาง", "การเรียน", "ที่พัก", "ความบันเทิง", "สุขภาพ", "อื่น ๆ"]


def build(query=None):
    items = storage.load()
    budget = StudentBudget(items)
    totals = budget.category_totals()
    total = sum(totals.values())
    rows = []
    for category in CATEGORIES:
        value = totals.get(category, 0)
        if value > 0:
            rows.append({"name": category, "value": value, "percent": value / total * 100 if total else 0})
    rows.sort(key=lambda x: x["value"], reverse=True)
    daily = budget.recent_daily_expense(7, date.today())
    return {"rows": rows, "total": total, "daily": list(daily.items()), "highest": rows[0] if rows else None}
