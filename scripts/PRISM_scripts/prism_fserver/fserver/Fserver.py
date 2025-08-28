# This Prism plugin adds a "Publish to Fserver..." option to the media player's right-click menu.
# It allows a user to copy a selected file to a destination directory.
# The destination path is configured once per project and saved in `.../00_PBV_DATA/fserver_path.txt`.

name = "Fserver"
classname = "Fserver"

import os
import logging
import shutil
from qtpy.QtWidgets import QAction, QMessageBox, QFileDialog

from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)

class Fserver:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"
        self.core.registerCallback("mediaPlayerContextMenuRequested", self.mediaPlayerContextMenuRequested, plugin=self)

    @err_catcher(name=__name__)
    def mediaPlayerContextMenuRequested(self, origin, menu):
        filepaths = origin.seq
        if not filepaths:
            return
            
        menu.addSeparator()
        publishAction = QAction("Publish to Fserver...", menu)
        publishAction.triggered.connect(lambda: self.publishToFserver(origin, filepaths[0]))
        menu.addAction(publishAction)

    @err_catcher(name=__name__)
    def get_or_set_fserver_path(self, origin):
        project_root = self.core.projectPath
        data_dir = os.path.join(project_root, "00_PBV_DATA")
        config_file_path = os.path.join(data_dir, "fserver_path.txt")

        os.makedirs(data_dir, exist_ok=True)
        
        fserver_path = None
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as f:
                fserver_path = f.read().strip()

        # Check if the path is valid and exists
        if fserver_path and os.path.isdir(fserver_path):
            # --- BEHAVIOR 1: Path is valid ---
            # Show a message confirming the path that will be used.
            info_message = f"The Fserver path is currently set to:\n\n{fserver_path}"
            QMessageBox.information(origin, "Fserver Path Set", info_message)
            logger.info(f"Found valid Fserver path: {fserver_path}")
            return fserver_path
        else:
            # --- BEHAVIOR 2: Path is not set or is invalid ---
            # Immediately open the dialog to select a folder.
            chosen_path = QFileDialog.getExistingDirectory(
                origin, "Please Select the Fserver Destination Directory"
            )

            if not chosen_path:
                logger.warning("User cancelled Fserver path selection.")
                return None
            
            # Save the newly chosen path to the file
            with open(config_file_path, 'w') as f:
                f.write(chosen_path)
            logger.info(f"Fserver path saved to: {chosen_path}")
            return chosen_path


    @err_catcher(name=__name__)
    def publishToFserver(self, origin, startPath):
        try:
            dest_dir = self.get_or_set_fserver_path(origin)
            if not dest_dir:
                return

            startDir = os.path.dirname(startPath) if os.path.exists(startPath) else ""
            source_path, _ = QFileDialog.getOpenFileName(
                origin, "Select File to Publish", startDir, "All Files (*.*)"
            )

            if not source_path:
                logger.info("User cancelled file selection.")
                return

            if os.path.isfile(source_path):
                filename = os.path.basename(source_path)
                final_dest_path = os.path.join(dest_dir, filename)

                shutil.copy2(source_path, final_dest_path)

                QMessageBox.information(origin, "Success", f"File published successfully!\n\nTo: {final_dest_path}")
                logger.info(f"Copied '{source_path}' to '{final_dest_path}'")
            else:
                QMessageBox.warning(origin, "Warning", "The selected path is not a valid file.")

        except Exception as e:
            logger.error(f"Failed to publish file to Fserver: {e}")
            QMessageBox.critical(origin, "Error", f"Failed to publish file to Fserver: {e}")