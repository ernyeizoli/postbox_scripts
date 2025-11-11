import c4d
import os
import time

BASE_PATH = r"C:\Users\User\Documents\dev\cache_aut"

# UI IDs
IDC_OBJ_COMBO     = 1000
IDC_PARAM_COMBO   = 1001
IDC_REFRESH       = 1002
IDC_ADD           = 1003
IDC_RUN           = 1004
IDC_CLEAR         = 1005
IDC_LIST_PARAMS   = 1006
IDC_COUNT_TEXT    = 1007

IDC_PARAM_GROUP   = 2000
IDC_PARAM_SCROLL  = 2001
IDC_ROW_BASE      = 30000

# FIX: Hardcode constant values
DESC_NAME_ID = 1
DESC_DATATYPE_ID = 8

# Helper: get list of all objects
def gather_scene_objects(doc):
    out = []
    def recurse(op):
        while op:
            out.append(op)
            if op.GetDown():
                recurse(op.GetDown())
            op = op.GetNext()
    recurse(doc.GetFirstObject())
    return out

# Helper: get description entries for object
def description_entries(obj):
    """Simplified and more direct way to get description entries."""
    try:
        raw = obj.GetDescription(c4d.DESCFLAGS_DESC_NONE) 
        if raw:
            for bc, pid, gid in raw:
                yield bc, pid, gid
    except Exception:
        pass # Object might not have a description

# Helper: build parameters list (name + DescID)
def build_params_for_obj(obj):
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

