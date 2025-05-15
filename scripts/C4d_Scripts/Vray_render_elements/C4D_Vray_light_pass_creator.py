# Version: 1.1.0
# Last Updated: 2025-05-15

import c4d
from c4d import gui
from c4d import documents

# Creates the render element object instance and populates its relevant parameters

def createLightSelect(light: c4d.BaseObject, createdNames: set, existingLightSelects: set):
    # ID_VRAY_RENDER_ELEMENT_LIGHT_SELECT
    baseName = light.GetName()
    if baseName in existingLightSelects:
        return None  # Skip if Light Select pass already exists

    newRenderElement = c4d.BaseObject(1054224)
    if not newRenderElement:
        raise Exception('Could not create V-Ray Light Select Render element')

    usedName = baseName
    suffix = 1
    # The name of the newly created render element must be deduplicated, to prevent channel name duplication
    while usedName in createdNames:
        usedName = baseName + ".{}".format(suffix)
        suffix += 1
    newRenderElement.SetName(usedName)
    createdNames.add(usedName)
    # These two are necessary to have the parameters properly working
    newRenderElement[c4d.VRAY_RENDER_ELEMENT_FILTER_PARAMETER_ID] = c4d.RENDERCHANNELLIGHTSELECT_FILTERING
    newRenderElement[c4d.VRAY_RENDER_ELEMENT_DENOISE_PARAMETER_ID] = c4d.RENDERCHANNELLIGHTSELECT_DENOISE
    # Modify relevant parameters
    newRenderElement[c4d.RENDERCHANNELLIGHTSELECT_DENOISE] = True
    newRenderElement[c4d.RENDERCHANNELLIGHTSELECT_LIGHT_SELECT_MODE] = c4d.RENDERCHANNELLIGHTSELECT_LIGHT_SELECT_MODE_FULL
    lightSelectSet: c4d.InExcludeData = c4d.InExcludeData()
    lightSelectSet.SetFlagCount(1)  # It is important to set the flag count
    lightSelectSet.InsertObject(light, 0)
    newRenderElement[c4d.VRAY_RENDER_ELEMENT_LIGHT_SELECT_LIGHT_LIST] = lightSelectSet
    # The hide part is necessary to avoid selecting the render element object when all document object are selected
    # from the object manager.
    newRenderElement.ChangeNBit(c4d.NBIT_OHIDE, c4d.NBITCONTROL_SET)
    return newRenderElement



# Returns true if the provided atom should be used as input light in the LightSelect.

def shouldUseLight(light: c4d.C4DAtom):
    # ID_VRAY_INSTANCE_LIGHT
    isVRayLight = light.IsInstanceOf(1053299)
    if isVRayLight:
        return True
    # Other possible lights?
    return False

def getDocumentLightsRecursive(obj: c4d.BaseObject):
    if not obj:
        return []
    result = []
    if shouldUseLight(obj):
        result.append(obj)
    child: c4d.BaseObject = obj.GetDown()
    while child:
        childResult = getDocumentLightsRecursive(child)
        if childResult:
            result.extend(childResult)
        child = child.GetNext()
    return result

def getDocumentLights(doc: c4d.documents.BaseDocument):
    topObject: c4d.BaseObject = doc.GetFirstObject()
    result = []
    while topObject:
        gatherResult = getDocumentLightsRecursive(topObject)
        if gatherResult:
            result.extend(gatherResult)
        topObject = topObject.GetNext()
    return result

# V-Ray Light types in Cinema 4D
VRAY_LIGHT_TYPES = [
    1053280,  # V-Ray Rectangle Light
    1053277,  # V-Ray Dome Light
    1053278,  # V-Ray Sphere Light
    1059898,  # V-Ray Mesh Light
    1053281,  # V-Ray IES Light
    1053287,  # V-Ray Sun Light
]

