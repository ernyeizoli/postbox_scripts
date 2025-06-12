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
        "mp_suffix": "",
        "has_vray": False,
        "vray_suffix": ""
    },
    "STANDARD_MP": {
        "beauty_suffix": "$prj_$camera_",
        "has_mp": True,
        "mp_suffix": "$prj_$camera_MP_",
        "has_vray": False,
        "vray_suffix": ""
    },
    "VRAY_DRAFT": {
        "beauty_suffix": "$prj_$camera_RGB",
        "has_mp": False,
        "mp_suffix": "",
        "has_vray": True,
        "vray_suffix": "$prj_$camera_MP_$frame"
    },
    "VRAY_HQ": {
        "beauty_suffix": "$prj_$camera_RGB",
        "has_mp": False,
        "mp_suffix": "",
        "has_vray": True,
        "vray_suffix": "$prj_$camera_MP_$frame"
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

    # Create beauty render path and Vray MP render path
    if render_settings_name not in RENDER_SETTINGS:
        raise Exception(f"Render setting '{render_settings_name}' not recognized.")
        return

    # Search for the V-Ray VideoPost
    vp = rd.GetFirstVideoPost()
    while vp:
        if vp.GetType() == ID_VRAY_VIDEOPOST:
            print(f"Found V-Ray VideoPost: {vp.GetName()}")
            break
        vp = vp.GetNext()
    else:
        vp = None  # Explicitly set to None if not found

    # Set the output filename for V-Ray and standard C4D
    doc.StartUndo()
    if vp is not None:
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, vp)
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, rd)
        
    base_path, _ = file_path.split("Post_Production", 1)
    render_folder_path = base_path + "Post_Production/007_Render/002_3D_Render/$prj/"

    # Set the paths
    # Set standard C4D render output path
    beauty_path = render_folder_path + RENDER_SETTINGS[render_settings_name]["beauty_suffix"]
    rd[c4d.RDATA_PATH] = beauty_path
    
    # Set V-Ray render output path if applicable
    if RENDER_SETTINGS[render_settings_name]["has_vray"] and vp is not None:
        vray_path = render_folder_path + RENDER_SETTINGS[render_settings_name]["vray_suffix"]
        vp[VRAY_VP_OUTPUT_SETTINGS_FILENAME] = vray_path
    
    # Set the mp output path if applicable
    if RENDER_SETTINGS[render_settings_name]["has_mp"]:
        mp_path = render_folder_path + RENDER_SETTINGS[render_settings_name]["mp_suffix"]
        rd[c4d.RDATA_MULTIPASS_FILENAME] = mp_path

    doc.EndUndo()
    c4d.EventAdd()

    if RENDER_SETTINGS[render_settings_name]["has_vray"] and vp is not None:
        gui.MessageDialog(f"V-Ray and C4D output filename set to:\n{vray_path, beauty_path}")
    elif RENDER_SETTINGS[render_settings_name]["has_mp"]:
        gui.MessageDialog(f"C4D output filename set to:\n{beauty_path}\nMultipass output filename set to:\n{mp_path}")
    else:
        gui.MessageDialog(f"C4D output filename set to:\n{beauty_path}\nThere's no V-Ray or Multipass for this setting.")

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
