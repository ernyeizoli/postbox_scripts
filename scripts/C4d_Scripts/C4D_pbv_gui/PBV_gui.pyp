import c4d
import os

# A unique ID for your plugin
PLUGIN_ID = 1000001

# --- Constants for our scripts ---
SCRIPT_FILENAME_SET = "PBV_filename_set.py"
SCRIPT_LIGHT_PASS = "PBV_vray_light_pass_creator.py"
SCRIPT_LIGHT_RENAME = "PBV_vray_light_renamer.py"
SCRIPT_REDSHIFT_LIGHT = "PBV_redshift_light.py"

SCRIPT_FILENAME_SET_REMIX = "PBV_filename_set_REMIX.py"

class MyScriptsDialog(c4d.gui.GeDialog):

    def GetIcon(self, name):
        """Helper function to load an icon by name from the user scripts folder."""
        library_folder = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_LIBRARY_USER)
        if library_folder is None: return None
        
        icon_path = os.path.join(library_folder, "scripts", name)
        
        icon = c4d.bitmaps.BaseBitmap()
        if icon.InitWith(icon_path)[0] == c4d.IMAGERESULT_OK:
            return icon
        print(f"Icon not found or could not load at: {icon_path}")
        return None

    def CreateLayout(self):
        self.SetTitle("PBV Tools")

        # ==================== V-RAY TOOLS ====================
        self.GroupBegin(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 0, "VRay_Tools")
        self.GroupBorderSpace(10, 10, 10, 10)
        self.AddStaticText(1200, c4d.BFH_CENTER, 0, 0, "--- V-RAY TOOLS ---")

        # --- Bitmap Button for "Rename V-Ray Lights" ---
        self.AddCustomGui(1003, c4d.CUSTOMGUI_BITMAPBUTTON, "", c4d.BFH_SCALEFIT, 15, 15)
        bmp = self.GetIcon("PBV_vray_light_renamer.tif")
        if bmp:
            gui = self.FindCustomGui(1003, c4d.CUSTOMGUI_BITMAPBUTTON)
            if gui:
                gui.SetImage(bmp)
        self.AddStaticText(1103, c4d.BFH_LEFT, 0, 0, "Rename V-Ray Lights")

        # --- Bitmap Button for "Create V-Ray Light Passes" ---
        self.AddCustomGui(1002, c4d.CUSTOMGUI_BITMAPBUTTON, "", c4d.BFH_SCALEFIT, 15, 15)
        bmp = self.GetIcon("PBV_vray_light_pass_creator.tif")
        if bmp:
            gui = self.FindCustomGui(1002, c4d.CUSTOMGUI_BITMAPBUTTON)
            if gui:
                gui.SetImage(bmp)
        self.AddStaticText(1102, c4d.BFH_LEFT, 0, 0, "Create V-Ray Light Passes")

        self.GroupEnd()

        # ==================== REDSHIFT TOOLS ====================
        self.GroupBegin(2000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 0, "Redshift_Tools")
        self.GroupBorderSpace(10, 10, 10, 10)
        self.AddStaticText(2200, c4d.BFH_CENTER, 0, 0, "--- REDSHIFT TOOLS ---")

        # --- Bitmap Button for "Redshift Light Renamer" ---
        self.AddCustomGui(1004, c4d.CUSTOMGUI_BITMAPBUTTON, "", c4d.BFH_SCALEFIT, 15, 15)
        bmp = self.GetIcon("PBV_redshift_light.tiff")
        if bmp:
            gui = self.FindCustomGui(1004, c4d.CUSTOMGUI_BITMAPBUTTON)
            if gui:
                gui.SetImage(bmp)
        self.AddStaticText(1104, c4d.BFH_LEFT, 0, 0, "Redshift Light Organizer")

        self.GroupEnd()

        # ==================== PROJECT TOOLS ====================
        self.GroupBegin(3000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 0, "Project_Tools")
        self.GroupBorderSpace(10, 10, 10, 10)
        self.AddStaticText(3200, c4d.BFH_CENTER, 0, 0, "--- PROJECT TOOLS ---")

        # --- Bitmap Button for "Set Render Filename" ---
        self.AddCustomGui(1001, c4d.CUSTOMGUI_BITMAPBUTTON, "", c4d.BFH_SCALEFIT, 15, 15)
        bmp = self.GetIcon("PBV_filename_set.tif")
        if bmp:
            gui = self.FindCustomGui(1001, c4d.CUSTOMGUI_BITMAPBUTTON)
            if gui:
                gui.SetImage(bmp)
        self.AddStaticText(1101, c4d.BFH_LEFT, 0, 0, "Set Render Filename")

        # --- Bitmap Button for "Set Render Filename REMIX" ---
        self.AddCustomGui(2010, c4d.CUSTOMGUI_BITMAPBUTTON, "", c4d.BFH_SCALEFIT, 15, 15)
        bmp = self.GetIcon("PBV_filename_set_REMIX.tif")
        if bmp:
            gui = self.FindCustomGui(2010, c4d.CUSTOMGUI_BITMAPBUTTON)
            if gui:
                gui.SetImage(bmp)
        self.AddStaticText(2110, c4d.BFH_LEFT, 0, 0, "Set Render Filename REMIX")

        self.GroupEnd()

        return True

    def RunScript(self, script_name):
        """Helper to execute a Python script from the user scripts folder."""
        library_folder = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_LIBRARY_USER)
        if library_folder is None:
            c4d.gui.MessageDialog("Could not find user library folder.")
            return
        script_path = os.path.join(library_folder, "scripts", script_name)
        if not os.path.isfile(script_path):
            c4d.gui.MessageDialog(f"Script not found:\n{script_path}")
            return
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                code = f.read()
            exec(code, {"__name__": "__main__", "__file__": script_path})
        except Exception as e:
            c4d.gui.MessageDialog(f"Error executing script:\n{e}")

    def Command(self, id, msg):
        """Handles user interaction with the UI."""
        if id == 1001:
            self.RunScript(SCRIPT_FILENAME_SET)
        if id == 1002:
            self.RunScript(SCRIPT_LIGHT_PASS)
        if id == 1003:
            self.RunScript(SCRIPT_LIGHT_RENAME)
        if id == 2010:
            self.RunScript(SCRIPT_FILENAME_SET_REMIX)
        if id == 1004:
            self.RunScript(SCRIPT_REDSHIFT_LIGHT)
        return True

class MyScriptsPlugin(c4d.plugins.CommandData):
    """The plugin that creates and opens the dialog."""
    dialog = None

    def Execute(self, doc):
        if self.dialog is None:
            self.dialog = MyScriptsDialog()
        return self.dialog.Open(c4d.DLG_TYPE_ASYNC, pluginid=PLUGIN_ID)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = MyScriptsDialog()
        return self.dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)

if __name__ == "__main__":
    c4d.plugins.RegisterCommandPlugin(PLUGIN_ID, "PBV Tools", 0, None, "A dockable UI for the PBV Python scripts.", MyScriptsPlugin())