"""End-to-end checks for the rebuilt application core."""
import json
import app as webapp
import money_store as store


def _files(tmp_path, monkeypatch):
    paths = {
        "TRANSACTIONS_FILE": tmp_path / "data.json",
        "ACCOUNTS_FILE": tmp_path / "accounts.json",
        "RESERVE_FILE": tmp_path / "reserve.json",
        "GOALS_FILE": tmp_path / "goals.json",
        "NO_SPEND_FILE": tmp_path / "no-spend.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(store, name, str(path))
    paths["TRANSACTIONS_FILE"].write_text("[]", encoding="utf-8")
    paths["ACCOUNTS_FILE"].write_text(json.dumps({"users": [{"username": "alice"}]}), encoding="utf-8")
    paths["RESERVE_FILE"].write_text("{}", encoding="utf-8")
    paths["GOALS_FILE"].write_text("[]", encoding="utf-8")
    paths["NO_SPEND_FILE"].write_text("{}", encoding="utf-8")


def _login(client):
    with client.session_transaction() as session:
        session["user"] = "alice"
        session["csrf_token"] = "test-token"


def test_protected_page_shows_login_before_authentication():
    client = webapp.app.test_client()
    response = client.get("/page2")
    assert response.status_code == 200
    assert "เข้าสู่ระบบ" in response.get_data(as_text=True)
    assert "กรุณาเข้าสู่ระบบเพื่อใช้งานแอป" in response.get_data(as_text=True)


def test_transaction_flow_never_goes_negative(tmp_path, monkeypatch):
    _files(tmp_path, monkeypatch)
    client = webapp.app.test_client(); _login(client)
    common = {"csrf_token": "test-token", "action": "add", "date": "2026-09-01", "category": "อื่น ๆ", "description": "test"}
    client.post("/page3", data={**common, "type": "income", "amount": "100"})
    response = client.post("/page3", data={**common, "type": "expense", "amount": "101"}, follow_redirects=True)
    assert "เงินพร้อมใช้ไม่พอ" in response.get_data(as_text=True)
    assert store.balance("alice") == 100


def test_legacy_rows_are_assigned_to_the_only_account(tmp_path, monkeypatch):
    _files(tmp_path, monkeypatch)
    with open(store.TRANSACTIONS_FILE, "w", encoding="utf-8") as file:
        json.dump([{"date": "2026-09-01", "type": "income", "amount": 500}], file)
    rows = store.transactions("alice")
    assert len(rows) == 1
    assert rows[0]["username"] == "alice"
    assert rows[0]["id"]


def test_goal_ids_prevent_cross_user_edits(tmp_path, monkeypatch):
    _files(tmp_path, monkeypatch)
    store.add_goal("alice", "Laptop", 1000)
    goal = store.goals("alice")[0]
    try:
        store.update_goal("bob", goal["id"], 500)
        assert False, "another user must not edit this goal"
    except store.MoneyError:
        pass
