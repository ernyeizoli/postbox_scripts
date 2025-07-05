// Polyfill to add the .trim() function if it's missing for older AE versions
if (!String.prototype.trim) {
  String.prototype.trim = function () {
    return this.replace(/^\s+|\s+$/g, '');
  };
}

// Function to show an alert message
function showAlert(message) {
    alert(message);
}

// Main function
function runAndReplace() {
    app.beginUndoGroup("Replace and Rename Footage and Layer");

    var activeComp = app.project.activeItem;
    if (activeComp === null || !(activeComp instanceof CompItem)) {
        showAlert("Please select a composition first.");
        return;
    }

    var selectedLayers = activeComp.selectedLayers;
    if (selectedLayers.length === 0) {
        showAlert("Please select a layer in the active composition.");
        return;
    }

    var selectedLayer = selectedLayers[0];
    var originalFootage = selectedLayer.source;

    if (!(originalFootage instanceof FootageItem) || !originalFootage.file) {
        showAlert("The selected layer does not have a replaceable file source.");
        return;
    }

    var originalName = File.decode(originalFootage.file.name);
    var footagePath = originalFootage.file.fsName;

    // --- CONFIGURATION ---
    var pythonExecutable = "python";

    // --- Automatic Path Detection ---
    // This finds the folder where this script is located.
    var thisScriptFile = new File($.fileName);
    var scriptFolder = thisScriptFile.parent;
    
    // This assumes 'process_footage.py' is in the SAME FOLDER as this script.
    var pythonScriptFile = new File(scriptFolder.fsName + "/process_footage.py");
    var pythonScriptPath = pythonScriptFile.fsName;


    // --- EXECUTION ---
    var command = '"' + pythonExecutable + '" "' + pythonScriptPath + '" "' + footagePath + '"';
    var returnedPath = system.callSystem(command);

    // --- HANDLING THE RETURN & REPLACING FOOTAGE ---
    if (returnedPath) {
        if (returnedPath.indexOf("Error") !== -1 || returnedPath.indexOf("can't open file") !== -1) {
            showAlert("Python script failed to execute.\n\nPython Error:\n" + returnedPath);
            return;
        }

        var newPath = returnedPath.trim();
        var newFile = new File(newPath);

        if (newFile.exists) {
            try {
                originalFootage.replaceWithSequence(newFile, true);
                var newName = File.decode(newFile.name);
                originalFootage.name = newName;
                selectedLayer.name = newName;
                var successMessage = "Footage Replaced Successfully!\n\nFrom: " + originalName + "\nTo: " + newName;
                showAlert(successMessage);
            } catch (e) {
                showAlert("An error occurred during sequence replacement:\n" + e.message);
            }
        } else {
            showAlert("Error: The returned file path does not exist.\nPath received from Python: " + newPath);
        }
    } else {
        showAlert("The Python script did not return anything. Check that 'process_footage.py' is in the same folder as this script.");
    }

    app.endUndoGroup();
}

// Run the main function
runAndReplace();