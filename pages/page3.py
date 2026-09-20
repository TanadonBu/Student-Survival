"""Student Survival planning lab: transactions, what-if tools and emergency reserve."""
from datetime import date
import json
import os
import storage
from flask import session
from models import StudentBudget

TITLE = "การเงิน"
CATEGORIES = ["อาหาร", "เดินทาง", "การเรียน", "ที่พัก", "ความบันเทิง", "สุขภาพ", "อื่น ๆ"]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVE_FILE = os.path.join(HERE, "emergency_reserve.json")
DEFAULT_TARGET = 2000.0


def _user_items(username):
    """เฉพาะรายการของ user ที่ login อยู่เท่านั้น (ไม่เห็นข้อมูลของ user คนอื่น)"""
    return [i for i in storage.load() if i.get("username") == username]


def _load_reserve(username):
    try:
        with open(RESERVE_FILE, encoding="utf-8") as file:
            data = json.load(file)
        entry = data.get(username or "", {}) if isinstance(data, dict) else {}
        return max(float(entry.get("saved", 0)), 0), max(float(entry.get("target", DEFAULT_TARGET)), 1)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0, DEFAULT_TARGET


def _save_reserve(username, saved, target):
    try:
        with open(RESERVE_FILE, encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        data = {}
    data[username or ""] = {"saved": round(saved, 2), "target": round(target, 2)}
    with open(RESERVE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def build(query=None):
    current_user = session.get("user")
    items = _user_items(current_user)
    budget = StudentBudget(items)
    reserve_saved, reserve_target = _load_reserve(current_user)
    average = budget.average_daily_expense(7)
    recommended = max(DEFAULT_TARGET, average * 7)
    reserve_gap = max(reserve_target - reserve_saved, 0)
    return {
        "items": sorted(items, key=lambda x: (x.get("date", ""), x.get("description", "")), reverse=True),
        "balance": budget.balance(),
        "daily": budget.daily_limit(20),
        "today": budget.today_expense(),
        "average": average,
        "runway": budget.runway_days(7),
        "categories": CATEGORIES,
        "budget": sorted(budget.category_totals().items(), key=lambda pair: pair[1], reverse=True),
        "reserve_saved": reserve_saved,
        "reserve_target": reserve_target,
        "reserve_gap": reserve_gap,
        "reserve_progress": budget.goal_progress(reserve_target, reserve_saved),
        "recommended_reserve": recommended,
    }


def handle(form):
    action = str(form.get("action", "")).strip()
    if action not in {"add", "delete", "reserve"}:
        return ""
    current_user = session.get("user")
    all_items = storage.load()

    if action == "add":
        try:
            amount = float(form.get("amount", 0))
        except (TypeError, ValueError):
            return "กรุณากรอกจำนวนเงินเป็นตัวเลข"
        if amount <= 0:
            return "จำนวนเงินต้องมากกว่า 0"
        transaction_type = form.get("type", "expense")
        if transaction_type not in {"income", "expense"}:
            transaction_type = "expense"
        category = form.get("category", "อื่น ๆ")
        if category not in CATEGORIES:
            category = "อื่น ๆ"
        note = str(form.get("description", "")).strip()[:80]
        all_items.append({
            "date": form.get("date") or date.today().isoformat(),
            "type": transaction_type,
            "category": category,
            "amount": amount,
            "description": note,
            "username": current_user,
        })
        storage.save(all_items)
        return "เพิ่มรายการเรียบร้อย"

    if action == "delete":
        try:
            index = int(form.get("index", -1))
            # ดัชนีอ้างอิงจากรายการที่ผู้ใช้คนนี้เห็นเท่านั้น เพื่อไม่ให้ลบข้อมูลของ user อื่น
            own_items = [i for i in all_items if i.get("username") == current_user]
            ordered = sorted(own_items, key=lambda x: (x.get("date", ""), x.get("description", "")), reverse=True)
            if 0 <= index < len(ordered):
                target = ordered[index]
                all_items.remove(target)
                storage.save(all_items)
                return "ลบรายการแล้ว"
        except (TypeError, ValueError):
            pass
        return "ไม่พบรายการที่ต้องการลบ"

    if action == "reserve":
        try:
            saved = float(form.get("reserve_saved", 0))
            target = float(form.get("reserve_target", DEFAULT_TARGET))
        except (TypeError, ValueError):
            return "กรุณากรอกเงินสำรองและเป้าหมายเป็นตัวเลข"
        if saved < 0 or target <= 0:
            return "เงินสำรองต้องไม่ติดลบ และเป้าหมายต้องมากกว่า 0"
        _save_reserve(current_user, saved, target)
        return "อัปเดตเงินสำรองฉุกเฉินแล้ว"

    return ""
