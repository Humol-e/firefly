import os
import requests
from datetime import date, timedelta
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler


class FinancialSkill(OVOSSkill):
    def initialize(self):
        self.firefly_url = os.environ.get("FIREFLY_III_URL", "http://localhost/api/v1")
        self.firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN", "")

    def _get_headers(self):
        
        return {
            "Authorization": f"Bearer {self.firefly_token}",
            "Accept": "application/json",
        }

    def _get_transactions(self, start="2025-09-01", end="2025-09-30"):
        params = {"start": start, "end": end}
        r = requests.get(
            f"{self.firefly_url}/transactions",
            headers=self._get_headers(),
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("data", [])

    def _current_month(self):
        today = date.today()
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start.isoformat(), (next_month - timedelta(days=1)).isoformat()

    @intent_handler("BalanceIntent")
    def handle_balance(self, message):
        try:
            transactions = self._get_transactions("2025-09-01", "2025-09-30")
            total = 0
            for tx in transactions:
                for transaction in tx.get("attributes", {}).get("transactions", []):
                    total += float(transaction.get("amount", 0))
            self.speak_dialog("BalanceIntent", {"total": round(total, 2)})
        except Exception as e:
            self.log.error(f"Error querying Firefly III: {e}")
            self.speak("I could not reach Firefly III right now.")

    @intent_handler("SpendingIntent")
    def handle_spending(self, message):
        try:
            start, end = self._current_month()
            transactions = self._get_transactions(start, end)
            total = 0
            for tx in transactions:
                for t in tx.get("attributes", {}).get("transactions", []):
                    amount = float(t.get("amount", 0))
                    if amount < 0:
                        total += abs(amount)
            self.speak_dialog("SpendingIntent", {"total": round(total, 2)})
        except Exception as e:
            self.log.error(f"Error querying Firefly III: {e}")
            self.speak("I could not reach Firefly III right now.")

    def stop(self):
        pass