import google.generativeai as genai
import os

# Your provided API key
GOOGLE_API_KEY = "AIzaSyAbDRav7Kj6yRVBEJMFaUPz0SbKDe6weoM"
genai.configure(api_key=GOOGLE_API_KEY)

print("Attempting to list available models for your API key...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}, Display Name: {m.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")
    print("Please ensure your API key is correct and has the necessary permissions.")

print("\n--- List complete ---")