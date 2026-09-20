from datetime import date, timedelta
from flask import session
import money_store as store

TITLE="No-Spend Day"
def build(query=None):
    username=session.get("user"); rows=store.transactions(username); saved=store.no_spend_days(username); today=date.today(); recent=[]
    for offset in range(13,-1,-1):
        day=(today-timedelta(days=offset)).isoformat(); amount=sum(float(r.get("amount",0)) for r in rows if r.get("type")=="expense" and r.get("date")==day); recent.append((day,amount))
    streak=0; cursor=today; saved_set=set(saved)
    while cursor.isoformat() in saved_set: streak+=1; cursor-=timedelta(days=1)
    return {"today":today.isoformat(),"today_spend":recent[-1][1],"total_recorded":len(saved),"streak":streak,"recent":recent[::-1],"actual_no_spend":[d for d,a in recent if a==0],"saved":saved}
def handle(form):
    if form.get("action")!="record": return ""
    try: store.record_no_spend(session.get("user"),form.get("date")); return "บันทึก No-Spend Day เรียบร้อย"
    except store.MoneyError as error: return str(error)
