import os
import shutil
import platform

SCRIPTS = ["Vray_render_elements"]  # Add more folder names here if needed


def get_c4d_version():
    if platform.system() == "Darwin":
        preferences_path = os.path.expanduser("~/Library/Preferences/Maxon/")
    elif platform.system() == "Windows":
        preferences_path = os.path.join(os.getenv("APPDATA"), "Maxon")
    else:
        raise RuntimeError("Unsupported OS")

    if not os.path.exists(preferences_path):
        raise FileNotFoundError("Maxon preferences folder not found")

    for folder in sorted(os.listdir(preferences_path), reverse=True):
        if "Cinema 4D" in folder:
            return folder
    raise RuntimeError("Could not detect installed Cinema 4D version")


def get_c4d_script_path(maxon_version):
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Preferences/Maxon/{maxon_version}/library/scripts/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", maxon_version, "library", "scripts/")
    else:
        raise RuntimeError("Unsupported OS")


def copy_files(src, dst):
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        if os.path.isfile(src_item):
            shutil.copy2(src_item, dst)
            print(f"✅ Copied {item} to {dst}")


def main():
    script_root = os.path.join("scripts", "C4d_Scripts")
    version = get_c4d_version()
    dst_root = get_c4d_script_path(version)

    for script_folder in SCRIPTS:
        full_path = os.path.join(script_root, script_folder)
        if os.path.isdir(full_path):
            copy_files(full_path, dst_root)


if __name__ == "__main__":
    main()
