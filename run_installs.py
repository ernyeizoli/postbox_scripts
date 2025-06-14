import subprocess
import sys
import os

NETWORK_SCRIPT_DIR = r"\\10.10.101.10\creative\work\Postbox\01_Config\Postbox_scripts"

def run_script(script_name):
    script_path = os.path.join(NETWORK_SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
    print(f"▶️ Running {script_name} from network location...")
    subprocess.run([sys.executable, script_path], check=False)
    print("-" * 40)

if __name__ == "__main__":
    input("Press Enter to start the install...")
    run_script("ae_installer.py")
    run_script("c4d_installer.py")
    input("\nAll done! Press Enter to exit.")