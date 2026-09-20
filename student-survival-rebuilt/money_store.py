"""Single, tested data layer for Student Survival.

All financial pages use this module so validation and ownership rules cannot
drift apart. Existing JSON files remain compatible with earlier versions.
"""
from __future__ import annotations

from datetime import date
import json
import math
import os
import tempfile
import threading
import uuid


ROOT = os.path.dirname(os.path.abspath(__file__))
TRANSACTIONS_FILE = os.path.join(ROOT, "data.json")
ACCOUNTS_FILE = os.path.join(ROOT, "accounts.json")
RESERVE_FILE = os.path.join(ROOT, "emergency_reserve.json")
GOALS_FILE = os.path.join(ROOT, "goals.json")
NO_SPEND_FILE = os.path.join(ROOT, "no_spend_days.json")
CATEGORIES = ["อาหาร", "เดินทาง", "การเรียน", "ที่พัก", "ความบันเทิง", "สุขภาพ", "อื่น ๆ"]
LOCK = threading.RLock()


class MoneyError(ValueError):
    pass


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as file:
            value = json.load(file)
        return value
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def _write(path, value):
    directory = os.path.dirname(path)
    descriptor, temporary = tempfile.mkstemp(prefix="money-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _amount(value, label="จำนวนเงิน"):
    try:
        number = round(float(value), 2)
    except (TypeError, ValueError):
        raise MoneyError(f"{label}ต้องเป็นตัวเลข")
    if not math.isfinite(number) or number < 0:
        raise MoneyError(f"{label}ต้องไม่ติดลบ")
    return number


def _day(value):
    text = str(value or date.today().isoformat())
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise MoneyError("รูปแบบวันที่ไม่ถูกต้อง")
    if parsed > date.today():
        raise MoneyError("ยังบันทึกข้อมูลของวันที่ในอนาคตไม่ได้")
    return text


def _single_username():
    accounts = _read(ACCOUNTS_FILE, {})
    users = accounts.get("users", []) if isinstance(accounts, dict) else []
    names = [str(user.get("username", "")).strip() for user in users if isinstance(user, dict)]
    names = [name for name in names if name]
    return names[0] if len(names) == 1 else None


def _transactions():
    rows = _read(TRANSACTIONS_FILE, [])
    return rows if isinstance(rows, list) else []


def _migrate_transactions():
    rows = _transactions()
    owner = _single_username()
    changed = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not row.get("id"):
            row["id"] = uuid.uuid4().hex
            changed = True
        if not row.get("username") and owner:
            row["username"] = owner
            changed = True
    if changed:
        _write(TRANSACTIONS_FILE, rows)
    return rows


def transactions(username):
    if not username:
        return []
    with LOCK:
        rows = _migrate_transactions()
        owned = [dict(row) for row in rows if isinstance(row, dict) and row.get("username") == username]
    return sorted(owned, key=lambda row: (row.get("date", ""), row.get("id", "")), reverse=True)


def balance(username, rows=None):
    rows = transactions(username) if rows is None else rows
    total = 0.0
    for row in rows:
        amount = _amount(row.get("amount", 0))
        total += amount if row.get("type") == "income" else -amount
    return round(max(total, 0), 2)


def reserve(username):
    values = _read(RESERVE_FILE, {})
    entry = values.get(username, {}) if isinstance(values, dict) else {}
    return _amount(entry.get("saved", 0)), max(_amount(entry.get("target", 2000)), 1)


def usable_balance(username):
    saved, _ = reserve(username)
    return round(max(balance(username) - saved, 0), 2)


def add_transaction(username, kind, amount, category, description, day_value):
    if not username:
        raise MoneyError("กรุณาเข้าสู่ระบบก่อนบันทึกข้อมูล")
    kind = str(kind)
    if kind not in {"income", "expense"}:
        raise MoneyError("ประเภทรายการไม่ถูกต้อง")
    number = _amount(amount)
    if number <= 0:
        raise MoneyError("จำนวนเงินต้องมากกว่า 0")
    if kind == "expense" and number > usable_balance(username):
        raise MoneyError(f"เงินพร้อมใช้ไม่พอ เหลือใช้ได้ ฿{usable_balance(username):,.2f}")
    row = {
        "id": uuid.uuid4().hex,
        "username": username,
        "date": _day(day_value),
        "type": kind,
        "category": category if category in CATEGORIES else "อื่น ๆ",
        "amount": number,
        "description": str(description or "").strip()[:80],
    }
    with LOCK:
        rows = _migrate_transactions()
        rows.append(row)
        _write(TRANSACTIONS_FILE, rows)
    return row


def delete_transaction(username, transaction_id):
    with LOCK:
        rows = _migrate_transactions()
        target = next((row for row in rows if row.get("id") == transaction_id and row.get("username") == username), None)
        if not target:
            raise MoneyError("ไม่พบรายการที่ต้องการลบ")
        owned_after = [row for row in rows if row.get("username") == username and row is not target]
        saved, _ = reserve(username)
        if balance(username, owned_after) < saved:
            raise MoneyError("ลบไม่ได้ เพราะเงินที่เหลือจะไม่พอรองรับเงินสำรอง")
        rows.remove(target)
        _write(TRANSACTIONS_FILE, rows)


def save_reserve(username, saved_value, target_value):
    saved = _amount(saved_value, "เงินสำรอง")
    target = _amount(target_value, "เป้าหมาย")
    if target <= 0:
        raise MoneyError("เป้าหมายต้องมากกว่า 0")
    if saved > balance(username):
        raise MoneyError(f"เงินสำรองต้องไม่เกินยอดคงเหลือ ฿{balance(username):,.2f}")
    with LOCK:
        values = _read(RESERVE_FILE, {})
        values = values if isinstance(values, dict) else {}
        values[username] = {"saved": saved, "target": target}
        _write(RESERVE_FILE, values)


def goals(username):
    rows = _read(GOALS_FILE, [])
    rows = rows if isinstance(rows, list) else []
    return [dict(row) for row in rows if isinstance(row, dict) and row.get("username") == username]


def add_goal(username, name, target_value):
    name = str(name or "").strip()[:60]
    target = _amount(target_value, "เป้าหมาย")
    if not name or target <= 0:
        raise MoneyError("กรุณากรอกชื่อและเป้าหมายที่มากกว่า 0")
    with LOCK:
        rows = _read(GOALS_FILE, [])
        rows = rows if isinstance(rows, list) else []
        rows.append({"id": uuid.uuid4().hex, "username": username, "name": name, "target": target, "saved": 0, "created": date.today().isoformat()})
        _write(GOALS_FILE, rows)


def update_goal(username, goal_id, saved_value):
    saved = _amount(saved_value, "เงินที่เก็บ")
    with LOCK:
        rows = _read(GOALS_FILE, [])
        target = next((row for row in rows if row.get("id") == goal_id and row.get("username") == username), None)
        if not target:
            raise MoneyError("ไม่พบเป้าหมาย")
        if saved > _amount(target.get("target", 0)):
            raise MoneyError("เงินที่เก็บต้องไม่เกินยอดเป้าหมาย")
        target["saved"] = saved
        _write(GOALS_FILE, rows)


def delete_goal(username, goal_id):
    with LOCK:
        rows = _read(GOALS_FILE, [])
        target = next((row for row in rows if row.get("id") == goal_id and row.get("username") == username), None)
        if not target:
            raise MoneyError("ไม่พบเป้าหมาย")
        rows.remove(target)
        _write(GOALS_FILE, rows)


def no_spend_days(username):
    values = _read(NO_SPEND_FILE, {})
    days = values.get(username, []) if isinstance(values, dict) else []
    return sorted({str(day) for day in days}, reverse=True)


def record_no_spend(username, day_value):
    selected = _day(day_value)
    spent = sum(_amount(row.get("amount", 0)) for row in transactions(username) if row.get("type") == "expense" and row.get("date") == selected)
    if spent > 0:
        raise MoneyError("วันที่เลือกมีรายจ่าย จึงบันทึกเป็น No-Spend Day ไม่ได้")
    with LOCK:
        values = _read(NO_SPEND_FILE, {})
        values = values if isinstance(values, dict) else {}
        values[username] = sorted(set(values.get(username, [])) | {selected})
        _write(NO_SPEND_FILE, values)
