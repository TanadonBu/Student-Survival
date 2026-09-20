from datetime import date, timedelta
import calendar
from flask import session
import money_store as store

TITLE = "Dashboard"

def build(query=None):
    username = session.get("user")
    rows = store.transactions(username)
    today = date.today(); month_key = today.strftime("%Y-%m")
    month_rows = [r for r in rows if str(r.get("date", "")).startswith(month_key)]
    income = sum(float(r.get("amount", 0)) for r in rows if r.get("type") == "income")
    expense = sum(float(r.get("amount", 0)) for r in rows if r.get("type") == "expense")
    month_income = sum(float(r.get("amount", 0)) for r in month_rows if r.get("type") == "income")
    month_expense = sum(float(r.get("amount", 0)) for r in month_rows if r.get("type") == "expense")
    categories = {}
    for r in month_rows:
        if r.get("type") == "expense":
            name = r.get("category", "อื่น ๆ"); categories[name] = categories.get(name, 0) + float(r.get("amount", 0))
    daily = {}
    for offset in range(6, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        daily[day] = sum(float(r.get("amount", 0)) for r in rows if r.get("type") == "expense" and r.get("date") == day)
    thai = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
    chart = [{"label": f"{thai[date.fromisoformat(d).weekday()]} {d[-2:]}", "amount": a} for d, a in daily.items()]
    available = store.usable_balance(username)
    days_left = max(calendar.monthrange(today.year, today.month)[1] - today.day + 1, 1)
    daily_limit = available / days_left; today_spend = daily.get(today.isoformat(), 0); average = sum(daily.values()) / 7
    saved, target = store.reserve(username)
    return {"income":income,"expense":expense,"balance":store.balance(username),"month_income":month_income,"month_expense":month_expense,"month_balance":max(month_income-month_expense,0),"top_categories":sorted(categories.items(),key=lambda x:x[1],reverse=True),"daily_chart":chart,"recent":rows[:6],"count":len(rows),"today_spend":today_spend,"daily_limit":daily_limit,"days_left":days_left,"average_7":average,"runway":available/average if average else 0,"projected_month":month_expense/max(today.day,1)*calendar.monthrange(today.year,today.month)[1],"budget_used":min(today_spend/daily_limit*100,100) if daily_limit else 0,"status":"อยู่ในงบวันนี้" if today_spend<=daily_limit else "ใช้เกินงบวันนี้","today_label":today.strftime("%d/%m/%Y"),"reserve_saved":saved,"reserve_target":target,"reserve_progress":min(saved/target*100,100),"usable_after_reserve":available,"no_spend_days":sum(1 for a in daily.values() if a==0)}
