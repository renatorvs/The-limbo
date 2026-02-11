import sys
import os
sys.path.append(os.getcwd())

try:
    import langchain_google_genai
    print("✅ langchain_google_genai imported successfully")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
