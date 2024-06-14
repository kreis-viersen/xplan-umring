"""
***************************************************************************
XPlan-Umring

        begin                : December 2023
        Copyright            : (C) 2023 by Kreis Viersen
        Email                : open@kreis-viersen.de

***************************************************************************

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import processing
import re
import uuid
import zipfile

from lxml import etree

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeatureRequest,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingFeedback,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
    QgsProcessingUtils,
    QgsSettings,
)

from qgis.PyQt.QtXml import QDomDocument

from qgis.utils import iface


class XPlanUmringAlgorithmFP60(QgsProcessingAlgorithm):
    def createInstance(self):
        return XPlanUmringAlgorithmFP60()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def name(self):
        return "flaechennutzungsplan60"

    def displayName(self):
        return "Flächennutzungsplan v6.0"

    def group(self):
        return self.groupId()

    def groupId(self):
        return ""

    def shortHelpString(self):
        return (
            "Umringpolygon(e) eines Flächennutzungsplans aus QGIS nach XPlanGML konvertieren."
            + "\n\n"
            + "Flächennutzungsplanumring(e) in QGIS digitalisieren oder vorhandenen(e) Umring(e) laden."
            + "\n\n"
            + "Wichtig: Der Eingabelayer muss ein Polygonlayer sein."
            + "\n\n"
            + "Eingabelayer für das Skript ist der Vektorlayer mit dem/den Umringen(en), die übrigen Skripteingaben ensprechend befüllen/auswählen und Speicherort für das XPlanArchiv festlegen."
            + "\n\n"
            + "Für die Verwendung in der xPlanBox sind maximal 100 und nur folgende Zeichen für den Plannamen erlaubt: A-Z a-z 0-9 . () _ - ä ü ö Ä Ü Ö ß und Leerzeichen"
            + "\n\n"
            + "Autor: Kreis Viersen"
            + "\n\n"
            + "Kontakt: open@kreis-viersen.de"
            + "\n\n"
            + "GitHub: https://github.com/kreis-viersen/xplan-umring"
        )

    def shortDescription(self):
        return "Umringpolygon(e) eines Flächennutzungsplans aus QGIS nach XPlanung konvertieren."

    def initAlgorithm(self, config=None):
        settings = QgsSettings()
        self.kommune = settings.value("xplan-umring/kommune", "")
        self.ags = settings.value("xplan-umring/ags", "")
        self.ortsteilname = ""
        if self.ags.startswith(("05114", "05154", "05158", "05166", "05170")):
            self.ortsteilname = self.kommune

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Umring",
                "Vektorlayer mit Umringpolygon(en) [Pflicht]",
                optional=False,
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Name",
                "Name [Pflicht]",
                optional=False,
                multiLine=False,
                defaultValue="Name Flächennutzungsplan",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Nummer",
                "Nummer",
                optional=True,
                multiLine=False,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Gemeindename",
                "Gemeindename",
                optional=True,
                multiLine=False,
                defaultValue=self.kommune,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Ortsteilname",
                "Ortsteilname",
                optional=True,
                multiLine=False,
                defaultValue=self.ortsteilname,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "AmtlicherGemeindeschlüssel",
                "Amtlicher Gemeindeschlüssel (AGS)",
                optional=True,
                multiLine=False,
                defaultValue=self.ags,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Beschreibung",
                "Beschreibung",
                optional=True,
                multiLine=False,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Kommentar",
                "Kommentar",
                optional=True,
                multiLine=False,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "Planart",
                "Planart [Pflicht]",
                options=[
                    "1000 (FPlan)",
                    "2000 (Gemeinsamer FPlan)",
                    "3000 (Regionaler FPlan)",
                    "4000 (FPlan und Regionalplan)",
                    "5000 (Sachlicher Teilplan)",
                    "9999 (Sonstiges)",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=True,
                defaultValue="1000 (FPlan)",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "Rechtsstand",
                "Rechtsstand",
                options=[
                    "1000 (Aufstellungsbeschluss)",
                    "2000 (Im Verfahren)",
                    "4000 (Wirksamkeit)",
                    "5000 (Untergegangen)",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=True,
                defaultValue="1000 (Aufstellungsbeschluss)",
            )
        )
        self.addParameter(
            QgsProcessingParameterDateTime(
                "DatumRechtsstand",
                "Datum Rechtsstand",
                optional=True,
                type=QgsProcessingParameterDateTime.Date,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "Koordinatenbezugssystem",
                "Koordinatenbezugssystem (KBS) [Pflicht]",
                options=[
                    "EPSG:25831",
                    "EPSG:25832",
                    "EPSG:25833",
                    "EPSG:5649",
                    "EPSG:4647",
                    "EPSG:5650",
                    "EPSG:5651",
                    "EPSG:5652",
                    "EPSG:5653",
                    "EPSG:31466",
                    "EPSG:31467",
                    "EPSG:31468",
                    "EPSG:31469",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=True,
                defaultValue="EPSG:25832",
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "Erstellungsmaßstab",
                "Erstellungsmaßstab",
                optional=True,
                type=QgsProcessingParameterNumber.Integer,
                minValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterDateTime(
                "DatumHerstellung",
                "Datum technische Herstellung",
                optional=True,
                type=QgsProcessingParameterDateTime.Date,
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                name="outputZip",
                description="Speicherpfad für erzeugtes XPlan-Archiv [Pflicht]",
                behavior=QgsProcessingParameterFile.Folder,
                fileFilter="Alle Dateien (*.*)",
            )
        )

    feedback = QgsProcessingFeedback()

    def processAlgorithm(self, parameters, context, feedback):
        def showWarning(message):
            iface.messageBar().pushMessage(
                message,
                level=Qgis.Warning,
            )
            feedback.pushWarning(message)

        name = self.parameterAsString(parameters, "Name", context).strip()

        chars = re.compile(r"^[A-Za-z0-9.()_\-äüöÄÜÖß\s]*$")
        if not (chars.match(name)):
            message = "XPlan-Umring - Ungültige Zeichen im Plannamen für die Verwendung in der xPlanBox gefunden. Erlaubt sind dort nur: A-Z a-z 0-9 . () _ - ä ü ö Ä Ü Ö ß und Leerzeichen"
            showWarning(message)

        if len(name) > 100:
            message = "XPlan-Umring - Der Planname hat mehr als 100 Zeichen. Dies ist für die Verwendung in der xPlanBox nicht erlaubt."
            showWarning(message)

        nummer = self.parameterAsString(parameters, "Nummer", context).strip()

        gemeindename = self.parameterAsString(
            parameters, "Gemeindename", context
        ).strip()
        ortsteilname = self.parameterAsString(
            parameters, "Ortsteilname", context
        ).strip()
        ags = self.parameterAsString(
            parameters, "AmtlicherGemeindeschlüssel", context
        ).strip()
        beschreibung = self.parameterAsString(
            parameters, "Beschreibung", context
        ).strip()
        kommentar = self.parameterAsString(parameters, "Kommentar", context).strip()

        planart = self.parameterAsString(parameters, "Planart", context)
        planart_key = planart.split()[0]

        rechtsstand = self.parameterAsString(parameters, "Rechtsstand", context)
        rechtsstand_key = rechtsstand.split()[0]

        datum = self.parameterAsString(parameters, "DatumRechtsstand", context).strip()

        kbs = self.parameterAsString(parameters, "Koordinatenbezugssystem", context)

        erstellungsmaßstab = self.parameterAsString(
            parameters, "Erstellungsmaßstab", context
        )

        herstellungsdatum = self.parameterAsString(
            parameters, "DatumHerstellung", context
        ).strip()

        my_output_folder = self.parameterAsString(parameters, "outputZip", context)

        outputs = {}

        # Mehr- zu einteilig
        alg_params = {
            "INPUT": parameters["Umring"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["GeometrienSammeln"] = processing.run(
            "native:collect",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Layer reprojizieren in ausgewähltes KBS
        alg_params = {
            "INPUT": outputs["GeometrienSammeln"]["OUTPUT"],
            "OPERATION": "",
            "TARGET_CRS": QgsCoordinateReferenceSystem(kbs),
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["LayerReprojizierenInKbs"] = processing.run(
            "native:reprojectlayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Geometrie nach Ausdruck force_polygon_ccw
        alg_params = {
            "EXPRESSION": "force_polygon_ccw( $geometry)",
            "INPUT": outputs["LayerReprojizierenInKbs"]["OUTPUT"],
            "OUTPUT_GEOMETRY": 0,  # Polygon
            "WITH_M": False,
            "WITH_Z": False,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["GeometrieNachAusdruck"] = processing.run(
            "native:geometrybyexpression",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Doppelte Stützpunkte entfernen
        alg_params = {
            "INPUT": outputs["GeometrieNachAusdruck"]["OUTPUT"],
            "TOLERANCE": 1e-06,
            "USE_Z_VALUE": False,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["DoppelteSttzpunkteEntfernen"] = processing.run(
            "native:removeduplicatevertices",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Z/M-Werte fallenlassen
        alg_params = {
            "INPUT": outputs["DoppelteSttzpunkteEntfernen"]["OUTPUT"],
            "DROP_M_VALUES": True,
            "DROP_Z_VALUES": True,
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ZmwerteFallenlassen"] = processing.run(
            "native:dropmzvalues",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        vlayer = QgsProcessingUtils.mapLayerFromString(
            outputs["ZmwerteFallenlassen"]["OUTPUT"], context
        )

        request = QgsFeatureRequest()
        request.setLimit(1)
        for feature in vlayer.getFeatures(request):
            doc = QDomDocument()
            gml_geometry = feature.geometry().constGet().asGml3(doc, 6)
            doc.appendChild(gml_geometry)
            gml_geometry_string = (
                doc.toString(2)
                .replace("<", "<gml:")
                .replace("<gml:/", "</gml:")
                .replace('xmlns="gml"', "")
            )

            bbox = feature.geometry().boundingBox()
            lower_corner = str(bbox.xMinimum()) + " " + str(bbox.yMinimum())
            upper_corner = str(bbox.xMaximum()) + " " + str(bbox.yMaximum())

        template = f"""<xplan:XPlanAuszug xmlns:adv="http://www.adv-online.de/nas" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xplan="http://www.xplanung.de/xplangml/6/0" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:wfs="http://www.opengis.net/wfs/2.0" gml:id="GML_707064d8-687a-494c-bb3e-1f9c23af0d50">
          <gml:boundedBy>
            <gml:Envelope srsName="{kbs}">
              <gml:lowerCorner>-1.36383928571428 -0.5625</gml:lowerCorner>
              <gml:upperCorner>1.08258928571429 0.839285714285714</gml:upperCorner>
            </gml:Envelope>
          </gml:boundedBy>
          <gml:featureMember>
            <xplan:FP_Bereich gml:id="ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f">
              <xplan:nummer>0</xplan:nummer>
              <xplan:name>{name}</xplan:name>
              <xplan:gehoertZuPlan xlink:href="#ID_5cad5f10-5fa3-42c8-bff7-22f21cf38e4c"></xplan:gehoertZuPlan>
            </xplan:FP_Bereich>
          </gml:featureMember>
          <gml:featureMember>
            <xplan:FP_Plan gml:id="ID_5cad5f10-5fa3-42c8-bff7-22f21cf38e4c">
              <gml:boundedBy>
                <gml:Envelope srsName="{kbs}">
                  <gml:lowerCorner>-1.36383928571428 -0.5625</gml:lowerCorner>
                  <gml:upperCorner>1.08258928571429 0.839285714285714</gml:upperCorner>
                </gml:Envelope>
              </gml:boundedBy>
              <xplan:name>{name}</xplan:name>
              <xplan:nummer>{nummer}</xplan:nummer>
              <xplan:beschreibung>{beschreibung}</xplan:beschreibung>
              <xplan:kommentar><![CDATA[{kommentar}]]></xplan:kommentar>
              <xplan:untergangsDatum>2022-09-09</xplan:untergangsDatum>
              <xplan:technHerstellDatum>{herstellungsdatum}</xplan:technHerstellDatum>
              <xplan:erstellungsMassstab>{erstellungsmaßstab}</xplan:erstellungsMassstab>
              <xplan:raeumlicherGeltungsbereich>
                {gml_geometry_string}
              </xplan:raeumlicherGeltungsbereich>
              <xplan:gemeinde>
                <xplan:XP_Gemeinde>
                  <xplan:ags>{ags}</xplan:ags>
                  <xplan:gemeindeName>{gemeindename}</xplan:gemeindeName>
                  <xplan:ortsteilName>{ortsteilname}</xplan:ortsteilName>
                </xplan:XP_Gemeinde>
              </xplan:gemeinde>
              <xplan:planArt>{planart_key}</xplan:planArt>
              <xplan:rechtsstand>{rechtsstand_key}</xplan:rechtsstand>
              <xplan:aufstellungsbeschlussDatum>2022-09-09</xplan:aufstellungsbeschlussDatum>
              <xplan:entwurfsbeschlussDatum>2022-09-09</xplan:entwurfsbeschlussDatum>
              <xplan:wirksamkeitsDatum></xplan:wirksamkeitsDatum>
              <xplan:bereich xlink:href="#ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f"></xplan:bereich>
            </xplan:FP_Plan>
          </gml:featureMember>
        </xplan:XPlanAuszug>"""

        tree = etree.ElementTree(etree.fromstring(template))
        root = tree.getroot()

        uuid_1 = "GML_" + str(uuid.uuid4())

        for xplanauszug_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}XPlanAuszug"
        ):
            xplanauszug_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_1

        uuid_2 = "ID_" + str(uuid.uuid4())

        for FP_Bereich_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}FP_Bereich"
        ):
            FP_Bereich_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_2

        for bereich_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}bereich"
        ):
            bereich_element.attrib["{http://www.w3.org/1999/xlink}href"] = "#" + uuid_2

        uuid_3 = "ID_" + str(uuid.uuid4())

        for FP_Plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}FP_Plan"
        ):
            FP_Plan_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_3

        for gehoertzuplan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}gehoertZuPlan"
        ):
            gehoertzuplan_element.attrib["{http://www.w3.org/1999/xlink}href"] = (
                "#" + uuid_3
            )

        for FP_Plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}FP_Plan"
        ):
            for raeumlicherGeltungsbereich_element in next(
                FP_Plan_element.iter("{http://www.xplanung.de/xplangml/6/0}*")
            ):
                for MultiSurface_element in raeumlicherGeltungsbereich_element.iter(
                    "{http://www.opengis.net/gml/3.2}MultiSurface"
                ):
                    MultiSurface_element.attrib[
                        "{http://www.opengis.net/gml/3.2}id"
                    ] = "ID_" + str(uuid.uuid4())
                    MultiSurface_element.attrib["srsName"] = kbs

        for polygon_element in root.iter("{http://www.opengis.net/gml/3.2}Polygon"):
            polygon_element.attrib["{http://www.opengis.net/gml/3.2}id"] = "ID_" + str(
                uuid.uuid4()
            )
            polygon_element.attrib["srsName"] = kbs

        for linestring_element in root.iter(
            "{http://www.opengis.net/gml/3.2}LineString"
        ):
            linestring_element.attrib["{http://www.opengis.net/gml/3.2}id"] = (
                "ID_" + str(uuid.uuid4())
            )
            linestring_element.attrib["srsName"] = kbs

        for curve_element in root.iter("{http://www.opengis.net/gml/3.2}Curve"):
            curve_element.attrib["{http://www.opengis.net/gml/3.2}id"] = "ID_" + str(
                uuid.uuid4()
            )
            curve_element.attrib["srsName"] = kbs

        for lowerCorner_element in root.iter(
            "{http://www.opengis.net/gml/3.2}lowerCorner"
        ):
            lowerCorner_element.text = lower_corner

        for upperCorner_element in root.iter(
            "{http://www.opengis.net/gml/3.2}upperCorner"
        ):
            upperCorner_element.text = upper_corner

        for FP_Plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}FP_Plan"
        ):
            untergangsDatum_element = next(
                FP_Plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}untergangsDatum"
                )
            )
            aufstellungsbeschlussDatum_element = next(
                FP_Plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}aufstellungsbeschlussDatum"
                )
            )
            wirksamkeitsDatum_element = next(
                FP_Plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}wirksamkeitsDatum"
                )
            )
            entwurfsbeschlussDatum_element = next(
                FP_Plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}entwurfsbeschlussDatum"
                )
            )
            if len(datum) > 0:
                if rechtsstand_key == "1000":
                    aufstellungsbeschlussDatum_element.text = datum
                    FP_Plan_element.remove(untergangsDatum_element)
                    FP_Plan_element.remove(wirksamkeitsDatum_element)
                    FP_Plan_element.remove(entwurfsbeschlussDatum_element)
                elif rechtsstand_key == "2000":
                    entwurfsbeschlussDatum_element.text = datum
                    FP_Plan_element.remove(aufstellungsbeschlussDatum_element)
                    FP_Plan_element.remove(wirksamkeitsDatum_element)
                    FP_Plan_element.remove(untergangsDatum_element)
                elif rechtsstand_key == "4000":
                    wirksamkeitsDatum_element.text = datum
                    FP_Plan_element.remove(untergangsDatum_element)
                    FP_Plan_element.remove(aufstellungsbeschlussDatum_element)
                    FP_Plan_element.remove(entwurfsbeschlussDatum_element)
                elif rechtsstand_key == "5000":
                    untergangsDatum_element.text = datum
                    FP_Plan_element.remove(aufstellungsbeschlussDatum_element)
                    FP_Plan_element.remove(wirksamkeitsDatum_element)
                    FP_Plan_element.remove(entwurfsbeschlussDatum_element)
            else:
                FP_Plan_element.remove(untergangsDatum_element)
                FP_Plan_element.remove(aufstellungsbeschlussDatum_element)
                FP_Plan_element.remove(wirksamkeitsDatum_element)
                FP_Plan_element.remove(entwurfsbeschlussDatum_element)

        for erstellungsmaßstab_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}erstellungsMassstab"
        ):
            if erstellungsmaßstab == "":
                FP_Plan_element.remove(erstellungsmaßstab_element)

        for herstellungsdatum_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}technHerstellDatum"
        ):
            if herstellungsdatum == "":
                FP_Plan_element.remove(herstellungsdatum_element)

        etree.indent(tree, space="\t", level=0)

        translation_table = str.maketrans(
            {
                "ä": "ae",
                "Ä": "Ae",
                "ö": "oe",
                "Ö": "Oe",
                "ü": "ue",
                "Ü": "Ue",
                "ß": "ss",
            }
        )

        name = name.translate(translation_table)
        name = re.sub(r"[^a-zA-Z0-9-_]", "_", name)
        name = re.sub("_+", "_", name)

        zip_name = name + ".zip"
        zip_path = os.path.join(my_output_folder, zip_name)

        with zipfile.ZipFile(zip_path, "w") as myzip:
            with myzip.open("xplan.gml", "w") as myfile:
                tree.write(myfile, encoding="UTF-8", xml_declaration=True)

        return {"XPlan-Archiv wurde erstellt": zip_path}
