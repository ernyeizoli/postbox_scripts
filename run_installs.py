import subprocess
import sys
import os

def run_script(script_name):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
    print(f"▶️ Running {script_name}...")
    subprocess.run([sys.executable, script_path], check=False)
    print("-" * 40)

if __name__ == "__main__":
    run_script("ae_installer.py")
    run_script("c4d_installer.py")
    input("\nAll done! Press Enter to exit.")