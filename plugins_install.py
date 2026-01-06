import os
import shutil
import platform
import re

# --- CONFIGURATION ---

# Source location for INSYDIUM plugin
INSYDIUM_SOURCE_PATH = r"\\10.10.101.10\creative\work\Postbox\09_Plugin_Scripts\CINEMA 4D\xparticles"

# Pattern to match INSYDIUM folders with version numbers (e.g., INSYDIUM_1856)
INSYDIUM_VERSIONED_PATTERN = re.compile(r"^INSYDIUM_(\d+)$", re.IGNORECASE)
# Pattern to match plain INSYDIUM folder (no version number)
INSYDIUM_PLAIN_PATTERN = re.compile(r"^INSYDIUM$", re.IGNORECASE)


# --- HELPER FUNCTIONS ---

def get_insydium_version(folder_name):
    """
    Extract version number from INSYDIUM folder name.
    Returns 0 for plain 'INSYDIUM' folder (treated as oldest version).
    Returns None if not a valid INSYDIUM folder.
    """
    # Check for versioned folder (e.g., INSYDIUM_1856)
    match = INSYDIUM_VERSIONED_PATTERN.match(folder_name)
    if match:
        return int(match.group(1))
    
    # Check for plain INSYDIUM folder (treat as version 0)
    if INSYDIUM_PLAIN_PATTERN.match(folder_name):
        return 0
    
    return None


def find_highest_insydium(path):
    """Find the INSYDIUM folder with the highest version number in the given path."""
    if not os.path.exists(path):
        return None, None
    
    highest_version = -1
    highest_folder = None
    
    try:
        for folder in os.listdir(path):
            if os.path.isdir(os.path.join(path, folder)):
                version = get_insydium_version(folder)
                if version is not None and version > highest_version:
                    highest_version = version
                    highest_folder = folder
    except PermissionError:
        print(f"  ⚠️ Permission denied accessing: {path}")
        return None, None
    
    if highest_folder:
        return highest_folder, highest_version
    return None, None


def find_all_insydium_folders(path):
    """Find all INSYDIUM folders in the given path, returns list of (folder_name, version) tuples."""
    if not os.path.exists(path):
        return []
    
    insydium_folders = []
    try:
        for folder in os.listdir(path):
            if os.path.isdir(os.path.join(path, folder)):
                version = get_insydium_version(folder)
                if version is not None:
                    insydium_folders.append((folder, version))
    except PermissionError:
        pass
    
    return insydium_folders


def cleanup_old_insydium(plugins_path, keep_folder):
    """Remove all INSYDIUM folders except the one to keep."""
    all_folders = find_all_insydium_folders(plugins_path)
    removed_count = 0
    
    for folder_name, version in all_folders:
        if folder_name != keep_folder:
            folder_path = os.path.join(plugins_path, folder_name)
            try:
                shutil.rmtree(folder_path)
                print(f"  🗑️ Removed old version: {folder_name}")
                removed_count += 1
            except PermissionError:
                print(f"  ⚠️ Could not remove {folder_name} (permission denied)")
            except Exception as e:
                print(f"  ⚠️ Could not remove {folder_name}: {e}")
    
    return removed_count


def get_all_c4d_versions():
    """Return all Cinema 4D version folders under Maxon preferences (Windows or macOS)."""
    if platform.system() == "Darwin":  # macOS
        preferences_path = os.path.expanduser("~/Library/Preferences/Maxon/")
    elif platform.system() == "Windows":
        preferences_path = os.path.join(os.getenv("APPDATA"), "Maxon")
    else:
        raise RuntimeError("Unsupported OS")

    if not os.path.exists(preferences_path):
        raise FileNotFoundError("Maxon preferences folder not found")

    # Include ALL Cinema 4D folders (including _x, _c suffixes for rendering)
    return [
        folder
        for folder in os.listdir(preferences_path)
        if (
            os.path.isdir(os.path.join(preferences_path, folder))
            and "Cinema 4D" in folder
        )
    ]


def get_c4d_plugin_path(version_folder):
    """Constructs the path to the 'plugins' folder for a given C4D version."""
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Preferences/Maxon/{version_folder}/plugins/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", version_folder, "plugins")
    else:
        raise RuntimeError("Unsupported OS")


def count_files(path):
    """Count total number of files in a directory recursively."""
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
    return count


