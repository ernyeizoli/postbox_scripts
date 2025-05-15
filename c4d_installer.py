import os
import shutil
import platform

def get_c4d_version():
    preferences_path = os.path.expanduser("~/Library/Preferences/Maxon/")
    if os.path.exists(preferences_path):
        for folder in os.listdir(preferences_path):
            if folder.startswith("Maxon Cinema 4D"):
                return folder  # Extract the full name
    return None

def get_c4d_script_path(maxon_version=None):
    if platform.system() == "Darwin":
        # c4d set the c4d version

        return os.path.expanduser(f"~/Library/Preferences/Maxon/{maxon_version}/library/scripts/")
    elif platform.system() == "Windows":
        # c4d set the c4d version
        return os.path.join(os.getenv("APPDATA"), "Maxon", maxon_version, "library", "scripts/")
    raise RuntimeError("Unsupported OS")

def copy_files(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        if os.path.isfile(src_item):
            shutil.copy2(src_item, dst)
            print(f"✅ Copied {item} to {dst}")

def main():
    script_root = os.path.join("scripts", "C4d_Scripts")
    version = get_c4d_version()
    dst_root = get_c4d_script_path(version)


    for folder in os.listdir(script_root):
        full_path = os.path.join(script_root, folder)
        if os.path.isdir(full_path):
            copy_files(full_path, dst_root)

if __name__ == "__main__":
    main()
