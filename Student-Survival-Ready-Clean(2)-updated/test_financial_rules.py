"""Regression tests for realistic, non-negative financial rules."""
import json

import app as webapp
import storage
from pages import page3, page4, page5, page7


def _use_temp_files(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    data_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_FILE", str(data_file))
    monkeypatch.setattr(page3, "RESERVE_FILE", str(tmp_path / "reserve.json"))
    monkeypatch.setattr(page4, "FILE", str(tmp_path / "no-spend.json"))
    monkeypatch.setattr(page5, "FILE", str(tmp_path / "reserve.json"))
    monkeypatch.setattr(page7, "FILE", str(tmp_path / "goals.json"))


def test_expense_cannot_exceed_balance(tmp_path, monkeypatch):
    _use_temp_files(tmp_path, monkeypatch)
    with webapp.app.test_request_context("/"):
        from flask import session
        session["user"] = "alice"
        assert page3.handle({"action": "add", "type": "income", "amount": "100", "date": "2026-01-01"}) == "เพิ่มรายการเรียบร้อย"
        message = page3.handle({"action": "add", "type": "expense", "amount": "100.01", "date": "2026-01-01"})
        assert "เงินพร้อมใช้ไม่พอ" in message
        assert page3.StudentBudget(page3._user_items("alice")).balance() == 100


def test_deleting_income_cannot_make_balance_negative(tmp_path, monkeypatch):
    _use_temp_files(tmp_path, monkeypatch)
    storage.save([
        {"username": "alice", "date": "2026-01-01", "type": "income", "category": "อื่น ๆ", "amount": 100, "description": "income"},
        {"username": "alice", "date": "2026-01-02", "type": "expense", "category": "อาหาร", "amount": 60, "description": "expense"},
    ])
    with webapp.app.test_request_context("/"):
        from flask import session
        session["user"] = "alice"
        assert "ไม่พอรองรับ" in page3.handle({"action": "delete", "index": "1"})
        assert len(storage.load()) == 2


def test_reserve_cannot_exceed_real_balance(tmp_path, monkeypatch):
    _use_temp_files(tmp_path, monkeypatch)
    storage.save([{"username": "alice", "date": "2026-01-01", "type": "income", "amount": 50}])
    with webapp.app.test_request_context("/"):
        from flask import session
        session["user"] = "alice"
        assert "ไม่เกินเงินคงเหลือ" in page5.handle({"action": "save", "saved": "60", "target": "100"})


def test_goals_are_private_per_user(tmp_path, monkeypatch):
    _use_temp_files(tmp_path, monkeypatch)
    goals_file = tmp_path / "goals.json"
    goals_file.write_text(json.dumps([
        {"username": "alice", "name": "A", "target": 100, "saved": 10},
        {"username": "bob", "name": "B", "target": 200, "saved": 20},
    ]), encoding="utf-8")
    with webapp.app.test_request_context("/"):
        from flask import session
        session["user"] = "alice"
        assert [goal["name"] for goal in page7.build()["goals"]] == ["A"]
