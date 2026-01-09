import c4d
from c4d import gui, documents
import maxon
import json
import os
import traceback

# Define the constants as plain strings, which the API expects.
vrayNodeSpace = "com.chaos.class.vray_node_renderer_nodespace"
vrayMtlBRDF = "com.chaos.vray_node.brdfvraymtl"
vrayMtlDiffusePort = "com.chaos.vray_node.brdfvraymtl.diffuse"

def create_materials_from_json(json_filepath):
    """
    Reads a JSON file and recreates V-Ray Node Materials in the active C4D document.
    """
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            all_materials_data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"--- SCRIPT ERROR: Failed to read or parse JSON file. ---\nError: {e}")
        traceback.print_exc()
        return

    doc = documents.GetActiveDocument()
    if not doc:
        print("--- SCRIPT ERROR: No active document found. ---")
        return

    doc.StartUndo()

    for material_data in all_materials_data:
        try:
            VRAY_NODE_MATERIAL_COMMAND_ID = 1058751
            c4d.CallCommand(VRAY_NODE_MATERIAL_COMMAND_ID)

            mat = doc.GetActiveMaterial()
            if mat is None:
                raise RuntimeError("CallCommand(1058751) did not result in a new active material.")

            node_material = mat.GetNodeMaterialReference()
            if not node_material or not node_material.HasSpace(vrayNodeSpace):
                raise RuntimeError("The material created via CallCommand is not a valid V-Ray Node Material.")

        except (RuntimeError, BaseException) as e:
            print(f"--- SCRIPT ERROR: An error occurred during material creation: ---\n{e}")
            traceback.print_exc()
            doc.EndUndo()
            return

        mat.SetName(material_data.get("name", "V-Ray Node Material"))
        doc.AddUndo(c4d.UNDOTYPE_NEW, mat)

        graph = node_material.GetGraph(vrayNodeSpace)
        if not graph:
            print(f"Failed to get graph for material {mat.GetName()}")
            continue

        with graph.BeginTransaction() as transaction:
            root = graph.GetViewRoot()
            node_mapping = {}

            # First Pass: Create all nodes
            for node_info in material_data.get("nodes", []):
                try:
                    asset_id = node_info["assetId"] # Use string directly
                    new_node = graph.AddChild("", asset_id)
                    if new_node:
                        node_mapping[node_info["nodePath"]] = new_node
                    else:
                        print(f"Failed to create node with assetId: {asset_id}")
                except Exception as e:
                    print(f"Error creating node {node_info.get('assetId')}: {e}")

            # Second Pass: Set values and create connections
            for node_info in material_data.get("nodes", []):
                original_node_path = node_info.get("nodePath")
                if original_node_path not in node_mapping:
                    continue

                created_node = node_mapping[original_node_path]

                if "diffuse" in node_info:
                    diffuse_info = node_info["diffuse"]
                    diffuse_input_port = created_node.GetInputs().FindChild(vrayMtlDiffusePort) # Pass string ID
                    
                    if not diffuse_input_port:
                        continue

                    if diffuse_info["type"] == "value":
                        color_val = diffuse_info["value"]
                        if isinstance(color_val, list) and len(color_val) == 3:
                            c4d_color = c4d.Vector(color_val[0], color_val[1], color_val[2])
                            diffuse_input_port.SetValue(c4d_color)

                    elif diffuse_info["type"] == "connection":
                        connected_port_path = diffuse_info["value"]
                        source_node_path = ".".join(connected_port_path.split('.')[:-1])
                        
                        if source_node_path in node_mapping:
                            source_node = node_mapping[source_node_path]
                            port_name = connected_port_path.split('.')[-1]

                            # --- DEBUGGING: Print connection information to the console ---
                            print("--- Connection Attempt ---")
                            print(f"Target Node: {created_node.GetPath()}")
                            print(f"Target Port: {vrayMtlDiffusePort}")
                            print(f"Source Node Path: '{source_node_path}'")
                            print(f"Searching for Source Port Name: '{port_name}'")
                            
                            # List all available output ports on the source node to see what we can connect from.
                            available_outputs = [p.GetId() for p in source_node.GetOutputs()]
                            print(f"Available output ports on source: {available_outputs}")
                            # --- END DEBUGGING ---
                            
                            # Use the simple name of the port to find it.
                            source_output_port = source_node.GetOutputs().FindChild(port_name) # Pass string name

                            if source_output_port:
                                print("SUCCESS: Found source port. Connecting nodes...")
                                source_output_port.Connect(diffuse_input_port)
                            else:
                                print(f"WARNING: Could not find specific output port '{port_name}'. Falling back to first available port.")
                                first_output = source_node.GetOutputs().GetFirst()
                                if first_output:
                                    print("SUCCESS: Found fallback port. Connecting nodes...")
                                    first_output.Connect(diffuse_input_port)
                                else:
                                    print("ERROR: Fallback failed. No output ports found on source node.")
                        else:
                             print(f"ERROR: Could not find the source node '{source_node_path}' in the list of created nodes.")

            transaction.Commit()

    doc.EndUndo()
    c4d.EventAdd()
    gui.MessageDialog(f"Successfully created {len(all_materials_data)} material(s).")


def main():
    json_filepath = c4d.storage.LoadDialog(
        title="Select Material JSON File",
        flags=c4d.FILESELECT_LOAD,
        force_suffix="json"
    )

    if not json_filepath:
        return

    create_materials_from_json(json_filepath)

if __name__ == '__main__':
    main()
