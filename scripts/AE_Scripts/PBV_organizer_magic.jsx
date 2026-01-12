// --- PBV One-Click EXR Organizer ---
// v4.0, January 2026
//
// One button: Select an EXR sequence, and it automatically:
// 1. Imports the footage
// 2. Creates a composition from it
// 3. Flattens precomps
// 4. Organizes layers
// 5. Deletes unused layers
//

(function organizeEXROneClick(thisObj) {
    var scriptName = "PBV One-Click EXR Organizer";

    // --- USER CONFIGURATION ---
    var effectName_Colorista = "Colorista V";
    var effectName_OCIO = "OCIO Display Transform";
    var effectName_Exposure = "Exposure";
    // --- END CONFIGURATION ---


    // --- HELPER FUNCTIONS ---
    function containsLayer(layerArray, layer) {
        if (!layer) return false;
        for (var i = 0; i < layerArray.length; i++) {
            if (layerArray[i] && layerArray[i].index === layer.index) {
                return true;
            }
        }
        return false;
    }

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

    // --- FLATTEN FUNCTION ---
    function flattenComp(comp) {
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
                newLayer.startTime = layer.startTime;
                newLayer.inPoint = layer.inPoint;
                newLayer.outPoint = layer.outPoint;
                newLayer.blendingMode = layer.blendingMode;
                newLayer.name = sourceComp.name.replace(/ source$/i, "");
                newLayer.transform.position.setValue(layer.transform.position.value);
                newLayer.transform.scale.setValue(layer.transform.scale.value);
                newLayer.transform.anchorPoint.setValue(layer.transform.anchorPoint.value);
                newLayer.transform.rotation.setValue(layer.transform.rotation.value);
                newLayer.transform.opacity.setValue(layer.transform.opacity.value);
                if (layer.property("Effects")) {
                    for (var e = 1; e <= layer.property("Effects").numProperties; e++) {
                        var effectToCopy = layer.property("Effects").property(e);
                        try {
                            var newEffect = newLayer.property("Effects").addProperty(effectToCopy.matchName);
                            for (var p = 1; p <= effectToCopy.numProperties; p++) {
                                if (newEffect.property(p).canSetValue) {
                                    newEffect.property(p).setValue(effectToCopy.property(p).value);
                                }
                            }
                        } catch (err) { /* Ignore if effect can't be copied */ }
                    }
                }
                layer.remove();
                replacedCount++;
            }
        }

        function toFrameIndex(timeValue) {
            return Math.round(timeValue / frameDuration);
        }

        function toTimeValue(frameIndex) {
            return frameIndex * frameDuration + 0.001;
        }

        function extractFrameFromName(name) {
            if (!name) return null;
            var rangeMatch = name.match(/\[(\d+)[^\]]*\]/);
            if (rangeMatch && rangeMatch[1]) return parseInt(rangeMatch[1], 10);
            var trailingMatch = name.match(/\.\D*?(\d{3,})/);
            return trailingMatch && trailingMatch[1] ? parseInt(trailingMatch[1], 10) : null;
        }

        function detectPlateStartFrame() {
            for (var idx = 1; idx <= comp.numLayers; idx++) {
                var lyr = comp.layer(idx);
                if (!lyr || !lyr.source) continue;
                var sourceName = lyr.source.name;
                var layerName = lyr.name;
                var fileName = (lyr.source.mainSource && lyr.source.mainSource.file) ? lyr.source.mainSource.file.name : null;
                var matchFrame = extractFrameFromName(sourceName) || extractFrameFromName(layerName) || extractFrameFromName(fileName);
                if (matchFrame !== null) return matchFrame;
            }
            return null;
        }

        var earliestLayerStartFrame = null;
        for (var k = 1; k <= comp.numLayers; k++) {
            var currentLayer = comp.layer(k);
            if (!currentLayer) continue;
            var layerStartFrame = toFrameIndex(currentLayer.inPoint);
            if (earliestLayerStartFrame === null || layerStartFrame < earliestLayerStartFrame) {
                earliestLayerStartFrame = layerStartFrame;
            }
        }

        var detectedStartFrame = detectPlateStartFrame();
        var targetStartFrame = null;

        if (detectedStartFrame !== null) {
            targetStartFrame = detectedStartFrame;
        } else {
            var dialogDefault = (earliestLayerStartFrame !== null) ? earliestLayerStartFrame : 1001;
            var manualFrameInput = prompt("No frame number was detected in your EXR name. Enter the first frame for this comp:", dialogDefault.toString(), scriptName);
            if (manualFrameInput === null) {
                targetStartFrame = dialogDefault;
            } else {
                var manualFrame = parseInt(manualFrameInput, 10);
                targetStartFrame = isNaN(manualFrame) ? dialogDefault : manualFrame;
            }
        }

        if (targetStartFrame !== null) {
            var snappedStart = toTimeValue(targetStartFrame);
            comp.displayStartTime = snappedStart;
            comp.time = snappedStart;
        }

        return replacedCount;
    }

    // --- ORGANIZE FUNCTION ---
    function organizeLayers(comp) {
        var lsLayers = [], cryptomatteLayer = null, extraTexLayer = null, specialLayerIndices = {};

        for (var i = comp.numLayers; i >= 1; i--) {
            var layer = comp.layer(i);
            if (layer.name === "ProEXR File Description") { layer.remove(); continue; }
            if (!layer.source) continue;
            var isSpecial = false, name = layer.name, sourceName = layer.source.name;

            if (name.indexOf("LS_") === 0 || sourceName.indexOf("LS_") === 0) {
                lsLayers.push(layer);
                layer.label = 2; // Yellow
                layer.blendingMode = BlendingMode.ADD;
                isSpecial = true;
                layer.enabled = true;
            }

            if (!cryptomatteLayer && layer.property("Effects")) {
                for (var j = 1; j <= layer.property("Effects").numProperties; j++) {
                    if (layer.property("Effects").property(j).name.toLowerCase().indexOf("cryptomatte") !== -1) {
                        cryptomatteLayer = layer;
                        layer.label = 10; // Purple
                        layer.enabled = false;
                        isSpecial = true;
                    }
                }
            }

            if (!extraTexLayer && (name.toLowerCase().indexOf("extra tex") !== -1 || sourceName.toLowerCase().indexOf("extra tex") !== -1)) {
                extraTexLayer = layer;
                layer.label = 16; // Dark Green
                layer.blendingMode = BlendingMode.MULTIPLY;
                layer.enabled = false;
                isSpecial = true;
            }

            if (isSpecial) {
                specialLayerIndices[layer.index] = true;
                layer.enabled = true;
            } else {
                layer.enabled = false;
            }
        }

        // Create Adjustment Layers
        var coloristaLayer;
        if (effectName_Colorista && effectName_Colorista !== "") {
            coloristaLayer = comp.layers.addSolid([1, 1, 1], "Colorista", comp.width, comp.height, comp.pixelAspect, comp.duration);
            coloristaLayer.adjustmentLayer = true;
            coloristaLayer.label = 11; // Pink
            coloristaLayer.property("Effects").addProperty(effectName_Colorista);
        }

        var ocioLayer;
        if (effectName_OCIO && effectName_OCIO !== "") {
            ocioLayer = comp.layers.addSolid([1, 1, 1], "OCIO", comp.width, comp.height, comp.pixelAspect, comp.duration);
            ocioLayer.adjustmentLayer = true;
            ocioLayer.label = 11;
            ocioLayer.property("Effects").addProperty(effectName_OCIO);
        }

        // Sort and re-order layers
        lsLayers.sort(function (a, b) { return a.name.localeCompare(b.name); });
        var lastMovedLayer = null;

        if (ocioLayer) { ocioLayer.moveToBeginning(); lastMovedLayer = ocioLayer; }
        if (coloristaLayer) { coloristaLayer.moveToBeginning(); if (lastMovedLayer) coloristaLayer.moveAfter(lastMovedLayer); lastMovedLayer = coloristaLayer; }
        if (extraTexLayer) { extraTexLayer.moveToBeginning(); if (lastMovedLayer) extraTexLayer.moveAfter(lastMovedLayer); lastMovedLayer = extraTexLayer; }
        if (cryptomatteLayer) { cryptomatteLayer.moveToBeginning(); if (lastMovedLayer) cryptomatteLayer.moveAfter(lastMovedLayer); lastMovedLayer = cryptomatteLayer; }

        for (var s = 0; s < lsLayers.length; s++) {
            if (lastMovedLayer) lsLayers[s].moveAfter(lastMovedLayer);
            else lsLayers[s].moveToBeginning();
            lastMovedLayer = lsLayers[s];
        }

        if (ocioLayer) ocioLayer.locked = true;

        // Add Exposure effect
        if (effectName_Exposure && effectName_Exposure !== "") {
            for (var m = 0; m < lsLayers.length; m++) {
                lsLayers[m].property("Effects").addProperty(effectName_Exposure);
            }
        }

        renameAndMoveAssembleComp();
        return lsLayers.length;
    }

    // --- DELETE UNUSED FUNCTION ---
    function deleteUnusedLayers(comp) {
        var protectedLayers = [];

        for (var i = 1; i <= comp.numLayers; i++) {
            var layer = comp.layer(i);
            if (layer.trackMatteType !== TrackMatteType.NO_TRACK_MATTE) {
                if (layer.trackMatteLayer && !containsLayer(protectedLayers, layer.trackMatteLayer)) {
                    protectedLayers.push(layer.trackMatteLayer);
                }
                if (!containsLayer(protectedLayers, layer)) {
                    protectedLayers.push(layer);
                }
            }
            if (layer.parent && !containsLayer(protectedLayers, layer)) {
                var currentLayer = layer;
                while (currentLayer.parent) {
                    if (!containsLayer(protectedLayers, currentLayer.parent)) {
                        protectedLayers.push(currentLayer.parent);
                    }
                    currentLayer = currentLayer.parent;
                }
            }
            if (layer.expressionEnabled && !containsLayer(protectedLayers, layer)) {
                protectedLayers.push(layer);
            }
        }

        var deletedCount = 0;
        for (var i = comp.numLayers; i >= 1; i--) {
            var layer = comp.layer(i);
            if (!layer.enabled && !containsLayer(protectedLayers, layer)) {
                layer.remove();
                deletedCount++;
            }
        }

        return deletedCount;
    }


    // --- UI CREATION ---
    function createUI(thisObj) {
        var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette", scriptName, undefined, { resizeable: true });
        if (myPanel === null) return;

        var res = "group { orientation:'column', alignment:['fill', 'top'], alignChildren:['fill', 'top'], " +
            "magicBtn: Button { text:'🎬 SELECT EXR & ORGANIZE', preferredSize:[220, 50] }," +
            "versionText: StaticText { text:'ver. 1', alignment:['center', 'bottom'] }," +
            "}";
        myPanel.grp = myPanel.add(res);

        // --- MAGIC ONE-CLICK BUTTON ---
        myPanel.grp.magicBtn.onClick = function () {
            app.beginUndoGroup("One-Click EXR Organize");

            try {
                // Step 1: Capture existing Item IDs (robust against sorting)
                var existingItemIds = {};
                for (var k = 1; k <= app.project.numItems; k++) {
                    existingItemIds[app.project.item(k).id] = true;
                }

                // Show hint (Removed for one-click workflow)
                // alert("Select your EXR file and choose:\n• Import as: Composition\n• Pre-compose layers: ✓\n• Contact sheet: ✓ (optional)");

                // Run import (result is ignored as it may be null)
                app.project.importFileWithDialog();

                // Step 2: Find NEW items by checking IDs
                // Iterate through all items and see which ones aren't in our 'existingItemIds' map
                var comp = null;
                var firstFrame = 1001; // Default
                var potentialComps = []; // Store other comps just in case

                // We check all items now, because new items could be inserted anywhere if sorted
                for (var i = 1; i <= app.project.numItems; i++) {
                    var item = app.project.item(i);

                    // If this ID already existed, skip it
                    if (existingItemIds[item.id]) continue;

                    // If we are here, 'item' is NEW
                    if (item instanceof FolderItem) {
                        var folder = item;
                        // Extract frame range from folder name like "LEV_FLAVMO... [1011-1085]"
                        var folderMatch = folder.name.match(/\[(\d+)-\d+\]/);
                        if (folderMatch && folderMatch[1]) {
                            firstFrame = parseInt(folderMatch[1], 10);
                        }

                        // Search inside the folder for the assemble comp
                        // Note: Items *inside* a new folder are also "new", but iterating the project items finds them too.
                        // However, checking children of a new folder is safe and direct.
                        for (var j = 1; j <= folder.numItems; j++) {
                            var subItem = folder.item(j);
                            if (subItem instanceof CompItem) {
                                if (subItem.name.toLowerCase().indexOf("assemble") !== -1) {
                                    comp = subItem;
                                    break;
                                } else {
                                    potentialComps.push(subItem);
                                }
                            }
                        }
                    } else if (item instanceof CompItem) {
                        if (item.name.toLowerCase().indexOf("assemble") !== -1) {
                            comp = item;
                        } else {
                            potentialComps.push(item);
                        }

                        // Extract frame range from comp name
                        var compMatch = item.name.match(/\[(\d+)-\d+\]/);
                        if (compMatch && compMatch[1]) {
                            firstFrame = parseInt(compMatch[1], 10);
                        }
                    }
                    if (comp) break; // Stop looking IF we found the correct one
                }

                // Pass 2: Fallback if no "assemble" found (use the first valid comp found)
                if (!comp && potentialComps.length > 0) {
                    comp = potentialComps[0];
                }

                if (!comp) {
                    // alert("❌ No 'assemble' composition found.\n\nPlease make sure to select 'Import as: Composition' in the import dialog.");
                    app.endUndoGroup();
                    return;
                }

                // Step 4: Set comp display start time to first frame
                var frameDuration = comp.frameDuration;
                var startTime = firstFrame * frameDuration;
                comp.displayStartTime = startTime;
                comp.time = startTime;

                // Open the comp in the viewer
                comp.openInViewer();

                // Step 5: Flatten precomps (replaces precomps with their source footage)
                var flattenedCount = flattenComp(comp);

                // Step 6: Organize layers
                var lsCount = organizeLayers(comp);

                // Step 7: Delete unused layers (DISABLED)
                // var deletedCount = deleteUnusedLayers(comp);

                // Done!
                // alert("✅ One-Click EXR Organize Complete!\n\n" +
                //     "🎬 Composition: " + comp.name + "\n" +
                //     "🎞️ First frame: " + firstFrame + "\n" +
                //     "📐 Flattened layers: " + flattenedCount + "\n" +
                //     "🔦 Light Select layers: " + lsCount);

            } catch (e) {
                // alert("❌ An error occurred:\n" + e.toString() + "\n\nTip: Check the plugin names in the USER CONFIGURATION section at the top of the script.");
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