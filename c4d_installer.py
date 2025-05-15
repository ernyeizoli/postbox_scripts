import os
import shutil
import platform

def get_c4d_script_path():
    if platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Preferences/Maxon/Maxon Cinema 4D 2025_FFA38A4B/library/scripts/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", "Maxon Cinema 4D 2025_FFA38A4B", "library", "scripts/")
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
    dst_root = get_c4d_script_path()

    for folder in os.listdir(script_root):
        full_path = os.path.join(script_root, folder)
        if os.path.isdir(full_path):
            copy_files(full_path, dst_root)

if __name__ == "__main__":
    main()
