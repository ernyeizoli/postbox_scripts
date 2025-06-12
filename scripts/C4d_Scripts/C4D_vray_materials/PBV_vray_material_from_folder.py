import c4d

def main():
    # V-Ray Node Material Plugin ID
    VRAY_NODE_MATERIAL_ID = 1058751

    # Create the material
    mat = c4d.BaseMaterial(VRAY_NODE_MATERIAL_ID)
    if mat is None:
        c4d.gui.MessageDialog("Could not create V-Ray Node Material. Is V-Ray installed?")
        return

    mat.SetName("V-Ray Node Material")
    doc = c4d.documents.GetActiveDocument()
    doc.InsertMaterial(mat)
    c4d.EventAdd()

if __name__ == '__main__':
    main()