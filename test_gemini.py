import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        return

    genai.configure(api_key=api_key)
    
    print("Fetching available models...")
    try:
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"Available models: {available_models}")
        
        if not available_models:
            print("No models supporting generateContent found.")
            return

        # Simple test generation
        model_name = 'gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
        print(f"Testing generation with {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, write a very short one-sentence greeting for a stock trader.")
        print(f"Response: {response.text}")
        print("Success!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_gemini()
