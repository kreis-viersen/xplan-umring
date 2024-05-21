"""
***************************************************************************
XPlan-Umring

        begin                : September 2022
        Copyright            : (C) 2022 by Kreis Viersen
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


class XPlanUmringAlgorithmBP60(QgsProcessingAlgorithm):
    def createInstance(self):
        return XPlanUmringAlgorithmBP60()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def name(self):
        return "bebauungsplan60"

    def displayName(self):
        return "Bebauungsplan v6.0"

    def group(self):
        return self.groupId()

    def groupId(self):
        return ""

    def shortHelpString(self):
        return (
            "Umringpolygon(e) eines Bebauungsplans aus QGIS nach XPlanGML konvertieren."
            + "\n\n"
            + "Bebauungsplanumring(e) in QGIS digitalisieren oder vorhandenen(e) Umring(e) laden."
            + "\n\n"
            + "Wichtig: Der Eingabelayer muss ein Polygonlayer sein."
            + "\n\n"
            + "Eingabelayer für das Skript ist der Vektorlayer mit dem/den Bebauungsplanumring(en), die übrigen Skripteingaben ensprechend befüllen/auswählen und Speicherort für das XPlanArchiv festlegen."
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
        return (
            "Umringpolygon(e) eines Bebauungsplans aus QGIS nach XPlanung konvertieren."
        )

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
                defaultValue="Name Bebauungsplan",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Nummer",
                "Nummer [Pflicht]",
                optional=False,
                multiLine=False,
                defaultValue="Nummer Bebaungsplan",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Gemeindename",
                "Gemeindename [Pflicht]",
                optional=False,
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
                "AGS8stelligPflicht",
                "AGS (8-stellig) [Pflicht]",
                optional=False,
                multiLine=False,
                defaultValue=self.ags,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Plangeber",
                "Plangeber",
                optional=True,
                multiLine=False,
                defaultValue="",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "Planart",
                "Planart [Pflicht]",
                options=[
                    "1000 (BPlan)",
                    "10000 (EinfacherBPlan)",
                    "10001 (QualifizierterBPlan)",
                    "3000 (VorhabenbezogenerBPlan)",
                    "4000 (InnenbereichsSatzung)",
                    "40000 (KlarstellungsSatzung)",
                    "40001 (EntwicklungsSatzung)",
                    "40002 (ErgaenzungsSatzung)",
                    "5000 (AussenbereichsSatzung)",
                    "7000 (OertlicheBauvorschrift)",
                    "9999 (Sonstiges)",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=False,
                defaultValue=[0],
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "Rechtsstand",
                "Rechtsstand [Pflicht]",
                options=[
                    "1000 (Aufstellungsbeschluss)",
                    "2000 (ImVerfahren)",
                    "3000 (Satzung)",
                    "4000 (InkraftGetreten)",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=False,
                defaultValue=[0],
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
        ags = self.parameterAsString(parameters, "AGS8stelligPflicht", context).strip()
        plangeber = self.parameterAsString(parameters, "Plangeber", context).strip()

        planart = self.parameterAsInt(parameters, "Planart", context)
        planart_keys = [
            1000,
            10000,
            10001,
            3000,
            4000,
            40000,
            40001,
            40002,
            5000,
            7000,
            9999,
        ]
        planart_key = str(planart_keys[planart])

        rechtsstand = self.parameterAsInt(parameters, "Rechtsstand", context)
        rechtsstand_keys = [1000, 2000, 3000, 4000]
        rechtsstand_key = str(rechtsstand_keys[rechtsstand])

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

        vlayer = QgsProcessingUtils.mapLayerFromString(
            outputs["DoppelteSttzpunkteEntfernen"]["OUTPUT"], context
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
            <xplan:BP_Bereich gml:id="ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f">
              <xplan:nummer>0</xplan:nummer>
              <xplan:name>Basisplan</xplan:name>
              <xplan:gehoertZuPlan xlink:href="#ID_5cad5f10-5fa3-42c8-bff7-22f21cf38e4c"></xplan:gehoertZuPlan>
            </xplan:BP_Bereich>
          </gml:featureMember>
          <gml:featureMember>
            <xplan:BP_Plan gml:id="ID_5cad5f10-5fa3-42c8-bff7-22f21cf38e4c">
              <gml:boundedBy>
                <gml:Envelope srsName="{kbs}">
                  <gml:lowerCorner>-1.36383928571428 -0.5625</gml:lowerCorner>
                  <gml:upperCorner>1.08258928571429 0.839285714285714</gml:upperCorner>
                </gml:Envelope>
              </gml:boundedBy>
              <xplan:name>Name Bebauungsplan</xplan:name>
              <xplan:nummer>Nummer Bebaungsplan</xplan:nummer>
              <xplan:technHerstellDatum>{herstellungsdatum}</xplan:technHerstellDatum>
              <xplan:erstellungsMassstab>{erstellungsmaßstab}</xplan:erstellungsMassstab>
              <xplan:raeumlicherGeltungsbereich>
                {gml_geometry_string}
              </xplan:raeumlicherGeltungsbereich>
              <xplan:gemeinde>
                <xplan:XP_Gemeinde>
                  <xplan:ags>05166032</xplan:ags>
                  <xplan:gemeindeName>Name der Kommune</xplan:gemeindeName>
                  <xplan:ortsteilName>Name der Kommune wenn nichts anderes bekannt</xplan:ortsteilName>
                </xplan:XP_Gemeinde>
              </xplan:gemeinde>
              <xplan:plangeber>
                <xplan:XP_Plangeber>
                  <xplan:name>plangebert</xplan:name>
                </xplan:XP_Plangeber>
              </xplan:plangeber>
              <xplan:planArt>1000</xplan:planArt>
              <xplan:rechtsstand>1000</xplan:rechtsstand>
              <xplan:aenderungenBisDatum></xplan:aenderungenBisDatum>
              <xplan:aufstellungsbeschlussDatum>2022-09-09</xplan:aufstellungsbeschlussDatum>
              <xplan:inkrafttretensDatum></xplan:inkrafttretensDatum>
              <xplan:satzungsbeschlussDatum></xplan:satzungsbeschlussDatum>
              <xplan:bereich xlink:href="#ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f"></xplan:bereich>
            </xplan:BP_Plan>
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

        for bp_bereich_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}BP_Bereich"
        ):
            bp_bereich_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_2

        for bereich_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}bereich"
        ):
            bereich_element.attrib["{http://www.w3.org/1999/xlink}href"] = "#" + uuid_2

        uuid_3 = "ID_" + str(uuid.uuid4())

        for bp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}BP_Plan"
        ):
            bp_plan_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_3

        for gehoertzuplan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}gehoertZuPlan"
        ):
            gehoertzuplan_element.attrib["{http://www.w3.org/1999/xlink}href"] = (
                "#" + uuid_3
            )

        for bp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}BP_Plan"
        ):
            for raeumlicherGeltungsbereich_element in next(
                bp_plan_element.iter("{http://www.xplanung.de/xplangml/6/0}*")
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

        for name_element in root.iter("{http://www.xplanung.de/xplangml/6/0}name"):
            name_element.text = name

        for bp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}BP_Plan"
        ):
            for nummer_element in bp_plan_element.iter(
                "{http://www.xplanung.de/xplangml/6/0}nummer"
            ):
                nummer_element.text = nummer

        for gemeindename_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}gemeindeName"
        ):
            gemeindename_element.text = gemeindename

        ortsteilname_element = next(
            bp_plan_element.iter("{http://www.xplanung.de/xplangml/6/0}ortsteilName")
        )

        if ortsteilname == "":
            for xp_gemeinde_element in root.iter(
                "{http://www.xplanung.de/xplangml/6/0}XP_Gemeinde"
            ):
                xp_gemeinde_element.remove(ortsteilname_element)
        else:
            ortsteilname_element.text = ortsteilname

        for ags_element in root.iter("{http://www.xplanung.de/xplangml/6/0}ags"):
            ags_element.text = ags

        for plangeber_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}plangeber"
        ):
            for name_element in plangeber_element.iter(
                "{http://www.xplanung.de/xplangml/6/0}name"
            ):
                name_element.text = plangeber

        for bp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}BP_Plan"
        ):
            aenderungenBisDatum_element = next(
                bp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}aenderungenBisDatum"
                )
            )
            aufstellungsbeschlussDatum_element = next(
                bp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}aufstellungsbeschlussDatum"
                )
            )
            satzungsbeschlussDatum_element = next(
                bp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}satzungsbeschlussDatum"
                )
            )
            inkrafttretensDatum_element = next(
                bp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}inkrafttretensDatum"
                )
            )
            if len(datum) > 0:
                if rechtsstand_key == "1000":
                    aufstellungsbeschlussDatum_element.text = datum
                    bp_plan_element.remove(aenderungenBisDatum_element)
                    bp_plan_element.remove(inkrafttretensDatum_element)
                    bp_plan_element.remove(satzungsbeschlussDatum_element)
                elif rechtsstand_key == "2000":
                    aenderungenBisDatum_element.text = datum
                    bp_plan_element.remove(aufstellungsbeschlussDatum_element)
                    bp_plan_element.remove(inkrafttretensDatum_element)
                    bp_plan_element.remove(satzungsbeschlussDatum_element)
                elif rechtsstand_key == "3000":
                    satzungsbeschlussDatum_element.text = datum
                    bp_plan_element.remove(aenderungenBisDatum_element)
                    bp_plan_element.remove(aufstellungsbeschlussDatum_element)
                    bp_plan_element.remove(inkrafttretensDatum_element)
                elif rechtsstand_key == "4000":
                    inkrafttretensDatum_element.text = datum
                    bp_plan_element.remove(aenderungenBisDatum_element)
                    bp_plan_element.remove(aufstellungsbeschlussDatum_element)
                    bp_plan_element.remove(satzungsbeschlussDatum_element)
            else:
                bp_plan_element.remove(aufstellungsbeschlussDatum_element)
                bp_plan_element.remove(aenderungenBisDatum_element)
                bp_plan_element.remove(inkrafttretensDatum_element)
                bp_plan_element.remove(satzungsbeschlussDatum_element)

        for planart_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}planArt"
        ):
            planart_element.text = planart_key

        for rechtsstand_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}rechtsstand"
        ):
            rechtsstand_element.text = rechtsstand_key

        for erstellungsmaßstab_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}erstellungsMassstab"
        ):
            if erstellungsmaßstab == "":
                bp_plan_element.remove(erstellungsmaßstab_element)

        for herstellungsdatum_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}technHerstellDatum"
        ):
            if herstellungsdatum == "":
                bp_plan_element.remove(herstellungsdatum_element)

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
        name = re.sub(r"^[\_]+", "", name)
        name = re.sub(r"[\_]+$", "", name)

        zip_name = name + ".zip"
        zip_path = os.path.join(my_output_folder, zip_name)

        with zipfile.ZipFile(zip_path, "w") as myzip:
            with myzip.open("xplan.gml", "w") as myfile:
                tree.write(myfile, encoding="UTF-8", xml_declaration=True)

        return {"XPlan-Archiv wurde erstellt": zip_path}
