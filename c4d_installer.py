import os
import shutil
import platform

# Add the names of the script folders you want to install
SCRIPTS = ["C4D_vray_filename_set", "C4D_vray_filename_set_REMIX", "C4D_vray_light_renamer", "C4D_vray_render_elements"]
PLUGINS = ["C4D_pbv_gui"]


def get_all_c4d_versions():
    """Return all Cinema 4D version folders under Maxon preferences (Windows or macOS) that do not have a postfix."""
    if platform.system() == "Darwin":
        preferences_path = os.path.expanduser("~/Library/Preferences/Maxon/")
    elif platform.system() == "Windows":
        preferences_path = os.path.join(os.getenv("APPDATA"), "Maxon")
    else:
        raise RuntimeError("Unsupported OS")

    if not os.path.exists(preferences_path):
        raise FileNotFoundError("Maxon preferences folder not found")

    # The list comprehension now filters out folders ending in '_x', '_c', etc.
    return [
        folder
        for folder in os.listdir(preferences_path)
        if (
            os.path.isdir(os.path.join(preferences_path, folder))
            and "Cinema 4D" in folder
            # ADDED: This condition excludes folders with a postfix like '_c' or '_x'.
            and not (len(folder) > 2 and folder[-2] == '_' and folder[-1].isalpha())
        )
    ]


def get_c4d_script_path(version_folder):
    """Constructs the path to the 'library/scripts' folder for a given C4D version."""
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Preferences/Maxon/{version_folder}/library/scripts/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", version_folder, "library", "scripts/")
    else:
        raise RuntimeError("Unsupported OS")


def get_c4d_plugin_path(version_folder):
    """Constructs the path to the 'plugins' folder for a given C4D version."""
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Preferences/Maxon/{version_folder}/plugins/")
    elif platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Maxon", version_folder, "plugins/")
    else:
        raise RuntimeError("Unsupported OS")


def copy_files(src, dst):
    """Copies all files from a source directory to a destination directory."""
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        if os.path.isfile(src_item):
            shutil.copy2(src_item, dst)
            print(f"✅ Copied {item} to {dst}")


def copy_folder(src, dst):
    """Copies an entire folder (recursively) to the destination directory."""
    if not os.path.exists(src):
        print(f"⚠️ Plugin folder not found, skipping: {src}")
        return
    dst_folder = os.path.join(dst, os.path.basename(src))
    if os.path.exists(dst_folder):
        shutil.rmtree(dst_folder)
    shutil.copytree(src, dst_folder)
    print(f"✅ Copied plugin folder {src} to {dst_folder}")


def main():
    """Main function to find C4D versions and copy scripts and plugins."""
    try:
        # Get the directory where this script is located
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_root = os.path.join(base_dir, "scripts", "C4D_Scripts")
        plugin_root = script_root  
        c4d_versions = get_all_c4d_versions()

        if not c4d_versions:
            print("❌ No matching Cinema 4D installation folders found.")
            return

        print(f"Found {len(c4d_versions)} target installation(s): {', '.join(c4d_versions)}")

        for version_folder in c4d_versions:
            # Scripts
            dst_script_root = get_c4d_script_path(version_folder)
            print(f"\n📂 Installing scripts to: {dst_script_root}")
            for script_folder in SCRIPTS:
                full_path = os.path.join(script_root, script_folder)
                if os.path.isdir(full_path):
                    copy_files(full_path, dst_script_root)
                else:
                    print(f"⚠️ Script folder not found, skipping: {full_path}")

            # Plugins
            dst_plugin_root = get_c4d_plugin_path(version_folder)
            print(f"\n📦 Installing plugins to: {dst_plugin_root}")
            for plugin_folder in PLUGINS:
                full_plugin_path = os.path.join(plugin_root, plugin_folder)
                copy_folder(full_plugin_path, dst_plugin_root)

    except (FileNotFoundError, RuntimeError) as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()