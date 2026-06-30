import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, "..", "backend", ".env")
load_dotenv(env_path)

api_key = os.environ.get("GEMINI_API_KEY")

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
except Exception as e:
    print("Failed to import or configure genai:", e)

test_models = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest"
]

with open("tmp/multiple_output.log", "w", encoding="utf-8") as f:
    for model_name in test_models:
        f.write(f"\n=========================================\n")
        f.write(f"Testing model: {model_name}\n")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello! Give a 1-sentence supportive message for PCOS health.")
            f.write(f"SUCCESS!\n")
            f.write(f"Response: {response.text}\n")
        except Exception as e:
            f.write(f"FAILED!\n")
            import traceback
            f.write(traceback.format_exc())
            f.write("\n")
print("Done testing models!")
