import c4d

def sanitize_name(name):
    """Enforces LS_ prefix and replaces spaces with underscores."""
    clean_name = name.replace(" ", "_")
    if not clean_name.startswith("LS_"):
        clean_name = "LS_" + clean_name
    return clean_name

def main():
    # --- CONSTANTS ---
    RS_LIGHT_OBJECT_ID = 1036751      # Redshift Light object type
    RS_LIGHT_TAG_ID = 1036751         # Redshift Light tag (same ID)
    RS_VIDEO_POST_ID = 1036219        # Redshift Video Post
    C4D_LIGHT_ID = 5102               # Cinema 4D native light

    # AOV Type for Light Group - Beauty type is ID 41
    REDSHIFT_AOV_TYPE_BEAUTY = 41

    # --- INITIALIZATION ---
    doc = c4d.documents.GetActiveDocument()
    rd = doc.GetActiveRenderData()

    # Find Redshift Video Post
    vp = rd.GetFirstVideoPost()
    while vp and vp.GetType() != RS_VIDEO_POST_ID:
        vp = vp.GetNext()

    if not vp:
        print("[ERROR] Redshift is not active in Render Settings.")
        return

    # Import redshift module
    import redshift

    doc.StartUndo()
    print("--- STARTING LIGHT & AOV SYNC ---")

    # --- 1. PROCESS LIGHTS IN SCENE ---
    # To handle hierarchies (nested lights), we use a helper to get everything
    def get_all_objects(op, out_list):
        while op:
            out_list.append(op)
            get_all_objects(op.GetDown(), out_list)
            op = op.GetNext()

    scene_elements = []
    get_all_objects(doc.GetFirstObject(), scene_elements)

    print(f"[DEBUG] Found {len(scene_elements)} objects in scene")

    processed_names = []

    for obj in scene_elements:
        obj_type = obj.GetType()
        obj_name = obj.GetName()

        # Check for Redshift Light object (native RS light)
        is_rs_light = (obj_type == RS_LIGHT_OBJECT_ID)

        # Check for C4D Light with Redshift tag
        is_c4d_light_with_rs = False
        rs_tag = None
        if obj_type == C4D_LIGHT_ID:
            rs_tag = obj.GetTag(RS_LIGHT_TAG_ID)
            is_c4d_light_with_rs = (rs_tag is not None)

        # Also check if it's just a C4D light (without RS tag)
        is_c4d_light = (obj_type == C4D_LIGHT_ID)

        if is_rs_light or is_c4d_light:
            old_name = obj_name
            new_name = sanitize_name(old_name)

            print(f"[DEBUG] Processing: {old_name} (Type: {obj_type}, RS Light: {is_rs_light}, C4D Light: {is_c4d_light})")

            # Rename the Object
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
            obj.SetName(new_name)

            # For Redshift lights, set the light group using c4d.REDSHIFT_LIGHT_LIGHT_GROUP
            if is_rs_light:
                obj[c4d.REDSHIFT_LIGHT_LIGHT_GROUP] = new_name
                print(f"[LIGHT] Renamed RS Light & Set Light Group: {new_name}")
                if new_name not in processed_names:
                    processed_names.append(new_name)

            # For C4D lights with RS tag, set the light group on the tag
            elif is_c4d_light_with_rs and rs_tag:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, rs_tag)
                rs_tag[c4d.REDSHIFT_LIGHT_LIGHT_GROUP] = new_name
                print(f"[LIGHT] Renamed C4D Light & Set Light Group: {new_name}")
                if new_name not in processed_names:
                    processed_names.append(new_name)

            # C4D light without RS tag
            else:
                print(f"[LIGHT] Renamed {new_name} (No RS Tag found - consider adding one)")

    # --- 2. CREATE AOVs IN REDSHIFT MANAGER ---
    print(f"\n[DEBUG] Processing {len(processed_names)} light groups for AOV creation: {processed_names}")

    # Get current AOVs using the correct API
    try:
        current_aovs = redshift.RendererGetAOVs(vp)
        if current_aovs is None:
            current_aovs = []
        print(f"[DEBUG] Found {len(current_aovs)} existing AOVs")
    except Exception as e:
        print(f"[ERROR] Failed to get existing AOVs: {e}")
        current_aovs = []

    # Build a set of existing AOV names for quick lookup
    existing_aov_names = set()
    for aov in current_aovs:
        try:
            aov_name = aov.GetParameter(c4d.REDSHIFT_AOV_NAME)
            aov_type = aov.GetParameter(c4d.REDSHIFT_AOV_TYPE)
            if aov_name:
                existing_aov_names.add(aov_name)
                print(f"[DEBUG] Existing AOV: '{aov_name}' (Type: {aov_type})")
        except Exception as e:
            print(f"[DEBUG] Could not read AOV: {e}")

    print(f"[DEBUG] Existing AOV names: {existing_aov_names}")

    # --- DENOISE SETTINGS ---
    # Beauty pass AOV types that should have denoising enabled
    BEAUTY_AOV_TYPES = [
        0,   # Beauty
        5,   # Diffuse Lighting
        6,   # Diffuse Lighting Raw
        8,   # Emission
        9,   # GI
        10,  # GI Raw
        13,  # Reflections
        14,  # Reflections Raw
        15,  # Refractions
        16,  # Refractions Raw
        18,  # Specular Lighting
        19,  # SSS
        20,  # SSS Raw
        3,   # Caustics
        4,   # Caustics Raw
        24,  # Volume Lighting
    ]

    # Helper function to enable denoise on an AOV
    def enable_denoise(aov):
        """Try to enable denoise on an AOV using various parameter IDs."""
        # Try standard c4d constants first
        if hasattr(c4d, 'REDSHIFT_AOV_DENOISE_ENABLED'):
            try:
                aov.SetParameter(c4d.REDSHIFT_AOV_DENOISE_ENABLED, True)
                return True
            except:
                pass
        
        if hasattr(c4d, 'REDSHIFT_AOV_DENOISE'):
            try:
                aov.SetParameter(c4d.REDSHIFT_AOV_DENOISE, True)
                return True
            except:
                pass
        
        # Try common parameter IDs for denoise
        for param_id in [1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015]:
            try:
                aov.SetParameter(c4d.DescID(c4d.DescLevel(param_id)), True)
                return True
            except:
                pass
        
        return False

    # Create new AOVs list (start with existing ones)
    new_aov_list = list(current_aovs)
    aovs_created = 0
    denoise_enabled_count = 0

    # --- ENABLE DENOISE FOR EXISTING BEAUTY PASSES ---
    print("\n[DEBUG] Enabling denoise for existing beauty passes...")
    for aov in current_aovs:
        try:
            aov_name = aov.GetParameter(c4d.REDSHIFT_AOV_NAME)
            aov_type = aov.GetParameter(c4d.REDSHIFT_AOV_TYPE)
            aov_enabled = aov.GetParameter(c4d.REDSHIFT_AOV_ENABLED)
            
            if aov_type in BEAUTY_AOV_TYPES and aov_enabled:
                if enable_denoise(aov):
                    denoise_enabled_count += 1
                    print(f"[DENOISE] Enabled for existing AOV: {aov_name}")
        except Exception as e:
            print(f"[DEBUG] Could not process AOV for denoise: {e}")

    # --- CREATE NEW AOVs FOR LIGHT GROUPS ---
    for light_group_name in processed_names:
        if light_group_name not in existing_aov_names:
            try:
                # Create new Light Group AOV
                new_aov = redshift.RSAOV()

                # Set AOV type to Beauty
                new_aov.SetParameter(c4d.REDSHIFT_AOV_TYPE, REDSHIFT_AOV_TYPE_BEAUTY)

                # Set the AOV name
                new_aov.SetParameter(c4d.REDSHIFT_AOV_NAME, light_group_name)

                # Enable the AOV
                new_aov.SetParameter(c4d.REDSHIFT_AOV_ENABLED, True)

                # Enable multipass
                new_aov.SetParameter(c4d.REDSHIFT_AOV_MULTIPASS_ENABLED, True)

                # Set the Light Group filter - uses REDSHIFT_AOV_LIGHTGROUP_NAMES (1026)
                # The light group names should be newline-separated
                new_aov.SetParameter(c4d.REDSHIFT_AOV_LIGHTGROUP_NAMES, light_group_name + "\n")

                # Enable denoise for the new AOV
                if enable_denoise(new_aov):
                    denoise_enabled_count += 1
                    print(f"[AOV] Created Light Group AOV with denoise: {light_group_name}")
                else:
                    print(f"[AOV] Created Light Group AOV (denoise param not found): {light_group_name}")

                # Add to our list
                new_aov_list.append(new_aov)
                aovs_created += 1
            except Exception as e:
                print(f"[ERROR] Failed to create AOV '{light_group_name}': {e}")
        else:
            print(f"[AOV] Skipping {light_group_name} (Already exists)")

    # Apply all AOVs at once using RendererSetAOVs
    if aovs_created > 0 or denoise_enabled_count > 0:
        try:
            redshift.RendererSetAOVs(vp, new_aov_list)
            print(f"[DEBUG] Successfully applied {len(new_aov_list)} AOVs to Redshift")
        except Exception as e:
            print(f"[ERROR] Failed to set AOVs: {e}")
    else:
        print("[DEBUG] No changes to apply")

    doc.EndUndo()
    c4d.EventAdd()
    print(f"\n--- SYNC COMPLETE ---")
    print(f"[SUMMARY] Lights processed: {len(processed_names)}, AOVs created: {aovs_created}, Denoise enabled: {denoise_enabled_count}")

if __name__=='__main__':
    main()