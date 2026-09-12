import os
import requests
from google import genai
from elevenlabs.client import ElevenLabs
import subprocess

FIREFLY_URL = "http://localhost/api/v1"
FIREFLY_TOKEN = os.environ.get("FIREFLY_III_ACCESS_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")

# 1. Firefly III — obtaining data
headers = {"Authorization": f"Bearer {FIREFLY_TOKEN}", "Accept": "application/json"}
accounts = requests.get(f"{FIREFLY_URL}/accounts", headers=headers).json().get("data", [])
txs = requests.get(
    f"{FIREFLY_URL}/transactions",
    headers=headers,
    params={"start": "2026-09-01", "end": "2026-09-30"}
).json().get("data", [])

context = f"I have {len(accounts)} accounts and {len(txs)} transactions in September. "
context += f"Total transactions amount: {sum(float(t['attributes']['transactions'][0]['amount']) for t in txs if t.get('attributes', {}).get('transactions'))}"

# 2. Gemini — natural answer
client = genai.Client(api_key=GEMINI_KEY)
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"You are a friendly financial assistant. Data: {context}. Question: How am I doing this month? Answer in 1-2 sentences."
)
answer_text = response.text
print(f"Gemini says: {answer_text}")

# 3. ElevenLabs — convertir a audio
eleven = ElevenLabs(api_key=ELEVEN_KEY)
audio = eleven.text_to_speech.convert(
    text=answer_text,
    voice_id=VOICE_ID,
    model_id="eleven_multilingual_v2"
)

output_file = "response.mp3"
with open(output_file, "wb") as f:
    for chunk in audio:
        f.write(chunk)

print(f"Audio saved in {output_file}")

# 4. Reproducir el audio (Windows)
subprocess.run(["start", output_file], shell=True)