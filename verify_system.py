import sys
import os
import importlib
import warnings

def check_import(module_name):
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} installed")
        return True
    except ImportError as e:
        print(f"❌ {module_name} MISSING: {e}")
        return False

def check_files():
    required = [
        "app/main.py",
        "app/services/agents.py",
        "app/services/rl_brain.py",
        "dashboard.py",
        "requirements.txt",
        "evidence_ledger.db"  # Should exist after training/running
    ]
    missing = []
    for f in required:
        if not os.path.exists(f):
            missing.append(f)
            print(f"❌ File Missing: {f}")
        else:
            print(f"✅ File Found: {f}")
    return len(missing) == 0

def check_db():
    import sqlite3
    try:
        if os.path.exists("evidence_ledger.db"):
            conn = sqlite3.connect("evidence_ledger.db")
            cursor = conn.execute("SELECT count(*) FROM evidence_chain")
            cnt = cursor.fetchone()[0]
            print(f"✅ Evidence Ledger contains {cnt} blocks")
            conn.close()
        else:
            print("⚠️ Evidence Ledger not created yet (Run app to create)")
    except Exception as e:
        print(f"❌ DB Check Failed: {e}")

if __name__ == "__main__":
    print("🔍 RUNNING VIBHISHAN SYSTEM VERIFICATION...")
    
    deps_ok = all([
        check_import("fastapi"),
        check_import("streamlit"),
        check_import("pandas"),
        check_import("langchain"),
        check_import("groq"),
        check_import("sentence_transformers")
    ])
    
    files_ok = check_files()
    
    check_db()
    
    if deps_ok and files_ok:
        print("\n🚀 SYSTEM READY FOR LAUNCH!")
        sys.exit(0)
    else:
        print("\n🛑 SYSTEM NOT READY. FIX ERRORS.")
        sys.exit(1)
