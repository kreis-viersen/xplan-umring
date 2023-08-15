# xplan-umring
### _QGIS-Plugin zum Erstellen einer XPlanGML-Datei für ein Umringszenario_

Bei Fragen, Anmerkungen, etc. erreichen Sie uns auch per E-Mail unter [open@kreis-viersen.de](mailto:open@kreis-viersen.de?subject=xplan-umring).

## Installation

Es wird **QGIS mindestens in der Version 3.24.0** benötigt.<br><br>
Das Plugin ist im offiziellen [QGIS-Plugin-Repository] enthalten und kann in QGIS über das Hauptmenü (*Erweiterungen -> Erweiterungen verwalten und installieren*) installiert und auch bei Verfügbarkeit einer neuen Version aktualisiert werden.

Nach der Installation des Plugins kann das gewünschte Werkzeug über einen Auswahldialog nach Klick auf das Toolbar-Icon hinzugefügt werden:

<img src="./screenshots/auswahldialog_xplan-umring.png"/>

Alternativ stehen die Werkzeuge unter **XPlan-Umring** über die QGIS-Werkzeugkiste zur Verfügung:

<img src="./screenshots/werkzeugkiste.png"/>

## Workflow

1. Umring(e) in QGIS digitalisieren oder vorhandene Umring(e) laden (z.B. mit dem QGIS-Plugin [Flurstücksfinder NRW]).<br>Wichtig: Der Eingabelayer muss ein Polygonlayer sein. 
2. Gewünschtes QGIS-Werkzeug unter `XPlan-Umring` ausführen.<br>Eingabelayer ist der Vektorlayer mit dem/den Umring(en), die übrigen Eingaben ensprechend befüllen/auswählen und Speicherort für das XPlan-Archiv festlegen.

<img src="./screenshots/eingabemaske.png"/>

## Anmerkungen

Einige Eingabefelder sind Pflicht. Hierbei handelt es sich **nicht** ausschließlich um Pflichtattribute gemäß der [XPlanung-Spezifikation]. Die Pflichtattribute ergeben sich auch durch die Verwendung der [XPlanBox] im [KRZN]-Gebiet. Die Attribute und Auswahlmöglichkeiten können sich zukunftig noch ändern, wir freuen uns über fachlichen Input :-)

Aktuell stehen für den Bebauungsplan vier Rechtsstände zur Auswahl, wodurch auch bestimmt wird, mit welchem Attribut das Datum angelegt wird:
- Aufstellungsbeschluss -> xplan:aufstellungsbeschlussDatum
- Entwurf / ImVerfahren -> xplan:aenderungenBisDatum
- Satzung -> xplan:satzungsbeschlussDatum
- InkraftGetreten -> xplan:inkrafttretensDatum

<img src="./screenshots/rechtsstand-datum.png"/>
Quelle (bearbeitet): https://xleitstelle.de/downloads/xplanung/releases/XPlanung%20Version%205.3/Objektartenkatalog%20%28PDF%29.pdf

## Klassisches Einsatz-Szenario

<img src="./screenshots/klassisches_einsatz-szenario.png"/>

## XPlan-Reader
QGIS-Plugin zum Import einer XPlanGML-Datei:<br>
https://github.com/kreis-viersen/xplan-reader

[QGIS-Plugin-Repository]: <https://plugins.qgis.org/plugins/xplan-umring/>
[Flurstücksfinder NRW]: <https://github.com/kreis-viersen/flurstuecksfinder-nrw>
[XPlanung-Spezifikation]: <https://xleitstelle.de/xplanung/releases-xplanung>
[KRZN]: <https://www.krzn.de/>
[XPlanBox]: <https://gitlab.opencode.de/diplanung/ozgxplanung>

