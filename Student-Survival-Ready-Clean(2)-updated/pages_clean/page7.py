from flask import session
import money_store as store
TITLE="เป้าหมาย"
def build(query=None):
    rows=store.goals(session.get("user"))
    for r in rows:
        target=float(r.get("target",0)); saved=float(r.get("saved",0)); r["progress"]=min(saved/target*100,100) if target else 0; r["gap"]=max(target-saved,0)
    return {"goals":rows}
def handle(form):
    action=form.get("action"); username=session.get("user")
    try:
        if action=="add": store.add_goal(username,form.get("name"),form.get("target")); return "เพิ่มเป้าหมายแล้ว"
        if action=="update": store.update_goal(username,form.get("id"),form.get("saved")); return "อัปเดตเป้าหมายแล้ว"
        if action=="delete": store.delete_goal(username,form.get("id")); return "ลบเป้าหมายแล้ว"
    except store.MoneyError as error: return str(error)
    return ""
