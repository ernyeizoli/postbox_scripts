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
# Define the FULL ID for the file port (Critical for FindChild to return a valid node)
ID_TEX_BITMAP_FILE = "com.chaos.vray_node.texbitmap.file"

VRAY_PORT_MAPPING = {
    'texturesColor': "com.chaos.vray_node.brdfvraymtl.diffuse",
    'texturesMetal': "com.chaos.vray_node.brdfvraymtl.metalness",
    'texturesSpecular': "com.chaos.vray_node.brdfvraymtl.reflect",
    'texturesRough': "com.chaos.vray_node.brdfvraymtl.reflect_glossiness", 
    'texturesGloss': "com.chaos.vray_node.brdfvraymtl.reflect_glossiness",
    'texturesTrans': "com.chaos.vray_node.brdfvraymtl.refract",
    'texturesEmm': "com.chaos.vray_node.brdfvraymtl.self_illumination",
    'texturesAlpha': "com.chaos.vray_node.brdfvraymtl.opacity",
    'texturesBump': "com.chaos.vray_node.brdfvraymtl.bump_map",
    'texturesNormal': "com.chaos.vray_node.brdfvraymtl.bump_map" 
}

def parse_folder(folder_path):
    texture_list = defaultdict(dict)
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
            texture_list[material_name][found_type] = file_path
    return texture_list

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

        for tex_type, file_path in textures_map.items():
            if tex_type not in VRAY_PORT_MAPPING: continue

            bitmap_node = graph.AddChild("", ID_TEX_BITMAP)
            
            # --- FIND PORT CORRECTLY (Use Full ID) ---
            # Using the short name "file" caused FindChild to return an invalid/proxy object 
            # in 2025, leading to the "no target to copy" error.
            file_port = bitmap_node.GetInputs().FindChild(ID_TEX_BITMAP_FILE)
            
            if file_port and not file_port.IsNullValue():
                # --- PATH SETTING LOGIC ---
                success = False
                
                # Method 1: Standard Maxon URL with SetSystemPath
                # This is the correct, official way to handle file paths (Local & Network)
                if not success:
                    try:
                        url_obj = maxon.Url()
                        url_obj.SetSystemPath(file_path)
                        file_port.SetPortValue(url_obj)
                        success = True
                    except Exception as e:
                        print(f"DEBUG: Url Set failed for {file_path}: {e}")

                # Method 2: Fallback to simple Maxon String
                if not success:
                    try:
                        file_port.SetPortValue(maxon.String(file_path))
                        success = True
                    except Exception:
                        pass

                if not success:
                    print(f"Error: Could not set file path for {tex_type} ({mat_name}).")
                    print(f"Path: {file_path}")

            else:
                print(f"Warning: Could not find 'file' port ({ID_TEX_BITMAP_FILE}) on bitmap node.")
            
            target_port_id = VRAY_PORT_MAPPING[tex_type]
            brdf_input_port = brdf_node.GetInputs().FindChild(target_port_id)
            
            bitmap_output_port = None
            outputs = bitmap_node.GetOutputs()
            if outputs:
                for port in outputs.GetChildren():
                    bitmap_output_port = port
                    break
            
            if brdf_input_port and bitmap_output_port:
                bitmap_output_port.Connect(brdf_input_port)
            else:
                print(f"Warning: Could not connect {tex_type} for {mat_name}")

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