import c4d
import maxon

ID_TEX_BITMAP = "com.chaos.vray_node.texbitmap"
ID_TEX_BITMAP_RGB_PRIMARIES = "com.chaos.vray_node.texbitmap.rgb_primaries"
VRAY_NODESPACE = "com.chaos.class.vray_node_renderer_nodespace"

def main():
    doc = c4d.documents.GetActiveDocument()
    
    # Create a new material
    c4d.CallCommand(1058751) # Create V-Ray Node Material
    mat = doc.GetActiveMaterial()
    if not mat: return
    mat.SetName("Test_Primaries_Values")
    
    node_material = mat.GetNodeMaterialReference()
    graph = node_material.GetGraph(VRAY_NODESPACE)
    if not graph: return

    with graph.BeginTransaction() as transaction:
        # Create 3 Bitmaps with different values for RGB Primaries
        for val in range(3):
            bitmap_node = graph.AddChild("", ID_TEX_BITMAP)
            
            # Try to set the name (might not show in Node Editor directly but useful if inspecting)
            # bitmap_node.SetValue("net.maxon.node.attribute.name", f"Bitmap_Val_{val}") 
            
            # Set RGB Primaries
            primaries_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_RGB_PRIMARIES)
            if primaries_port:
                try:
                    primaries_port.SetPortValue(val)
                    print(f"Created Bitmap with RGB Primaries = {val}")
                except Exception as e:
                    print(f"Error setting value {val}: {e}")
            else:
                 try:
                    bitmap_node.SetValue(ID_TEX_BITMAP_RGB_PRIMARIES, val)
                    print(f"Created Bitmap with RGB Primaries = {val} (Direct Set)")
                 except Exception as e:
                    print(f"Error setting value {val} directly: {e}")

        transaction.Commit()
    
    c4d.EventAdd()
    print("Done. Please check the 'Test_Primaries_Values' material in the Node Editor.")
    print("You should see 3 Bitmap nodes. Check the 'RGB Primaries' dropdown for each.")

if __name__ == '__main__':
    main()
