"""Student Survival planning lab: transactions, what-if tools and emergency reserve."""
from datetime import date
import json
import os
import storage
from models import StudentBudget

TITLE = "การเงิน"
CATEGORIES = ["อาหาร", "เดินทาง", "การเรียน", "ที่พัก", "ความบันเทิง", "สุขภาพ", "อื่น ๆ"]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVE_FILE = os.path.join(HERE, "emergency_reserve.json")
DEFAULT_TARGET = 2000.0


def _load_reserve():
    try:
        with open(RESERVE_FILE, encoding="utf-8") as file:
            data = json.load(file)
        return max(float(data.get("saved", 0)), 0), max(float(data.get("target", DEFAULT_TARGET)), 1)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0, DEFAULT_TARGET


def _save_reserve(saved, target):
    with open(RESERVE_FILE, "w", encoding="utf-8") as file:
        json.dump({"saved": round(saved, 2), "target": round(target, 2)}, file, ensure_ascii=False, indent=2)


def build(query=None):
    items = storage.load()
    budget = StudentBudget(items)
    reserve_saved, reserve_target = _load_reserve()
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
    items = storage.load()

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
        items.append({
            "date": form.get("date") or date.today().isoformat(),
            "type": transaction_type,
            "category": category,
            "amount": amount,
            "description": note,
        })
        storage.save(items)
        return "เพิ่มรายการเรียบร้อย"

    if action == "delete":
        try:
            index = int(form.get("index", -1))
            ordered = sorted(items, key=lambda x: (x.get("date", ""), x.get("description", "")), reverse=True)
            if 0 <= index < len(ordered):
                target = ordered[index]
                items.remove(target)
                storage.save(items)
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
        _save_reserve(saved, target)
        return "อัปเดตเงินสำรองฉุกเฉินแล้ว"

    return ""
