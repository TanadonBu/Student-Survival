"""No-Spend Day tracker for Student Survival."""
from datetime import date, timedelta
import json
import os
import storage
from models import StudentBudget

TITLE = "No-Spend Day"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "no_spend_days.json")


def _load():
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        return sorted(set(str(x) for x in data if isinstance(x, str)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return []


def _save(days):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(set(days)), f, ensure_ascii=False, indent=2)


def _streak(no_spend, end=None):
    end = end or date.today()
    count = 0
    current = end
    while current.isoformat() in no_spend:
        count += 1
        current -= timedelta(days=1)
    return count


def build(query=None):
    items = storage.load()
    budget = StudentBudget(items)
    saved = set(_load())
    today = date.today()
    recent = budget.recent_daily_expense(14, today)
    actual_no_spend = [day for day, amount in recent.items() if amount == 0]
    total_recorded = len(saved)
    streak = _streak(saved, today)
    return {
        "today": today.isoformat(),
        "today_spend": budget.today_expense(today.isoformat()),
        "total_recorded": total_recorded,
        "streak": streak,
        "recent": list(recent.items())[::-1],
        "actual_no_spend": actual_no_spend,
        "saved": sorted(saved, reverse=True),
    }


def handle(form):
    action = str(form.get("action", "")).strip()
    if action != "record":
        return ""
    selected = str(form.get("date", "")).strip() or date.today().isoformat()
    try:
        date.fromisoformat(selected)
    except ValueError:
        return "รูปแบบวันที่ไม่ถูกต้อง"
    items = storage.load()
    expense = sum(float(x.get("amount", 0)) for x in items if x.get("type") == "expense" and str(x.get("date", "")) == selected)
    if expense > 0:
        return "วันนี้มีรายจ่าย จึงยังบันทึกเป็น No-Spend Day ไม่ได้"
    days = _load()
    if selected not in days:
        days.append(selected)
    _save(days)
    return "บันทึก No-Spend Day เรียบร้อย"
