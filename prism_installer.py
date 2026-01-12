import os
import shutil

# --- CONFIGURATION ---

# Destination paths for Prism2 plugins
PRISM_PLUGINS_PATH = r"C:\ProgramData\Prism2\plugins"
PRISM_C4D_SCRIPTS_PATH = r"C:\ProgramData\Prism2\plugins\Cinema4D\Scripts"

# Legacy items to clean up from old installations (in plugins/Custom)
LEGACY_ITEMS = [
    # Old single-file PBV_AE_Import (before folder structure)
    os.path.join(PRISM_PLUGINS_PATH, "Custom", "PBV_AE_Import"),
    # Old fserver folder
    os.path.join(PRISM_PLUGINS_PATH, "Custom", "fserver"),
    # Old test folders
    os.path.join(PRISM_PLUGINS_PATH, "Custom", "test"),
    os.path.join(PRISM_PLUGINS_PATH, "Custom", "test2"),
    # Old PBV_FSERVER_publish in Custom
    os.path.join(PRISM_PLUGINS_PATH, "Custom", "PBV_FSERVER_publish"),
]


# --- CORE FILE OPERATIONS ---

def cleanup_legacy_items():
    """Remove old/legacy files and folders from previous installations."""
    print("\n🧹 Cleaning up legacy installations...")
    cleaned_count = 0
    
    for item_path in LEGACY_ITEMS:
        if os.path.exists(item_path):
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"  🗑️ Removed legacy file: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"  🗑️ Removed legacy folder: {item_path}")
                cleaned_count += 1
            except Exception as e:
                print(f"  ⚠️ Could not remove {item_path}: {e}")
    
    if cleaned_count == 0:
        print("  ✓ No legacy items found")
    else:
        print(f"  ✓ Cleaned up {cleaned_count} legacy item(s)")


def copy_folder(src, dst):
    """Copies an entire folder (recursively) to the destination directory."""
    if not os.path.exists(src):
        print(f"  ⚠️ Source folder not found, skipping: {src}")
        return False
    
    dst_folder = os.path.join(dst, os.path.basename(src))
    try:
        if os.path.exists(dst_folder):
            shutil.rmtree(dst_folder)
            print(f"  🔄 Removed existing folder: {os.path.basename(dst_folder)}")
        
        os.makedirs(dst, exist_ok=True)
        shutil.copytree(src, dst_folder)
        print(f"  ✅ Installed: {os.path.basename(src)}")
        return True
    except PermissionError:
        print(f"  ❌ Error: Permission denied to write to {dst}")
        return False
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}")
        return False


def overwrite_file(src, dst_path):
    """Overwrites a file at the specified destination path."""
    if not os.path.exists(src):
        print(f"  ⚠️ Source file not found, skipping: {src}")
        return False
    
    try:
        dst_folder = os.path.dirname(dst_path)
        os.makedirs(dst_folder, exist_ok=True)
        
        if os.path.exists(dst_path):
            print(f"  🔄 Overwriting: {os.path.basename(dst_path)}")
        
        shutil.copy2(src, dst_path)
        print(f"  ✅ Installed: {os.path.basename(src)}")
        return True
    except PermissionError:
        print(f"  ❌ Error: Permission denied to write to {dst_path}")
        return False
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}")
        return False


def install_all_plugins(prism_scripts_folder, dest_folder):
    """
    Installs all plugin folders from PRISM_scripts to the destination.
    
    Args:
        prism_scripts_folder: Path to scripts/PRISM_scripts folder
        dest_folder: Destination folder (plugins/)
        
    Returns:
        tuple: (success_count, total_count)
    """
    if not os.path.exists(prism_scripts_folder):
        print(f"  ⚠️ PRISM_scripts folder not found: {prism_scripts_folder}")
        return 0, 0
    
    # Get all subdirectories in PRISM_scripts (each is a plugin)
    plugin_folders = [
        d for d in os.listdir(prism_scripts_folder)
        if os.path.isdir(os.path.join(prism_scripts_folder, d))
    ]
    
    success_count = 0
    for plugin_name in plugin_folders:
        src_path = os.path.join(prism_scripts_folder, plugin_name)
        if copy_folder(src_path, dest_folder):
            success_count += 1
    
    return success_count, len(plugin_folders)


# --- MAIN EXECUTION ---

def main():
    """Main function to install Prism2 plugins and scripts."""
    print("=" * 60)
    print("  Prism2 Plugin Installer")
    print("=" * 60)
    
    # Get the base directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prism_scripts_folder = os.path.join(base_dir, "scripts", "PRISM_scripts")
    prism_apps_folder = os.path.join(base_dir, "scripts", "PRISM_Apps")
    
    # Step 1: Clean up legacy installations
    cleanup_legacy_items()
    
    # Step 2: Install all plugins from PRISM_scripts to plugins/
    print(f"\n📂 Installing plugins to {PRISM_PLUGINS_PATH}...")
    plugin_success, plugin_total = install_all_plugins(
        prism_scripts_folder, 
        PRISM_PLUGINS_PATH
    )
    
    # Step 3: Install Cinema4D app override
    print(f"\n📄 Installing Cinema4D app override to {PRISM_C4D_SCRIPTS_PATH}...")
    src_c4d_file = os.path.join(prism_apps_folder, "PBV_Cinema4D", "Prism_Cinema4D_Functions.py")
    dst_c4d_file = os.path.join(PRISM_C4D_SCRIPTS_PATH, "Prism_Cinema4D_Functions.py")
    c4d_success = 1 if overwrite_file(src_c4d_file, dst_c4d_file) else 0
    
    # Summary
    total_success = plugin_success + c4d_success
    total_operations = plugin_total + 1
    
    print("\n" + "=" * 60)
    print(f"  Installation complete: {total_success}/{total_operations} operations successful")
    if total_success == total_operations:
        print("  ✅ All plugins installed successfully!")
    else:
        print("  ⚠️ Some operations failed - check messages above")
    print("=" * 60)


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit.")
