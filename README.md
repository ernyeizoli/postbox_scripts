# 🛠️ Postbox Scripts

Some scripts for use internally to automate the repetitive tasks.

This guide explains the workflow for installing and maintaining the Postbox Scripts for Cinema 4D and After Effects.

---

##  Workflow

This repository is designed for a two-stage deployment to ensure all artists are using the same, stable set of tools.

#### Stage 1: Central Repository Update (Admin/TD Task)

The official released versions of the scripts are maintained on the shared drive. The designated folder on this drive is a Git repository cloned from GitHub.

-   **Location:** `creative\work\Postbox\01_Config\Postbox_scripts`
-   **Action:** A technical director or admin updates this central folder by running `git pull` when this is run here the current release from the github is released. This fetches the latest, tested changes from the master GitHub repository, making them the new official version for the studio.

#### Stage 2: Local Machine Update (Artist Machines)

Each artist's computer does not need Git. Instead, installer scripts (`ae_installer.py` and `c4d_installer.py`) are run to copy the tools from the central network drive to the local application folders.

-   **Trigger:** This can be done manually, or set up to run automatically on system restart.
-   **Action:** The installer scripts detect all local versions of After Effects and Cinema 4D and copy the latest scripts from the shared drive into the correct local folders. This ensures that every artist has the most up-to-date toolset without needing to interact with Git directly.

#### Stage 3: Cinema 4D

Extensions -> Script manager, from the dropdown select the script and drag and drop to the toolbar.

#### Stage 3: AFter Effects

Window -> select the wanted script.

---

## Scripts Included

Here is a breakdown of the scripts included in this repository.

### After Effects Scripts

These scripts are installed into the `ScriptUI Panels` folder for each detected After Effects version.

-   **`EXR_organizer.jsx` (The Ultimate EXR Organizer)**
    A powerful panel with three main functions to manage complex multi-pass EXR renders.
    -   **FLATTEN:** Replaces selected pre-compositions with their source footage, perfectly copying all transformations, effects, and keyframes.
    -   **ORGANIZE:** Intelligently structures your composition. It identifies and sorts render passes (like Light Selects, Cryptomatte, Extra Tex), sets their blending modes, creates adjustment layers for grading (Colorista, OCIO), and applies a base Exposure effect.
    -   **DELETE UNUSED:** Safely cleans your composition by removing any hidden layers that are not being used as a track matte or a parent in a layer hierarchy.

-   **`PBV_Comp_helper_12.jsx`**
    Deprecated, basically the same but with more bugs.

### Cinema 4D Scripts

These Python scripts are installed into the `library/scripts` folder for each detected Cinema 4D version, making them available in the scripts menu.

-   **`C4D_vray_filename_set`**
    -   `C4D_filename_set.py`: Automates the process of setting standardized output paths and filenames for V-Ray renders, ensuring all files follow a consistent studio naming convention.

-   **`C4D_vray_light_renamer`**
    -   `C4D_vray_light_renamer.py`: Quickly renames all V-Ray lights in the scene based on a defined pattern. Indispensable for keeping complex lighting setups clean and organized.

-   **`C4D_vray_render_elements`**
    -   `C4D_Vray_light_pass_creator.py`: Automatically generates V-Ray Light Select render elements for every light in the scene, saving significant time during render setup.

-   **`C4D_vray_materials (in progress)`**
    -   `C4D_vray_material_from_folder.py`: Creates a complete V-Ray material by simply pointing it to a folder containing PBR texture maps (e.g., diffuse, reflection, glossiness, normal).

### Installer Scripts

These scripts are the core of the auto-update system. They should be ran from the place they are in with **`python c4d_installer.py`**  and **`python ae_installer.py`** commands

-   **`c4d_installer.py`**:
    Scans the machine for all Cinema 4D installations and copies the relevant C4D scripts from the central network drive to each version's user preferences folder.

-   **`ae_installer.py`**:
    Performs the same function for After Effects. It detects all AE installations and copies the `.jsx` scripts to the `ScriptUI Panels` folder, automatically requesting administrator privileges on Windows if needed.
