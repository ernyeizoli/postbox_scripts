# Version: 1.1.0
# Last Updated: 2025-05-28

import c4d
from c4d import gui

# Constants
ID_VRAY_VIDEOPOST = 1053272
VRAY_VP_OUTPUT_SETTINGS_FILENAME = 1000403  # Based on your enum

# Nested render suffix dictionary
RENDER_SETTINGS = {
    "HW_PREVIEW": {
        "beauty_suffix": "$prj_$camera_HW_",
        "has_mp": False,
        "mp_suffix": ""
    },
    "STANDARD_MP": {
        "beauty_suffix": "$prj_$camera_",
        "has_mp": False,
        "mp_suffix": ""
    },
    "VRAY_DRAFT": {
        "beauty_suffix": "$prj_$camera_RGB",
        "has_mp": True,
        "mp_suffix": "$prj_$camera_MP_$frame"
    },
    "VRAY_HQ": {
        "beauty_suffix": "$prj_$camera_RGB",
        "has_mp": True,
        "mp_suffix": "$prj_$camera_MP_$frame"
    }
}


def get_current_file_path():
    doc = c4d.documents.GetActiveDocument()  # Get the active document
    file_path = doc.GetDocumentPath()  # Get the file path
    file_name = doc.GetDocumentName()  # Get the file name
    if file_name:
        full_path = f"{file_path}/{file_name}"
        return file_path, file_name, full_path
    else:
        return file_path, None, "Unsaved Document"
        gui.MessageDialog("Unsaved Document")

def get_render_setting_name():
    doc = c4d.documents.GetActiveDocument()  # Get the active document
    render_data = doc.GetActiveRenderData()  # Get the active render settings
    render_settings_name = render_data.GetName()  # Get the name of the render setting
    
    return render_settings_name

def set_render_save_path(file_path, render_settings_name):
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        raise Exception("No active document found.")

    rd = doc.GetActiveRenderData()
    if not rd:
        raise Exception("No render settings found.")

    # Search for the V-Ray VideoPost
    vp = rd.GetFirstVideoPost()
    while vp:
        if vp.GetType() == ID_VRAY_VIDEOPOST:
            print(f"Found V-Ray VideoPost: {vp.GetName()}")
            break
        vp = vp.GetNext()

    if not vp:
        raise Exception("V-Ray VideoPost not found.")

    # Set the output filename for V-Ray and standard C4D
    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, vp)
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, rd)

    # Create beauty render path and Vray MP render path
    if render_settings_name in RENDER_SETTINGS:
        beauty_suffix = RENDER_SETTINGS[render_settings_name]["beauty_suffix"]
        mp_suffix = RENDER_SETTINGS[render_settings_name]["mp_suffix"]
    else:
        raise Exception(f"Render setting '{render_settings_name}' not recognized.")
        return
    
    base_path, _ = file_path.split("Post_Production", 1)

    render_folder_path = base_path + "Post_Production/007_Render/002_3D_Render/"

    beauty_path = render_folder_path + beauty_suffix
    mp_path = render_folder_path + mp_suffix

    # Set the paths in V-Ray VideoPost and C4D Render Settings
    rd[c4d.RDATA_PATH] = beauty_path  # Set standard C4D render output path
    if RENDER_SETTINGS[render_settings_name]["has_mp"]:
        vp[VRAY_VP_OUTPUT_SETTINGS_FILENAME] = mp_path # Set Vray render output path

    doc.EndUndo()
    c4d.EventAdd()

    if RENDER_SETTINGS[render_settings_name]["has_mp"]:
        gui.MessageDialog(f"V-Ray and C4D output filename set to:\n{mp_path, beauty_path}")
    else:
        gui.MessageDialog(f"C4D output filename set to:\n{beauty_path}\nV-Ray does not use multipass for this setting.")

# Run it
if __name__ == '__main__':

    file_path, file_name, full_path = get_current_file_path()
    if not file_path:
        gui.MessageDialog("No document path found. Please save your document first.")
        raise Exception("No document path found.")
    
    render_settings_name = get_render_setting_name()

    try:
        set_render_save_path(file_path, render_settings_name)
    except Exception as e:
        gui.MessageDialog(f"Error: {e}")
