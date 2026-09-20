from flask import session
import money_store as store
TITLE="Emergency Reserve"
def build(query=None):
    username=session.get("user"); cash=store.balance(username); saved,target=store.reserve(username)
    return {"balance":cash,"saved":saved,"target":target,"progress":min(saved/target*100,100),"gap":max(target-saved,0),"usable":max(cash-saved,0),"safety_ratio":min(saved/max(cash,1)*100,100)}
def handle(form):
    if form.get("action")!="save": return ""
    try: store.save_reserve(session.get("user"),form.get("saved"),form.get("target")); return "อัปเดตเงินสำรองแล้ว"
    except store.MoneyError as error: return str(error)
