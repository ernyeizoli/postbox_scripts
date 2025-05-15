import os
import shutil
import platform

def get_c4d_script_path():
    if platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Preferences/Maxon/Cinema 4D R26/library/scripts/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", "Cinema 4D R26", "library", "scripts/")
    raise RuntimeError("Unsupported OS")

def copy_folder(src, dst):
    dst_folder = os.path.join(dst, os.path.basename(src))
    if os.path.exists(dst_folder):
        shutil.rmtree(dst_folder)
    shutil.copytree(src, dst_folder)
    print(f"✅ Installed {os.path.basename(src)} to {dst_folder}")

def main():
    script_root = os.path.join("scripts", "C4d_Scripts")
    dst_root = get_c4d_script_path()

    for folder in os.listdir(script_root):
        full_path = os.path.join(script_root, folder)
        if os.path.isdir(full_path):
            copy_folder(full_path, dst_root)

if __name__ == "__main__":
    main()
