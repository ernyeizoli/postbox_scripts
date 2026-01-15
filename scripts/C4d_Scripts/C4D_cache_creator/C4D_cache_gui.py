import c4d
import os
import time

# X-Particles xpCache Object plugin ID
XP_CACHE_OBJECT_ID = 1028775

# Try to get X-Particles cache fill constant
try:
    XPARTICLES_CACHE_FILL_ID = c4d.XOCA_CACHE_FILL
except AttributeError:
    XPARTICLES_CACHE_FILL_ID = None

# UI IDs
IDC_OBJ_COMBO     = 1000
IDC_PARAM_COMBO   = 1001
IDC_REFRESH       = 1002
IDC_ADD           = 1003
IDC_RUN           = 1004
IDC_CLEAR         = 1005
IDC_LIST_PARAMS   = 1006
IDC_COUNT_TEXT    = 1007
IDC_OUTPUT_PATH   = 1008
IDC_BROWSE_PATH   = 1009
IDC_XP_CACHE      = 1010
IDC_RENDER        = 1011

IDC_PARAM_GROUP   = 2000
IDC_PARAM_SCROLL  = 2001
IDC_ROWS_CONTAINER = 2002
IDC_ROW_BASE      = 30000

# Description constants
DESC_NAME_ID = 1
DESC_DATATYPE_ID = 8

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def gather_scene_objects(doc):
    """Get list of all objects in the scene."""
    out = []
    def recurse(op):
        while op:
            out.append(op)
            if op.GetDown():
                recurse(op.GetDown())
            op = op.GetNext()
    recurse(doc.GetFirstObject())
    return out

def description_entries(obj):
    """Get description entries for object."""
    try:
        raw = obj.GetDescription(c4d.DESCFLAGS_DESC_NONE) 
        if raw:
            for bc, pid, gid in raw:
                yield bc, pid, gid
    except Exception:
        pass

def build_params_for_obj(obj):
    """Build parameters list (name + DescID) for an object."""
    out = []
    if obj is None:
        return out
    for bc, pid, gid in description_entries(obj):
        if not bc:
            continue
        try:
            name  = bc[DESC_NAME_ID]
            dtype = bc[DESC_DATATYPE_ID]
        except Exception:
            continue
        if dtype not in (c4d.DTYPE_GROUP, c4d.DTYPE_SEPARATOR):
            out.append((str(name), pid))
    return out

def find_xp_cache_object(doc):
    """Find X-Particles cache object in the scene."""
    def traverse(op):
        while op:
            if op.GetType() == XP_CACHE_OBJECT_ID:
                return op
            down = traverse(op.GetDown())
            if down:
                return down
            op = op.GetNext()
        return None
    return traverse(doc.GetFirstObject())

def wait_for_xp_cache(xp_cache, timeout=600):
    """Wait for X-Particles cache fill to complete."""
    if XPARTICLES_CACHE_FILL_ID is None:
        return False
    
    print("[XP Cache] Waiting for fill to complete...", end="", flush=True)
    waited = 0.0
    active_detected = False
    
    while waited < timeout:
        try:
            active = bool(xp_cache[XPARTICLES_CACHE_FILL_ID])
        except:
            active = False
        
        if active:
            active_detected = True
            if int(waited * 5) % 5 == 0:
                print(".", end="", flush=True)
        else:
            if active_detected or waited >= 1.0:
                print(" Done!")
                return True
        
        c4d.GeSyncMessage(c4d.EVMSG_ASYNCEDITORMOVE)
        c4d.DrawViews()
        time.sleep(0.2)
        waited += 0.2
    
    print(" Timeout!")
    return False

def fill_xp_cache(xp_cache):
    """Trigger X-Particles cache fill."""
    if not xp_cache or XPARTICLES_CACHE_FILL_ID is None:
        return False
    
    c4d.CallButton(xp_cache, XPARTICLES_CACHE_FILL_ID)
    c4d.EventAdd(c4d.EVENT_ANIMATE)
    return wait_for_xp_cache(xp_cache)

# ============================================================================
# MAIN DIALOG
# ============================================================================

