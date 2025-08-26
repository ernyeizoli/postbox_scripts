// PBV Delivery 3.2 — _REPLACEABLE_EXR, Color Layers (A/B), RENAME (Adjustment -> FX names, Null -> Parent of ...)
// JUST DO IT! now also runs RENAME across all comps at the end.
{
    function myScript(thisObj){
        function myScript_buildUI(thisObj){
            var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette", "PBV Delivery 3.2", undefined, {resizeable:true});
            var justDoItButton = myPanel.add("button",[10,10,180,30], "JUST DO IT!");
            var divider = myPanel.add("panel", [10, 10, 180, 15]);
            divider.graphics.backgroundColor = divider.graphics.newBrush (divider.graphics.BrushType.SOLID_COLOR, [1, 1, 0], 1);

            var myButton      = myPanel.add("button",[10,10,180,30], "Folder Structure");
            var movecomps     = myPanel.add("button",[10,10,180,30], "Move Comps");
            var moveAi        = myPanel.add("button",[10,10,180,30], "Move Vector files");
            var movepng       = myPanel.add("button",[10,10,180,30], "Move Images");
            var movepsd       = myPanel.add("button",[10,10,180,30], "Move PSD files");
            var moveplates    = myPanel.add("button",[10,10,180,30], "Move Footages");
            var movesound     = myPanel.add("button",[10,10,180,30], "Move Sound");
            var movesolids    = myPanel.add("button",[10,10,180,30], "Move Solids");
            var colorActive   = myPanel.add("button",[10,10,180,30], "Color Layers (Active Comp)");
            var colorAll      = myPanel.add("button",[10,10,180,30], "Color Layers (All Comps)");
            var renameAdjBtn  = myPanel.add("button",[10,10,180,30], "RENAME (Adjustment/Null)");
            var deletefolders = myPanel.add("button",[10,10,180,30], "Delete Empty Folders");

            var label = myPanel.add("statictext", [28, 0, 150, 30], "Postbox Delivery - 2025");
            label.graphics.font = ScriptUI.newFont("Arial-BoldMT", "BOLD", 16);
            label.graphics.foregroundColor = label.graphics.newPen(label.graphics.PenType.SOLID_COLOR, [1, 1, 0], 1);
            label.alignment = "center";
            movesolids.graphics.foregroundColor = label.graphics.newPen(label.graphics.PenType.SOLID_COLOR, [1, 1, 0], 1);

            // ---------- helpers ----------
            function getExt(name){
                var i = name.lastIndexOf(".");
                return (i>=0) ? name.substring(i+1).toLowerCase() : "";
            }
            function isEXRSequence(footageItem){
                try {
                    if (!(footageItem instanceof FootageItem)) return false;
                    if (getExt(footageItem.name) !== "exr") return false;
                    return (footageItem.mainSource && footageItem.mainSource.isStill === false);
                } catch(e){ return false; }
            }
            function isEXRStill(footageItem){
                try {
                    if (!(footageItem instanceof FootageItem)) return false;
                    if (getExt(footageItem.name) !== "exr") return false;
                    return (footageItem.mainSource && footageItem.mainSource.isStill === true);
                } catch(e){ return false; }
            }
            function findOrCreateFolder(parentFolder, name){
                for (var j=1; j<=parentFolder.numItems; j++){
                    var it = parentFolder.item(j);
                    if (it instanceof FolderItem && it.name === name) return it;
                }
                return parentFolder.items.addFolder(name);
            }
            function getOrCreateStructure(){
                var root = app.project.rootFolder;
                var ASSETS = findOrCreateFolder(root, "_ASSETS");
                var REPL_EXR = findOrCreateFolder(root, "_REPLACEABLE_EXR"); // next to _ASSETS

                var AUDIO   = findOrCreateFolder(ASSETS, "AUDIO");
                var COMPS   = findOrCreateFolder(ASSETS, "COMPS");
                var ELEMENTS= findOrCreateFolder(ASSETS, "ELEMENTS");
                var FOOTAGE = findOrCreateFolder(ASSETS, "FOOTAGE");
                var SOLIDS  = findOrCreateFolder(ASSETS, "SOLIDS");

                var AI      = findOrCreateFolder(ELEMENTS, "AI");
                var IMG     = findOrCreateFolder(ELEMENTS, "IMG");
                var PS      = findOrCreateFolder(ELEMENTS, "PS");

                return {root:root, ASSETS:ASSETS, REPL_EXR:REPL_EXR, AUDIO:AUDIO, COMPS:COMPS, ELEMENTS:ELEMENTS, FOOTAGE:FOOTAGE, SOLIDS:SOLIDS, AI:AI, IMG:IMG, PS:PS};
            }

            // ---------- Folder Structure ----------
            myButton.helpTip = "Create the right Directories (adds _REPLACEABLE_EXR next to _ASSETS)";
            myButton.onClick = function() { getOrCreateStructure(); };

            // ---------- Move Comps ----------
            movecomps.helpTip = "Move all the compositions to _ASSETS/COMPS (active comp stays in root).";
            movecomps.onClick = function() {
                var S = getOrCreateStructure();
                var compFolder = S.COMPS;
                var rootFolder = S.root;
                var activeComp = app.project.activeItem;

                var comps = [];
                for (var i = 1; i <= app.project.numItems; i++) {
                    if (app.project.item(i) instanceof CompItem) comps.push(app.project.item(i));
                }
                for (var k = 0; k < comps.length; k++) {
                    if (activeComp && comps[k] === activeComp){
                        activeComp.parentFolder = rootFolder; // keep in root
                    } else {
                        comps[k].parentFolder = compFolder;
                    }
                }
            };

            // ---------- Move AI/EPS/PDF/SVG ----------
            moveAi.helpTip = "Move all the Illustrator/Vector files to _ASSETS/ELEMENTS/AI";
            moveAi.onClick = function (){
                var S = getOrCreateStructure();
                var aiFolder = S.AI; if (!aiFolder) return;
                var ai = [];
                for(var i = 1; i <= app.project.numItems; i++){
                    var it = app.project.item(i);
                    var ext = getExt(it.name);
                    if ((it instanceof FootageItem) && (ext==="ai" || ext==="eps" || ext==="pdf" || ext==="svg")){
                        ai.push(it);
                    }
                }
                for (var j = 0; j < ai.length; j++) ai[j].parentFolder = aiFolder;
            };

            // ---------- Move Images (incl. EXR stills) ----------
            movepng.helpTip = "Move images to _ASSETS/ELEMENTS/IMG (png/jpg/jpeg/tif/tiff/bmp/gif/webp + EXR stills)";
            movepng.onClick = function (){
                var S = getOrCreateStructure();
                var pngFolder = S.IMG; if (!pngFolder) return;
                var items = [];
                for(var i = 1; i <= app.project.numItems; i++){
                    var it = app.project.item(i);
                    if (!(it instanceof FootageItem)) continue;
                    var ext = getExt(it.name);
                    var isImg = (ext==="png" || ext==="jpg" || ext==="jpeg" || ext==="tif" || ext==="tiff" || ext==="bmp" || ext==="gif" || ext==="webp");
                    if (isImg || isEXRStill(it)){ items.push(it); }
                }
                for (var j = 0; j < items.length; j++) items[j].parentFolder = pngFolder;
            };

            // ---------- Move PSD/PSB ----------
            movepsd.helpTip = "Move all the PSD/PSB files to _ASSETS/ELEMENTS/PS";
            movepsd.onClick = function (){
                var S = getOrCreateStructure();
                var psdFolder = S.PS; if (!psdFolder) return;
                var psds = [];
                for(var i = 1; i <= app.project.numItems; i++){
                    var it = app.project.item(i);
                    var ext = getExt(it.name);
                    if ((it instanceof FootageItem) && (ext === "psd" || ext === "psb")) psds.push(it);
                }
                for (var j = 0; j < psds.length; j++) psds[j].parentFolder = psdFolder;
            };

            // ---------- Move Footage (EXR seq excluded; they go to _REPLACEABLE_EXR) ----------
            moveplates.helpTip = "Move video footages to _ASSETS/FOOTAGE (EXR sequences go to _REPLACEABLE_EXR)";
            moveplates.onClick = function (){
                var S = getOrCreateStructure();
                var platesFolder = S.FOOTAGE; if (!platesFolder) return;
                var exrFolder = S.REPL_EXR;

                var vids = [], exrSeq = [];
                for(var i = 1; i <= app.project.numItems; i++){
                    var it = app.project.item(i);
                    if (!(it instanceof FootageItem)) continue;
                    var ext = getExt(it.name);

                    if (ext === "exr"){
                        if (isEXRSequence(it)) exrSeq.push(it);
                        continue; // EXR stillt a Move Images kezeli
                    }

                    if (ext==="mov" || ext==="mp4" || ext==="mxf" || ext==="avi" || ext==="mkv" || ext==="r3d" || ext==="ari" || ext==="mts" || ext==="m2ts" || ext==="webm"){
                        vids.push(it);
                    }
                }
                for (var v=0; v<vids.length; v++) vids[v].parentFolder = platesFolder;
                for (var e=0; e<exrSeq.length; e++) exrSeq[e].parentFolder = exrFolder;
            };

            // ---------- Move Sound ----------
            movesound.helpTip = "Move all the Sound files to _ASSETS/AUDIO";
            movesound.onClick = function (){
                var S = getOrCreateStructure();
                var soundFolder = S.AUDIO; if (!soundFolder) return;
                var sounds = [];
                for(var i = 1; i <= app.project.numItems; i++){
                    var it = app.project.item(i);
                    var ext = getExt(it.name);
                    if ((it instanceof FootageItem) && (ext==="wav" || ext==="aif" || ext==="aiff" || ext==="mp3" || ext==="ogg" || ext==="flac")){
                        sounds.push(it);
                    }
                }
                for (var j = 0; j < sounds.length; j++) sounds[j].parentFolder = soundFolder;
            };

            // ---------- Move Solids (from any 'Solids' folder) ----------
            movesolids.helpTip = "Move all items from any 'Solids' folder into _ASSETS/SOLIDS";
            movesolids.onClick = function () {
                var S = getOrCreateStructure();
                var solidsTarget = S.SOLIDS;

                function findFoldersByName(folder, name, resultArray) {
                    for (var i = 1; i <= folder.numItems; i++) {
                        if (folder.item(i) instanceof FolderItem && folder.item(i).name === name) {
                            resultArray.push(folder.item(i));
                        } else if (folder.item(i) instanceof FolderItem) {
                            findFoldersByName(folder.item(i), name, resultArray);
                        }
                    }
                    return resultArray;
                }

                var solidsFolders = findFoldersByName(app.project.rootFolder, "Solids", []);
                for (var l = 0; l < solidsFolders.length; l++) {
                    var currentSolidsFolder = solidsFolders[l];
                    for (var m = currentSolidsFolder.numItems; m >= 1; m--) {
                        try { currentSolidsFolder.item(m).parentFolder = solidsTarget; } catch(e){}
                    }
                }
            };

            // ---------- COLOR LABELS ----------
            var LABELS = {
                YELLOW: 2,  ORANGE: 11, BLUE: 8, RED: 1, CYAN: 14, PEACH: 6, FUCHSIA: 13, PURPLE: 10
            };

            function colorizeComp(comp){
                if (!(comp && comp instanceof CompItem)) return;
                for (var i=1; i<=comp.numLayers; i++){
                    var L = comp.layer(i);

                    var isPrecompLayer    = (L instanceof AVLayer) && (L.source instanceof CompItem);
                    var isFootageLayer    = (L instanceof AVLayer) && (L.source instanceof FootageItem);
                    var isTextLayer       = (L instanceof TextLayer);
                    var isShapeLayer      = (L instanceof ShapeLayer);
                    var isAdjustmentLayer = (L.adjustmentLayer === true);
                    var isSolidLayer      = (L instanceof AVLayer) && isFootageLayer && (function(){
                        try { return (L.source.mainSource instanceof SolidSource); } catch(e){ return false; }
                    })();
                    var isNullLayer       = (L instanceof AVLayer) && (function(){
                        try { return L.nullLayer === true; } catch(e){ return false; }
                    })();
                    var isAudioLayer      = (L instanceof AVLayer) && (function(){
                        try { return (L.hasAudio === true && L.hasVideo === false); } catch(e){ return false; }
                    })();
                    var isCameraLayer     = (L instanceof CameraLayer);

                    if (isTextLayer){ L.label = LABELS.YELLOW;
                    } else if (isAdjustmentLayer || isSolidLayer){ L.label = LABELS.ORANGE;
                    } else if (isFootageLayer){ L.label = LABELS.BLUE;
                    } else if (isNullLayer){ L.label = LABELS.RED;
                    } else if (isAudioLayer){ L.label = LABELS.CYAN;
                    } else if (isCameraLayer){ L.label = LABELS.PEACH;
                    } else if (isShapeLayer){ L.label = LABELS.FUCHSIA;
                    } else if (isPrecompLayer){ L.label = LABELS.PURPLE; }
                }
            }

            colorActive.helpTip = "Színezi az AKTÍV kompozíció rétegeit a megadott szabályok szerint.";
            colorActive.onClick = function(){
                var comp = app.project.activeItem;
                if (!(comp && comp instanceof CompItem)) return alert("No active composition found.");
                app.beginUndoGroup("Color Layers (Active Comp)");
                colorizeComp(comp);
                app.endUndoGroup();
            };

            colorAll.helpTip = "Színezi a TELJES PROJEKT összes kompozíciójának rétegeit.";
            colorAll.onClick = function(){
                app.beginUndoGroup("Color Layers (All Comps)");
                for (var i=1; i<=app.project.numItems; i++){
                    var it = app.project.item(i);
                    if (it instanceof CompItem) colorizeComp(it);
                }
                app.endUndoGroup();
            };

            // ---------- RENAME (Adjustment -> FX names, Null -> Parent of: child names) ----------
            function getEffectNamesFromLayer(layer){
                var names = [];
                try{
                    var fx = layer.property("Effects");
                    if (!fx) return names;
                    for (var j = 1; j <= fx.numProperties; j++){
                        var eff = fx.property(j);
                        if (eff && eff.name) names.push(eff.name);
                    }
                }catch(e){}
                return names;
            }
            function renameAdjustmentLayersInComp(comp){
                if (!(comp && comp instanceof CompItem)) return;
                for (var i = 1; i <= comp.numLayers; i++){
                    var L = comp.layer(i);
                    if (L && L.adjustmentLayer === true){
                        var fxNames = getEffectNamesFromLayer(L);
                        if (fxNames.length > 0){ L.name = fxNames.join(", "); }
                    }
                }
            }
            function renameNullParentsInComp(comp){
                if (!(comp && comp instanceof CompItem)) return;
                var nulls = [];
                for (var i=1; i<=comp.numLayers; i++){
                    var L = comp.layer(i);
                    try { if (L instanceof AVLayer && L.nullLayer === true){ nulls.push(L); } } catch(e){}
                }
                for (var n=0; n<nulls.length; n++){
                    var N = nulls[n], childNames = [];
                    for (var k=1; k<=comp.numLayers; k++){
                        var C = comp.layer(k);
                        try{ if (C !== N && C.parent === N){ childNames.push(C.name); } }catch(e){}
                    }
                    if (childNames.length > 0){ N.name = "Parent of: " + childNames.join(", "); }
                }
            }
            function renameInAllComps(){
                for (var i=1; i<=app.project.numItems; i++){
                    var it = app.project.item(i);
                    if (it instanceof CompItem){
                        renameAdjustmentLayersInComp(it);
                        renameNullParentsInComp(it);
                    }
                }
            }

            renameAdjBtn.helpTip = "AKTÍV kompozíció: Adjustment → FX names; Null → Parent of: <children>";
            renameAdjBtn.onClick = function(){
                var comp = app.project.activeItem;
                if (!(comp && comp instanceof CompItem)) return alert("No active composition found.");
                app.beginUndoGroup("Rename: Adjustment + Null (Active Comp)");
                renameAdjustmentLayersInComp(comp);
                renameNullParentsInComp(comp);
                app.endUndoGroup();
            };

            // ---------- Delete Empty Folders (eredeti viselkedés) ----------
            deletefolders.helpTip = "Delete all empty folders";
            deletefolders.onClick = function removeFolders(theFolder) {
                var del = [];
                for (var i = 1; i<=app.project.numItems; i++) {
                    if (app.project.item(i) instanceof FolderItem && app.project.item(i).numItems==0)
                        del.push(app.project.item(i));
                }
                for (var k = 0; k < del.length; k++) del[k].remove();
            };

            // ---------- JUST DO IT (temp-átnevezős eredeti logika + végén RENAME ALL COMPS) ----------
            justDoItButton.onClick = function() {
                // Pre-funkció: az összes mappa átnevezése "temp"-re (eredeti viselkedés)
                for (var i = 1; i <= app.project.numItems; i++) {
                    var item = app.project.item(i);
                    if (item instanceof FolderItem) { item.name = "temp"; }
                }

                // 20x kör, eredeti sorrendben
                for (var r = 0; r < 20; r++) {
                    myButton.onClick();
                    movecomps.onClick();
                    moveAi.onClick();
                    movepng.onClick();
                    movepsd.onClick();
                    moveplates.onClick(); // EXR seq -> _REPLACEABLE_EXR, videók -> FOOTAGE
                    movesound.onClick();
                    movesolids.onClick();
                    colorAll.onClick();

                    // Temp mappa tartalmának áthelyezése a SOLIDS mappába
                    var tempFolder = null, solidsFolder = null;
                    for (var j = 1; j <= app.project.numItems; j++) {
                        if ((app.project.item(j) instanceof FolderItem) && (app.project.item(j).name == "temp")) { tempFolder = app.project.item(j); break; }
                    }
                    for (var k = 1; k <= app.project.numItems; k++) {
                        if ((app.project.item(k) instanceof FolderItem) && (app.project.item(k).name == "SOLIDS")) { solidsFolder = app.project.item(k); break; }
                    }
                    if (tempFolder && solidsFolder) {
                        for (var l = tempFolder.numItems; l >= 1; l--) {
                            tempFolder.item(l).parentFolder = solidsFolder;
                        }
                    }
                    deletefolders.onClick();
                }

                // ÚJ: RENAME minden kompozíción (Adjustment + Null)
                app.beginUndoGroup("JUST DO IT! — Rename All Comps");
                renameInAllComps();
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
