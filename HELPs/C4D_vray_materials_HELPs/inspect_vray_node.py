import c4d
import maxon

def main():
    # Get the active material
    mat = c4d.documents.GetActiveDocument().GetActiveMaterial()
    if not mat:
        print("Please select a V-Ray Node Material.")
        return

    # Get the Node Material reference
    node_material = mat.GetNodeMaterialReference()
    if not node_material:
        print("Not a Node Material.")
        return

    # Get the Graph for V-Ray
    graph = node_material.GetGraph("com.chaos.class.vray_node_renderer_nodespace")
    if not graph:
        print("Could not find V-Ray Graph.")
        return

    print(f"--- Inspecting Material: {mat.GetName()} ---")

    # Iterate over all nodes in the graph to find Bitmap nodes
    root = graph.GetViewRoot()
    children = []
    root.GetChildren(children, maxon.NODE_KIND.NODE)

    for node in children:
        asset_id = node.GetValue("net.maxon.node.attribute.assetid")[0]
        
        # Check if it's a V-Ray Bitmap node (or just print all to be safe)
        if "texbitmap" in str(asset_id):
            print(f"\nFound Node: {asset_id}")
            print("-" * 30)
            
            # Inspect Inputs (Parameters)
            inputs = node.GetInputs()
            for port in inputs.GetChildren():
                port_id = port.GetId()
                try:
                    # Try to get the value
                    val = port.GetDefaultValue()
                    print(f"Port ID: {port_id} | Value: {val}")
                except:
                    print(f"Port ID: {port_id} | Value: <Could not read>")

if __name__ == '__main__':
    main()
