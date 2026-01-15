import c4d
import os
import shutil
# X-Particles xpCache Object plugin ID
XP_CACHE_OBJECT_ID = 1028775
def find_first_object_of_type(op, type_id):
    """Depth-first search for the first object with given type id."""
    while op:
        if op.GetType() == type_id:
            return op
        down = find_first_object_of_type(op.GetDown(), type_id)
        if down:
            return down
        op = op.GetNext()
    return None
def ensure_document_saved(doc):
    """Ensure the document is saved, otherwise prompt Save As."""
    if not doc.GetDocumentPath():
        c4d.CallCommand(12218)  # Save As...
        if not doc.GetDocumentPath():
            raise RuntimeError("A jelenet nincs elmentve.")
def build_cache_folder(doc):
    """
    Create:
    ../003_Cache/Cache_script_<scene_name_without_ext>
    """
    doc_path = doc.GetDocumentPath()
    doc_name = doc.GetDocumentName()
    scene_name, _ = os.path.splitext(doc_name)
    parent_dir = os.path.dirname(doc_path)  # one folder up
    cache_root = os.path.join(parent_dir, "003_Cache")
    cache_folder = os.path.join(cache_root, f"Cache_{scene_name}")
    # Remove existing cache folder to avoid overwrite dialogs
    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)
    os.makedirs(cache_folder, exist_ok=True)
    return cache_folder
def main():
    doc = c4d.documents.GetActiveDocument()
    if not doc:
        return
    # 1. Make sure the document is saved
    ensure_document_saved(doc)
    # 2. Find xpCache object
    cache_obj = doc.GetActiveObject()
    if not cache_obj or cache_obj.GetType() != XP_CACHE_OBJECT_ID:
        cache_obj = find_first_object_of_type(doc.GetFirstObject(), XP_CACHE_OBJECT_ID)
    if not cache_obj:
        raise RuntimeError("Nem található xpCache Object a jelenetben.")
    # 3. Create cache folder
    cache_folder_path = build_cache_folder(doc)
    # 4. Set xpCache folder (STRING, not Filename)
    cache_obj[c4d.XOCA_CACHE_FOLDER] = cache_folder_path
    c4d.EventAdd()
    print("xpCache folder set to:", cache_folder_path)
    # 5. Build Cache
    c4d.CallButton(cache_obj, c4d.XOCA_CACHE_FILL)
    # 6. Render to Picture Viewer
    c4d.CallCommand(12099)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        c4d.gui.MessageDialog(f"Hiba történt:\n{e}")
    finally:
        c4d.EventAdd()