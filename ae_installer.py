import ctypes
import os
import shutil
import sys
import platform

# --- CONFIGURATION ---
SCRIPTS_TO_INSTALL = [
    "PBV_organizer.jsx",
    "PBV_Comp_helper.jsx"
]

SCRIPTS_TO_SCRIPTS_FOLDER = [
    "process_footage.py",
    "FootageVersionScanner.jsx"
]

# --- PLATFORM AND ADMIN CHECKS (WINDOWS ONLY) ---

def is_admin():
    """Checks if the script is running with administrative privileges on Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        # This will fail on non-Windows systems, which is expected.
        return False

def run_as_admin():
    """Re-runs the script with administrative privileges on Windows."""
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None,
        1
    )

# --- DYNAMIC PATH FINDING ---

def get_all_ae_versions():
    """Return all Adobe After Effects application folders (Windows or macOS)."""
    if platform.system() == "Darwin":  # macOS
        base_path = "/Applications"
    elif platform.system() == "Windows":
        base_path = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        if not base_path:
             raise RuntimeError("Could not find the Program Files directory.")
        base_path = os.path.join(base_path, "Adobe")
    else:
        raise RuntimeError(f"Unsupported OS: {platform.system()}")

    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Adobe installation directory not found at: {base_path}")

    return [
        folder
        for folder in os.listdir(base_path)
        if "Adobe After Effects" in folder and os.path.isdir(os.path.join(base_path, folder))
    ]

def get_ae_script_path(version_folder):
    """Constructs the path to the 'ScriptUI Panels' folder for a given AE version."""
    if platform.system() == "Darwin":
        base_path = "/Applications"
        return os.path.join(base_path, version_folder, "Scripts", "ScriptUI Panels")
    elif platform.system() == "Windows":
        base_path = os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Adobe")
        return os.path.join(base_path, version_folder, "Support Files", "Scripts", "ScriptUI Panels")
    else:
        raise RuntimeError(f"Unsupported OS: {platform.system()}")

def get_ae_scripts_folder(version_folder):
    """Constructs the path to the 'Scripts' folder for a given AE version."""
    if platform.system() == "Darwin":
        base_path = "/Applications"
        return os.path.join(base_path, version_folder, "Scripts")
    elif platform.system() == "Windows":
        base_path = os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Adobe")
        return os.path.join(base_path, version_folder, "Support Files", "Scripts")
    else:
        raise RuntimeError(f"Unsupported OS: {platform.system()}")

# --- CORE FILE OPERATIONS ---

def copy_script_file(src_file, dst_folder):
    """Copies a single script file to the destination folder."""
    destination_path = os.path.join(dst_folder, os.path.basename(src_file))
    try:
        print(f"  Attempting to copy: {os.path.basename(src_file)}")
        # Create destination directory if it doesn't exist
        os.makedirs(dst_folder, exist_ok=True)
        shutil.copy2(src_file, destination_path)
        print(f"  ✅ Copied successfully to {destination_path}")

    except FileNotFoundError:
        print(f"  ❌ Error: Source file not found at {src_file}.")
    except PermissionError:
        print(f"  ❌ Error: Permission denied to write to {dst_folder}.")
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}")

# --- MAIN EXECUTION ---

def main():
    """Main function to find AE versions and copy scripts."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_source_root = os.path.join(base_dir, "scripts", "AE_Scripts")
        
        ae_versions = get_all_ae_versions()

        if not ae_versions:
            print("❌ No Adobe After Effects installation folders found.")
            return

        print(f"Found {len(ae_versions)} target installation(s): {', '.join(ae_versions)}\n")

        for version in ae_versions:
            print(f"📂 Installing scripts for {version}...")

            # Copy to ScriptUI Panels
            destination_folder = get_ae_script_path(version)
            for script_name in SCRIPTS_TO_INSTALL:
                source_file_path = os.path.join(script_source_root, script_name)
                copy_script_file(source_file_path, destination_folder)

            # Copy to Scripts folder
            scripts_folder = get_ae_scripts_folder(version)
            for script_name in SCRIPTS_TO_SCRIPTS_FOLDER:
                source_file_path = os.path.join(script_source_root, script_name)
                copy_script_file(source_file_path, scripts_folder)

            print("-" * 20)

    except (FileNotFoundError, RuntimeError) as e:
        print(f"❌ A critical error occurred: {e}")

if __name__ == "__main__":
    # If on Windows, check for admin rights. If not admin, request them and restart.
    if platform.system() == "Windows":
        if not is_admin():
            print("Administrator privileges are required. Requesting permission...")
            run_as_admin()
            sys.exit() # Exit the non-admin instance

    # Run the main installer logic
    main()

    # Keep the console window open to see the output
    input("\nPress Enter to exit.")