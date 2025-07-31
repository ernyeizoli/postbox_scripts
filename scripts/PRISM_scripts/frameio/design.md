# Prism to Frame.io Publisher Plugin - Design Document

This document outlines the design for a Prism Pipeline plugin that allows users to publish media versions directly to Frame.io.

## 1. Overview

The primary goal of this plugin is to streamline the review workflow by integrating Prism Pipeline with Frame.io. It will add a new action to the Project Browser, enabling users to right-click any media version (e.g., a playblast, render) and upload it to a specified path on Frame.io. A simple UI will allow the user to confirm or edit the destination path before publishing.

***

## 2. User Interface (UI) and Workflow

The user experience is designed to be straightforward and requires minimal steps.

### 2.1 Context Menu Integration

When a user right-clicks a media version inside the Prism Project Browser, a new option will appear in the context menu:

* **Menu Item:** "Publish to FrameIO"
* **Icon:** A small Frame.io logo will be displayed next to the menu item for quick identification.

*(Image: A mockup showing the right-click menu in Prism's Project Browser with the "Publish to FrameIO" option visible.)*

### 2.2 Publisher Dialog Window

Clicking "Publish to FrameIO" will open a modal dialog window with the following elements:

1.  **Instructional Text:** A label at the top will inform the user, e.g., "Review the destination path for Frame.io."
2.  **Path Input Field:** A line edit box will display a pre-filled, default destination path.
    * **Default Path:** The path will be automatically generated based on the Prism project structure. The default format will be:
        `{Prism Project Name} / {Asset/Shot Name} / {Task Type} /`
        *Example*: `Project_X / SH010 / lighting /`
    * **Editable:** The user can freely modify this path before publishing.
3.  **Action Buttons:**
    * **Publish:** This button initiates the upload process to the path specified in the input field. The window will close upon clicking.
    * **Cancel:** This button closes the dialog window without performing any action.

*(Image: A mockup of the simple dialog window with the path input field and "Publish" / "Cancel" buttons.)*

### 2.3 User Workflow

The process from the user's perspective is as follows:

1.  **Navigate:** The user browses to a media version in the Prism Project Browser.
2.  **Right-Click:** The user right-clicks the desired version to open the context menu.
3.  **Select Action:** The user clicks "Publish to FrameIO".
4.  **Confirm Path:** The Publisher Dialog appears. The user reviews the default path.
5.  **Publish:** The user either clicks "Publish" to accept the default path or modifies it first and then clicks "Publish".
6.  **Notification:** A Prism status message will appear in the corner of the screen, indicating whether the upload was successful or failed.

***

## 3. Technical Implementation

### 3.1 Prism Integration

* **Context Menu Hook:** The plugin will use Prism's `ContextMenuActions` hook. A script will check if the selected item is a media version (`state/output`) and, if so, add the "Publish to FrameIO" action.
* **Action Execution:** The action will trigger a Python function that creates and displays the Publisher Dialog window.

### 3.2 Frame.io API Communication

* **Client:** The official `frameioclient` Python library will be used for all communication with the Frame.io API. This library will need to be included in the plugin's environment.
* **Authentication:** The Frame.io API developer token will be stored securely. A good place would be in the plugin's settings, accessible via `pcore.getPluginSettings('FrameIO')`.
* **Upload Logic:**
    1.  The script will retrieve the active Frame.io team and find the project matching the Prism project name. If it doesn't exist, it should be created.
    2.  It will then parse the path from the UI and recursively find or create the necessary folder structure on Frame.io.
    3.  Finally, it will upload the media file to the target destination folder.

### 3.3 UI Backend

* **Framework:** The UI will be built using **PySide2/PyQt5**, consistent with Prism's environment.
* **Dialog Logic:** The dialog class will be initialized with the selected media file path and the context from Prism. It will be responsible for generating the default Frame.io path, capturing user input, and passing the final path to the uploader function when the "Publish" button is clicked.

***

## 4. Proposed File Structure

The plugin will be organized within its own directory in the Prism plugins folder: