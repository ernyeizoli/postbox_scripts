# -*- coding: utf-8 -*-
#
# PRISM - Pipeline for animation and VFX projects
# www.prism-pipeline.com
#

import logging
import os
from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from qtpy.QtWidgets import QAction
from qtpy.QtCore import Qt

# Define the logger for this plugin
logger = logging.getLogger(__name__)

class Prism_publish_to_fserver_Functions(object):
    def __init__(self, core, plugin):
        """Initializes the plugin and connects to Prism's event system."""
        self.core = core
        self.plugin = plugin
        self.originBrowser = None
        # Register the callbacks for your plugin
#        self.core.registerCallback("onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self)
        context_callbacks = [
#            "openPBFileContextMenu",
 #           "mediaBrowserContextMenuRequested",
  #          "productSelectorContextMenuRequested",
            "openPBListContextMenu"
        ]
        # Register our handler function for every callback in the list.
        for callback_name in context_callbacks:
            self.core.registerCallback(callback_name, self.add_context_menu_item, plugin=self)


    @err_catcher(name=__name__)
    def isActive(self):
        return True
    # if returns true, the plugin will be loaded by Prism

    @err_catcher(name=__name__)
    def add_context_menu_item(self, *args, **kwargs):
        """
        Adds the "Publish to FrameIO" item to the right-click context menu.
        """
        # A safety check to make sure we have enough arguments
        if len(args) < 4:
            logger.error(f"Context menu callback received an unexpected number of arguments: {len(args)}")
            return
        # Assign the arguments from the tuple to variables
        origin = args[0]
        rcmenu = args[1]
        pubFileData = args[3]  # The data dictionary for the media file
        # Create the QAction (the menu item)
        publishAction = QAction("Publish to Fserver", rcmenu)
        # FIX: The triggered signal must call publishToFrameIO with the
        # correct arguments that it expects: 'origin' and 'pubFileData'.
        publishAction.triggered.connect(lambda: self.publish_to_fserver(origin, pubFileData))
        # Add the action to the context menu
        rcmenu.addAction(publishAction)

    @err_catcher(name=__name__)
    def publish_to_fserver(self, origin, pubFileData):
        """
        This function contains the logic to publish the selected file.
        """
        # pubFileData is a QListWidgetItem, extract the dict from its data
        file_data = pubFileData.data(Qt.UserRole)
        if not isinstance(file_data, dict):
            logger.error("No file data found in QListWidgetItem.")
            self.core.popup("Error: No file data found.", parent=origin)
            return

        file_path = file_data.get("path")
        logger.info(f"Publishing file to Fserver: {file_path}")

        # --- ADD YOUR UPLOAD/PUBLISH LOGIC HERE ---

        self.core.popup(f"Published:\n{os.path.basename(file_path)}", parent=origin)

