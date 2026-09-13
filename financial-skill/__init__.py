import os
import requests
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from google import genai
from google.genai import types
from elevenlabs.client import ElevenLabs


# ============ TOOLS FOR GEMINI ============

def get_account_balances() -> str:
    """Returns the current account balances from Firefly III."""
    firefly_url = os.environ.get("FIREFLY_III_URL", "http://localhost/api/v1")
    firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN")

    headers = {
        "Authorization": f"Bearer {firefly_token}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            f"{firefly_url}/accounts",
            headers=headers,
            params={"type": "asset"},
            timeout=5,
        )
        response.raise_for_status()
        accounts_data = response.json().get("data", [])
        if not accounts_data:
            return "You don't have any asset accounts configured."
        balances = []
        for account in accounts_data:
            attr = account.get("attributes", {})
            name = attr.get("name", "Unknown Account")
            balance = float(attr.get("current_balance", 0.0))
            balances.append(f"{name}: ${balance:.2f}")
        return ", ".join(balances)
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Firefly III: {e}"

def get_category_spending(category: str, start_date: str, end_date: str) -> str:
    """Returns total spending for a SPECIFIC category in a date range.

    Args:
        category: Category name (e.g., "Coffee", "Dining Out", "Groceries").
        start_date: YYYY-MM-DD format.
        end_date: YYYY-MM-DD format.
    """
    firefly_url = os.environ.get("FIREFLY_III_URL", "http://localhost/api/v1")
    firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {firefly_token}", "Accept": "application/json"}

    search_query = f"date_after:{start_date} date_before:{end_date} type:withdrawal"
    total = 0.0
    try:
        page = 1
        has_more = True
        while has_more:
            r = requests.get(f"{firefly_url}/search", headers=headers,
                             params={"query": search_query, "page": page}, timeout=10)
            r.raise_for_status()
            res = r.json()
            for item in res.get("data", []):
                for split in item.get("attributes", {}).get("transactions", []):
                    if (split.get("category_name") or "").lower() == category.lower():
                        total += abs(float(split.get("amount", 0.0)))
            pg = res.get("meta", {}).get("pagination", {})
            if pg.get("current_page", 1) >= pg.get("total_pages", 1) or not res.get("data"):
                has_more = False
            else:
                page += 1
        return f"You spent ${total:.2f} on {category} between {start_date} and {end_date}."
    except Exception as e:
        return f"Error: {e}"


def compare_months() -> str:
    """Compares spending between the current month and the previous month."""
    from datetime import date, timedelta
    today = date.today()
    start_current = today.replace(day=1)
    end_prev = start_current - timedelta(days=1)
    start_prev = end_prev.replace(day=1)

    def total_spending(start, end):
        firefly_url = os.environ.get("FIREFLY_III_URL", "http://localhost/api/v1")
        firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN")
        headers = {"Authorization": f"Bearer {firefly_token}", "Accept": "application/json"}
        query = f"date_after:{start.isoformat()} date_before:{end.isoformat()} type:withdrawal"
        total = 0.0
        r = requests.get(f"{firefly_url}/search", headers=headers,
                         params={"query": query}, timeout=10)
        for item in r.json().get("data", []):
            for split in item.get("attributes", {}).get("transactions", []):
                total += abs(float(split.get("amount", 0.0)))
        return total

    try:
        cur = total_spending(start_current, today)
        prev = total_spending(start_prev, end_prev)
        diff = cur - prev
        direction = "more" if diff > 0 else "less"
        return (f"This month you've spent ${cur:.2f}. Last month was ${prev:.2f}. "
                f"You're spending ${abs(diff):.2f} {direction} this month.")
    except Exception as e:
        return f"Error: {e}"


def get_top_categories(start_date: str, end_date: str) -> str:
    """Returns the top 3 spending categories for a date range.

    Args:
        start_date: YYYY-MM-DD format.
        end_date: YYYY-MM-DD format.
    """
    firefly_url = os.environ.get("FIREFLY_III_URL", "http://localhost/api/v1")
    firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {firefly_token}", "Accept": "application/json"}
    query = f"date_after:{start_date} date_before:{end_date} type:withdrawal"
    by_cat = {}
    try:
        r = requests.get(f"{firefly_url}/search", headers=headers,
                         params={"query": query}, timeout=10)
        for item in r.json().get("data", []):
            for split in item.get("attributes", {}).get("transactions", []):
                cat = split.get("category_name") or "Uncategorized"
                by_cat[cat] = by_cat.get(cat, 0) + abs(float(split.get("amount", 0.0)))
        top3 = sorted(by_cat.items(), key=lambda x: -x[1])[:3]
        result = ", ".join(f"{cat}: ${amt:.2f}" for cat, amt in top3)
        return f"Top categories between {start_date} and {end_date}: {result}"
    except Exception as e:
        return f"Error: {e}"

