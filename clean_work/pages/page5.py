"""Emergency Reserve dashboard for Student Survival."""
import json
import os
import storage
from models import StudentBudget

TITLE = "Emergency Reserve"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "emergency_reserve.json")
DEFAULT_TARGET = 2000.0


def _load():
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        saved = max(float(data.get("saved", 0)), 0)
        target = max(float(data.get("target", DEFAULT_TARGET)), 1)
        return saved, target
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0, DEFAULT_TARGET


def _save(saved, target):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"saved": round(saved, 2), "target": round(target, 2)}, f, ensure_ascii=False, indent=2)


def build(query=None):
    balance = StudentBudget(storage.load()).balance()
    saved, target = _load()
    progress = min(saved / target * 100, 100)
    gap = max(target - saved, 0)
    usable = max(balance - saved, 0)
    return {
        "balance": balance,
        "saved": saved,
        "target": target,
        "progress": progress,
        "gap": gap,
        "usable": usable,
        "safety_ratio": min(saved / max(balance, 1) * 100, 100),
    }


def handle(form):
    if str(form.get("action", "")).strip() != "save":
        return ""
    try:
        saved = float(form.get("saved", 0))
        target = float(form.get("target", DEFAULT_TARGET))
    except (TypeError, ValueError):
        return "กรุณากรอกจำนวนเงินเป็นตัวเลข"
    if saved < 0 or target <= 0:
        return "เงินสำรองต้องไม่ติดลบ และเป้าหมายต้องมากกว่า 0"
    _save(saved, target)
    return "อัปเดต Emergency Reserve แล้ว"
