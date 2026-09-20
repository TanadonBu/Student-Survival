"""Emergency Reserve dashboard for Student Survival."""
import json
import math
import os
import storage
from flask import session
from models import StudentBudget

TITLE = "Emergency Reserve"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "emergency_reserve.json")
DEFAULT_TARGET = 2000.0


def _user_items(username):
    """เฉพาะรายการของ user ที่ login อยู่เท่านั้น (ไม่เห็นข้อมูลของ user คนอื่น)"""
    return [i for i in storage.load() if i.get("username") == username]


def _load(username):
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        entry = data.get(username or "", {}) if isinstance(data, dict) else {}
        saved = max(float(entry.get("saved", 0)), 0)
        target = max(float(entry.get("target", DEFAULT_TARGET)), 1)
        return saved, target
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0, DEFAULT_TARGET


def _save(username, saved, target):
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        data = {}
    data[username or ""] = {"saved": round(saved, 2), "target": round(target, 2)}
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build(query=None):
    current_user = session.get("user")
    balance = StudentBudget(_user_items(current_user)).balance()
    saved, target = _load(current_user)
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
    if not session.get("user"):
        return "กรุณาเข้าสู่ระบบก่อนบันทึกข้อมูล"
    try:
        saved = float(form.get("saved", 0))
        target = float(form.get("target", DEFAULT_TARGET))
    except (TypeError, ValueError):
        return "กรุณากรอกจำนวนเงินเป็นตัวเลข"
    if not math.isfinite(saved) or not math.isfinite(target) or saved < 0 or target <= 0:
        return "เงินสำรองต้องไม่ติดลบ และเป้าหมายต้องมากกว่า 0"
    balance = StudentBudget(_user_items(session.get("user"))).balance()
    if saved > balance + 1e-9:
        return f"เงินสำรองต้องไม่เกินเงินคงเหลือ ฿{balance:,.2f}"
    _save(session.get("user"), saved, target)
    return "อัปเดต Emergency Reserve แล้ว"
