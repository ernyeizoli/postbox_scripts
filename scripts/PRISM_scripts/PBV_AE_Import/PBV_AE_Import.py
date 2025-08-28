name = "PBV_AE_Import"
classname = "PBV_AE_Import"

import socket
import logging
from qtpy.QtWidgets import QAction
from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)

class PBV_AE_Import:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"
        self.core.registerCallback("mediaPlayerContextMenuRequested", self.mediaPlayerContextMenuRequested, plugin=self)

    def mediaPlayerContextMenuRequested(self, origin, menu):
        if self.core.requestedApp == "AfterEffects":
            filepaths = origin.seq
            if not filepaths:
                return
                
            menu.addSeparator()
            my_action = QAction("PBV Import to After Effects from folder", menu)
            
            # Simplified connect statement - no middleman function needed.
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