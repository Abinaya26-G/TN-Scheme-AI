
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing from .env")

client = genai.Client(api_key=api_key)

print("Checking available Gemini models...\n")

try:
    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            print(model.name)

except Exception as error:
    print("Model list failed:")
    print(type(error).__name__, error)
