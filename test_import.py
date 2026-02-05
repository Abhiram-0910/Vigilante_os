
import sys
import os
import traceback

# Add current directory to sys.path
sys.path.append(os.getcwd())

print("Attempting to import app.main...")
try:
    from app.main import app
    print("SUCCESS: app.main imported successfully.")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"FAILURE: Exception: {e}")
    traceback.print_exc()
