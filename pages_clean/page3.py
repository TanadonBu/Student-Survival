from datetime import date, timedelta
from flask import session
import money_store as store

TITLE = "การเงิน"; CATEGORIES = store.CATEGORIES

def build(query=None):
    username=session.get("user"); rows=store.transactions(username); saved,target=store.reserve(username)
    allocation=store.allocation(username); current_balance=store.balance(username)
    start=(date.today()-timedelta(days=6)).isoformat(); average=sum(float(r.get("amount",0)) for r in rows if r.get("type")=="expense" and r.get("date","")>=start)/7
    categories={}
    for r in rows:
        if r.get("type")=="expense":
            name=r.get("category","อื่น ๆ"); categories[name]=categories.get(name,0)+float(r.get("amount",0))
    available=store.usable_balance(username)
    return {"today_date":date.today().isoformat(),"items":rows,"balance":current_balance,"daily":available/20,"today":sum(float(r.get("amount",0)) for r in rows if r.get("type")=="expense" and r.get("date")==date.today().isoformat()),"average":average,"runway":available/average if average else 0,"categories":CATEGORIES,"budget":sorted(categories.items(),key=lambda x:x[1],reverse=True),"reserve_saved":saved,"reserve_target":target,"reserve_gap":max(target-saved,0),"reserve_progress":min(saved/target*100,100),"recommended_reserve":max(2000,average*7),"allocation":allocation,"allocation_amounts":{key:round(current_balance*value/100,2) for key,value in allocation.items()}}

def handle(form):
    action=str(form.get("action","")); username=session.get("user")
    try:
        if action=="add": store.add_transaction(username,form.get("type"),form.get("amount"),form.get("category"),form.get("description"),form.get("date")); return "เพิ่มรายการเรียบร้อย"
        if action=="delete": store.delete_transaction(username,str(form.get("id",""))); return "ลบรายการแล้ว"
        if action=="reserve":
            new_saved=store.add_reserve(username,form.get("reserve_addition"),form.get("reserve_target"))
            return f"บวกเงินสำรองแล้ว ฿{new_saved:,.2f}"
        if action=="allocation":
            store.save_allocation(username,form)
            return "บันทึกสัดส่วนการแบ่งเงินแล้ว"
    except store.MoneyError as error: return str(error)
    return ""