def get_spending_history(start_date: str, end_date: str, categories: str = "") -> str:
    """Returns total spending from Firefly III for a date range and optional categories.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        categories: Optional comma-separated categories.
    """
    firefly_url = os.environ.get("FIREFLY_III_URL", "http://localhost/api/v1")
    firefly_token = os.environ.get("FIREFLY_III_ACCESS_TOKEN")

    if not firefly_token:
        return "Error: Firefly III API token is missing."

    headers = {
        "Authorization": f"Bearer {firefly_token}",
        "Accept": "application/json",
    }

    search_query = f"date_after:{start_date} date_before:{end_date} type:withdrawal"
    target_categories = [c.strip().lower() for c in categories.split(",")] if categories else []

    try:
        total_spent = 0.0
        page = 1
        has_more = True
        while has_more:
            r = requests.get(
                f"{firefly_url}/search",
                headers=headers,
                params={"query": search_query, "page": page},
                timeout=10,
            )
            r.raise_for_status()
            res = r.json()
            data = res.get("data", [])
            for item in data:
                splits = item.get("attributes", {}).get("transactions", [])
                for split in splits:
                    tx_cat = (split.get("category_name") or "").lower()
                    if not target_categories or tx_cat in target_categories:
                        total_spent += abs(float(split.get("amount", 0.0)))
            pagination = res.get("meta", {}).get("pagination", {})
            if pagination.get("current_page", 1) >= pagination.get("total_pages", 1) or not data:
                has_more = False
            else:
                page += 1
        label = f" in {categories}" if categories else ""
        return f"Between {start_date} and {end_date}, you spent ${total_spent:.2f}{label}."
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


def find_nearby_places(place_type: str, max_price_usd: int, location: str = "Houston, Texas") -> str:
    """Searches for places fitting a category and budget.

    Args:
        place_type: Type of location (e.g., "coffee shop").
        max_price_usd: Maximum dollar amount per person.
        location: City or neighborhood name.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return "Google Places API key is missing."
    if max_price_usd <= 10:
        price_level = 1
    elif max_price_usd <= 25:
        price_level = 2
    elif max_price_usd <= 50:
        price_level = 3
    else:
        price_level = 4
    url = "https://places.googleapis.com/v1/places:searchText"


    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.priceLevel"
    }

    body = {
        "textQuery": f"{place_type} in {location}",
        "priceLevels": [price_level],
        "languageCode": "en"
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json().get("places", [])[:3]

        if not results:
            return f"No {place_type} found in {location} within your budget."

        formatted = []
        for place in results:
            name = place.get("displayName", {}).get("text", "Unknown")
            rating = place.get("rating", "N/A")
            formatted.append(f"{name} ({rating} stars)")

        return " | ".join(formatted)
    except requests.exceptions.RequestException as e:
        return f"Error searching places: {e}"

# ============ SKILL ============

class FinancialSkill(OVOSSkill):
    def initialize(self):
        self.log.info("=" * 60)
        self.log.info("FINANCIAL SKILL: initialize() called")
        gemini_key = os.environ.get("GEMINI_API_KEY")
        eleven_key = os.environ.get("ELEVENLABS_API_KEY")
        self.log.info(f"GEMINI key present: {bool(gemini_key)}")
        self.log.info(f"ELEVEN key present: {bool(eleven_key)}")
        self.gemini = genai.Client(api_key=gemini_key)
        self.eleven = ElevenLabs(api_key=eleven_key)
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        self.output_file = "/home/ovos/response.mp3"
        self.log.info("FINANCIAL SKILL: initialize() done")
        self.log.info("=" * 60)

    @intent_handler("Finance.intent")
    def handle_finance_query(self, message):
        self.log.info("=" * 60)
        self.log.info("FINANCIAL SKILL: Handler activated!")
        self.log.info(f"Raw message: {message.data}")
        user_utterance = message.data.get("utterance", "")
        self.log.info(f"USER SAID: {user_utterance}")
        self.log.info("=" * 60)

        config = types.GenerateContentConfig(
            tools=[get_account_balances, get_spending_history, get_category_spending, compare_months,get_top_categories,find_nearby_places],
            system_instruction=(
                "You are Bando, a friendly financial advisor for a college student. "
                "Use the tools to answer with REAL data. Key rules: "
                "1) For 'how much did I spend on X', use get_category_spending. "
                "2) For 'how much did I spend' (general), use get_spending_history. "
                "3) For 'am I over budget' or 'where do I spend most', use get_top_categories. "
                "4) For 'compare months' or 'trend', use compare_months. "
                "5) For 'balance', use get_account_balances. "
                "6) For place recommendations, use find_nearby_places. "
                "Always keep responses under 3 sentences. Be warm, encouraging, and practical. "
                "Add a specific actionable tip when giving advice."
            ),
        )

        try:
            self.log.info(f"Sending to Gemini: {user_utterance}")
            gemini_response = self.gemini.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_utterance,
                config=config,
            )
            answer = gemini_response.text
            self.log.info(f"GEMINI RESPONDED: {answer}")

            self.log.info(f"Sending to ElevenLabs: {answer[:80]}...")
            audio_stream = self.eleven.text_to_speech.convert(
                text=answer,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            with open(self.output_file, "wb") as f:
                for chunk in audio_stream:
                    if chunk:
                        f.write(chunk)

            self.log.info(f"AUDIO SAVED: {self.output_file}")
            self.speak("I've prepared your financial answer. Check your laptop for the audio.")

        except Exception as e:
            self.log.error(f"EXECUTION ERROR: {e}")
            import traceback
            self.log.error(traceback.format_exc())
            self.speak("I ran into an issue analyzing your financial data.")

    def stop(self):
        pass