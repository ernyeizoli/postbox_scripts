import ctypes
import os
import shutil
import sys

def is_admin():
    """Checks if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-runs the script with administrative privileges."""
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None,
        1
    )

def copy_file():
    """Copies the file from the source to the destination."""
    #source_path = r"\\10.10.101.10\creative\work\Postbox\01_Config\Postbox_scripts\EXR_organizer.jsx"
    # Make sure the source_path includes the FULL FILENAME
    source_path = r"C:\Users\User\Documents\dev\postbox_scripts\scripts\AE_Scripts\EXR_organizer.jsx"

    # The destination path is already correct
    destination_path = r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\Scripts\ScriptUI Panels\EXR_organizer.jsx"

    try:
        print(f"Attempting to copy file from: {source_path}")
        print(f"To: {destination_path}")
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        shutil.copy(source_path, destination_path)
        print("\nFile copied successfully! ✅")

    except FileNotFoundError:
        print(f"\nError: Source file not found at {source_path}. ❌")
        print("Please ensure the network drive is accessible.")
    except PermissionError:
        print(f"\nError: Permission denied to write to {destination_path}. ❌")
        print("Please ensure you have the necessary administrator rights.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e} ❌")

if __name__ == "__main__":
    if is_admin():
        copy_file()
    else:
        print("Administrator privileges are required. Requesting permission...")
        run_as_admin()

    # This input is to keep the console window open after the script finishes
    # so the user can see the output.
    input("\nPress Enter to exit.")