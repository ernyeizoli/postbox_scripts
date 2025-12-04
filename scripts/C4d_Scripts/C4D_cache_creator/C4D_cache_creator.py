import c4d
import os
import time
import subprocess
from datetime import datetime

# --- CONFIGURATION ---
BASE_PATH = r"C:\Users\User\Documents\dev\cache_aut"
C4D_EXECUTABLE = r"C:\Program Files\Maxon Cinema 4D 2024\Cinema 4D.exe"

# IMPORTANT: Set this to FALSE for heavy scenes to prevent freezing
# FALSE = Renders in background via command line (recommended)
# TRUE  = Renders directly in C4D (may freeze UI on heavy scenes)
RENDER = False
USE_DIRECT_RENDER = False

# Ensure base path exists
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)

def show_status(message):
    """Displays status in console and status bar"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    c4d.gui.StatusSetText(message)

def wait_for_editor_completion():
    """Waits for editor operations to complete"""
    print("\n[INFO] Waiting for operation to complete...", end="", flush=True)
    
    max_attempts = 1500  # ~5 minutes
    attempts = 0
    
    while c4d.CheckIsRunning(c4d.CHECKISRUNNING_EDITORRENDERING) and attempts < max_attempts:
        attempts += 1
        if attempts % 10 == 0:  # Dot every ~2 seconds
            print(".", end="", flush=True)
        c4d.GeSyncMessage(c4d.EVMSG_ASYNCEDITORMOVE)
        c4d.DrawViews()
        time.sleep(0.2)
    
    if attempts >= max_attempts:
        print("\n[ERROR] Operation timed out!")
        return False
    
    print("\n[INFO] Operation completed.")
    return True

def clear_cloth_cache(cloth_tag):
    """Safely clears cloth cache using UI buttons"""
    if not cloth_tag:
        print("[ERROR] Cloth tag not found!")
        return False
    
    show_status("Clearing cloth cache...")
    c4d.CallButton(cloth_tag, c4d.SIMULATION_DELCACHE_ALL)
    c4d.EventAdd(c4d.EVENT_ANIMATE)
    c4d.DrawViews()
    time.sleep(0.5)
    return True

def bake_cloth_cache(doc, cloth_tag):
    """Bakes cloth cache with proper completion detection"""
    if not cloth_tag:
        print("[ERROR] Cloth tag not found!")
        return False
    
    if not clear_cloth_cache(cloth_tag):
        return False
    
    show_status("Baking cloth cache...")
    c4d.CallButton(cloth_tag, c4d.SIMULATION_DO_CALCULATE_ALL)
    c4d.EventAdd(c4d.EVENT_ANIMATE)
    c4d.DrawViews()
    
    if not wait_for_editor_completion():
        return False
    
    time.sleep(1)  # Safety buffer
    return True

def set_turbulence_scale(turbulence, scale_percent):
    """Sets turbulence scale (0-100%)"""
    if not turbulence:
        print("[ERROR] Turbulence object not found!")
        return False
    
    turbulence[c4d.TURBULENCEOBJECT_SCALE] = scale_percent / 100.0
    turbulence.Message(c4d.MSG_UPDATE)
    c4d.EventAdd()
    print(f"[INFO] Turbulence scale set to: {scale_percent}%")
    return True

def save_project_copy(doc, scale):
    """Saves a copy of the project with unique name"""
    filename = f"cloth_cache_turbulence_{scale:03d}.c4d"
    filepath = os.path.join(BASE_PATH, filename)
    
    print(f"[INFO] Saving project copy: {filename}...")
    temp_doc = doc.GetClone()
    
    if not c4d.documents.SaveDocument(temp_doc, filepath, c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT):
        print(f"[ERROR] Failed to save project: {filename}")
        return None
    
    print(f"[INFO] Project saved: {filename}")
    return filepath

def render_direct(doc, scale):
    """Renders directly in current session (may freeze UI)"""
    render_data = doc.GetActiveRenderData()
    output_path = os.path.join(BASE_PATH, f"render_turbulence_{scale:03d}")
    render_data[c4d.RDATA_PATH] = output_path
    
    c4d.EventAdd()
    c4d.DrawViews()
    
    msg = f"Rendering scale {scale}%..."
    print(f"[INFO] {msg}")
    show_status(msg)
    
    # Stop any existing renders first
    c4d.CallCommand(430000748)  # Stop Rendering
    
    time.sleep(0.5)  # Brief pause
    
    # Start render to Picture Viewer
    c4d.CallCommand(12099)  # Render to Picture Viewer
    
    # Wait for render to complete
    print("[INFO] Waiting for render to complete...", end="", flush=True)
    
    max_wait = 600  # 10 minutes max
    wait_time = 0
    
    while c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING) and wait_time < max_wait:
        wait_time += 1
        if wait_time % 5 == 0:  # Dot every ~1 second
            print(".", end="", flush=True)
        c4d.GeSyncMessage(c4d.EVMSG_ASYNCEDITORMOVE)
        c4d.DrawViews()
        time.sleep(0.2)
    
    if wait_time >= max_wait:
        print("\n[WARNING] Render may still be running in background.")
    else:
        print("\n[INFO] Render completed.")
    
    time.sleep(1)
    return True

def render_command_line(doc, scale):
    """Renders using command line (non-blocking, recommended)"""
    project_file = os.path.join(BASE_PATH, f"cloth_cache_turbulence_{scale:03d}.c4d")
    output_file = os.path.join(BASE_PATH, f"render_turbulence_{scale:03d}")
    
    # Save project with correct render path
    if not save_project_copy(doc, scale):
        return False
    
    # Update render path in saved file
    temp_doc = c4d.documents.LoadDocument(project_file, c4d.SCENEFILTER_0)
    if temp_doc:
        render_data = temp_doc.GetActiveRenderData()
        render_data[c4d.RDATA_PATH] = output_file
        c4d.documents.SaveDocument(temp_doc, project_file, c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT)
        c4d.documents.KillDocument(temp_doc)
        time.sleep(0.5)
    
    # Build command line
    cmd = f'"{C4D_EXECUTABLE}" -nogui -render "{project_file}"'
    print(f"[INFO] Launching background render: {cmd}")
    
    try:
        # Start process and don't wait
        subprocess.Popen(cmd, shell=True, close_fds=True)
        print(f"[INFO] ✓ Render launched for scale {scale}%")
        print(f"[INFO] Output will be: {output_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to launch render: {e}")
        return False

def main():
    doc = c4d.documents.GetActiveDocument()
    show_status("Initializing script...")
    
    print("\n" + "="*70)
    print("C4D Cloth Cache & Render Automation")
    print(f"Render Mode: {'DIRECT (UI may freeze)' if USE_DIRECT_RENDER else 'COMMAND LINE (Background)'}")
    print(f"C4D Executable: {C4D_EXECUTABLE}")
    print(f"Output Folder: {BASE_PATH}")
    print("="*70 + "\n")
    
    plane = doc.SearchObject("Plane")
    turbulence = doc.SearchObject("Turbulence")
    
    if not plane or not turbulence:
        c4d.gui.MessageDialog("ERROR: 'Plane' or 'Turbulence' object not found!")
        return False
    
    cloth_tag = plane.GetTag(c4d.Tcloth)
    if not cloth_tag:
        c4d.gui.MessageDialog("ERROR: No Cloth tag found on 'Plane' object!")
        return False
    
    # Test with ONE scale first
    scales = [20, 100, 1]  # Change to [20, 50, 100] after testing
    
    for i, scale in enumerate(scales):
        print(f"\n{'='*60}")
        print(f"STEP {i+1}/{len(scales)}: Processing Turbulence Scale {scale}%")
        print(f"{'='*60}")
        
        if not set_turbulence_scale(turbulence, scale):
            continue
        
        if not bake_cloth_cache(doc, cloth_tag):
            c4d.gui.MessageDialog(f"ERROR: Failed to bake cache for scale {scale}%")
            continue
        
        if RENDER:
            if USE_DIRECT_RENDER:
                render_direct(doc, scale)
            else:
                render_command_line(doc, scale)
            
            # Critical: Let C4D breathe between iterations
            print("[INFO] Cooling down...", end="", flush=True)
            for _ in range(15):  # 3 second pause
                c4d.GeSyncMessage(c4d.EVMSG_ASYNCEDITORMOVE)
                c4d.DrawViews()
                time.sleep(0.2)
            print(" done.")
        else:
            msg = "Render was not on."
    
    c4d.gui.StatusClear()
    
    # Final message
    if not FINAL:
        msg = "Render was not turned on."
    elif USE_DIRECT_RENDER:
        msg = "Direct rendering complete! Check Picture Viewer."
    else:
        msg = "Command line renders launched! Or script ended who knows??"
    
    c4d.gui.MessageDialog(msg)
    print("\n" + "="*70)
    print("[INFO] Script finished!")
    print("="*70)
    return True

if __name__ == '__main__':
    main()
    c4d.EventAdd()