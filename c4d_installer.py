import os
import shutil
import platform

SCRIPTS = ["C4D_vray_filename_set", "C4D_vray_light_renamer", "C4D_vray_render_elements"]  # Add additional script folders here


def get_all_c4d_versions():
    """Return all Cinema 4D version folders under Maxon preferences (Windows or macOS)."""
    if platform.system() == "Darwin":
        preferences_path = os.path.expanduser("~/Library/Preferences/Maxon/")
    elif platform.system() == "Windows":
        preferences_path = os.path.join(os.getenv("APPDATA"), "Maxon")
    else:
        raise RuntimeError("Unsupported OS")

    if not os.path.exists(preferences_path):
        raise FileNotFoundError("Maxon preferences folder not found")

    return [
        folder
        for folder in os.listdir(preferences_path)
        if os.path.isdir(os.path.join(preferences_path, folder)) and "Cinema 4D" in folder
    ]


def get_c4d_script_path(version_folder):
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Preferences/Maxon/{version_folder}/library/scripts/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", version_folder, "library", "scripts/")
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
    script_root = os.path.join("scripts", "C4D_Scripts")
    c4d_versions = get_all_c4d_versions()

    for version_folder in c4d_versions:
        dst_root = get_c4d_script_path(version_folder)
        print(f"📂 Installing to: {dst_root}")
        for script_folder in SCRIPTS:
            full_path = os.path.join(script_root, script_folder)
            if os.path.isdir(full_path):
                copy_files(full_path, dst_root)


if __name__ == "__main__":
    main()
