import c4d
import maxon
import os
import re
import traceback
from collections import defaultdict

# --- CONFIGURATION & CONSTANTS ---

TEXTURE_EXT = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".exr", ".targa"]

TEXTURE_KEYWORDS = {
    'texturesColor': ['diffuse', 'diff', 'albedo', 'alb', 'base', 'col', 'color', 'basecolor'],
    'texturesMetal': ['metalic', 'metalness', 'metal', 'mtl', 'met'],
    'texturesSpecular': ['specularity', 'specular', 'spec', 'spc'],
    'texturesRough': ['roughness', 'rough', 'rgh'],
    'texturesGloss': ['gloss', 'glossy', 'glossiness'],
    'texturesTrans': ['transmisson', 'transparency', 'trans'],
    'texturesEmm': ['emission', 'emissive', 'emit', 'emm'],
    'texturesAlpha': ['alpha', 'opacity', 'opac'],
    'texturesBump': ['bump', 'bmp', 'height', 'displacement', 'displace', 'disp'],
    'texturesNormal': ['normal', 'nor', 'nrm', 'nrml', 'norm']
}

VRAY_NODESPACE = "com.chaos.class.vray_node_renderer_nodespace"
ID_BRDF_VRAY = "com.chaos.vray_node.brdfvraymtl"
ID_TEX_BITMAP = "com.chaos.vray_node.texbitmap"
ID_TEX_BITMAP_INVERT = "com.chaos.vray_node.texbitmap.invert"

ID_TEX_NORMAL_MAP = "com.chaos.vray_node.texnormalbump"
ID_TEX_NORMAL_INPUT = "com.chaos.vray_node.texnormalbump.bump_tex_color"
ID_TEX_NORMAL_MAP_TYPE = "com.chaos.vray_node.texnormalbump.map_type"

# Full IDs for Bitmap Ports
ID_TEX_BITMAP_FILE = "com.chaos.vray_node.texbitmap.file"
ID_TEX_BITMAP_UVWGEN = "com.chaos.vray_node.texbitmap.uvwgen"
ID_TEX_BITMAP_RGB_PRIMARIES = "com.chaos.vray_node.texbitmap.rgb_primaries"
ID_TEX_BITMAP_IMPORTED_PRIMARIES = "com.chaos.vray_node.texbitmap.imported_primaries"

# Asset ID for the UVW Generator
ID_UVW_GEN = "com.chaos.vray_node.uvwgenchannel"

VRAY_PORT_MAPPING = {
    'texturesColor': "com.chaos.vray_node.brdfvraymtl.diffuse",
    'texturesMetal': "com.chaos.vray_node.brdfvraymtl.metalness",
    'texturesSpecular': "com.chaos.vray_node.brdfvraymtl.reflect",
    'texturesRough': "com.chaos.vray_node.brdfvraymtl.reflect_glossiness", 
    'texturesGloss': "com.chaos.vray_node.brdfvraymtl.reflect_glossiness",
    'texturesTrans': "com.chaos.vray_node.brdfvraymtl.refract",
    'texturesEmm': "com.chaos.vray_node.brdfvraymtl.self_illumination",
    'texturesAlpha': "com.chaos.vray_node.brdfvraymtl.opacity",
    # Note: Both Bump and Normal target the bump_map port on BRDF
    'texturesBump': "com.chaos.vray_node.brdfvraymtl.bump_map",
    'texturesNormal': "com.chaos.vray_node.brdfvraymtl.bump_map" 
}

def parse_folder(folder_path):
    """
    Scans the folder, groups files by material, and applies priority rules.
    """
    candidates = defaultdict(lambda: defaultdict(list))
    
    if not os.path.exists(folder_path):
        return {}

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        
        if not os.path.isfile(file_path): continue
        if not file.lower().endswith(tuple(TEXTURE_EXT)): continue
        if "_" not in file: continue

        split_text = file.split("_")
        material_name = split_text[0] 

        found_type = None
        for part in split_text[1:]: 
            part_lower = part.lower()
            for type_key, keywords in TEXTURE_KEYWORDS.items():
                if any(kw in part_lower for kw in keywords):
                    found_type = type_key
                    break
            if found_type: break
        
        if found_type:
            candidates[material_name][found_type].append(file)

    final_texture_list = defaultdict(dict)

    for mat_name, types in candidates.items():
        for type_key, file_list in types.items():
            
            chosen_file = file_list[0]
            
            # RULE: Normal Maps (Prefer GL over DX)
            if type_key == 'texturesNormal':
                gl_files = [f for f in file_list if 'gl' in f.lower().replace('.', '_').split('_')]
                if gl_files:
                    chosen_file = gl_files[0]

            # RULE: Roughness (Prefer Pure Rough over Roughness+AO)
            elif type_key == 'texturesRough':
                pure_rough_files = [f for f in file_list if 'ao' not in f.lower().replace('.', '_').split('_')]
                if pure_rough_files:
                    chosen_file = pure_rough_files[0]
            
            final_texture_list[mat_name][type_key] = os.path.join(folder_path, chosen_file)

    return final_texture_list

