"""Student Survival command center dashboard."""
from datetime import date, timedelta
import calendar
import json
import os
import storage
from flask import session
from models import StudentBudget

TITLE = "Dashboard"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVE_FILE = os.path.join(HERE, "emergency_reserve.json")
DEFAULT_RESERVE = {"saved": 0.0, "target": 2000.0}


def _user_items(username):
    """เฉพาะรายการของ user ที่ login อยู่เท่านั้น (ไม่เห็นข้อมูลของ user คนอื่น)"""
    return [i for i in storage.load() if i.get("username") == username]


def _load_reserve(username):
    try:
        with open(RESERVE_FILE, encoding="utf-8") as file:
            data = json.load(file)
        entry = data.get(username or "", DEFAULT_RESERVE) if isinstance(data, dict) else DEFAULT_RESERVE
        return max(float(entry.get("saved", 0)), 0), max(float(entry.get("target", 2000)), 1)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0, 2000.0



def build(query=None):
    current_user = session.get("user")
    items = _user_items(current_user)
    budget = StudentBudget(items)
    today = date.today()
    month = today.strftime("%Y-%m")
    month_items = [x for x in items if str(x.get("date", ""))[:7] == month]
    income = sum(float(x.get("amount", 0)) for x in items if x.get("type") == "income")
    expense = sum(float(x.get("amount", 0)) for x in items if x.get("type") == "expense")
    month_income = sum(float(x.get("amount", 0)) for x in month_items if x.get("type") == "income")
    month_expense = sum(float(x.get("amount", 0)) for x in month_items if x.get("type") == "expense")

    categories = {}
    for item in month_items:
        if item.get("type") == "expense":
            category = item.get("category", "อื่น ๆ")
            categories[category] = categories.get(category, 0) + float(item.get("amount", 0))
    top_categories = sorted(categories.items(), key=lambda pair: pair[1], reverse=True)

    daily = budget.recent_daily_expense(7, today)
    daily_chart = []
    thai_days = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
    for day_key, amount in daily.items():
        day = date.fromisoformat(day_key)
        daily_chart.append({
            "label": f"{thai_days[day.weekday()]} {day.day}",
            "amount": amount,
        })

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_left = max(days_in_month - today.day + 1, 1)
    today_spend = budget.today_expense(today.isoformat())
    daily_limit = budget.daily_limit(days_left)
    average_7 = budget.average_daily_expense(7)
    runway = budget.runway_days(7)
    projected_month = (month_expense / today.day * days_in_month) if today.day else month_expense
    budget_used = (today_spend / daily_limit * 100) if daily_limit > 0 else 0
    budget_used = min(budget_used, 100)
    status = "อยู่ในงบวันนี้" if today_spend <= daily_limit else "ใช้เกินงบวันนี้"

    recent = sorted(items, key=lambda x: (x.get("date", ""), x.get("description", "")), reverse=True)[:6]
    reserve_saved, reserve_target = _load_reserve(current_user)
    usable_after_reserve = max(budget.balance() - reserve_saved, 0)
    no_spend_days = sum(1 for amount in daily.values() if amount == 0)
    reserve_progress = min(reserve_saved / reserve_target * 100, 100) if reserve_target > 0 else 0
    return {
        "income": income,
        "expense": expense,
        "balance": budget.balance(),
        "month_income": month_income,
        "month_expense": month_expense,
        "month_balance": month_income - month_expense,
        "top_categories": top_categories,
        "daily_chart": daily_chart,
        "recent": recent,
        "count": len(items),
        "today_spend": today_spend,
        "daily_limit": daily_limit,
        "days_left": days_left,
        "average_7": average_7,
        "runway": runway,
        "projected_month": projected_month,
        "budget_used": budget_used,
        "status": status,
        "today_label": today.strftime("%d/%m/%Y"),
        "reserve_saved": reserve_saved,
        "reserve_target": reserve_target,
        "reserve_progress": reserve_progress,
        "usable_after_reserve": usable_after_reserve,
        "no_spend_days": no_spend_days,
    }
