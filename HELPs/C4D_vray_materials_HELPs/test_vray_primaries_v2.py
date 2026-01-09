import c4d
import maxon

ID_TEX_BITMAP = "com.chaos.vray_node.texbitmap"
ID_TEX_BITMAP_RGB_PRIMARIES = "com.chaos.vray_node.texbitmap.rgb_primaries"
ID_TEX_BITMAP_IMPORTED_PRIMARIES = "com.chaos.vray_node.texbitmap.imported_primaries"
VRAY_NODESPACE = "com.chaos.class.vray_node_renderer_nodespace"

def main():
    doc = c4d.documents.GetActiveDocument()
    
    # Create a new material
    c4d.CallCommand(1058751) # Create V-Ray Node Material
    mat = doc.GetActiveMaterial()
    if not mat: return
    mat.SetName("Test_Primaries_V2")
    
    node_material = mat.GetNodeMaterialReference()
    graph = node_material.GetGraph(VRAY_NODESPACE)
    if not graph: return

    with graph.BeginTransaction() as transaction:
        # Test 1: Imported Primaries = True (Default)
        for val in range(3):
            bitmap_node = graph.AddChild("", ID_TEX_BITMAP)
            
            # Set Imported Primaries = True
            imp_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_IMPORTED_PRIMARIES)
            if imp_port: imp_port.SetPortValue(True)
            
            # Set RGB Primaries
            prim_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_RGB_PRIMARIES)
            if prim_port: prim_port.SetPortValue(val)
            
            print(f"Node T{val}: Imported=True, RGB_Primaries={val}")

        # Test 2: Imported Primaries = False
        for val in range(3):
            bitmap_node = graph.AddChild("", ID_TEX_BITMAP)
            
            # Set Imported Primaries = False
            imp_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_IMPORTED_PRIMARIES)
            if imp_port: imp_port.SetPortValue(False)
            
            # Set RGB Primaries
            prim_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_RGB_PRIMARIES)
            if prim_port: prim_port.SetPortValue(val)
            
            print(f"Node F{val}: Imported=False, RGB_Primaries={val}")

        transaction.Commit()
    
    c4d.EventAdd()
    print("Done. Check 'Test_Primaries_V2'.")
    print("Nodes T0-T2: Imported=True")
    print("Nodes F0-F2: Imported=False")

if __name__ == '__main__':
    main()
