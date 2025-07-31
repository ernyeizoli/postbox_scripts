// This script will organize your files in project panel, You can move all the specific files to their particular folders respectively, 
{
	function myScript(thisObj){
        function myScript_buildUI(thisObj){
            var myPanel = (thisObj instanceof Panel) ? thisObj : new Window("palette", "PBV Delivery 2.2", undefined, {resizeable:true});
            var justDoItButton = myPanel.add("button",[10,10,125,30], "JUST DO IT!");
            var justDoItText = justDoItButton.text;
            var divider = myPanel.add("panel", [10, 10, 125, 15]); // Méret beállítása a gombok méretének felére
            divider.graphics.backgroundColor = divider.graphics.newBrush (divider.graphics.BrushType.SOLID_COLOR, [1, 1, 0], 1);

            var myButton = myPanel.add("button",[10,10,125,30], "Folder Structure");
            var movecomps = myPanel.add("button",[10,10,125,30], "Move Comps");
            var moveAi = myPanel.add("button",[10,10,125,30], "Move Vector files");
            var movepng = myPanel.add("button",[10,10,125,30], "Move Images");
            var movepsd = myPanel.add("button",[10,10,125,30], "Move PSD files");
            var moveplates = myPanel.add("button",[10,10,125,30], "Move Footages");
            var movesound = myPanel.add("button",[10,10,125,30], "Move Sound");
            var movesolids = myPanel.add("button",[10,10,125,30], "Move Solids");
            var deletefolders = myPanel.add("button",[10,10,125,30], "Delete Empty Folders");
            var label = myPanel.add("statictext", [28, 0, 150, 30], "Postbox Delivery - 2024");

            // Állítsd be a szöveg formázását és igazítását
            label.graphics.font = ScriptUI.newFont("Arial-BoldMT", "BOLD", 16);
            label.graphics.foregroundColor = label.graphics.newPen(label.graphics.PenType.SOLID_COLOR, [1, 1, 0], 1);
            label.alignment = "center";    
            movesolids.graphics.foregroundColor = label.graphics.newPen(label.graphics.PenType.SOLID_COLOR, [1, 1, 0], 1);
               
            myButton.helpTip = "Create the right Directories";
            myButton.onClick = function() {
      
        var mainFolder = false;

        
        for (var i = 1; i <= app.project.rootFolder.numItems; i++) {
            if ((app.project.rootFolder.item(i) instanceof FolderItem) && (app.project.rootFolder.item(i).name == "_ASSETS")) {
                mainFolder = app.project.rootFolder.item(i);
                break;
            }
        }
        
        if (!mainFolder) {
            mainFolder = app.project.rootFolder.items.addFolder("_ASSETS");
        }
        
        // Almappák létrehozása a főmappa részeként
        var subFolders = ["AUDIO", "COMPS", "ELEMENTS", "FOOTAGE", "SOLIDS"];
        
        for (var j = 0; j < subFolders.length; j++) {
            var subFolder = false;
        
            for (var k = 1; k <= mainFolder.numItems; k++) {
                if ((mainFolder.item(k) instanceof FolderItem) && (mainFolder.item(k).name == subFolders[j])) {
                    subFolder = mainFolder.item(k);
                    break;
                }
            }
        
            if (!subFolder) {
                subFolder = mainFolder.items.addFolder(subFolders[j]);
            }
        }
        
        // Az "ELEMENTS" mappa részeinek létrehozása
        var elementsFolder = false;

        for (var l = 1; l <= mainFolder.numItems; l++) {
            if ((mainFolder.item(l) instanceof FolderItem) && (mainFolder.item(l).name == "ELEMENTS")) {
                elementsFolder = mainFolder.item(l);
                break;
            }
        }
        
        if (!elementsFolder) {
            elementsFolder = mainFolder.items.addFolder("ELEMENTS");
        }
        
        var elementsSubFolders = ["AI", "IMG", "PS"];
        
        for (var m = 0; m < elementsSubFolders.length; m++) {
            var elementsSubFolder = false;
        
            for (var n = 1; n <= elementsFolder.numItems; n++) {
                if ((elementsFolder.item(n) instanceof FolderItem) && (elementsFolder.item(n).name == elementsSubFolders[m])) {
                    elementsSubFolder = elementsFolder.item(n);
                    break;
                }
            }
        
            if (!elementsSubFolder) {
                elementsSubFolder = elementsFolder.items.addFolder(elementsSubFolders[m]);
            }
        }

}
//Move Comps		
movecomps.helpTip = "Move all the compositions to comp folder";			
movecomps.onClick = function() {
    var compFolder = null;
    var rootFolder = app.project.rootFolder;
    var activeComp = app.project.activeItem; // Az aktuálisan aktív kompozíció lekérdezése

    // COMPS mappa keresése vagy létrehozása
    for (var i = 1; i <= app.project.numItems; i++) {
        if ((app.project.item(i) instanceof FolderItem) && (app.project.item(i).name == "COMPS")) {
            compFolder = app.project.item(i);
            break;
        }
    }

    if (compFolder == null) {
        compFolder = rootFolder.items.addFolder("COMPS"); // Létrehozzuk, ha nem létezik
    }

    var comps = [];

    // Összegyűjtjük az összes kompozíciót
    for (var i = 1; i <= app.project.numItems; i++) {
        if (app.project.item(i) instanceof CompItem) {
            comps.push(app.project.item(i));
        }
    }

    // Az összes kompozíciót áthelyezzük a COMPS mappába, kivéve az aktív kompozíciót
    for (var i = 0; i < comps.length; i++) {
        if (comps[i] !== activeComp) { // Az aktív kompozíció marad a gyökérben
            comps[i].parentFolder = compFolder;
        }
    }

    // Az aktív kompozíció a gyökérben marad, nem mozgatjuk
    if (activeComp != null) {
        activeComp.parentFolder = rootFolder; // Gyökérben hagyjuk
    }
};


//JUST DO IT BUTTON
  justDoItButton.onClick = function() {
    // Pre-funkció: az összes mappa átnevezése "temp"-re
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof FolderItem) {
            item.name = "temp"; // Mappák átnevezése "temp"-re
        }
    }

    // Iterálás az alábbi gombokon, és mindegyik gomb funkcionalitásának 20-szeri végrehajtása
    for (var i = 0; i < 20; i++) {
        myButton.onClick();
        movecomps.onClick();
        moveAi.onClick();
        movepng.onClick();
        movepsd.onClick();
        moveplates.onClick();
        movesound.onClick();
        movesolids.onClick();

        // Temp mappa tartalmának áthelyezése a SOLIDS mappába
        var tempFolder = null;
        var solidsFolder = null;

        // Megkeressük a "temp" nevű mappát
        for (var j = 1; j <= app.project.numItems; j++) {
            if ((app.project.item(j) instanceof FolderItem) && (app.project.item(j).name == "temp")) {
                tempFolder = app.project.item(j);
                break;
            }
        }

        // Megkeressük vagy létrehozzuk a "SOLIDS" mappát
        for (var k = 1; k <= app.project.numItems; k++) {
            if ((app.project.item(k) instanceof FolderItem) && (app.project.item(k).name == "SOLIDS")) {
                solidsFolder = app.project.item(k);
                break;
            }
        }

        // Ha találtunk temp mappát, áthelyezzük a tartalmát a SOLIDS mappába
        if (tempFolder) {
            for (var l = 1; l <= tempFolder.numItems; l++) {
                tempFolder.item(l).parentFolder = solidsFolder;
            }
        }

        deletefolders.onClick(); // Üres mappák törlése
    }
};



// Move AI/Eps Code

moveAi.helpTip = "Move all the Illustrator files to ai folder";
moveAi.onClick = function (){
var aiFolder = null;
  for (var i = 1; i <= app.project.numItems; i++){
    if ((app.project.item(i) instanceof FolderItem) && (app.project.item(i).name == "AI")){
        
      aiFolder = app.project.item(i);
      break;
    }
  }

  if (aiFolder == null) return;
  var ai = [];
for(var i = 1; i <= app.project.numItems; i++){
    var splitName = app.project.item(i).name.split(".");
    if((app.project.item(i) instanceof FootageItem) && (splitName[splitName.length-1].toLowerCase() == "ai") || (splitName[splitName.length-1].toLowerCase() == "eps"))
    ai.push(app.project.item(i));
  }
  for (var i = 0; i < ai.length; i++)
        ai[i].parentFolder = aiFolder;
  
  }

// End Code

// Move Png Code

movepng.helpTip = "Move all the Png files to png folder";
movepng.onClick = function (){
var pngFolder = null;
  for (var i = 1; i <= app.project.numItems; i++){
    if ((app.project.item(i) instanceof FolderItem) && (app.project.item(i).name == "IMG")){
        
      pngFolder = app.project.item(i);
      break;
    }
  }

  if (pngFolder == null) return;
  var pngs = [];
for(var i = 1; i <= app.project.numItems; i++){
    var splitName = app.project.item(i).name.split(".");
    if((app.project.item(i) instanceof FootageItem) && (splitName[splitName.length-1].toLowerCase() == "png") || (splitName[splitName.length-1].toLowerCase() == "jpg") || (splitName[splitName.length-1].toLowerCase() == "tif"))
    pngs.push(app.project.item(i));
  }
  for (var i = 0; i < pngs.length; i++)
        pngs[i].parentFolder = pngFolder;
  
  }

// End Code

// Move Sound

movesound.helpTip = "Move all the Sound files to sound folder";
movesound.onClick = function (){
var soundFolder = null;
  for (var i = 1; i <= app.project.numItems; i++){
    if ((app.project.item(i) instanceof FolderItem) && (app.project.item(i).name == "AUDIO")){
        
      soundFolder = app.project.item(i);
      break;
    }
  }

  if (soundFolder == null) return;
  var sound = [];
for(var i = 1; i <= app.project.numItems; i++){
    var splitName = app.project.item(i).name.split(".");
    if((app.project.item(i) instanceof FootageItem) && (splitName[splitName.length-1].toLowerCase() == "wav") || (splitName[splitName.length-1].toLowerCase() == "mp3"))
    sound.push(app.project.item(i));
  }
  for (var i = 0; i < sound.length; i++)
        sound[i].parentFolder = soundFolder;
  
  }

// Move Solid
movesolids.helpTip = "Move all solids, adjustment layers and Null objects into SOLIDS";
movesolids.onClick = function () {
    // Keresd meg az összes Solids nevű mappát a projektben
    var solidsFolders = findFoldersByName(app.project.rootFolder, "Solids", []);

    // Ellenőrizd, hogy vannak-e Solids mappák
    if (solidsFolders.length > 0) {
        // Keresd vagy hozd létre az _ASSETS/SOLIDS mappát
        var targetRootFolderName = "_ASSETS";
        var targetSubFolderName = "SOLIDS";

        var rootFolder = findOrCreateFolder(app.project.rootFolder, targetRootFolderName);
        var targetFolder = findOrCreateFolder(rootFolder, targetSubFolderName);

        // Mozgasd az összes Solids mappát a _ASSETS/SOLIDS mappába
        for (var l = 0; l < solidsFolders.length; l++) {
            var currentSolidsFolder = solidsFolders[l];
            for (var m = 1; m <= currentSolidsFolder.numItems; m++) {
                var currentItem = currentSolidsFolder.item(m);
                currentItem.parentFolder = targetFolder;
            }
        }
    }
}

// Rekurzív függvény a mappák keresésére név alapján
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

// Rekurzív függvény a mappa keresésére és létrehozására
function findOrCreateFolder(parentFolder, folderName) {
    for (var j = 1; j <= parentFolder.numItems; j++) {
        if (parentFolder.item(j) instanceof FolderItem && parentFolder.item(j).name === folderName) {
            return parentFolder.item(j);
        }
    }
    return parentFolder.items.addFolder(folderName);

}
// End Code

// Move PSD Code

movepsd.helpTip = "Move all the PSD files to psd folder";
movepsd.onClick = function (){
  var psdFolder = null;
    for (var i = 1; i <= app.project.numItems; i++){
      if ((app.project.item(i) instanceof FolderItem) && (app.project.item(i).name == "PS")){
        psdFolder = app.project.item(i);
        break;
      }
    }
    if (psdFolder == null) return;
      var psds = [];
      for(var i = 1; i <= app.project.numItems; i++){
        var splitName = app.project.item(i).name.split(".");
        if((app.project.item(i) instanceof FootageItem) && (splitName[splitName.length-1].toLowerCase() == "psd"))
          psds.push(app.project.item(i));
      }
      for (var i = 0; i < psds.length; i++)
        psds[i].parentFolder = psdFolder;
  }

// End Code

// Move Plates Code

moveplates.helpTip = "Move all the Footages to plates folder";
moveplates.onClick = function (){
var platesFolder = null;
  for (var i = 1; i <= app.project.numItems; i++){
    if ((app.project.item(i) instanceof FolderItem) && (app.project.item(i).name == "FOOTAGE")){
        
      platesFolder = app.project.item(i);
      break;
    }
  }

  if (platesFolder == null) return;
  var plates = [];
for(var i = 1; i <= app.project.numItems; i++){
    var splitName = app.project.item(i).name.split(".");
    if((app.project.item(i) instanceof FootageItem) && (splitName[splitName.length-1].toLowerCase() == "mov") || (splitName[splitName.length-1].toLowerCase() == "mp4") || (splitName[splitName.length-1].toLowerCase() == "exr"))
    plates.push(app.project.item(i));
}
for (var i = 0; i < plates.length; i++)
      plates[i].parentFolder = platesFolder;

}


// Delete Empty Folders Code

deletefolders.helpTip = "Delete all empty folders";
deletefolders.onClick = function removeFolders(theFolder) {
  var del = [];
    for (var i = 1; i<=app.project.numItems; i++) {
    if(app.project.item(i) instanceof FolderItem& app.project.item(i).numItems==0)
    del.push(app.project.item(i));
  }
  for (var i = 0; i < del.length; i++)
    del[i].remove();

  

  // loop from last to first item so removing a folder won't affect the index
 // for (var i = theFolder.numItems; i > 0; i--) {
 
  //if (theFolder.item(i) instanceof FolderItem) {
  // if subfolder contains items, enter recursive function again using the subfolder
  //if (theFolder.item(i).numItems > 0) removeFolders(theFolder.item(i));
 
  // if either it never contained any items, or the contents has now been removed after leaving the later recursions, delete the folder
  //if (theFolder.item(i).numItems == 0) theFolder.item(i).remove();
  //}
  //}
}
 
// enter function for the first time using the root folder
//removeFolders(app.project);


// End Code

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