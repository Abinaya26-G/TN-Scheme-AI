
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing in .env")

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]

for model_name in models_to_test:
    print(f"\nTesting {model_name}...")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Reply exactly: Gemini connection successful!"
        )

        print("SUCCESS!")
        print("Model:", model_name)
        print("Response:", response.text)
        break

    except errors.APIError as error:
        print("Failed:", error.code, error.message)

        if error.code == 503:
            print("Temporary service unavailability.")
        elif error.code == 429:
            print("Check your API quota and rate limits.")

    except Exception as error:
        print(type(error).__name__, error)
