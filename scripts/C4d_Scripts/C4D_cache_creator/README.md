# C4D Wedge Tool - User Manual

## Quick Start

1. **Run** `C4D_cache_gui.py` via Extensions > Script Manager
2. **Set output path** for saved files
3. **Select object** from dropdown
4. **Select parameter** from dropdown
5. **Click "Add Param"**
6. **Enter values** as comma-separated: `10, 25, 50, 100`
7. **Click "▶ Run Wedge"**

---

## Interface

| Control | Description |
|---------|-------------|
| Output | Folder where `.c4d` files are saved |
| Object dropdown | Select scene object |
| Param dropdown | Select parameter to wedge |
| **Add Param** | Add selected parameter to list |
| **Refresh** | Reload objects from scene |
| **List All** | Print all params to Console |
| **Fill XP Cache** | Trigger X-Particles cache per iteration |
| **Render** | Render to Picture Viewer per iteration |
| **Run Wedge** | Execute all iterations |
| **Clear** | Remove all parameters |

---

## Value Entry

Enter comma-separated values:
```
10, 25, 50, 100
```

Multiple parameters = cartesian product:
- Param A: `10, 50` (2 values)
- Param B: `100, 200, 300` (3 values)  
- **Result:** 6 files (2 × 3)

---

## Output Files

Files are named:
```
wedge_0000_ParamName_Value.c4d
wedge_0001_ParamName_Value.c4d
...
```