def connect_normal_map(graph, bitmap_output_port, brdf_input_port):
    """
    Placeholder function for Normal Map handling.
    
    Args:
        graph (maxon.GraphModelRef): The material graph.
        bitmap_output_port (maxon.GraphNode): The output port of the Bitmap node.
        brdf_input_port (maxon.GraphNode): The input port of the BRDF node (Bump Map).
    """
    # Currently doing nothing special, just connecting the bitmap directly.
    # Logic for creating a specific Normal Map node can be added here later.

    normal_node = graph.AddChild("", ID_TEX_NORMAL_MAP)

    # Set Map Type to Normal Map (Tangent Space) - Value 1
    try:
        # Find the port for map_type
        map_type_port = normal_node.GetInputs().FindChild(ID_TEX_NORMAL_MAP_TYPE)
        if map_type_port and not map_type_port.IsNullValue():
             map_type_port.SetPortValue(1) # 1 = Normal Map (Tangent)
        else:
             # Fallback: Try setting value directly on the attribute if port finding fails
             normal_node.SetValue(ID_TEX_NORMAL_MAP_TYPE, 1)
    except Exception as e:
        print(f"Warning: Could not set Normal Map Type: {e}")

    # 2. Connect Bitmap -> Normal Map
    # We need to find the specific input port on the new normal node.
    # usually: "com.chaos.vray_node.texnormalbump.bump_map"
    normal_input = normal_node.GetInputs().FindChild(ID_TEX_NORMAL_INPUT)

    if bitmap_output_port and normal_input:
        bitmap_output_port.Connect(normal_input)
    
    # 3. Connect Normal Map -> BRDF
    # We need to find the output port of our new normal node to plug into the material.
    # Since we don't know the exact ID, we just grab the first available output.
    normal_output = None
    for port in normal_node.GetOutputs().GetChildren():
        normal_output = port
        break
        
    if normal_output and brdf_input_port:
        normal_output.Connect(brdf_input_port)

    

