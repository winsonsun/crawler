import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Available models:")
for model in client.models.list():
    print(f"Name: {model.name}, Supported Actions: {model.supported_actions}")
