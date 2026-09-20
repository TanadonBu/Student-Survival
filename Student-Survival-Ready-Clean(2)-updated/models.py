"""Student Survival data model for budgeting and daily planning."""
from datetime import date, timedelta


class StudentBudget:
    """Small model that turns transaction data into student-friendly indicators."""

    def __init__(self, items):
        self.items = items or []

    def balance(self):
        total = 0.0
        for item in self.items:
            amount = float(item.get("amount", 0))
            total += amount if item.get("type") == "income" else -amount
        return total

    def category_totals(self):
        totals = {}
        for item in self.items:
            if item.get("type") == "expense":
                category = item.get("category", "อื่น ๆ")
                totals[category] = totals.get(category, 0) + float(item.get("amount", 0))
        return totals

    def today_expense(self, day=None):
        day = day or date.today().isoformat()
        return sum(
            float(item.get("amount", 0))
            for item in self.items
            if item.get("type") == "expense" and str(item.get("date", "")) == day
        )

    def recent_daily_expense(self, days=7, end=None):
        end = end or date.today()
        start = end - timedelta(days=max(int(days), 1) - 1)
        totals = {}
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            totals[day.isoformat()] = 0.0
        for item in self.items:
            if item.get("type") != "expense":
                continue
            key = str(item.get("date", ""))
            if key in totals:
                totals[key] += float(item.get("amount", 0))
        return totals

    def average_daily_expense(self, days=7):
        values = list(self.recent_daily_expense(days).values())
        return sum(values) / len(values) if values else 0.0

    def daily_limit(self, days_left):
        return max(self.balance() / max(int(days_left), 1), 0)

    def runway_days(self, days=7):
        average = self.average_daily_expense(days)
        if average <= 0:
            return 0
        return max(self.balance(), 0) / average

    def goal_progress(self, target, saved=None):
        """Return progress percentage for a separate savings/reserve amount."""
        saved = max(self.balance(), 0) if saved is None else max(float(saved), 0)
        target = float(target)
        return min(saved / target * 100, 100) if target > 0 else 0
