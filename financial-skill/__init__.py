from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
import requests
import os

class FinancialSkill(OVOSSkill):
    def initialize(self):
        self.firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN")
        self.firefly_url = "http://localhost/api/v1"

    @intent_handler("BalanceIntent")
    def handle_balance(self, message):
        headers = {
            "Authorization": f"Bearer {self.firefly_token}",
            "Accept": "application/json"
        }
        try:
            response = requests.get(f"{self.firefly_url}/accounts", headers=headers)
            data = response.json()
            # Procesar y devolver respuesta
            self.speak_dialog("balance_response", {"data": data})
        except Exception as e:
            self.speak_dialog("error_response")