def create_vray_material(doc, mat_name, textures_map):
    c4d.CallCommand(1058751) 
    mat = doc.GetActiveMaterial()
    if not mat: return
    mat.SetName(mat_name)
    node_material = mat.GetNodeMaterialReference()
    graph = node_material.GetGraph(VRAY_NODESPACE)
    if not graph: return

    with graph.BeginTransaction() as transaction:
        brdf_node = None
        root = graph.GetViewRoot()
        for node in root.GetInnerNodes(mask=maxon.NODE_KIND.NODE, includeThis=False):
            assetId = node.GetValue("net.maxon.node.attribute.assetid")[0]
            if str(assetId) == ID_BRDF_VRAY:
                brdf_node = node
                break
        
        if not brdf_node:
            print(f"Could not find BRDF for {mat_name}")
            return

        # 1. Create UVW Transform Node
        uvw_node = graph.AddChild("", ID_UVW_GEN)
        uvw_output_port = None
        if uvw_node:
             for port in uvw_node.GetOutputs().GetChildren():
                 uvw_output_port = port
                 break

        # 2. Create Textures
        for tex_type, file_path in textures_map.items():
            if tex_type not in VRAY_PORT_MAPPING: continue

            # A. Create Bitmap Node
            bitmap_node = graph.AddChild("", ID_TEX_BITMAP)
            
            # B. Set File Path
            file_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_FILE)
            if file_port and not file_port.IsNullValue():
                success = False
                # Try URL first
                if not success:
                    try:
                        url_obj = maxon.Url()
                        url_obj.SetSystemPath(file_path)
                        file_port.SetPortValue(url_obj)
                        success = True
                    except Exception as e:
                        pass
                if not success:
                    try:
                        file_port.SetPortValue(maxon.String(file_path))
                        success = True
                    except:
                        pass
                if not success:
                    print(f"Error: Could not set file path for {tex_type} ({mat_name}).")
            
            # --- NEW: Set RGB Primaries to sRGB for Color Textures ---
            if tex_type == 'texturesColor':
                print(f"DEBUG: Processing Color Texture for {mat_name}")
                # 1. Disable "Imported Primaries" (Crucial for RGB Primaries to take effect)
                imported_primaries_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_IMPORTED_PRIMARIES)
                if imported_primaries_port:
                    try:
                        imported_primaries_port.SetPortValue(False)
                        print("DEBUG: Set Imported Primaries to False (Port)")
                    except Exception as e:
                        print(f"DEBUG: Failed to set Imported Primaries (Port): {e}")
                else:
                    try:
                        bitmap_node.SetValue(ID_TEX_BITMAP_IMPORTED_PRIMARIES, False)
                        print("DEBUG: Set Imported Primaries to False (Direct)")
                    except Exception as e:
                        print(f"DEBUG: Failed to set Imported Primaries (Direct): {e}")

                # 2. Set "RGB Primaries" to sRGB (Value 2)
                primaries_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_RGB_PRIMARIES)
                if primaries_port:
                    try:
                        primaries_port.SetPortValue(2) # 2 = sRGB
                        print("DEBUG: Set RGB Primaries to 2 (Port)")
                    except Exception as e:
                        print(f"DEBUG: Failed to set RGB Primaries (Port): {e}")
                else:
                    # Fallback: Try setting value directly on the node if port finding fails
                    try:
                        bitmap_node.SetValue(ID_TEX_BITMAP_RGB_PRIMARIES, 2)
                        print("DEBUG: Set RGB Primaries to 2 (Direct)")
                    except Exception as e:
                        print(f"DEBUG: Failed to set RGB Primaries (Direct): {e}")

            # C. Connect UVW Transform -> Bitmap
            if uvw_output_port:
                uvw_input_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_UVWGEN)
                if uvw_input_port:
                    uvw_output_port.Connect(uvw_input_port)
                        bitmap_node.SetValue(ID_TEX_BITMAP_IMPORTED_PRIMARIES, False)
                        print("DEBUG: Set Imported Primaries to False (Direct)")
                    except Exception as e:
                        print(f"DEBUG: Failed to set Imported Primaries (Direct): {e}")

                # 2. Set "RGB Primaries" to sRGB (Value 2)
                primaries_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_RGB_PRIMARIES)
                if primaries_port:
                    try:
                        primaries_port.SetPortValue(2) # 2 = sRGB
                        print("DEBUG: Set RGB Primaries to 2 (Port)")
                        
                        # --- VERIFICATION ---
                        # Read back the values to confirm they stuck
                        check_imp = imported_primaries_port.GetPortValue() if imported_primaries_port else "N/A"
                        check_prim = primaries_port.GetPortValue()
                        print(f"DEBUG: VERIFY - Imported: {check_imp}, RGB: {check_prim}")
                        
                    except Exception as e:
                        print(f"DEBUG: Failed to set RGB Primaries (Port): {e}")
                else:
                    # Fallback: Try setting value directly on the node if port finding fails
                    try:
                        bitmap_node.SetValue(ID_TEX_BITMAP_RGB_PRIMARIES, 2)
                        print("DEBUG: Set RGB Primaries to 2 (Direct)")
                    except Exception as e:
                        print(f"DEBUG: Failed to set RGB Primaries (Direct): {e}")

            # C. Connect UVW Transform -> Bitmap
            if uvw_output_port:
                uvw_input_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_UVWGEN)
                if uvw_input_port:
                    uvw_output_port.Connect(uvw_input_port)

            # D. Handle Connections to BRDF
            target_port_id = VRAY_PORT_MAPPING[tex_type]
            brdf_input_port = brdf_node.GetInputs().FindChild(target_port_id)
            bitmap_output_port = None
            outputs = bitmap_node.GetOutputs()
            if outputs:
                for port in outputs.GetChildren():
                    bitmap_output_port = port
                    break
            
            if not bitmap_output_port: continue

            # --- LOGIC BRANCHING ---
            # --- LOGIC FOR ROUGHNESS VS GLOSSINESS (Case Insensitive) ---
            if tex_type == 'texturesRough' or tex_type == 'texturesGloss':
                # Determine if it is actually Roughness (which V-Ray treats as Inverted Glossiness)
                # Convert to lower case for case-insensitive check
                filename_lower = os.path.basename(file_path).lower()
                
                is_roughness = "rough" in filename_lower
                
                # If it's roughness, check the 'invert' box on the bitmap node
                if is_roughness:
                    invert_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_INVERT)
                    if invert_port and not invert_port.IsNullValue():
                        try:
                            invert_port.SetPortValue(True)
                            print(f"Info: Inverted Roughness map for {mat_name}")
                        except:
                            print(f"Warning: Failed to set Invert on Roughness map")

            
            
            if tex_type == 'texturesBump':
                # User Request: Don't connect displacement/bump to BRDF
                print(f"Info: Created Displacement/Bump node for {mat_name} but left unconnected.")
                continue

            elif tex_type == 'texturesNormal':
                # Use the dedicated function for Normal Map handling (currently a placeholder)
                connect_normal_map(graph, bitmap_output_port, brdf_input_port)

            else:
                # Standard Connection (Color, Roughness, etc.)
                if brdf_input_port:
                    bitmap_output_port.Connect(brdf_input_port)

        transaction.Commit()
    doc.AddUndo(c4d.UNDOTYPE_NEW, mat)

def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc: return
    folder_path = c4d.storage.LoadDialog(title="Select Folder", flags=c4d.FILESELECT_DIRECTORY)
    if not folder_path: return
    print(f"Scanning: {folder_path}...")
    materials_dict = parse_folder(folder_path)
    if not materials_dict:
        c4d.gui.MessageDialog("No valid textures found.")
        return
    doc.StartUndo()
    count = 0
    for mat_name, textures in materials_dict.items():
        print(f"Creating Material: {mat_name}")
        try:
            create_vray_material(doc, mat_name, textures)
            count += 1
        except Exception as e:
            print(f"Critical Error creating material {mat_name}: {e}")
            traceback.print_exc()
    doc.EndUndo()
    c4d.EventAdd()
    c4d.gui.MessageDialog(f"Created {count} V-Ray Materials.")

if __name__ == '__main__':
    main()