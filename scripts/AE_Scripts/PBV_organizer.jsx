// --- The Ultimate EXR Organizer ---
// v3.1, September 2025 (select, ls bugfix)
//
// This script provides a panel with three tools to streamline EXR workflows:
// 1. FLATTEN: Replaces precomps with their source footage, copying all transforms and effects.
// 2. ORGANIZE: Intelligently sorts and sets up EXR passes, adds adjustment layers, and applies effects.
// 3. DELETE UNUSED: Safely removes hidden layers that are not part of any parent/matte relationship.
//

(function organizeEXRLayers(thisObj) {
    var scriptName = "Ultimate EXR Organizer";

    // Instructions: Find the exact name of your effect in the After Effects "Effects & Presets" panel
    // and type it inside the quotes. If you don't want to add a specific effect,
    // just leave the quotes empty, like "".
    //
    var effectName_Colorista = "Colorista V";
    var effectName_OCIO = "OCIO Display Transform";
    var effectName_Exposure = "Exposure";
    // --- END CONFIGURATION ---


    // --- HELPER FUNCTIONS ---
    // Safely checks if a layer object is in an array.
    function containsLayer(layerArray, layer) {
        if (!layer) return false;
        for (var i = 0; i < layerArray.length; i++) {
            if (layerArray[i] && layerArray[i].index === layer.index) {
                return true;
            }
        }
        return false;
    }

    // Finds the composition named "assemble" for renaming.
    function findAssembleComp(project, selected) {
        if (selected && selected instanceof CompItem && selected.name.toLowerCase().indexOf("assemble") !== -1) {
            return selected;
        }
        for (var i = 1; i <= project.numItems; i++) {
            var item = project.item(i);
            if (item instanceof CompItem && item.name.toLowerCase().indexOf("assemble") !== -1) {
                return item;
            }
        }
        return null;
    }

    // Renames the "assemble" comp and moves it to the root folder.
    function renameAndMoveAssembleComp() {
        var proj = app.project;
        if (!proj) return;
        var selectedItem = proj.selection.length > 0 ? proj.selection[0] : null;
        var assembleComp = findAssembleComp(proj, selectedItem);
        if (!assembleComp) return;

        var nameBefore = assembleComp.name;
        var mpIndex = nameBefore.indexOf("MP_");
        if (mpIndex !== -1) {
            var newName = nameBefore.substring(0, mpIndex) + "COMP_";
            if (newName.length > 0) {
                assembleComp.name = newName;
            }
        }
        assembleComp.parentFolder = proj.rootFolder;
    }


    // --- UI CREATION ---
    function createUI(thisObj) {
        var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette", scriptName, undefined, { resizeable: true });
        if (myPanel === null) return;

        var res = "group { orientation:'column', alignment:['fill', 'top'], alignChildren:['fill', 'top'], " +
            "flattenBtn: Button { text:'FLATTEN SELECTED COMP' }," +
            "organizeBtn: Button { text:'ORGANIZE LAYERS' }," +
            "deleteBtn: Button { text:'DELETE UNUSED' }," +
            "launchScannerBtn: Button { text:'RUN FOOTAGE VERSION SCANNER' }," + // <-- Add this line
            "}";
        myPanel.grp = myPanel.add(res);

        // --- FLATTEN BUTTON ---
        myPanel.grp.flattenBtn.onClick = function() {
            var comp = app.project.activeItem;
            if (!(comp && comp instanceof CompItem)) { return alert("No active composition selected."); }
            if (comp && comp instanceof CompItem && comp.selectedLayers.length > 0) {
                var selectedLayers = comp.selectedLayers; // Get the array of selected layers
                return alert("DESELECT ALL LAYERS AND TRY AGAIN! " + selectedLayers.length + " layers selected.");        
            }
            app.beginUndoGroup("Flatten Precomps with Effects");
            var replacedCount = 0;
            var originalDisplayStart = comp.displayStartTime;
            var frameDuration = comp.frameDuration;
            for (var j = comp.numLayers; j >= 1; j--) {
                var layer = comp.layer(j);
                if (!layer.source || !(layer.source instanceof CompItem)) continue;
                var sourceComp = layer.source;
                if (sourceComp.numLayers >= 1) {
                    var innerLayer = sourceComp.layer(1);
                    innerLayer.copyToComp(comp);
                    var newLayer = comp.layer(1);
                    newLayer.moveBefore(layer);
                    newLayer.startTime = layer.startTime; newLayer.inPoint = layer.inPoint; newLayer.outPoint = layer.outPoint;
                    newLayer.blendingMode = layer.blendingMode; newLayer.name = sourceComp.name.replace(/ source$/i, "");
                    newLayer.transform.position.setValue(layer.transform.position.value); newLayer.transform.scale.setValue(layer.transform.scale.value);
                    newLayer.transform.anchorPoint.setValue(layer.transform.anchorPoint.value); newLayer.transform.rotation.setValue(layer.transform.rotation.value);
                    newLayer.transform.opacity.setValue(layer.transform.opacity.value);
                    if (layer.property("Effects")) {
                        for (var e = 1; e <= layer.property("Effects").numProperties; e++) {
                            var effectToCopy = layer.property("Effects").property(e);
                            try {
                                var newEffect = newLayer.property("Effects").addProperty(effectToCopy.matchName);
                                for (var p = 1; p <= effectToCopy.numProperties; p++) {
                                    if (newEffect.property(p).canSetValue) { newEffect.property(p).setValue(effectToCopy.property(p).value); }
                                }
                            } catch (err) { /* Ignore if effect can't be copied */ }
                        }
                    }
                    layer.remove();
                    replacedCount++;
                }
            }
            var earliestLayerStart = null;
            for (var k = 1; k <= comp.numLayers; k++) {
                var currentLayer = comp.layer(k);
                if (!currentLayer) { continue; }
                var layerStart = currentLayer.inPoint;
                if (earliestLayerStart === null || layerStart < earliestLayerStart) {
                    earliestLayerStart = layerStart;
                }
            }
            var startChangeLog = "Comp start unchanged.";
            var newDisplayStart = originalDisplayStart;
            if (earliestLayerStart !== null) {
                var snappedStart = Math.round(earliestLayerStart / frameDuration) * frameDuration;
                comp.displayStartTime = snappedStart; // Align comp start with earliest layer
                comp.time = snappedStart; // Keep playhead parked on the new start frame
                try {
                    var compViewer = comp.openInViewer(); // Refresh the active viewer to reflect the new start frame
                    if (compViewer && compViewer.type === ViewerType.VIEWER_COMPOSITION) {
                        compViewer.time = snappedStart;
                    }
                } catch (viewerErr) {
                    // Safe fail if viewer update is unavailable
                }
                newDisplayStart = comp.displayStartTime;
                var originalFrame = Math.round(originalDisplayStart / frameDuration);
                var newFrame = Math.round(newDisplayStart / frameDuration);
                startChangeLog = "Comp start changed from frame " + originalFrame + " (" + originalDisplayStart.toFixed(3) + "s) to frame " + newFrame + " (" + newDisplayStart.toFixed(3) + "s).";
            }
            app.endUndoGroup();
            var message = "✅ Flatten complete.\n\nReplaced layers: " + replacedCount + "\n" + startChangeLog;
            alert(message);
            $.writeln("[Ultimate EXR Organizer] " + startChangeLog);
        };

        // --- ORGANIZE BUTTON (Fully Optimized) ---
        myPanel.grp.organizeBtn.onClick = function() {
            var comp = app.project.activeItem;
            if (!(comp && comp instanceof CompItem)) { return alert("No active composition found."); }
            
            app.beginUndoGroup("Organize Layers");
            try {
                // Pass 1: Identify and collect layers
                var lsLayers = [], cryptomatteLayer = null, extraTexLayer = null, specialLayerIndices = {};
                for (var i = comp.numLayers; i >= 1; i--) {
                    var layer = comp.layer(i);
                    if (layer.name === "ProEXR File Description") { layer.remove(); continue; }
                    if (!layer.source) continue;
                    var isSpecial = false, name = layer.name, sourceName = layer.source.name;
                    if (name.indexOf("LS_") === 0 || sourceName.indexOf("LS_") === 0) {
                        lsLayers.push(layer); 
                        layer.label = 2; /*Yellow*/ 
                        layer.blendingMode = BlendingMode.ADD; 
                        isSpecial = true;
                        layer.enabled = true;
                    }
                    if (!cryptomatteLayer && layer.property("Effects")) {
                        for (var j = 1; j <= layer.property("Effects").numProperties; j++) {
                            if (layer.property("Effects").property(j).name.toLowerCase().indexOf("cryptomatte") !== -1) {
                                cryptomatteLayer = layer;
                                layer.label = 10; /*Purple*/
                                layer.enabled = false;
                                isSpecial = true;
                            }
                        }
                    }
                    if (!extraTexLayer && (name.toLowerCase().indexOf("extra tex") !== -1 || sourceName.toLowerCase().indexOf("extra tex") !== -1)) {
                        extraTexLayer = layer;
                        layer.label = 16; /*Dark Green*/
                        layer.blendingMode = BlendingMode.MULTIPLY;
                        layer.enabled = false;
                        isSpecial = true;
                    }
                    if (isSpecial) { 
                        specialLayerIndices[layer.index] = true;
                        layer.enabled = true; // Ensure special layers are enabled
                    }
                    else {
                        layer.enabled = false; // Disable non-special layers immediately
                    }
                }

                //alert("Found " + lsLayers.length + " Light Select layers.\n")

                // Pass 2: Disable non-special layers using a fast lookup
                //for (var k = 1; k <= comp.numLayers; k++) {
                //    var l = comp.layer(k);
                //    if (!specialLayerIndices[l.index]) l.enabled = false;
                //}

                // Pass 3: Create Adjustment Layers if configured
                var coloristaLayer;
                if (effectName_Colorista && effectName_Colorista !== "") {
                    coloristaLayer = comp.layers.addSolid([1, 1, 1], "Colorista", comp.width, comp.height, comp.pixelAspect, comp.duration);
                    coloristaLayer.adjustmentLayer = true; coloristaLayer.label = 11; /*Pink*/
                    coloristaLayer.property("Effects").addProperty(effectName_Colorista);
                }
                var ocioLayer;
                if (effectName_OCIO && effectName_OCIO !== "") {
                    ocioLayer = comp.layers.addSolid([1, 1, 1], "OCIO", comp.width, comp.height, comp.pixelAspect, comp.duration);
                    ocioLayer.adjustmentLayer = true; ocioLayer.label = 11; 
                    ocioLayer.property("Effects").addProperty(effectName_OCIO);
                }

                // Pass 4: Sort and re-order layers efficiently to prevent freezing
                lsLayers.sort(function(a, b) { return a.name.localeCompare(b.name); });
                var lastMovedLayer = null;
                if (ocioLayer) { ocioLayer.moveToBeginning(); lastMovedLayer = ocioLayer; }
                if (coloristaLayer) { coloristaLayer.moveToBeginning(); if(lastMovedLayer) coloristaLayer.moveAfter(lastMovedLayer); lastMovedLayer = coloristaLayer; }
                if (extraTexLayer) { extraTexLayer.moveToBeginning(); if(lastMovedLayer) extraTexLayer.moveAfter(lastMovedLayer); lastMovedLayer = extraTexLayer; }
                if (cryptomatteLayer) { cryptomatteLayer.moveToBeginning(); if(lastMovedLayer) cryptomatteLayer.moveAfter(lastMovedLayer); lastMovedLayer = cryptomatteLayer; }
                for (var s = 0; s < lsLayers.length; s++) {
                    if (lastMovedLayer) lsLayers[s].moveAfter(lastMovedLayer); else lsLayers[s].moveToBeginning();
                    lastMovedLayer = lsLayers[s];
                }
                // Lock ocio layer to prevent accidental changes
                ocioLayer.locked = true;

                // Pass 5: Add Exposure effect if configured
                if (effectName_Exposure && effectName_Exposure !== "") {
                    for (var m = 0; m < lsLayers.length; m++) {
                        lsLayers[m].property("Effects").addProperty(effectName_Exposure);
                    }
                }
                
                // Pass 6: Rename and move assemble comp
                renameAndMoveAssembleComp();
                
                alert("✅ Organization complete.");

            } catch (e) {
                alert("An error occurred: " + e.toString() + "\n\nTip: Check the plugin names in the USER CONFIGURATION section at the top of the script. Make sure they exactly match the names in your Effects & Presets panel.");
            } finally {
                app.endUndoGroup();
            }
        };

        // --- DELETE UNUSED BUTTON ---
        myPanel.grp.deleteBtn.onClick = function() {
            var comp = app.project.activeItem;
            if (!(comp && comp instanceof CompItem)) { return alert("⚠️ No active composition."); }
            app.beginUndoGroup("Delete Hidden Layers");
            var protectedLayers = [];
            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i);
                if (layer.trackMatteType !== TrackMatteType.NO_TRACK_MATTE) {
                    if (layer.trackMatteLayer && !containsLayer(protectedLayers, layer.trackMatteLayer)) { protectedLayers.push(layer.trackMatteLayer); }
                    if (!containsLayer(protectedLayers, layer)) { protectedLayers.push(layer); }
                }
                if (layer.parent && !containsLayer(protectedLayers, layer)) {
                    var currentLayer = layer;
                    while(currentLayer.parent) {
                         if (!containsLayer(protectedLayers, currentLayer.parent)) protectedLayers.push(currentLayer.parent);
                         currentLayer = currentLayer.parent;
                    }
                }
                if (layer.expressionEnabled && !containsLayer(protectedLayers, layer)) { protectedLayers.push(layer); }
            }
            var deletedCount = 0;
            for (var i = comp.numLayers; i >= 1; i--) {
                var layer = comp.layer(i);
                if (!layer.enabled && !containsLayer(protectedLayers, layer)) {
                    layer.remove();
                    deletedCount++;
                }
            }
            app.endUndoGroup();
            alert("✅ Deletion complete.\n" + deletedCount + " unused hidden layers removed.");
        };

        // --- LAUNCH FOOTAGE VERSION SCANNER BUTTON ---
        myPanel.grp.launchScannerBtn.onClick = function() {
            // Get the file path of the currently running panel script
            var currentScriptFile = new File($.fileName);

            // Get the parent folder and then go one level up
            var targetFolder = currentScriptFile.parent.parent;

            // Construct the path to the scanner script
            var scannerScriptPath = targetFolder.fsName + "/FootageVersionScanner.jsx";

            // Create a File object for the scanner script
            var scannerScriptFile = new File(scannerScriptPath);

            // Check if the scanner script exists
            if (!scannerScriptFile.exists) {
                return alert("⚠️ Scanner script not found:\n" + scannerScriptPath);
            }

            // Execute the scanner script
            app.beginUndoGroup("Run Footage Version Scanner");
            try {
                // Load and run the scanner script
                $.evalFile(scannerScriptFile);
            } catch (e) {
                alert("Error running scanner script: " + e.toString());
            } finally {
                app.endUndoGroup();
            }
        };

        myPanel.layout.layout(true);
        return myPanel;
    }

    // --- SCRIPT EXECUTION ---
    var myScriptPal = createUI(thisObj);
    if (myScriptPal instanceof Window) {
        myScriptPal.center();
        myScriptPal.show();
    }
})(this);