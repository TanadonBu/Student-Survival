"""Financial goals page for Student Survival."""
from datetime import date
import json
import os

TITLE = "เป้าหมาย"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "goals.json")


def _load():
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return []


def _save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build(query=None):
    goals = _load()
    for goal in goals:
        target = max(float(goal.get("target", 0)), 0)
        saved = max(float(goal.get("saved", 0)), 0)
        goal["progress"] = min(saved / target * 100, 100) if target else 0
        goal["gap"] = max(target - saved, 0)
    return {"goals": goals}


def handle(form):
    action = str(form.get("action", "")).strip()
    goals = _load()
    if action == "add":
        name = str(form.get("name", "")).strip()[:60]
        try:
            target = float(form.get("target", 0))
        except (TypeError, ValueError):
            return "กรุณากรอกเป้าหมายเป็นตัวเลข"
        if not name or target <= 0:
            return "กรุณากรอกชื่อเป้าหมายและจำนวนเงินที่มากกว่า 0"
        goals.append({"name": name, "target": target, "saved": 0, "created": date.today().isoformat()})
        _save(goals)
        return "เพิ่มเป้าหมายแล้ว"
    if action == "update":
        try:
            index = int(form.get("index", -1))
            saved = float(form.get("saved", 0))
        except (TypeError, ValueError):
            return "ข้อมูลเป้าหมายไม่ถูกต้อง"
        if 0 <= index < len(goals) and saved >= 0:
            goals[index]["saved"] = saved
            _save(goals)
            return "อัปเดตเป้าหมายแล้ว"
        return "ไม่พบเป้าหมาย"
    if action == "delete":
        try:
            index = int(form.get("index", -1))
        except (TypeError, ValueError):
            return "ไม่พบเป้าหมาย"
        if 0 <= index < len(goals):
            goals.pop(index)
            _save(goals)
            return "ลบเป้าหมายแล้ว"
        return "ไม่พบเป้าหมาย"
    return ""
