# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
# This Prism plugin adds a "Publish to Fserver..." option to the media player's 
# right-click menu. It allows a user to copy the selected file to a destination 
# directory. The destination path is configured once per project and saved in 
# `.../00_PBV_DATA/fserver_path.txt`.
#
####################################################

import os
import logging
import shutil
from qtpy.QtWidgets import QAction, QMessageBox, QFileDialog

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


logger = logging.getLogger(__name__)


class Prism_PBV_FSERVER_publish_Functions(object):
    """
    Functions class for the Fserver publish plugin.
    
    This plugin adds a context menu item to the Prism media player that allows
    users to publish (copy) the right-clicked file to a configured Fserver 
    destination folder.
    """
    
    def __init__(self, core, plugin):
        """
        Initialize the plugin and register callbacks.
        
        Args:
            core: The Prism core instance - provides access to all Prism functionality
            plugin: Reference to this plugin instance
        """
        self.core = core
        self.plugin = plugin
        
        # Register callback for the media player's right-click context menu
        # This callback fires when user right-clicks on a media item in the media player
        self.core.registerCallback(
            "mediaPlayerContextMenuRequested", 
            self.mediaPlayerContextMenuRequested, 
            plugin=self
        )

    @err_catcher(name=__name__)
    def isActive(self):
        """
        Tells Prism whether this plugin should be loaded.
        
        Returns:
            bool: True if plugin should be active, False otherwise
        """
        return True

    @err_catcher(name=__name__)
    def mediaPlayerContextMenuRequested(self, origin, menu):
        """
        Called when user right-clicks in the media player.
        Adds a "Publish to Fserver..." option to the context menu.
        
        Args:
            origin: The widget/window that triggered the context menu
            menu: The QMenu object where we add our action
        """
        # Get the file paths from the media player's current sequence
        filepaths = origin.seq
        if not filepaths:
            return  # No files selected, don't add menu item
        
        # Add a separator line before our action for visual clarity
        menu.addSeparator()
        
        # Create the menu action with descriptive text
        publishAction = QAction("Publish to Fserver...", menu)
        
        # Connect the action's triggered signal to our publish function
        # Pass the first filepath - this is the file that was right-clicked
        publishAction.triggered.connect(
            lambda: self.publishToFserver(origin, filepaths[0])
        )
        
        # Add the action to the menu
        menu.addAction(publishAction)

    @err_catcher(name=__name__)
    def get_or_set_fserver_path(self, origin):
        """
        Gets the configured Fserver destination path, or prompts user to set one.
        
        The path is stored in a text file within the project's 00_PBV_DATA folder.
        This allows each project to have its own Fserver destination.
        
        Args:
            origin: Parent widget for dialogs
            
        Returns:
            str or None: The Fserver path if valid, None if cancelled
        """
        # Build path to config file: {project_root}/00_PBV_DATA/fserver_path.txt
        project_root = self.core.projectPath
        data_dir = os.path.join(project_root, "00_PBV_DATA")
        config_file_path = os.path.join(data_dir, "fserver_path.txt")

        # Ensure the data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Try to read existing path from config file
        fserver_path = None
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as f:
                fserver_path = f.read().strip()

        # Check if the saved path is valid and the directory exists
        if fserver_path and os.path.isdir(fserver_path):
            # --- Path is valid, just return it (no dialog) ---
            logger.info(f"Using existing Fserver path: {fserver_path}")
            return fserver_path
        else:
            # --- Path is not set or is invalid ---
            # Open a folder selection dialog so user can choose destination
            chosen_path = QFileDialog.getExistingDirectory(
                origin, "Please Select the Fserver Destination Directory"
            )

            if not chosen_path:
                # User cancelled the dialog
                logger.warning("User cancelled Fserver path selection.")
                return None
            
            # Normalize the path to use Windows backslashes for UNC paths
            chosen_path = os.path.normpath(chosen_path)
            
            # Save the chosen path to the config file for future use
            with open(config_file_path, 'w') as f:
                f.write(chosen_path)
            logger.info(f"Fserver path saved to: {chosen_path}")
            return chosen_path

    @err_catcher(name=__name__)
    def publishToFserver(self, origin, source_path):
        """
        Copies the right-clicked file directly to the Fserver destination.
        
        Args:
            origin: Parent widget for dialogs
            source_path: Path to the file that was right-clicked (will be copied)
        """
        try:
            # Normalize the source path
            source_path = os.path.normpath(source_path)
            
            # Check if source file exists
            if not os.path.isfile(source_path):
                QMessageBox.warning(
                    origin, 
                    "Warning", 
                    f"The selected file does not exist:\n{source_path}"
                )
                return

            # Step 1: Get or set the Fserver destination directory
            dest_dir = self.get_or_set_fserver_path(origin)
            if not dest_dir:
                return  # User cancelled destination selection

            # Step 2: Copy the file directly to the destination
            filename = os.path.basename(source_path)
            final_dest_path = os.path.join(dest_dir, filename)

            # Check if file already exists at destination
            if os.path.exists(final_dest_path):
                reply = QMessageBox.question(
                    origin,
                    "File Exists",
                    f"The file already exists at destination:\n{final_dest_path}\n\nOverwrite?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    logger.info("User cancelled overwrite.")
                    return

            # shutil.copy2 preserves file metadata (timestamps, permissions)
            shutil.copy2(source_path, final_dest_path)

            # Show success message
            QMessageBox.information(
                origin, 
                "Success", 
                f"File published successfully!\n\nFrom: {source_path}\n\nTo: {final_dest_path}"
            )
            logger.info(f"Copied '{source_path}' to '{final_dest_path}'")

        except Exception as e:
            # Catch any unexpected errors and show them to the user
            logger.error(f"Failed to publish file to Fserver: {e}")
            QMessageBox.critical(
                origin, 
                "Error", 
                f"Failed to publish file to Fserver: {e}"
            )