def rename_vray_lights():
    """Finds and renames V-Ray lights with the 'LS_' prefix if necessary."""
    doc = c4d.documents.GetActiveDocument()  # Active document
    renamed_lights = []  # List of renamed lights
    existing_names = set()  # Store existing names to avoid conflicts

    def scan_objects(obj):
        """Recursive function to traverse all objects."""
        while obj:
            if obj.GetType() in VRAY_LIGHT_TYPES:  # If the object is a V-Ray Light type
                original_name = obj.GetName()

                # If the name does not start with "LS_", modify it
                if not original_name.startswith("LS_"):
                    new_name = f"LS_{original_name}"

                    # Ensure the new name is unique
                    counter = 1
                    unique_name = new_name
                    while unique_name in existing_names:
                        unique_name = f"{new_name}_{counter}"
                        counter += 1

                    obj.SetName(unique_name)  # Set the new name
                    renamed_lights.append(f"{original_name} -> {unique_name}")
                    existing_names.add(unique_name)  # Add the new name to the set

                else:
                    existing_names.add(original_name)  # If already correct, store the name

            scan_objects(obj.GetDown())  # Check child objects
            obj = obj.GetNext()  # Check next object

    scan_objects(doc.GetFirstObject())  # Traverse the hierarchy

    c4d.EventAdd()  # Refresh Cinema 4D

    # Display a dialog with the renamed lights
    if renamed_lights:
        return True
    else:
        return False

# Main function
def create_light_selects():
    """ Creates a V-Ray Light Select Render element for each VRay light in the document"""
    activeDocument = c4d.documents.GetActiveDocument()
    vrayRenderElementsHook=activeDocument.FindSceneHook(1054363) # ID_VRAY_RENDER_ELEMENTS_SCENE_HOOK
    if not vrayRenderElementsHook:
        raise Exception('Could not find V-Ray Render Elements Scene Hook')
    elementsHookBranchInfo=vrayRenderElementsHook.GetBranchInfo()
    vrayRenderElementsRootHead=None
    for branchInfo in elementsHookBranchInfo:
        # ID_VRAY_RENDER_ELEMENT_ROOT
        if branchInfo['id']==1054149:
            vrayRenderElementsRootHead=branchInfo['head']
            break

    if not vrayRenderElementsRootHead:
        raise Exception('Could not find V-Ray Render Elements Root Head')
    
    # Gather existing Light Select passes
    existingLightSelects = set()
    child = vrayRenderElementsRootHead.GetDown()
    while child:
        if child.IsInstanceOf(1054224):  # ID_VRAY_RENDER_ELEMENT_LIGHT_SELECT
            existingLightSelects.add(child.GetName())
        child = child.GetNext()

    # Note that this list may be filtered further if necessary.
    documentLights=getDocumentLights(activeDocument)
    if not documentLights:
        raise Exception('No lights found in the document')
    
    renderElementNames: set = set()
    try:
        undoStarted=activeDocument.StartUndo()
        anythingAdded = False
        # Iterate over all the gathered lights and create a new Light Select RE for each light.
        for light in documentLights:
            lightSelectRE = createLightSelect(light, renderElementNames, existingLightSelects)
            if lightSelectRE:
                lightSelectRE.InsertUnderLast(vrayRenderElementsRootHead)
                if undoStarted:
                    anythingAdded = True
                    activeDocument.AddUndo(c4d.UNDOTYPE_NEWOBJ, lightSelectRE)

    except Exception as error:
        if undoStarted:
            activeDocument.EndUndo()
            if anythingAdded:
                activeDocument.DoUndo()
        raise error
    
    finally:
        if undoStarted:
            activeDocument.EndUndo()
        c4d.EventAdd()

# Add the rename functionality to the main script
if __name__ == '__main__':
    try:
        renamed = rename_vray_lights()
        create_light_selects()  # Call the main function to create light select passes
        if renamed:
            gui.MessageDialog('Renamed V-Ray lights with the "LS_" prefix. All lights are added to the Light Select pass.')
        else:
            gui.MessageDialog('No V-Ray lights needed renaming. All lights are added to the Light Select pass.')
    except Exception as error:
        gui.MessageDialog('Error: ' + ' '.join(map(str, error.args)), c4d.GEMB_ICONSTOP)