class ParamAutomationDialog(c4d.gui.GeDialog):
    def __init__(self):
        self.obj_list             = []
        self.current_param_list   = []
        # --- MODIFIED: Row data now stores 3 values ---
        self.rows                 = []  # dict: {object, pid, name, val1, val2, val3}

    def CreateLayout(self):
        self.SetTitle("Parameter Automation")

        # top controls
        self.GroupBegin(1, c4d.BFH_SCALEFIT, 5, 0)
        self.AddComboBox(IDC_OBJ_COMBO,  c4d.BFH_SCALEFIT, initw=250)
        self.AddComboBox(IDC_PARAM_COMBO, c4d.BFH_SCALEFIT, initw=300)
        self.AddButton(IDC_REFRESH, c4d.BFH_LEFT, name="Refresh")
        self.AddButton(IDC_ADD,     c4d.BFH_LEFT, name="Add")
        self.AddButton(IDC_LIST_PARAMS, c4d.BFH_LEFT, name="List to Console")
        self.GroupEnd()

        # second row
        self.GroupBegin(2, c4d.BFH_SCALEFIT, 4, 0)
        self.AddButton(IDC_RUN,   c4d.BFH_LEFT, name="Run Values")
        self.AddButton(IDC_CLEAR, c4d.BFH_LEFT, name="Clear List")
        self.AddStaticText(0, c4d.BFH_SCALEFIT, name="") # Spacer
        self.AddStaticText(IDC_COUNT_TEXT, c4d.BFH_RIGHT, name="Count: 0", initw=100)
        self.GroupEnd()

        # --- RE-ADDED: The parameter list ---
        self.GroupBegin(IDC_PARAM_GROUP, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 0, "Parameters", c4d.BFV_BORDERGROUP_FOLD_OPEN)
        self.ScrollGroupBegin(IDC_PARAM_SCROLL, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, c4d.SCROLLGROUP_VERT)
        
        # This layout logic runs every time LayoutFlushGroup is called
        if not self.rows:
            self.GroupBegin(0, c4d.BFH_CENTER, 1, 1, "", 0, 0)
            self.AddStaticText(0, c4d.BFH_CENTER, 0, 0, "No parameters added.", 0)
            self.GroupEnd()
        else:
            # --- MODIFIED: Add 3 value fields ---
            for i, r in enumerate(self.rows):
                base = IDC_ROW_BASE + i*100
                # Group has 6 elements: Label, Val1, Val2, Val3, Spacer, Delete
                self.GroupBegin(base, c4d.BFH_SCALEFIT, 6, 0, "", 0, 0)
                
                obj_name = "DELETED"
                if r['object'] and r['object'].IsAlive():
                    obj_name = r['object'].GetName()
                
                label = "{} ▸ {}".format(obj_name, r['name'])
                self.AddStaticText(base+1, c4d.BFH_LEFT, name=label, initw=250)
                
                self.AddEditNumberArrows(base+2, c4d.BFH_LEFT, initw=90)
                self.SetFloat(base+2, r.get('val1', 0.0))
                
                self.AddEditNumberArrows(base+3, c4d.BFH_LEFT, initw=90)
                self.SetFloat(base+3, r.get('val2', 0.0))
                
                self.AddEditNumberArrows(base+4, c4d.BFH_LEFT, initw=90)
                self.SetFloat(base+4, r.get('val3', 0.0))
                
                self.AddStaticText(base+5, c4d.BFH_SCALEFIT, name="") # Spacer
                self.AddButton(base+6, c4d.BFH_RIGHT, name="X")
                self.GroupEnd()
        
        self.GroupEnd()  # scroll group
        self.GroupEnd()  # main parameter group

        return True
    
    def _update_count_text(self):
        """Updates the parameter count text."""
        count = len(self.rows)
        self.SetString(IDC_COUNT_TEXT, f"Count: {count}")

    def InitValues(self):
        self.populate_objects()
        self._update_count_text() # Set initial count
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

    def Command(self, id, msg):
        doc = c4d.documents.GetActiveDocument()
        if not doc:
            return True

        if id == IDC_OBJ_COMBO:
            sel = self.GetLong(IDC_OBJ_COMBO)
            self.populate_param_combo(sel)
            return True

        if id == IDC_REFRESH:
            self.populate_objects() # Refresh everything
            self.rows = [] # Clear internal list on refresh
            self.LayoutFlushGroup(IDC_PARAM_SCROLL) # Rebuild param list
            self._update_count_text() # Update count
            return True
            
        if id == IDC_LIST_PARAMS:
            sel_obj_idx = self.GetLong(IDC_OBJ_COMBO)
            if sel_obj_idx is None or sel_obj_idx < 0 or sel_obj_idx >= len(self.obj_list):
                c4d.gui.MessageDialog("Select an object first.")
                return True
            
            obj = self.obj_list[sel_obj_idx]
            print(f"--- All Parameters for: {obj.GetName()} [{obj.GetType()}] ---")
            
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
                        val = "<Write-Only or Button>"
                        
                    print(f"Name: '{name}', DescID: {pid}, DataType: {dtype}, Value: {val}")
                    count += 1
                except Exception as e:
                    print(f"Error processing a parameter: {e} (DescID: {pid})")
            
            if count == 0:
                print("No parameters found.")
            
            print(f"--- End of list ({count} params) ---")
            c4d.gui.MessageDialog("Full parameter list printed to Python Console (Window > Console).")
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
            
            for r in self.rows:
                if r['object'] == obj and r['pid'] == pid:
                    c4d.gui.MessageDialog("Parameter already added.")
                    return True
            
            # --- MODIFIED: Add 3 default values ---
            cur_val_float = 0.0
            try:
                cur = obj.GetParameter(pid, c4d.DESCFLAGS_GET_NONE)
                if isinstance(cur, c4d.Vector):
                    cur_val_float = float(cur.x) 
                else:
                    cur_val_float = float(cur) if cur is not None else 0.0
            except Exception:
                cur_val_float = 0.0
            
            # Add to internal list
            self.rows.append({
                'object': obj, 'pid': pid, 'name': pname, 
                'val1': cur_val_float, 'val2': cur_val_float, 'val3': cur_val_float
            })
            
            print(f"Added parameter: Object='{obj.GetName()}', Param='{pname}', DescID={pid}")
            
            # Flush the scroll group
            self.LayoutFlushGroup(IDC_PARAM_SCROLL)
            self._update_count_text()
            return True

        if id == IDC_CLEAR:
            self.rows = []
            self.LayoutFlushGroup(IDC_PARAM_SCROLL)
            self._update_count_text()
            return True

        if id == IDC_RUN:
            os.makedirs(BASE_PATH, exist_ok=True)
            c4d.gui.SetCursor(c4d.CURSOR_WAIT)
            
            original_values = []
            for r in self.rows:
                if not r['object'] or not r['object'].IsAlive():
                    continue
                try:
                    original_values.append((r['object'], r['pid'], r['object'][r['pid']]))
                except:
                    pass
            
            # --- MODIFIED: Run logic for 3 values ---
            for r in self.rows:
                obj = r['object']; pid = r['pid']; name = r['name']
                if not obj or not obj.IsAlive():
                    print(f"Skipping deleted object: {name}")
                    continue
                
                # Get the 3 values
                vals_to_run = [r.get('val1', 0.0), r.get('val2', 0.0), r.get('val3', 0.0)]
                
                safe = name.replace(" ","_").replace(".","_").lower()
                
                for v in vals_to_run:
                    try:
                        dtype = obj.GetParameter(pid, c4d.DESCFLAGS_GET_NONE)
                        val_to_set = v
                        if isinstance(dtype, c4d.Vector):
                            val_to_set = c4d.Vector(v, v, v) 
                        elif isinstance(dtype, bool):
                            val_to_set = bool(v)
                        elif isinstance(dtype, int):
                            val_to_set = int(v)
                        
                        doc.StartUndo()
                        obj.SetParameter(pid, val_to_set, c4d.DESCFLAGS_SET_NONE)
                        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                        doc.EndUndo()
                    except Exception:
                        try:
                            # Fallback 
                            dtype = obj[pid]
                            val_to_set = v
                            if isinstance(dtype, c4d.Vector):
                                val_to_set = c4d.Vector(v, v, v)
                            elif isinstance(dtype, bool):
                                val_to_set = bool(v)
                            elif isinstance(dtype, int):
                                val_to_set = int(v)
                            obj[pid] = val_to_set
                        except Exception as e:
                            print(f"Failed to set param {name} to value {v}: {e}")
                            
                    c4d.EventAdd() # Redraw viewport
                    time.sleep(0.02)
                    
                    obj_name_safe = obj.GetName().replace(" ", "_")
                    fname = "{}_{}_{}.c4d".format(obj_name_safe, safe, v)
                    path = os.path.join(BASE_PATH, fname)
                    
                    c4d.documents.SaveDocument(doc, path, c4d.SAVEDOCUMENTFLAGS_0, c4d.FORMAT_C4DEXPORT)
            
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
            c4d.gui.MessageDialog("Done")
            return True

        # --- MODIFIED: dynamic row controls for 3 values ---
        if id >= IDC_ROW_BASE:
            idx    = (id - IDC_ROW_BASE) // 100
            gadget = (id - IDC_ROW_BASE) % 100
            
            # Find the correct row index in our list
            row_to_modify = None
            for i, r in enumerate(self.rows):
                if (IDC_ROW_BASE + i * 100) == (id - gadget):
                    row_to_modify = i
                    break

            if row_to_modify is not None:
                if gadget == 2: # Value 1
                    try:
                        self.rows[row_to_modify]['val1'] = float(self.GetFloat(id))
                    except:
                        pass
                    return True
                if gadget == 3: # Value 2
                    try:
                        self.rows[row_to_modify]['val2'] = float(self.GetFloat(id))
                    except:
                        pass
                    return True
                if gadget == 4: # Value 3
                    try:
                        self.rows[row_to_modify]['val3'] = float(self.GetFloat(id))
                    except:
                        pass
                    return True
                if gadget == 6: # Delete button (now 6th element)
                    
                    self.rows.pop(row_to_modify)
                    self.LayoutFlushGroup(IDC_PARAM_SCROLL)
                    self._update_count_text()
                    return True
            return True

        return True

# ---------- main ----------
# Global dialog instance
global_param_automation_dialog = None

def main():
    global global_param_automation_dialog
    
    if global_param_automation_dialog and global_param_automation_dialog.IsOpen():
        global_param_automation_dialog.Close()
    
    global_param_automation_dialog = ParamAutomationDialog()
    global_param_automation_dialog.Open(c4d.DLG_TYPE_ASYNC, defaultw=900, defaulth=420)

if __name__ == '__main__':
    main()