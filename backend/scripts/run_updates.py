# backend/scripts/run_updates.py
import subprocess
import sys
import os

def run_script(script_name):
    """Runs a python script located in the same directory."""
    print(f"--- Running {script_name} ---")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_name)
    
    try:
        # Using sys.executable ensures we use the same python interpreter
        result = subprocess.run(
            [sys.executable, script_path], 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("--- Stderr ---")
            print(result.stderr)
        print(f"--- Successfully finished {script_name} ---")
    except subprocess.CalledProcessError as e:
        print(f"!!! ERROR running {script_name} !!!")
        print(f"Return code: {e.returncode}")
        print("--- Stdout ---")
        print(e.stdout)
        print("--- Stderr ---")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Starting daily commander database update process...")
    run_script("update_commanders.py")
    run_script("update_partner_background.py")
    print("✅ All update scripts completed successfully.")