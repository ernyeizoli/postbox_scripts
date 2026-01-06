import os
import shutil

# --- CONFIGURATION ---

# Destination paths for Prism2 plugins
PRISM_CUSTOM_PLUGINS_PATH = r"C:\ProgramData\Prism2\plugins\Custom"
PRISM_C4D_SCRIPTS_PATH = r"C:\ProgramData\Prism2\plugins\Cinema4D\Scripts"

# Source folders/files relative to scripts/PRISM_scripts
PLUGIN_FOLDER_TO_INSTALL = "PBV_FSERVER_publish"
PLUGIN_FILE_TO_INSTALL = r"PBV_AE_Import\PBV_AE_Import.py"
C4D_FILE_TO_OVERWRITE = r"PBV_Cinema4D\Prism_Cinema4D_Functions.py"


# --- CORE FILE OPERATIONS ---

def copy_folder(src, dst):
    """Copies an entire folder (recursively) to the destination directory."""
    if not os.path.exists(src):
        print(f"⚠️ Source folder not found, skipping: {src}")
        return False
    
    dst_folder = os.path.join(dst, os.path.basename(src))
    try:
        if os.path.exists(dst_folder):
            shutil.rmtree(dst_folder)
            print(f"  🔄 Removed existing folder: {dst_folder}")
        
        os.makedirs(dst, exist_ok=True)
        shutil.copytree(src, dst_folder)
        print(f"  ✅ Copied folder {os.path.basename(src)} to {dst_folder}")
        return True
    except PermissionError:
        print(f"  ❌ Error: Permission denied to write to {dst}")
        return False
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}")
        return False


def copy_file(src, dst_folder):
    """Copies a single file to the destination folder."""
    if not os.path.exists(src):
        print(f"⚠️ Source file not found, skipping: {src}")
        return False
    
    try:
        os.makedirs(dst_folder, exist_ok=True)
        dst_path = os.path.join(dst_folder, os.path.basename(src))
        shutil.copy2(src, dst_path)
        print(f"  ✅ Copied {os.path.basename(src)} to {dst_path}")
        return True
    except PermissionError:
        print(f"  ❌ Error: Permission denied to write to {dst_folder}")
        return False
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}")
        return False


def overwrite_file(src, dst_path):
    """Overwrites a file at the specified destination path."""
    if not os.path.exists(src):
        print(f"⚠️ Source file not found, skipping: {src}")
        return False
    
    try:
        dst_folder = os.path.dirname(dst_path)
        os.makedirs(dst_folder, exist_ok=True)
        
        if os.path.exists(dst_path):
            print(f"  🔄 Overwriting existing file: {dst_path}")
        
        shutil.copy2(src, dst_path)
        print(f"  ✅ Copied {os.path.basename(src)} to {dst_path}")
        return True
    except PermissionError:
        print(f"  ❌ Error: Permission denied to write to {dst_path}")
        return False
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}")
        return False


# --- MAIN EXECUTION ---

def main():
    """Main function to install Prism2 plugins and scripts."""
    print("=" * 50)
    print("Prism2 Plugin Installer")
    print("=" * 50)
    
    # Get the base directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prism_scripts_root = os.path.join(base_dir, "scripts", "PRISM_scripts")
    
    success_count = 0
    total_operations = 3
    
    # 1. Copy PBV_FSERVER_publish folder to plugins\Custom
    print(f"\n📂 Installing {PLUGIN_FOLDER_TO_INSTALL} to {PRISM_CUSTOM_PLUGINS_PATH}...")
    src_folder = os.path.join(prism_scripts_root, PLUGIN_FOLDER_TO_INSTALL)
    if copy_folder(src_folder, PRISM_CUSTOM_PLUGINS_PATH):
        success_count += 1
    
    # 2. Copy PBV_AE_Import.py to plugins\Custom
    print(f"\n📄 Installing PBV_AE_Import.py to {PRISM_CUSTOM_PLUGINS_PATH}...")
    src_file = os.path.join(prism_scripts_root, PLUGIN_FILE_TO_INSTALL)
    if copy_file(src_file, PRISM_CUSTOM_PLUGINS_PATH):
        success_count += 1
    
    # 3. Overwrite Prism_Cinema4D_Functions.py in Cinema4D\Scripts
    print(f"\n📄 Overwriting Prism_Cinema4D_Functions.py in {PRISM_C4D_SCRIPTS_PATH}...")
    src_c4d_file = os.path.join(prism_scripts_root, C4D_FILE_TO_OVERWRITE)
    dst_c4d_file = os.path.join(PRISM_C4D_SCRIPTS_PATH, "Prism_Cinema4D_Functions.py")
    if overwrite_file(src_c4d_file, dst_c4d_file):
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Installation complete: {success_count}/{total_operations} operations successful")
    print("=" * 50)


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit.")
