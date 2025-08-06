
###
### Overwrite from line 365 to to line 376 in Prism_AfterEffects_Functions.py
###

cmd = """
if (app.project) {
    try {
        // Get the full path of the file from the pipeline
        var sourceFilePath = "%s";
        
        // Create a File object to easily access its properties
        var sourceFile = new File(sourceFilePath);
        
        // Get the parent folder of the file. The '.parent' property returns a Folder object.
        var targetFolder = sourceFile.parent;

        // Check if the folder exists and set it as the default for the upcoming dialog
        if (targetFolder && targetFolder.exists) {
            app.project.setDefaultImportFolder(targetFolder);
        }

        // Now, open the import dialog. It will start in the 'targetFolder'.
        // We no longer need the old ImportOptions code here because importFileWithDialog does not use it.
        var importedItem = app.project.importFileWithDialog();

        // The user might cancel the dialog, which returns 'null'. We must check for this.
        if (importedItem) {
            // Success: return a JSON string with the result.
            '{"result": true, "fileName": "' + importedItem.name + '"}';
        } else {
            // User cancelled: return a failure message.
            '{"result": false, "details": "Import dialog was cancelled by user."}';
        }

    } catch (e) {
        // Catch any other potential errors during execution.
        '{"result": false, "details": "' + e.toString() + '"}';
    }
} else {
    // No project is open in After Effects.
    '{"result": false, "details": "No project found."}';
}
""" % (filepaths[0].replace("\\", "/"))