# Prism Plugin: Publish to F_server

***

## Overview

This plugin provides a simple way for users to publish media versions from the Prism Project Browser directly to a designated server, referred to as `F_server`. It adds a context menu option that, when clicked, opens a dialog window where the user can confirm or change the destination path before initiating the file transfer.

***

## User Interface (UI)

The plugin introduces two new UI elements.

### Context Menu Integration

When a user right-clicks on any media version (e.g., a playblast, render) in the Prism Project Browser, a new option will appear in the context menu:

* **`Publish to F_server`** 📁

This option will be placed logically among other publishing or export-related actions.

### Publishing Window

Clicking the `Publish to F_server` menu item will open a modal dialog window with the following components:

1.  **Window Title:** "Publish to F_server"
2.  **Informational Label:** A simple text label, e.g., "Review the destination path and click 'Publish'."
3.  **Path Input Field:** A text input field displaying the automatically generated destination path.
    * The user can **manually edit** this path.
    * This field will be pre-populated based on the project's context.
4.  **Buttons:**
    * **`Publish`:** The primary action button. When clicked, it initiates the file copy process to the path specified in the input field. The window closes upon success.
    * **`Cancel`:** Closes the window without performing any action.

***

## Workflow

The user workflow is designed to be quick and intuitive.

1.  **Right-Click:** The user navigates to a media version in the Prism Project Browser and right-clicks it.
2.  **Select Action:** The user selects `Publish to F_server` from the context menu.
3.  **Confirm Path:** The "Publish to F_server" window appears. It displays a default destination path, constructed from the current project context.
    * *Example Default Path:* `F:/PROJECTS/{project_name}/{category}/{asset_name}/publish/v{version_number}/`
4.  **Modify Path (Optional):** If the default path is incorrect or needs to be changed, the user can type a new path directly into the input field.
5.  **Initiate Publish:** The user clicks the **`Publish`** button.
6.  **Process:** The plugin copies the selected media version's files to the final destination path on `F_server`.
7.  **Feedback:** Prism's status bar will show a notification indicating whether the publish was successful or if it failed.

***

## Technical Implementation

### File Structure

The plugin will be contained within a single folder in the Prism plugins directory (`Prism/Plugins/Custom/`).