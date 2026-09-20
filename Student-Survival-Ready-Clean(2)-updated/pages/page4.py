"""No-Spend Day tracker for Student Survival."""
from datetime import date, timedelta
import json
import os
import storage
from flask import session
from models import StudentBudget

TITLE = "No-Spend Day"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "no_spend_days.json")


def _user_items(username):
    """เฉพาะรายการของ user ที่ login อยู่เท่านั้น (ไม่เห็นข้อมูลของ user คนอื่น)"""
    return [i for i in storage.load() if i.get("username") == username]


def _load_all():
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def _load(username):
    data = _load_all()
    days = data.get(username or "", [])
    return sorted(set(str(x) for x in days if isinstance(x, str)))


def _save(username, days):
    data = _load_all()
    data[username or ""] = sorted(set(days))
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _streak(no_spend, end=None):
    end = end or date.today()
    count = 0
    current = end
    while current.isoformat() in no_spend:
        count += 1
        current -= timedelta(days=1)
    return count


def build(query=None):
    current_user = session.get("user")
    items = _user_items(current_user)
    budget = StudentBudget(items)
    saved = set(_load(current_user))
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
    current_user = session.get("user")
    if not current_user:
        return "กรุณาเข้าสู่ระบบก่อนบันทึกข้อมูล"
    selected = str(form.get("date", "")).strip() or date.today().isoformat()
    try:
        selected_date = date.fromisoformat(selected)
    except ValueError:
        return "รูปแบบวันที่ไม่ถูกต้อง"
    if selected_date > date.today():
        return "ยังบันทึก No-Spend Day ของวันที่ในอนาคตไม่ได้"
    items = _user_items(current_user)
    expense = sum(float(x.get("amount", 0)) for x in items if x.get("type") == "expense" and str(x.get("date", "")) == selected)
    if expense > 0:
        return "วันนี้มีรายจ่าย จึงยังบันทึกเป็น No-Spend Day ไม่ได้"
    days = _load(current_user)
    if selected not in days:
        days.append(selected)
    _save(current_user, days)
    return "บันทึก No-Spend Day เรียบร้อย"
