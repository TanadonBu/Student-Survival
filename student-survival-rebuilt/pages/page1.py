"""Student Survival account center: register and login."""
import hashlib, hmac, json, os, re, secrets
from flask import session
TITLE = "เข้าสู่ระบบ / สมัครสมาชิก"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_FILE = os.path.join(HERE, "accounts.json")
ADMIN_USERNAME = "admin"

def _load():
    if not os.path.exists(ACCOUNTS_FILE): return {"users": [], "admin": {}}
    try:
        with open(ACCOUNTS_FILE, encoding="utf-8") as f: return json.load(f)
    except (OSError, json.JSONDecodeError): return {"users": [], "admin": {}}

def _save(data):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()

def _valid_username(username):
    username=str(username or "").strip()
    return 3 <= len(username) <= 30 and bool(re.fullmatch(r"[\w .-]+", username, flags=re.UNICODE))

def build(query=None):
    if session.get("user"): return {"redirect_home": True}
    accounts=_load()
    return {"users": accounts.get("users", []), "view": (query or {}).get("view","account")}

def handle(form):
    action=str(form.get("action","")).strip()
    username=str(form.get("username","")).strip()
    password=form.get("password","")
    data=_load(); users=data.setdefault("users",[])
    if action == "register":
        if not _valid_username(username): return "ชื่อผู้ใช้ต้องมี 3–30 ตัวอักษร"
        if len(password) < 6: return "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"
        if any(u.get("username","").lower()==username.lower() for u in users): return "ชื่อผู้ใช้นี้มีอยู่แล้ว"
        salt=secrets.token_hex(16)
        users.append({"username":username,"salt":salt,"password_hash":_hash(password,salt)})
        _save(data); session["user"]=username; return "สมัครสมาชิกสำเร็จ"
    if action == "login":
        for u in users:
            if u.get("username","").lower()==username.lower() and hmac.compare_digest(_hash(password,u.get("salt","")),u.get("password_hash","")):
                session["user"]=u["username"]; return "เข้าสู่ระบบสำเร็จ"
        return "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
    return ""