class WedgeDialog(c4d.gui.GeDialog):
    def __init__(self):
        self.obj_list = []
        self.current_param_list = []
        # Row data: {object, pid, name, values: [list of floats]}
        self.rows = []
        self.output_path = ""

    def CreateLayout(self):
        self.SetTitle("C4D Wedge Tool")

        # === OUTPUT PATH ===
        self.GroupBegin(100, c4d.BFH_SCALEFIT, 3, 0)
        self.AddStaticText(0, c4d.BFH_LEFT, name="Output:", initw=50)
        self.AddEditText(IDC_OUTPUT_PATH, c4d.BFH_SCALEFIT, initw=400)
        self.AddButton(IDC_BROWSE_PATH, c4d.BFH_LEFT, name="...", initw=30)
        self.GroupEnd()

        # === OBJECT/PARAM SELECTION ===
        self.GroupBegin(1, c4d.BFH_SCALEFIT, 5, 0)
        self.AddComboBox(IDC_OBJ_COMBO, c4d.BFH_SCALEFIT, initw=200)
        self.AddComboBox(IDC_PARAM_COMBO, c4d.BFH_SCALEFIT, initw=250)
        self.AddButton(IDC_REFRESH, c4d.BFH_LEFT, name="Refresh")
        self.AddButton(IDC_ADD, c4d.BFH_LEFT, name="Add Param")
        self.AddButton(IDC_LIST_PARAMS, c4d.BFH_LEFT, name="List All")
        self.GroupEnd()

        # === OPTIONS ===
        self.GroupBegin(2, c4d.BFH_SCALEFIT, 5, 0)
        self.AddCheckbox(IDC_XP_CACHE, c4d.BFH_LEFT, 0, 0, "Fill XP Cache")
        self.AddCheckbox(IDC_RENDER, c4d.BFH_LEFT, 0, 0, "Render")
        self.AddStaticText(0, c4d.BFH_SCALEFIT, name="")
        self.AddButton(IDC_RUN, c4d.BFH_RIGHT, name="▶ Run Wedge")
        self.AddButton(IDC_CLEAR, c4d.BFH_RIGHT, name="Clear")
        self.GroupEnd()

        # === PARAMETER LIST ===
        self.GroupBegin(IDC_PARAM_GROUP, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 0, "Wedge Parameters")
        self.ScrollGroupBegin(IDC_PARAM_SCROLL, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, c4d.SCROLLGROUP_VERT | c4d.SCROLLGROUP_HORIZ)
        
        # Inner container for rows - this is what we flush
        self.GroupBegin(IDC_ROWS_CONTAINER, c4d.BFH_SCALEFIT | c4d.BFV_TOP, 1, 0)
        self._build_param_rows()
        self.GroupEnd()  # rows container
        
        self.GroupEnd()  # scroll
        self.GroupEnd()  # param group

        # === STATUS ===
        self.GroupBegin(3, c4d.BFH_SCALEFIT, 1, 0)
        self.AddStaticText(IDC_COUNT_TEXT, c4d.BFH_LEFT, name="Parameters: 0 | Total iterations: 0")
        self.GroupEnd()

        return True

    def _build_param_rows(self):
        """Build the parameter rows in the scroll area."""
        if not self.rows:
            self.GroupBegin(0, c4d.BFH_CENTER, 1, 1)
            self.AddStaticText(0, c4d.BFH_CENTER, 0, 0, "No parameters added. Select object & parameter, then click 'Add Param'.")
            self.GroupEnd()
        else:
            for i, r in enumerate(self.rows):
                base = IDC_ROW_BASE + i * 100
                self.GroupBegin(base, c4d.BFH_SCALEFIT, 0, 1)  # Horizontal group
                
                # Object/Parameter label
                obj_name = "DELETED"
                if r['object'] and r['object'].IsAlive():
                    obj_name = r['object'].GetName()
                label = f"{obj_name} ▸ {r['name']}"
                self.AddStaticText(base + 1, c4d.BFH_LEFT, name=label, initw=180)
                
                # Values input as comma-separated text
                self.AddStaticText(base + 2, c4d.BFH_LEFT, name="Values:", initw=45)
                self.AddEditText(base + 3, c4d.BFH_SCALEFIT, initw=300)
                values_str = ", ".join([str(v) for v in r.get('values', [0.0])])
                self.SetString(base + 3, values_str)
                
                # Delete button
                self.AddButton(base + 4, c4d.BFH_RIGHT, name="X", initw=25)
                
                self.GroupEnd()

    def _save_current_values(self):
        """Read current values from UI text fields and save to self.rows."""
        for i, r in enumerate(self.rows):
            base = IDC_ROW_BASE + i * 100
            try:
                values_str = self.GetString(base + 3)
                if values_str:
                    r['values'] = self._parse_values(values_str)
            except:
                pass  # Widget might not exist yet

    def _update_status(self):
        """Update the status text with parameter and iteration counts."""
        param_count = len(self.rows)
        total_iterations = 1
        for r in self.rows:
            total_iterations *= max(1, len(r.get('values', [0.0])))
        self.SetString(IDC_COUNT_TEXT, f"Parameters: {param_count} | Total iterations: {total_iterations}")

    def InitValues(self):
        # Set default output path
        doc = c4d.documents.GetActiveDocument()
        if doc and doc.GetDocumentPath():
            default_path = os.path.join(doc.GetDocumentPath(), "wedge_output")
        else:
            default_path = os.path.join(os.path.expanduser("~"), "Documents", "c4d_wedge")
        self.output_path = default_path
        self.SetString(IDC_OUTPUT_PATH, default_path)
        
        self.populate_objects()
        self._update_status()
        return True

    def populate_objects(self):
        doc = c4d.documents.GetActiveDocument()
        self.obj_list = gather_scene_objects(doc)
        
        self.FreeChildren(IDC_OBJ_COMBO)
        
        if not self.obj_list:
            self.AddChild(IDC_OBJ_COMBO, 0, "-- no objects --")
        else:
            for i, obj in enumerate(self.obj_list):
                name = obj.GetName() or "<unnamed>"
                self.AddChild(IDC_OBJ_COMBO, i, name)
            self.SetLong(IDC_OBJ_COMBO, 0)
        
        self.populate_param_combo(self.GetLong(IDC_OBJ_COMBO))

    def populate_param_combo(self, obj_index):
        self.FreeChildren(IDC_PARAM_COMBO)
        
        self.current_param_list = []
        if obj_index is None or obj_index < 0 or obj_index >= len(self.obj_list):
            self.AddChild(IDC_PARAM_COMBO, 0, "-- select object --")
            return
            
        obj = self.obj_list[obj_index]
        params = build_params_for_obj(obj)
        
        if not params:
            self.AddChild(IDC_PARAM_COMBO, 0, "-- no listable params --")
            return
            
        for i, (nm, pid) in enumerate(params):
            self.AddChild(IDC_PARAM_COMBO, i, nm)
            
        self.current_param_list = params
        self.SetLong(IDC_PARAM_COMBO, 0)

    def _parse_values(self, values_str):
        """Parse comma-separated values string into list of floats."""
        values = []
        for part in values_str.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                values.append(float(part))
            except ValueError:
                continue
        return values if values else [0.0]

    def _run_wedge(self):
        """Execute the wedge - iterate through all value combinations."""
        doc = c4d.documents.GetActiveDocument()
        if not doc:
            return
        
        # Get output path
        self.output_path = self.GetString(IDC_OUTPUT_PATH)
        if not self.output_path:
            c4d.gui.MessageDialog("Please set an output path.")
            return
        
        os.makedirs(self.output_path, exist_ok=True)
        
        # Get options
        fill_xp = self.GetBool(IDC_XP_CACHE)
        do_render = self.GetBool(IDC_RENDER)
        
        # Find XP cache if needed
        xp_cache = None
        if fill_xp:
            xp_cache = find_xp_cache_object(doc)
            if not xp_cache:
                c4d.gui.MessageDialog("X-Particles cache object not found in scene!")
                fill_xp = False
        
        # Read values from UI
        for i, r in enumerate(self.rows):
            base = IDC_ROW_BASE + i * 100
            values_str = self.GetString(base + 3)
            r['values'] = self._parse_values(values_str)
        
        # Store original values
        original_values = []
        for r in self.rows:
            if r['object'] and r['object'].IsAlive():
                try:
                    original_values.append((r['object'], r['pid'], r['object'][r['pid']]))
                except:
                    pass
        
        # Calculate total iterations
        from itertools import product
        value_lists = [r['values'] for r in self.rows]
        if not value_lists:
            c4d.gui.MessageDialog("No parameters added.")
            return
        
        all_combinations = list(product(*value_lists))
        total = len(all_combinations)
        
        print(f"\n{'='*60}")
        print(f"C4D WEDGE - Starting {total} iterations")
        print(f"Output: {self.output_path}")
        print(f"{'='*60}\n")
        
        c4d.gui.SetCursor(c4d.CURSOR_WAIT)
        
        for idx, combo in enumerate(all_combinations):
            # Build iteration name
            parts = []
            for i, val in enumerate(combo):
                safe_name = self.rows[i]['name'].replace(" ", "_")[:10]
                parts.append(f"{safe_name}_{val}")
            iter_name = "_".join(parts)
            
            print(f"[{idx+1}/{total}] {iter_name}")
            
            # Set parameter values
            doc.StartUndo()
            for i, val in enumerate(combo):
                r = self.rows[i]
                obj = r['object']
                pid = r['pid']
                
                if not obj or not obj.IsAlive():
                    continue
                
                try:
                    dtype = obj.GetParameter(pid, c4d.DESCFLAGS_GET_NONE)
                    if isinstance(dtype, c4d.Vector):
                        obj[pid] = c4d.Vector(val, val, val)
                    elif isinstance(dtype, bool):
                        obj[pid] = bool(val)
                    elif isinstance(dtype, int):
                        obj[pid] = int(val)
                    else:
                        obj[pid] = val
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                except Exception as e:
                    print(f"  Warning: Could not set {r['name']}: {e}")
            
            doc.EndUndo()
            c4d.EventAdd()
            c4d.DrawViews()
            time.sleep(0.05)
            
            # Fill XP cache if enabled
            if fill_xp and xp_cache:
                print(f"  Filling X-Particles cache...")
                fill_xp_cache(xp_cache)
            
            # Save project
            filename = f"wedge_{idx:04d}_{iter_name}.c4d"
            filepath = os.path.join(self.output_path, filename)
            c4d.documents.SaveDocument(doc, filepath, c4d.SAVEDOCUMENTFLAGS_0, c4d.FORMAT_C4DEXPORT)
            print(f"  Saved: {filename}")
            
            # Render if enabled
            if do_render:
                print(f"  Rendering...")
                c4d.CallCommand(12099)  # Render to Picture Viewer
                # Wait a bit for render to start
                time.sleep(0.5)
        
        # Restore original values
        doc.StartUndo()
        for obj, pid, val in original_values:
            if obj and obj.IsAlive():
                try:
                    obj[pid] = val
                    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                except:
                    pass
        doc.EndUndo()
        c4d.EventAdd()
        
        c4d.gui.SetCursor(c4d.CURSOR_DEFAULT)
        
        print(f"\n{'='*60}")
        print(f"WEDGE COMPLETE - {total} iterations saved to:")
        print(f"{self.output_path}")
        print(f"{'='*60}\n")
        
        c4d.gui.MessageDialog(f"Wedge complete!\n{total} iterations saved to:\n{self.output_path}")

    def Command(self, id, msg):
        doc = c4d.documents.GetActiveDocument()
        if not doc:
            return True

        if id == IDC_OBJ_COMBO:
            sel = self.GetLong(IDC_OBJ_COMBO)
            self.populate_param_combo(sel)
            return True

        if id == IDC_REFRESH:
            self.populate_objects()
            return True

        if id == IDC_BROWSE_PATH:
            path = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_ANYTHING, flags=c4d.FILESELECT_DIRECTORY)
            if path:
                self.SetString(IDC_OUTPUT_PATH, path)
            return True

        if id == IDC_LIST_PARAMS:
            sel_obj_idx = self.GetLong(IDC_OBJ_COMBO)
            if sel_obj_idx is None or sel_obj_idx < 0 or sel_obj_idx >= len(self.obj_list):
                c4d.gui.MessageDialog("Select an object first.")
                return True
            
            obj = self.obj_list[sel_obj_idx]
            print(f"\n--- All Parameters for: {obj.GetName()} [{obj.GetType()}] ---")
            
            count = 0
            for bc, pid, gid in description_entries(obj):
                if not bc:
                    continue
                try:
                    name = bc[DESC_NAME_ID]
                    dtype = bc[DESC_DATATYPE_ID]
                    try:
                        val = obj[pid]
                    except:
                        val = "<Write-Only>"
                    print(f"  {name}: {val} (DescID: {pid})")
                    count += 1
                except:
                    pass
            
            print(f"--- {count} parameters ---\n")
            c4d.gui.MessageDialog("Parameter list printed to Console (Window > Console)")
            return True

        if id == IDC_ADD:
            sel_obj_idx = self.GetLong(IDC_OBJ_COMBO)
            sel_param_idx = self.GetLong(IDC_PARAM_COMBO)
            
            if sel_obj_idx is None or sel_obj_idx < 0 or sel_obj_idx >= len(self.obj_list):
                c4d.gui.MessageDialog("Select an object first.")
                return True
            if sel_param_idx is None or sel_param_idx < 0 or sel_param_idx >= len(self.current_param_list):
                c4d.gui.MessageDialog("Select a parameter.")
                return True
                
            obj = self.obj_list[sel_obj_idx]
            pname, pid = self.current_param_list[sel_param_idx]
            
            # Check if already added
            for r in self.rows:
                if r['object'] == obj and r['pid'] == pid:
                    c4d.gui.MessageDialog("Parameter already added.")
                    return True
            
            # Get current value
            cur_val = 0.0
            try:
                cur = obj.GetParameter(pid, c4d.DESCFLAGS_GET_NONE)
                if isinstance(cur, c4d.Vector):
                    cur_val = float(cur.x) 
                else:
                    cur_val = float(cur) if cur is not None else 0.0
            except:
                pass
            
            # Add with default values
            self.rows.append({
                'object': obj, 
                'pid': pid, 
                'name': pname, 
                'values': [cur_val]
            })
            
            print(f"Added: {obj.GetName()} > {pname}")
            
            self._save_current_values()  # Preserve existing row values
            self.LayoutFlushGroup(IDC_ROWS_CONTAINER)
            self._build_param_rows()
            self.LayoutChanged(IDC_ROWS_CONTAINER)
            self._update_status()
            return True

        if id == IDC_CLEAR:
            self.rows = []
            self.LayoutFlushGroup(IDC_ROWS_CONTAINER)
            self._build_param_rows()
            self.LayoutChanged(IDC_ROWS_CONTAINER)
            self._update_status()
            return True

        if id == IDC_RUN:
            self._run_wedge()
            return True

        # Handle dynamic row delete buttons
        if id >= IDC_ROW_BASE:
            idx = (id - IDC_ROW_BASE) // 100
            gadget = (id - IDC_ROW_BASE) % 100
            
            if gadget == 4 and idx < len(self.rows):  # Delete button
                self._save_current_values()  # Preserve other rows' values
                self.rows.pop(idx)
                self.LayoutFlushGroup(IDC_ROWS_CONTAINER)
                self._build_param_rows()
                self.LayoutChanged(IDC_ROWS_CONTAINER)
                self._update_status()
                return True

        return True


    def Message(self, msg, result):
        """Handle drag and drop messages - accepts objects from Object Manager."""
        if msg.GetId() == c4d.BFM_DRAGRECEIVE:
            # Get drag info
            drag_type = msg[c4d.BFM_DRAG_TYPE]
            drag_data = msg[c4d.BFM_DRAG_DATA]
            
            if msg[c4d.BFM_DRAG_FINISHED]:
                # Drag finished - process the drop
                if drag_type == c4d.DRAGTYPE_ATOMARRAY and drag_data:
                    # Objects were dropped from Object Manager
                    for obj in drag_data:
                        if isinstance(obj, c4d.BaseObject):
                            # Find and select this object in our dropdown
                            for i, list_obj in enumerate(self.obj_list):
                                if list_obj == obj:
                                    self.SetLong(IDC_OBJ_COMBO, i)
                                    self.populate_param_combo(i)
                                    print(f"[Wedge] Selected object: {obj.GetName()}")
                                    break
                            break
                return True
            else:
                # Accept object drags
                if drag_type == c4d.DRAGTYPE_ATOMARRAY:
                    return self.SetDragDestination(c4d.MOUSE_POINT_HAND)
                    
        return c4d.gui.GeDialog.Message(self, msg, result)
    
    def _add_param_from_drag(self, obj, descid):
        """Add a parameter from drag and drop."""
        # Check if already added
        for r in self.rows:
            if r['object'] == obj and r['pid'] == descid:
                print(f"[Wedge] Parameter already in list")
                return
        
        # Get parameter name
        description = obj.GetDescription(c4d.DESCFLAGS_DESC_NONE)
        pname = "Unknown"
        for bc, pid, gid in description:
            if bc and pid == descid:
                try:
                    pname = bc[DESC_NAME_ID]
                except:
                    pass
                break
        
        # Get current value
        cur_val = 0.0
        try:
            cur = obj.GetParameter(descid, c4d.DESCFLAGS_GET_NONE)
            if isinstance(cur, c4d.Vector):
                cur_val = float(cur.x)
            elif cur is not None:
                cur_val = float(cur)
        except:
            pass
        
        # Add to rows
        self._save_current_values()
        self.rows.append({
            'object': obj,
            'pid': descid,
            'name': str(pname),
            'values': [cur_val]
        })
        
        print(f"[Wedge] Added via drag: {obj.GetName()} > {pname}")
        
        self.LayoutFlushGroup(IDC_ROWS_CONTAINER)
        self._build_param_rows()
        self.LayoutChanged(IDC_ROWS_CONTAINER)
        self._update_status()


# ============================================================================
# MAIN
# ============================================================================
global_wedge_dialog = None

def main():
    global global_wedge_dialog
    
    if global_wedge_dialog and global_wedge_dialog.IsOpen():
        global_wedge_dialog.Close()
    
    global_wedge_dialog = WedgeDialog()
    global_wedge_dialog.Open(c4d.DLG_TYPE_ASYNC, defaultw=700, defaulth=400)

if __name__ == '__main__':
    main()