import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, "..", "backend", ".env")
load_dotenv(env_path)

api_key = os.environ.get("GEMINI_API_KEY")

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    print("Available models:")
    for m in genai.list_models():
        print(f"- {m.name}")
except Exception as e:
    import traceback
    traceback.print_exc()
