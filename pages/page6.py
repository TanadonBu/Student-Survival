"""Spending analysis page for Student Survival."""
from datetime import date
import storage
from flask import session
from models import StudentBudget

TITLE = "วิเคราะห์"
CATEGORIES = ["อาหาร", "เดินทาง", "การเรียน", "ที่พัก", "ความบันเทิง", "สุขภาพ", "อื่น ๆ"]


def _user_items(username):
    """เฉพาะรายการของ user ที่ login อยู่เท่านั้น (ไม่เห็นข้อมูลของ user คนอื่น)"""
    return [i for i in storage.load() if i.get("username") == username]


def build(query=None):
    items = _user_items(session.get("user"))
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