def copy_with_progress(src_folder, dst_folder):
    """
    Copy a folder with progress display.
    Shows file count and percentage as files are copied.
    """
    total_files = count_files(src_folder)
    copied_files = [0]  # Use list for mutable counter in nested function
    
    def copy_progress(src, dst, *, follow_symlinks=True):
        """Custom copy function that updates progress."""
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
        copied_files[0] += 1
        percent = (copied_files[0] / total_files) * 100 if total_files > 0 else 100
        # Print progress on the same line
        print(f"\r  📦 Progress: {copied_files[0]}/{total_files} files ({percent:.0f}%)", end="", flush=True)
        return dst
    
    shutil.copytree(src_folder, dst_folder, copy_function=copy_progress)
    print()  # New line after progress completes


def copy_insydium_folder(src_folder, dst_plugins_path, old_folder_name=None):
    """
    Copy INSYDIUM folder to destination with progress display.
    Removes old INSYDIUM folder after successful copy.
    """
    dst_folder = os.path.join(dst_plugins_path, os.path.basename(src_folder))
    
    try:
        # Create plugins directory if it doesn't exist
        os.makedirs(dst_plugins_path, exist_ok=True)
        
        # Count files first
        total_files = count_files(src_folder)
        print(f"  📦 Copying {os.path.basename(src_folder)} ({total_files} files)...")
        
        # Copy the new INSYDIUM folder with progress
        copy_with_progress(src_folder, dst_folder)
        print(f"  ✅ Copied successfully to {dst_folder}")
        
        # Remove old folder after successful copy
        if old_folder_name:
            old_folder_path = os.path.join(dst_plugins_path, old_folder_name)
            if os.path.exists(old_folder_path):
                shutil.rmtree(old_folder_path)
                print(f"  🗑️ Removed old version: {old_folder_name}")
        
        return True
        
    except PermissionError:
        print(f"\n  ❌ Error: Permission denied to write to {dst_plugins_path}")
        return False
    except Exception as e:
        print(f"\n  ❌ An unexpected error occurred: {e}")
        return False


# --- MAIN EXECUTION ---

def main():
    """Main function to install the latest INSYDIUM plugin to all C4D versions."""
    print("=" * 60)
    print("INSYDIUM Plugin Installer")
    print("=" * 60)
    
    # Find the highest version INSYDIUM folder in source
    print(f"\n🔍 Scanning source: {INSYDIUM_SOURCE_PATH}")
    source_folder, source_version = find_highest_insydium(INSYDIUM_SOURCE_PATH)
    
    if not source_folder:
        print("❌ No INSYDIUM folder found in source location.")
        return
    
    print(f"✅ Found latest version: {source_folder} (v{source_version})")
    source_full_path = os.path.join(INSYDIUM_SOURCE_PATH, source_folder)
    
    # Get all C4D installations
    try:
        c4d_versions = get_all_c4d_versions()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"❌ Error finding C4D installations: {e}")
        return
    
    if not c4d_versions:
        print("❌ No Cinema 4D installation folders found.")
        return
    
    print(f"\n📂 Found {len(c4d_versions)} C4D installation(s): {', '.join(c4d_versions)}")
    
    updated_count = 0
    skipped_count = 0
    
    for version in c4d_versions:
        print(f"\n{'─' * 40}")
        print(f"📁 Processing: {version}")
        
        plugins_path = get_c4d_plugin_path(version)
        
        # Check current installed version
        installed_folder, installed_version = find_highest_insydium(plugins_path)
        
        if installed_folder:
            print(f"  Currently installed: {installed_folder} (v{installed_version})")
            
            if source_version > installed_version:
                print(f"  ⬆️ Upgrade available: v{installed_version} → v{source_version}")
                if copy_insydium_folder(source_full_path, plugins_path, installed_folder):
                    updated_count += 1
            else:
                print(f"  ✓ Already up to date (v{installed_version})")
                # Clean up any old INSYDIUM folders that might still exist
                cleanup_old_insydium(plugins_path, installed_folder)
                skipped_count += 1
        else:
            print(f"  No INSYDIUM installed, installing v{source_version}...")
            if copy_insydium_folder(source_full_path, plugins_path):
                updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"Installation complete: {updated_count} updated, {skipped_count} already up to date")
    print("=" * 60)


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit.")
