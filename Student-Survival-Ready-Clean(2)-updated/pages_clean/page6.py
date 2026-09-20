from datetime import date, timedelta
from flask import session
import money_store as store
TITLE="วิเคราะห์"
def build(query=None):
    rows=store.transactions(session.get("user")); totals={}
    for r in rows:
        if r.get("type")=="expense":
            name=r.get("category","อื่น ๆ"); totals[name]=totals.get(name,0)+float(r.get("amount",0))
    total=sum(totals.values()); result=[{"name":n,"value":v,"percent":v/total*100 if total else 0} for n,v in totals.items()]; result.sort(key=lambda x:x["value"],reverse=True); daily=[]
    for offset in range(6,-1,-1):
        day=(date.today()-timedelta(days=offset)).isoformat(); daily.append((day,sum(float(r.get("amount",0)) for r in rows if r.get("type")=="expense" and r.get("date")==day)))
    return {"rows":result,"total":total,"daily":daily,"highest":result[0] if result else None}
