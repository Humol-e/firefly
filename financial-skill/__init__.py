import os
import requests
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

    def _get_accounts(self):
        r = requests.get(f"{self.firefly_url}/accounts", headers=self._get_headers(), timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])

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

    @intent_handler("BalanceIntent")
    def handle_balance(self, message):
        try:
            accounts = self._get_accounts()
            total = 0
            for acc in accounts:
                attrs = acc.get("attributes", {})
                if attrs.get("type") == "asset":
                    total += float(attrs.get("current_balance", 0))
            self.speak_dialog("balance_response", {"total": total})
        except Exception as e:
            self.log.error(f"Error consultando Firefly III: {e}")
            self.speak_dialog("error_response")

    @intent_handler("SpendingIntent")
    def handle_spending(self, message):
        try:
            transactions = self._get_transactions()
            total = 0
            for tx in transactions:
                for t in tx.get("attributes", {}).get("transactions", []):
                    amount = float(t.get("amount", 0))
                    if amount < 0:
                        total += abs(amount)
            self.speak_dialog("spending_response", {"total": round(total, 2)})
        except Exception as e:
            self.log.error(f"Error consultando Firefly III: {e}")
            self.speak_dialog("error_response")

    def stop(self):
        pass