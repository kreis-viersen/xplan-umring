# umringpolygon-zu-xplanung
Umringpolygon eines Bebauungsplans aus QGIS nach XPlanung konvertieren.

Bei Fragen, Anmerkungen, etc. erreichen Sie uns auch per E-Mail unter [open@kreis-viersen.de](mailto:open@kreis-viersen.de?subject=umringpolygon-zu-xplanung).

## Es wird benötigt:
QGIS mit Skript [`xplan-umring.py`](https://kreis-viersen.github.io/umringpolygon-zu-xplanung/xplan-umring.py).

## Workflow

1. Bebauungsplanumring in QGIS digitalisieren oder vorhandenen Umring laden.<br>Wichtig: Der Vektorlayer darf nur ein Objekt (= den Umring) vom Typ Polygon beinhalten.
2. QGIS-Skript `xplan-umring` ausführen.<br>Eingabelayer ist der Vektorlayer mit dem Bebauungsplanumring, die übrigen Modelleingaben ensprechend befüllen/auswählen und Speicherort für das XPlan-Archiv festlegen.