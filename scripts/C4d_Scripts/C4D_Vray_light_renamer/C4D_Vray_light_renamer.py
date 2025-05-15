# Version: 1.1.0
# Last Updated: 2025-05-15

import c4d
from c4d import gui

# V-Ray Light típusok Cinema 4D-ben
VRAY_LIGHT_TYPES = [
    1053280,  # V-Ray Rectangle Light
    1053277,  # V-Ray Dome Light
    1053278,  # V-Ray Sphere Light
    1059898,  # V-Ray Mesh Light
    1053281,  # V-Ray IES Light
]

def rename_vray_lights():
    """Megkeresi és átnevezi a V-Ray lámpákat a 'LS_' előtaggal, ha szükséges."""
    doc = c4d.documents.GetActiveDocument()  # Aktív dokumentum
    renamed_lights = []  # Lista az átnevezett lámpákhoz
    existing_names = set()  # Létező nevek tárolása az ütközések elkerülésére

    def scan_objects(obj):
        """Rekurzív függvény az összes objektum bejárására"""
        while obj:
            if obj.GetType() in VRAY_LIGHT_TYPES:  # Ha V-Ray Light típusú az objektum
                original_name = obj.GetName()

                # Ha a név nem "LS_"-sel kezdődik, módosítjuk
                if not original_name.startswith("LS_"):
                    new_name = f"LS_{original_name}"

                    # Ha már létezik ilyen név, számokkal különböztetjük meg
                    counter = 1
                    unique_name = new_name
                    while unique_name in existing_names:
                        unique_name = f"{new_name}_{counter}"
                        counter += 1

                    obj.SetName(unique_name)  # Új név beállítása
                    renamed_lights.append(f"{original_name} -> {unique_name}")
                    existing_names.add(unique_name)  # Új név hozzáadása

                else:
                    existing_names.add(original_name)  # Ha már jó, eltároljuk a nevét

            scan_objects(obj.GetDown())  # Alobjektumok vizsgálata
            obj = obj.GetNext()  # Következő objektum vizsgálata

    scan_objects(doc.GetFirstObject())  # Hierarchia bejárása

    c4d.EventAdd()  # Frissítés Cinema 4D-ben

    # Felugró ablak megjelenítése az átnevezett lámpákkal
    if renamed_lights:
        message = "Átnevezett V-Ray lámpák:\n\n" + "\n".join(renamed_lights)
    else:
        message = "Nem volt szükség átnevezésre, minden lámpa megfelelő nevet visel."

    gui.MessageDialog(message, c4d.GEMB_OK)  # Felugró ablak megjelenítése

# Fő script futtatása
if __name__ == '__main__':
    rename_vray_lights()