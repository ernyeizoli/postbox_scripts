import sys
import os
import re

def find_newest_version(input_path):
    """
    Finds the newest version of a path by looking for a versioned folder
    (e.g., 'name_v0001'), scanning for higher versions, and then updating
    both the directory path and the filename to match the new version.
    """
    # Regex to find a basename, a '_v', and four digits.
    # e.g., 'TER_FORT_TEST_SC010_v0001'
    version_pattern = re.compile(r'^(.*)_v(\d{4})$', re.IGNORECASE)

    # Normalize the input path and determine if it's a file
    norm_input_path = os.path.normpath(input_path)
    is_file = os.path.splitext(norm_input_path)[1] != ""
    original_filename = os.path.basename(norm_input_path)
    
    # *** FIX: Start walking from the directory, not the full file path ***
    if is_file:
        path_to_check = os.path.dirname(norm_input_path)
    else:
        path_to_check = norm_input_path
    
    # This will store parts of the path that are inside the versioned folder
    # (e.g., a 'Main' subfolder)
    sub_path_parts = []

    while True:
        # If the path to check is empty or we've hit the root, stop.
        if not path_to_check or os.path.dirname(path_to_check) == path_to_check:
            break

        current_basename = os.path.basename(path_to_check)
        match = version_pattern.fullmatch(current_basename)

        if match:
            # --- We found the versioned folder ---
            base_name = match.group(1)
            current_version_num = int(match.group(2))
            
            parent_dir = os.path.dirname(path_to_check)
            highest_version_num = current_version_num
            newest_version_folder = current_basename
            
            try:
                # Scan the parent directory for other versions
                for entry in os.scandir(parent_dir):
                    if entry.is_dir():
                        scan_match = version_pattern.fullmatch(entry.name)
                        if scan_match and scan_match.group(1) == base_name:
                            v_num = int(scan_match.group(2))
                            if v_num > highest_version_num:
                                highest_version_num = v_num
                                newest_version_folder = entry.name
            except FileNotFoundError:
                return f"Error: Cannot access directory '{parent_dir}'."

            # --- Construct the new path and filename ---
            sub_path_parts.reverse()
            new_dir_path = os.path.join(parent_dir, newest_version_folder, *sub_path_parts)

            if is_file:
                old_v_str = f"v{current_version_num:04d}"
                new_v_str = f"v{highest_version_num:04d}"
                new_filename = original_filename.replace(old_v_str, new_v_str)
                final_path = os.path.join(new_dir_path, new_filename)
            else:
                final_path = new_dir_path
            
            return os.path.normpath(final_path)

        # --- If not a versioned folder, go one level up ---
        sub_path_parts.append(current_basename)
        path_to_check = os.path.dirname(path_to_check)

    return "No versioned folder (e.g., 'name_v0001') found in path."

if __name__ == "__main__":
    if len(sys.argv) > 1:
        footage_path = sys.argv[1]
        processed_path = find_newest_version(footage_path)
        print(processed_path)
    else:
        print("Error: No footage path provided.", file=sys.stderr)