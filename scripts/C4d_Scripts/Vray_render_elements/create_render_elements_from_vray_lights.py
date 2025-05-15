import c4d
from c4d import gui
from c4d import documents

# Creates the render element object instance and populates its relevant parameters

def createLightSelect(light: c4d.BaseObject, createdNames: set):

    # ID_VRAY_RENDER_ELEMENT_LIGHT_SELECT

    newRenderElement = c4d.BaseObject(1054224)

    if not newRenderElement:

        raise Exception('Could not create V-Ray Light Select Render element')



    baseName = light.GetName()

    usedName = baseName

    suffix = 1

    # The name of the newly created render element must be deduplicated, to prevent channel name duplication

    while usedName in createdNames:

        usedName = baseName + ".{}".format(suffix)

        suffix += 1



    newRenderElement.SetName(usedName)

    createdNames.add(usedName)



    # These two are necessary to have the parameters properly working

    newRenderElement[c4d.VRAY_RENDER_ELEMENT_FILTER_PARAMETER_ID]=c4d.RENDERCHANNELLIGHTSELECT_FILTERING

    newRenderElement[c4d.VRAY_RENDER_ELEMENT_DENOISE_PARAMETER_ID]=c4d.RENDERCHANNELLIGHTSELECT_DENOISE



    # Modify relevant parameters

    newRenderElement[c4d.RENDERCHANNELLIGHTSELECT_DENOISE]=True

    newRenderElement[c4d.RENDERCHANNELLIGHTSELECT_LIGHT_SELECT_MODE]=c4d.RENDERCHANNELLIGHTSELECT_LIGHT_SELECT_MODE_FULL



    lightSelectSet: c4d.InExcludeData = c4d.InExcludeData()

    lightSelectSet.SetFlagCount(1) # It is important to set the flag count

    lightSelectSet.InsertObject(light, 0)

    newRenderElement[c4d.VRAY_RENDER_ELEMENT_LIGHT_SELECT_LIGHT_LIST]=lightSelectSet



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



# Main function

def main():

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

            lightSelectRE = createLightSelect(light, renderElementNames)

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



# Execute main()

if __name__=='__main__':

    try:

        main()

    except Exception as error:

        gui.MessageDialog(' '.join(map(str, error.args)), c4d.GEMB_ICONSTOP)