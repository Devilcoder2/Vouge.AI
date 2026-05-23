import sys
from pathlib import Path

# Add root folder to python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from google import genai
from app.config import settings

def run_diagnostics():
    print("--- GEMINI API DIAGNOSTICS START ---")
    
    # 1. Verify key loading
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("[CRITICAL] GEMINI_API_KEY is not loaded correctly from the environment or .env file!", file=sys.stderr)
        return
        
    print(f"Active API Key Loaded: {settings.GEMINI_API_KEY[:8]}...{settings.GEMINI_API_KEY[-4:]}")
    
    # 2. Connect to the unified GenAI client
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        print("Successfully initialized genai.Client.")
        
        # 3. Query the official list of available models
        print("Querying ModelService.ListModels()...")
        models = client.models.list()
        
        available_models = []
        for m in models:
            available_models.append(m.name)
            
        print(f"\nFound {len(available_models)} available models for your API key:")
        for name in sorted(available_models):
            print(f" - {name}")
            
    except Exception as e:
        print(f"\n[CRITICAL] Failed to query available models: {str(e)}", file=sys.stderr)
        
    print("--- GEMINI API DIAGNOSTICS END ---")

if __name__ == "__main__":
    run_diagnostics()
