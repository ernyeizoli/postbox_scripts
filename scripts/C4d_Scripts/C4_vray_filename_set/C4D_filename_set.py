# Version: 1.1.0
# Last Updated: 2025-05-28

import c4d
from c4d import gui

# Constants
ID_VRAY_VIDEOPOST = 1053272
VRAY_VP_OUTPUT_SETTINGS_FILENAME = 1000403  # Based on your enum

def set_vray_vp_output_filename(new_filename):
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

    # Set the output filename
    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, vp)

    vp[VRAY_VP_OUTPUT_SETTINGS_FILENAME] = new_filename

    doc.EndUndo()
    c4d.EventAdd()

    gui.MessageDialog(f"V-Ray output filename set to:\n{new_filename}")

# Run it
if __name__ == '__main__':
    try:
        set_vray_vp_output_filename("C:/renders/hdsfdsfsdfsfadijhdsfijhdst.png")
    except Exception as e:
        gui.MessageDialog(f"Error: {e}")
