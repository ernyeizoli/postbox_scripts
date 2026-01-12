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
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


import socket
import logging
from qtpy.QtWidgets import QAction

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


logger = logging.getLogger(__name__)


class Prism_PBV_AE_Import_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.core.registerCallback("mediaPlayerContextMenuRequested", self.mediaPlayerContextMenuRequested, plugin=self)

    @err_catcher(name=__name__)
    def isActive(self):
        return True

    def mediaPlayerContextMenuRequested(self, origin, menu):
        if self.core.requestedApp == "AfterEffects":
            filepaths = origin.seq
            if not filepaths:
                return
                
            menu.addSeparator()
            my_action = QAction("PBV Import to After Effects from folder", menu)
            my_action.triggered.connect(lambda: self.importMedia(filepaths[0]))
            menu.addAction(my_action)

    @err_catcher(name=__name__)
    def importMedia(self, filepath):
        filepaths = self.core.media.getFilesFromSequence(filepath)
        if not filepaths:
            return

        cmd = """
if (app.project) {
    try {
        var sourceFilePath = "%s";
        var sourceFile = new File(sourceFilePath);
        var targetFolder = sourceFile.parent;

        if (targetFolder && targetFolder.exists) {
            app.project.setDefaultImportFolder(targetFolder);
        }

        var importedItem = app.project.importFileWithDialog();

        if (importedItem) {
            '{"result": true, "fileName": "' + importedItem.name + '"}';
        } else {
            '{"result": false, "details": "Import dialog was cancelled by user."}';
        }
    } catch (e) {
        '{"result": false, "details": "' + e.toString() + '"}';
    }
} else {
    '{"result": false, "details": "No project found."}';
}
""" % (filepaths[0].replace("\\", "/"))

        self.sendCmd(cmd)

    @err_catcher(name=__name__)
    def sendCmd(self, cmd):
        HOST = '127.0.0.1'
        PORT = 9888
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((HOST, PORT))
            except Exception as e:
                logger.debug("sending cmd: %s" % cmd)
                self.core.popup("Failed to communicate with After Effects.\nMake sure it is running and ready.")
                return

            data = (cmd).encode("utf-8")
            s.sendall(data)
            data = s.recv(1024)

        return data
