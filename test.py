import os
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

try:
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello! Respond with the word Success."
    )

    print("--- Connection Result ---")
    print(response.text.strip())

except Exception as e:
    print("--- Connection Failed ---")
    print(e)