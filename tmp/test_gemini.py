import os
import sys
from dotenv import load_dotenv

# load dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Let's climb up to find backend/.env
env_path = os.path.join(BASE_DIR, "..", "backend", ".env")
load_dotenv(env_path)

api_key = os.environ.get("GEMINI_API_KEY")
print("API KEY FOUND IN ENV:", api_key)

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    print("Testing gemini-1.5-flash...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("Sending prompt 'hello'...")
    response = model.generate_content("Hello")
    print("gemini-1.5-flash response text:", response.text)
except Exception as e:
    import traceback
    print("gemini-1.5-flash error occurred:")
    traceback.print_exc()

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    print("\nTesting gemini-1.5-flash-8b...")
    model = genai.GenerativeModel("gemini-1.5-flash-8b")
    print("Sending prompt 'hello'...")
    response = model.generate_content("Hello")
    print("gemini-1.5-flash-8b response text:", response.text)
except Exception as e:
    import traceback
    print("gemini-1.5-flash-8b error occurred:")
    traceback.print_exc()
