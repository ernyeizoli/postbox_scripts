// PBV Delivery 3.0 — safer organizer for After Effects
// - Deterministic, single-pass "JUST DO IT!" (no renaming to temp)
// - Consistent _ASSETS structure (+ _REPLACEABLE_EXR)
// - Expanded extension sets; correct operator precedence
// - Recursive empty-folder deletion
// - "Color Layers" button for timeline layer labels (configurable label IDs)

{
function myScript(thisObj){

    // ==== CONFIG: label IDs (1..16) — adjust to your AE label palette if needed ====
    // Default guesses for vanilla AE:
    // 2: Yellow, 11: /Orange, 8: Blue, 1: Red, 14: Aqua/Cyan, 6: Peach, 13: Pink/Fuchsia, 9: Violet/Purple
    var LABELS = {
        YELLOW: 2,      // Text
        ORANGE: 11,      // Adjustment / Solid
        BLUE: 8,        // Footage
        RED: 1,         // Null
        CYAN: 14,        // Audio
        PEACH: 6,       // Camera (often same as ORANGE/Peach)
        FUCHSIA: 13,     // Shape
        PURPLE: 10       // Precomp
    };

    // ==== HELPERS ====
    function getExt(name){
        var idx = name.lastIndexOf(".");
        return (idx >= 0) ? name.substring(idx+1).toLowerCase() : "";
    }
    function isComp(item){ return (item instanceof CompItem); }
    function isFolder(item){ return (item instanceof FolderItem); }
    function isFootage(item){ return (item instanceof FootageItem); }

    function findOrCreateFolder(parent, name){
        for (var i=1; i<=parent.numItems; i++){
            var it = parent.item(i);
            if (isFolder(it) && it.name === name) return it;
        }
        return parent.items.addFolder(name);
    }

    function getOrCreateStructure(){
        var root = app.project.rootFolder;
        var ASSETS = findOrCreateFolder(root, "_ASSETS");
        var REPL_EXR = findOrCreateFolder(root, "_REPLACEABLE_EXR");

        // _ASSETS children
        var AUDIO   = findOrCreateFolder(ASSETS, "AUDIO");
        var COMPS   = findOrCreateFolder(ASSETS, "COMPS");
        var ELEMENTS= findOrCreateFolder(ASSETS, "ELEMENTS");
        var FOOTAGE = findOrCreateFolder(ASSETS, "FOOTAGE");
        var SOLIDS  = findOrCreateFolder(ASSETS, "SOLIDS");

        var AI      = findOrCreateFolder(ELEMENTS, "AI");
        var IMG     = findOrCreateFolder(ELEMENTS, "IMG");
        var PS      = findOrCreateFolder(ELEMENTS, "PS");

        return {
            ROOT: root,
            ASSETS: ASSETS,
            REPL_EXR: REPL_EXR,
            AUDIO: AUDIO,
            COMPS: COMPS,
            ELEMENTS: ELEMENTS,
            FOOTAGE: FOOTAGE,
            SOLIDS: SOLIDS,
            AI: AI,
            IMG: IMG,
            PS: PS
        };
    }

    function isEXRSequence(footageItem){
        if (!isFootage(footageItem)) return false;
        var ext = getExt(footageItem.name);
        if (ext !== "exr") return false;
        // Sequence detection: in AE, sequences are not "still"
        try {
            if (footageItem.mainSource && typeof footageItem.mainSource.isStill !== "undefined"){
                return (footageItem.mainSource.isStill === false);
            }
        } catch(e){}
        // Fallback: treat as non-sequence if unsure
        return false;
    }

    function moveAll(predicateFn, targetFolder){
        // iterate once over project items; collect, then move
        var bucket = [];
        for (var i=1; i<=app.project.numItems; i++){
            var it = app.project.item(i);
            if (predicateFn(it)){
                bucket.push(it);
            }
        }
        for (var j=0; j<bucket.length; j++){
            bucket[j].parentFolder = targetFolder;
        }
    }

    function deleteEmptyFoldersRecursive(folder){
        // Depth-first: clean children first
        for (var i=folder.numItems; i>=1; i--){
            var it = folder.item(i);
            if (isFolder(it)){
                deleteEmptyFoldersRecursive(it);
                // After cleaning sub-tree, remove if empty
                if (it.numItems === 0){
                    try { it.remove(); } catch(e){}
                }
            }
        }
    }

    // ==== MOVERS (deterministic) ====
    function buildFolderStructure(){
        return getOrCreateStructure();
    }

    function moveComps(struct){
        // move ALL comps into _ASSETS/COMPS
        var target = struct.COMPS;
        var comps = [];
        for (var i=1; i<=app.project.numItems; i++){
            var it = app.project.item(i);
            if (isComp(it)){
                comps.push(it);
            }
        }
        for (var j=0; j<comps.length; j++){
            comps[j].parentFolder = target;
        }
    }

    function moveVectors(struct){
        var target = struct.AI;
        moveAll(function(it){
            if (!isFootage(it)) return false;
            var ext = getExt(it.name);
            return (ext === "ai" || ext === "eps" || ext === "pdf" || ext === "svg");
        }, target);
    }

    function moveImages(struct){
        var target = struct.IMG;
        moveAll(function(it){
            if (!isFootage(it)) return false;
            var ext = getExt(it.name);
            // single EXR treated as image; EXR sequence goes elsewhere
            if (ext === "exr"){
                return (isEXRSequence(it) === false);
            }
            return (
                ext === "png" || ext === "jpg" || ext === "jpeg" ||
                ext === "tif" || ext === "tiff" || ext === "bmp" ||
                ext === "gif" || ext === "webp"
            );
        }, target);
    }

    function movePSDs(struct){
        var target = struct.PS;
        moveAll(function(it){
            if (!isFootage(it)) return false;
            var ext = getExt(it.name);
            return (ext === "psd" || ext === "psb");
        }, target);
    }

    function moveFootages(struct){
        var target = struct.FOOTAGE;
        moveAll(function(it){
            if (!isFootage(it)) return false;
            var ext = getExt(it.name);
            // exclude EXR sequences (they go to _REPLACEABLE_EXR)
            if (ext === "exr") return false;
            return (
                ext === "mov" || ext === "mp4" || ext === "mxf" || ext === "avi" ||
                ext === "mkv" || ext === "r3d" || ext === "ari" || ext === "mts" ||
                ext === "m2ts" || ext === "webm" || ext === "hevc" || ext === "h264" ||
                ext === "prores" // name-based, just in case
            );
        }, target);
    }

    function moveAudio(struct){
        var target = struct.AUDIO;
        moveAll(function(it){
            if (!isFootage(it)) return false;
            var ext = getExt(it.name);
            return (
                ext === "wav" || ext === "aif" || ext === "aiff" ||
                ext === "mp3" || ext === "ogg" || ext === "flac"
            );
        }, target);
    }

    function moveSolids(struct){
        // find all "Solids" folders anywhere and move their items into _ASSETS/SOLIDS
        var solidsTarget = struct.SOLIDS;
        function findFoldersByName(folder, name, out){
            for (var i=1; i<=folder.numItems; i++){
                var it = folder.item(i);
                if (isFolder(it) && it.name === name) out.push(it);
                if (isFolder(it)) findFoldersByName(it, name, out);
            }
        }
        var solidsFolders = [];
        findFoldersByName(app.project.rootFolder, "Solids", solidsFolders);

        for (var s=0; s<solidsFolders.length; s++){
            var f = solidsFolders[s];
            // move children (not the folder itself)
            // iterate from 1..numItems because content shrinks as we move
            for (var i=f.numItems; i>=1; i--){
                try{
                    f.item(i).parentFolder = solidsTarget;
                }catch(e){}
            }
        }
    }

    function moveEXRSequences(struct){
        var target = struct.REPL_EXR;
        moveAll(function(it){
            return isEXRSequence(it);
        }, target);
    }

    // ==== COLOR LAYERS (active comp) ====
  // === LABEL ID-k — igazítsd a saját palettádhoz (a példában: 2=Yellow, 10=Purple stb.)
var LABELS = {
    YELLOW: 2,   // Text
    ORANGE: 11,   // Adjustment / Solid
    BLUE: 8,     // Footage
    RED: 1,      // Null
    CYAN: 14,     // Audio
    PEACH: 6,    // Camera (ha külön színt akarsz, állíts más ID-t)
    FUCHSIA: 13,  // Shape
    PURPLE: 10   // Precomp  (a referenciádban Purple=10, ezért módosítottam)
};

// === HELYES, ÜTKÖZÉSMENTES VERZIÓ ===
function colorLayersByType(){
    var comp = app.project.activeItem;
    if (!(comp && comp instanceof CompItem)) { alert("No active composition found."); return; }

    app.beginUndoGroup("Color Layers - Active Comp");

    for (var i = 1; i <= comp.numLayers; i++){
        var L = comp.layer(i);

        // rétegtípusok biztonságos felismerése — a neveket NEM ütköztetjük segédfüggvényekkel
        var isPrecompLayer   = (L instanceof AVLayer) && (L.source instanceof CompItem);
        var isFootageLayer   = (L instanceof AVLayer) && (L.source instanceof FootageItem);
        var isTextLayer      = (L instanceof TextLayer);
        var isShapeLayer     = (L instanceof ShapeLayer);
        var isAdjustmentLayer= (L.adjustmentLayer === true);
        var isSolidLayer     = (L instanceof AVLayer) && isFootageLayer && (function(){
            try { return (L.source.mainSource instanceof SolidSource); } catch(e){ return false; }
        })();
        var isNullLayer      = (L instanceof AVLayer) && (function(){
            try { return L.nullLayer === true; } catch(e){ return false; }
        })();
        var isAudioLayer     = (L instanceof AVLayer) && (function(){
            try { return (L.hasAudio === true && L.hasVideo === false); } catch(e){ return false; }
        })();
        var isCameraLayer    = (L instanceof CameraLayer);

        // Prioritás a kéréseid szerint
        if (isTextLayer){
            L.label = LABELS.YELLOW;          // Text - Sárga
        } else if (isAdjustmentLayer || isSolidLayer){
            L.label = LABELS.ORANGE;          // Adjustment / Solid - Narancs
        } else if (isFootageLayer){
            L.label = LABELS.BLUE;            // Footage - Kék
        } else if (isNullLayer){
            L.label = LABELS.RED;             // Null - Piros
        } else if (isAudioLayer){
            L.label = LABELS.CYAN;            // Audio - Cián
        } else if (isCameraLayer){
            L.label = LABELS.PEACH;           // Camera - Barack/Peach
        } else if (isShapeLayer){
            L.label = LABELS.FUCHSIA;         // Shape - Fuchsia
        } else if (isPrecompLayer){
            L.label = LABELS.PURPLE;          // Precomp - Lila
        }
    }

    app.endUndoGroup();
}


    // ==== UI ====
    function myScript_buildUI(thisObj){
        var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette", "PBV Delivery 3.0", undefined, {resizeable:true});

        var justDoItButton = myPanel.add("button",[10,10,180,30], "JUST DO IT!");
        var divider = myPanel.add("panel", [10, 10, 180, 15]);
        divider.graphics.backgroundColor = divider.graphics.newBrush (divider.graphics.BrushType.SOLID_COLOR, [1, 1, 0], 1);

        var makeFolders = myPanel.add("button",[10,10,180,30], "Folder Structure");
        var moveCompsBtn = myPanel.add("button",[10,10,180,30], "Move Comps");
        var moveAiBtn    = myPanel.add("button",[10,10,180,30], "Move Vector files");
        var moveImgBtn   = myPanel.add("button",[10,10,180,30], "Move Images");
        var movePsdBtn   = myPanel.add("button",[10,10,180,30], "Move PSD files");
        var moveFootBtn  = myPanel.add("button",[10,10,180,30], "Move Footages");
        var moveSoundBtn = myPanel.add("button",[10,10,180,30], "Move Sound");
        var moveSolidsBtn= myPanel.add("button",[10,10,180,30], "Move Solids");
        var colorLayersBtn=myPanel.add("button",[10,10,180,30], "Color Layers - Active Comp");
        var deleteFoldersBtn = myPanel.add("button",[10,10,180,30], "Delete Empty Folders (recursive)");

        var label = myPanel.add("statictext", [28, 0, 300, 30], "Postbox Delivery - 2025");
        label.graphics.font = ScriptUI.newFont("Arial-BoldMT", "BOLD", 16);
        label.graphics.foregroundColor = label.graphics.newPen(label.graphics.PenType.SOLID_COLOR, [1, 1, 0], 1);
        label.alignment = "center";

        // Tooltips
        makeFolders.helpTip = "Create the _ASSETS structure (+ _REPLACEABLE_EXR).";
        moveCompsBtn.helpTip = "Move all compositions into _ASSETS/COMPS.";
        moveAiBtn.helpTip = "Move Illustrator/EPS/PDF/SVG into _ASSETS/ELEMENTS/AI.";
        moveImgBtn.helpTip = "Move images (png/jpg/jpeg/tif/tiff/bmp/gif/webp + single EXR) into _ASSETS/ELEMENTS/IMG.";
        movePsdBtn.helpTip = "Move PSD/PSB into _ASSETS/ELEMENTS/PS.";
        moveFootBtn.helpTip = "Move video footage (mov/mp4/mxf/avi/mkv/r3d/ari/...) into _ASSETS/FOOTAGE (EXR sequences excluded).";
        moveSoundBtn.helpTip = "Move audio (wav/aif/aiff/mp3/ogg/flac) into _ASSETS/AUDIO.";
        moveSolidsBtn.helpTip = "Move items from any 'Solids' folder into _ASSETS/SOLIDS.";
        colorLayersBtn.helpTip = "Color active comp layers by type (Text/Adj/Solid/Footage/Null/Audio/Camera/Shape/Precomp).";
        deleteFoldersBtn.helpTip = "Recursively delete empty folders.";

        // Button actions
        makeFolders.onClick = function(){ app.beginUndoGroup("Build Folder Structure"); getOrCreateStructure(); app.endUndoGroup(); };
        moveCompsBtn.onClick = function(){ app.beginUndoGroup("Move Comps"); moveComps(getOrCreateStructure()); app.endUndoGroup(); };
        moveAiBtn.onClick    = function(){ app.beginUndoGroup("Move Vectors"); moveVectors(getOrCreateStructure()); app.endUndoGroup(); };
        moveImgBtn.onClick   = function(){ app.beginUndoGroup("Move Images"); moveImages(getOrCreateStructure()); app.endUndoGroup(); };
        movePsdBtn.onClick   = function(){ app.beginUndoGroup("Move PSDs"); movePSDs(getOrCreateStructure()); app.endUndoGroup(); };
        moveFootBtn.onClick  = function(){ app.beginUndoGroup("Move Footage"); moveFootages(getOrCreateStructure()); app.endUndoGroup(); };
        moveSoundBtn.onClick = function(){ app.beginUndoGroup("Move Audio"); moveAudio(getOrCreateStructure()); app.endUndoGroup(); };
        moveSolidsBtn.onClick= function(){ app.beginUndoGroup("Move Solids"); moveSolids(getOrCreateStructure()); app.endUndoGroup(); };
        colorLayersBtn.onClick=function(){ colorLayersByType(); };
        deleteFoldersBtn.onClick=function(){ app.beginUndoGroup("Delete Empty Folders"); deleteEmptyFoldersRecursive(app.project.rootFolder); app.endUndoGroup(); };

        // JUST DO IT! — single pass, deterministic, no renaming
        justDoItButton.onClick = function(){
            app.beginUndoGroup("JUST DO IT!");

            var S = buildFolderStructure();

            // Order is deterministic:
            // 1) Group solids, then comps, then footage types
            moveSolids(S);
            moveComps(S);
            movePSDs(S);
            moveVectors(S);
            moveImages(S);
            moveEXRSequences(S);   // special bucket
            moveFootages(S);       // excludes EXR
            moveAudio(S);

            // Tidy up
            deleteEmptyFoldersRecursive(app.project.rootFolder);

            app.endUndoGroup();
        };

        myPanel.layout.layout(true);
        return myPanel;
    }

    var myScriptPal = myScript_buildUI(thisObj);
    if (myScriptPal != null && myScriptPal instanceof Window){
        myScriptPal.center();
        myScriptPal.show();
    }
}
myScript(this);
}
