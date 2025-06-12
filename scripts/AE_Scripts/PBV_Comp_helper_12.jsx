// EXR Flattener + Organizer UI Panel (with DELETE UNUSED button)
(function organizeEXRLayers(thisObj) {
    var scriptName = "EXR_Organizer_WithFlatten";

    function createUI(thisObj) {
        var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette", scriptName, undefined, {resizeable:true});

        var res =
        "group { orientation:'column', alignment:['fill', 'top'], alignChildren:['fill', 'top'], " +
        "flattenBtn: Button { text:'FLATTEN SELECTED COMP' }," +
        "organizeBtn: Button { text:'ORGANIZE LAYERS' }," +
        "deleteBtn: Button { text:'DELETE UNUSED' }," +
        "}";

        myPanel.grp = myPanel.add(res);

        // FLATTEN BUTTON FUNCTION
        myPanel.grp.flattenBtn.onClick = function() {
            var comp = app.project.activeItem;
            if (!(comp && comp instanceof CompItem)) {
                alert("No active composition selected.");
                return;
            }

            var replacedCount = 0;
            app.beginUndoGroup("Flatten Precomps with Effects");

            for (var j = comp.numLayers; j >= 1; j--) {
                var layer = comp.layer(j);
                if (!layer.source) continue;

                var sourceComp = layer.source;
                if (sourceComp instanceof CompItem && sourceComp.numLayers >= 1) {
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

                    if (layer.effect) {
                        for (var e = 1; e <= layer.effect.numProperties; e++) {
                            layer.effect(e).duplicate().moveTo(newLayer);
                        }
                    }

                    layer.remove();
                    replacedCount++;
                }
            }

            app.endUndoGroup();
            alert("✅ Flatten complete.\n\nReplaced layers: " + replacedCount);
        };

        // ORGANIZE BUTTON FUNCTION
        myPanel.grp.organizeBtn.onClick = function() {
            app.beginUndoGroup("Organize Footage Layers");

            var comp = app.project.activeItem;
            if (!(comp && comp instanceof CompItem)) {
                alert("No active composition found.");
                return;
            }

            var lsLayers = [];
            var cryptomatteLayer = null;
            var extraTexLayer = null;

            for (var i = comp.numLayers; i >= 1; i--) {
                var layer = comp.layer(i);

                if (layer.name === "ProEXR File Description") {
                    layer.remove();
                    continue;
                }

                if (!layer.source) continue;

                var name = layer.name;
                var sourceName = layer.source.name;

                if (name.indexOf("LS_") === 0 || sourceName.indexOf("LS_") === 0) {
                    lsLayers.push(layer);
                    layer.label = 2; // Yellow
                    layer.blendingMode = BlendingMode.ADD;
                }

                if (!cryptomatteLayer && layer.effect && layer.effect.numProperties > 0) {
                    for (var j = 1; j <= layer.effect.numProperties; j++) {
                        if (layer.effect.property(j).name.toLowerCase().indexOf("cryptomatte") !== -1) {
                            cryptomatteLayer = layer;
                            layer.label = 10; // Purple
                            layer.enabled = false;
                        }
                    }
                }

                if (!extraTexLayer && (name.toLowerCase().indexOf("extra tex") !== -1 || sourceName.toLowerCase().indexOf("extra tex") !== -1)) {
                    extraTexLayer = layer;
                    layer.label = 16; // Dark Green
                    layer.blendingMode = BlendingMode.MULTIPLY;
                    layer.enabled = false;
                }
            }

            for (var k = 1; k <= comp.numLayers; k++) {
                var l = comp.layer(k);
                if (lsLayers.indexOf(l) === -1 && l !== cryptomatteLayer && l !== extraTexLayer) {
                    l.enabled = false;
                }
            }

            lsLayers.sort(function(a, b) {
                return a.name.localeCompare(b.name);
            });

            if (cryptomatteLayer) {
                cryptomatteLayer.moveToBeginning();
            }
            if (extraTexLayer) {
                extraTexLayer.moveBefore(cryptomatteLayer || comp.layer(1));
            }
            for (var s = lsLayers.length - 1; s >= 0; s--) {
                lsLayers[s].moveToBeginning();
            }

            // ➕ ADD EXPOSURE + COLORISTA + OCIO
            // 1. Exposure az LS_ layerekre
            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i);
                if (layer.name.indexOf("LS_") === 0) {
                    layer.property("Effects").addProperty("Exposure");
                }
            }

            // 2. Colorista adjustment layer
            var coloristaLayer = comp.layers.addSolid([1, 1, 1], "Colorista", comp.width, comp.height, comp.pixelAspect, comp.duration);
            coloristaLayer.adjustmentLayer = true;
            coloristaLayer.name = "Colorista";
            coloristaLayer.label = 11;
            coloristaLayer.property("Effects").addProperty("Colorista V");

            // 3. OCIO adjustment layer a legtetejére
            var ocioLayer = comp.layers.addSolid([1, 1, 1], "OCIO", comp.width, comp.height, comp.pixelAspect, comp.duration);
            ocioLayer.adjustmentLayer = true;
            ocioLayer.name = "OCIO";
            ocioLayer.label = 11;
            ocioLayer.property("Effects").addProperty("OCIO Display Transform");
            ocioLayer.moveToBeginning();
            ocioLayer.locked = true;

		// 🧪 OCIO Input Color Space ellenőrzés
		var ocioEffect = ocioLayer.property("Effects").property("OCIO Display Transform");
		if (
 		   ocioEffect &&
  		  ocioEffect.property("Input Color Space") &&
  		  ocioEffect.property("Input Color Space").isModified !== undefined
		) {
  		  var inputValue = ocioEffect.property("Input Color Space").value;
  		  if (inputValue !== 14) {
    		    alert("⚠️ Ellenőrizd a projekt Color Management beállításait!");
    }
}



            alert("✅ Organization complete.\n\n📁 LS layers: " + lsLayers.length +
                  "\n🎨 Cryptomatte: " + (cryptomatteLayer ? "found" : "not found") +
                  "\n🟢 Extra Tex: " + (extraTexLayer ? "found" : "not found") );

            app.endUndoGroup();

// VÉGÉRE HOZZÁADOTT RÉSZ – Assemble comp átnevezés és gyökérbe helyezés
(function () {
    var proj = app.project;
    if (!proj) {
        alert("Nincs megnyitott projekt.");
        return;
    }

    // Már van egy UndoGroup, nem nyitunk újat

    var selectedItem = proj.selection[0];
    if (!(selectedItem instanceof CompItem)) {
        return;
    }

    var assembleComp = findAssembleComp(proj, selectedItem);
    if (!assembleComp) {
        return;
    }

    var nameBefore = assembleComp.name;
    var mpIndex = nameBefore.indexOf("MP_");
    if (mpIndex !== -1) {
        var newName = nameBefore.substring(0, mpIndex) + "COMP_";
        if (newName.length > 0) {
            assembleComp.name = newName;
        }
    }

    moveToRootFolder(assembleComp, proj.rootFolder);
    collapseAllFolders(proj.rootFolder);

    function findAssembleComp(project, selected) {
        if (selected.name.toLowerCase().indexOf("assemble") !== -1) {
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

    function moveToRootFolder(item, root) {
        item.parentFolder = root;
    }

    function collapseAllFolders(folder) {
        for (var i = 1; i <= folder.numItems; i++) {
            var item = folder.item(i);
            if (item instanceof FolderItem) {
                item.selected = false;
                collapseAllFolders(item);
            }
        }
    }
})();
        };

        // DELETE UNUSED BUTTON FUNCTION
        myPanel.grp.deleteBtn.onClick = function() {
            var comp = app.project.activeItem;
            if (!(comp && comp instanceof CompItem)) {
                alert("⚠️ No active composition.");
                return;
            }

            app.beginUndoGroup("Delete Hidden Layers (with protection)");
            var protectedLayers = [];

            // 1. Matte kapcsolatok
            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i);
                if (layer.trackMatteType !== TrackMatteType.NO_TRACK_MATTE && layer.trackMatteLayer != null) {
                    if (protectedLayers.indexOf(layer) === -1) protectedLayers.push(layer);
                    if (protectedLayers.indexOf(layer.trackMatteLayer) === -1) protectedLayers.push(layer.trackMatteLayer);
                }
            }

            // 2. Parent kapcsolatok
            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i);
                if (layer.parent !== null) {
                    if (protectedLayers.indexOf(layer) === -1) protectedLayers.push(layer);
                    if (protectedLayers.indexOf(layer.parent) === -1) protectedLayers.push(layer.parent);
                }
            }

            // 3. Expression vizsgálat
            function hasExpression(l) {
                function checkProp(p) {
                    return (p && p.canSetExpression && p.expressionEnabled);
                }
                var t = l.property("Transform");
                if (t) {
                    for (var j = 1; j <= t.numProperties; j++) {
                        if (checkProp(t.property(j))) return true;
                    }
                }
                if (checkProp(l.property("Opacity")) || checkProp(l.property("Time Remap"))) return true;

                var effects = l.property("ADBE Effect Parade");
                if (effects) {
                    for (var e = 1; e <= effects.numProperties; e++) {
                        var effect = effects.property(e);
                        for (var p = 1; p <= effect.numProperties; p++) {
                            if (checkProp(effect.property(p))) return true;
                        }
                    }
                }
                return false;
            }

            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i);
                if (hasExpression(layer) && protectedLayers.indexOf(layer) === -1) {
                    protectedLayers.push(layer);
                }
            }

            // 4. Törlés rejtett, nem védett rétegekre
            for (var i = comp.numLayers; i >= 1; i--) {
                var layer = comp.layer(i);
                if (!layer.enabled && protectedLayers.indexOf(layer) === -1) {
                    layer.remove();
                }
            }

            app.endUndoGroup();
        };

        myPanel.layout.layout(true);
        return myPanel;
    }

    var myScriptPal = createUI(thisObj);
    if (myScriptPal instanceof Window) {
        myScriptPal.center();
        myScriptPal.show();
    }
})(this);
