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
    QgsFeatureRequest,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
    QgsProcessingUtils,
)

from qgis.PyQt.QtXml import QDomDocument


class XPlanUmringAlgorithmLP60(QgsProcessingAlgorithm):
    def createInstance(self):
        return XPlanUmringAlgorithmLP60()

    def name(self):
        return "landschaftsplan60"

    def displayName(self):
        return "Landschaftsplan v6.0"

    def group(self):
        return self.groupId()

    def groupId(self):
        return ""

    def shortHelpString(self):
        return (
            "Umringpolygon(e) eines Landschaftsplans aus QGIS nach XPlanGML konvertieren."
            + "\n\n"
            + "Landschaftsplanumring(e) in QGIS digitalisieren oder vorhandenen(e) Umring(e) laden."
            + "\n\n"
            + "Wichtig: Der Eingabelayer muss ein Polygonlayer sein."
            + "\n\n"
            + "Eingabelayer für das Skript ist der Vektorlayer mit dem/den Landschaftsplan(en), die übrigen Skripteingaben ensprechend befüllen/auswählen und Speicherort für das XPlanArchiv festlegen."
            + "\n\n"
            + "Autor: Kreis Viersen"
            + "\n\n"
            + "Kontakt: open@kreis-viersen.de"
            + "\n\n"
            + "GitHub: https://github.com/kreis-viersen/xplan-umring"
        )

    def shortDescription(self):
        return "Umringpolygon(e) eines Landschaftsplans aus QGIS nach XPlanung konvertieren."

    def initAlgorithm(self, config=None):
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
                defaultValue="Name Landschaftsplan",
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
            QgsProcessingParameterEnum(
                "Bundesland",
                "Bundesland [Pflicht]",
                options=[
                    "1000 (Brandenburg)",
                    "1100 (Berlin)",
                    "1200 (Baden-Württemberg)",
                    "1300 (Bayern)",
                    "1400 (Bremen)",
                    "1500 (Hessen)",
                    "1600 (Hamburg)",
                    "1700 (Mecklenburg-Vorpommern)",
                    "1800 (Niedersachsen)",
                    "1900 (Nordrhein-Westfalen)",
                    "2000 (Rheinland-Pfalz)",
                    "2100 (Schleswig-Holstein)",
                    "2200 (Saarland)",
                    "2300 (Sachsen)",
                    "2400 (Sachsen-Anhalt)",
                    "2500 (Thüringen)",
                    "3000 (Der Bund.)",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=True,
                defaultValue="1900 (Nordrhein-Westfalen)",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Gemeindename",
                "Gemeindename",
                optional=True,
                multiLine=False,
                defaultValue="",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Ortsteilname",
                "Ortsteilname",
                optional=True,
                multiLine=False,
                defaultValue="",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "AmtlicherGemeindeschlüssel",
                "Amtlicher Gemeindeschlüssel (AGS)",
                optional=True,
                multiLine=False,
                defaultValue="",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "Plangeber",
                "Plangeber",
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
                    "1000 (Landschaftsprogramm)",
                    "2000 (Landschaftsrahmenplan)",
                    "3000 (Landschaftsplan)",
                    "4000 (Gruenordnungsplan)",
                    "9999 (Sonstiges)",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=True,
                defaultValue="3000 (Landschaftsplan)",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "RechtlicheAussenwirkung",
                "Rechtliche Außenwirkung [Pflicht]",
                options=[
                    "ja",
                    "nein",
                ],
                optional=False,
                allowMultiple=False,
                usesStaticStrings=False,
                defaultValue="ja",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "Rechtsstand",
                "Rechtsstand",
                options=[
                    "1000 (Aufstellungsbeschluss)",
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
            QgsProcessingParameterFile(
                name="outputZip",
                description="Speicherpfad für erzeugtes XPlan-Archiv [Pflicht]",
                behavior=QgsProcessingParameterFile.Folder,
                fileFilter="Alle Dateien (*.*)",
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        name = self.parameterAsString(parameters, "Name", context).strip()
        nummer = self.parameterAsString(parameters, "Nummer", context).strip()

        bundesland = self.parameterAsString(parameters, "Bundesland", context)
        bundesland_key = bundesland.split()[0]

        print(bundesland_key)

        gemeindename = self.parameterAsString(
            parameters, "Gemeindename", context
        ).strip()
        ortsteilname = self.parameterAsString(
            parameters, "Ortsteilname", context
        ).strip()
        ags = self.parameterAsString(
            parameters, "AmtlicherGemeindeschlüssel", context
        ).strip()
        plangeber = self.parameterAsString(parameters, "Plangeber", context).strip()

        planart = self.parameterAsString(parameters, "Planart", context)
        planart_key = planart.split()[0]

        rechtliche_aussenwirkung = self.parameterAsInt(
            parameters, "RechtlicheAussenwirkung", context
        )
        rechtliche_aussenwirkung_keys = [
            "true",
            "false",
        ]
        rechtliche_aussenwirkung_key = str(
            rechtliche_aussenwirkung_keys[rechtliche_aussenwirkung]
        )

        rechtsstand = self.parameterAsString(parameters, "Rechtsstand", context)
        rechtsstand_key = rechtsstand.split()[0]

        datum = self.parameterAsString(parameters, "DatumRechtsstand", context).strip()

        kbs = self.parameterAsString(parameters, "Koordinatenbezugssystem", context)

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
            <xplan:LP_Bereich gml:id="ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f">
              <xplan:nummer>0</xplan:nummer>
              <xplan:name>Basisplan</xplan:name>
              <xplan:gehoertZuPlan xlink:href="#ID_5cad5f10-5fa3-42c8-bff7-22f21cf38e4c"></xplan:gehoertZuPlan>
            </xplan:LP_Bereich>
          </gml:featureMember>
          <gml:featureMember>
            <xplan:LP_Plan gml:id="ID_5cad5f10-5fa3-42c8-bff7-22f21cf38e4c">
              <gml:boundedBy>
                <gml:Envelope srsName="{kbs}">
                  <gml:lowerCorner>-1.36383928571428 -0.5625</gml:lowerCorner>
                  <gml:upperCorner>1.08258928571429 0.839285714285714</gml:upperCorner>
                </gml:Envelope>
              </gml:boundedBy>
              <xplan:name>Name Bebauungsplan</xplan:name>
              <xplan:nummer>Nummer Bebaungsplan</xplan:nummer>
              <xplan:untergangsDatum></xplan:untergangsDatum>
              <xplan:raeumlicherGeltungsbereich>
                {gml_geometry_string}
              </xplan:raeumlicherGeltungsbereich>
              <xplan:bundesland>{bundesland_key}</xplan:bundesland>	   
              <xplan:rechtlicheAussenwirkung>{rechtliche_aussenwirkung_key}</xplan:rechtlicheAussenwirkung>
              <xplan:planArt>{planart_key}</xplan:planArt>
              <xplan:gemeinde>
                <xplan:XP_Gemeinde>
                  <xplan:ags>05166032</xplan:ags>
                  <xplan:gemeindeName>Name der Kommune(n)</xplan:gemeindeName>
                  <xplan:ortsteilName>Name der Kommune(n) wenn nichts anderes bekannt</xplan:ortsteilName>
                </xplan:XP_Gemeinde>
              </xplan:gemeinde>
              <xplan:plangeber>
                <xplan:XP_Plangeber>
                  <xplan:name>plangebert</xplan:name>
                </xplan:XP_Plangeber>
              </xplan:plangeber>
              <xplan:rechtsstand>{rechtsstand_key}</xplan:rechtsstand>
              <xplan:aufstellungsbeschlussDatum>2022-09-09</xplan:aufstellungsbeschlussDatum>
              <xplan:inkrafttretenDatum></xplan:inkrafttretenDatum>
              <xplan:bereich xlink:href="#ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f"></xplan:bereich>
            </xplan:LP_Plan>
          </gml:featureMember>
        </xplan:XPlanAuszug>"""

        print(rechtsstand_key)

        tree = etree.ElementTree(etree.fromstring(template))
        root = tree.getroot()

        uuid_1 = "GML_" + str(uuid.uuid4())

        for xplanauszug_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}XPlanAuszug"
        ):
            xplanauszug_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_1

        uuid_2 = "ID_" + str(uuid.uuid4())

        for LP_Bereich_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}LP_Bereich"
        ):
            LP_Bereich_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_2

        for bereich_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}bereich"
        ):
            bereich_element.attrib["{http://www.w3.org/1999/xlink}href"] = "#" + uuid_2

        uuid_3 = "ID_" + str(uuid.uuid4())

        for lp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}LP_Plan"
        ):
            lp_plan_element.attrib["{http://www.opengis.net/gml/3.2}id"] = uuid_3

        for gehoertzuplan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}gehoertZuPlan"
        ):
            gehoertzuplan_element.attrib["{http://www.w3.org/1999/xlink}href"] = (
                "#" + uuid_3
            )

        for lp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}LP_Plan"
        ):
            for raeumlicherGeltungsbereich_element in next(
                lp_plan_element.iter("{http://www.xplanung.de/xplangml/6/0}*")
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

        for lp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}LP_Plan"
        ):
            for nummer_element in lp_plan_element.iter(
                "{http://www.xplanung.de/xplangml/6/0}nummer"
            ):
                nummer_element.text = nummer

        for gemeindename_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}gemeindeName"
        ):
            gemeindename_element.text = gemeindename

        for ortsteilname_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}ortsteilName"
        ):
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

        for lp_plan_element in root.iter(
            "{http://www.xplanung.de/xplangml/6/0}LP_Plan"
        ):
            untergangsDatum_element = next(
                lp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}untergangsDatum"
                )
            )
            aufstellungsbeschlussDatum_element = next(
                lp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}aufstellungsbeschlussDatum"
                )
            )
            inkrafttretenDatum_element = next(
                lp_plan_element.iter(
                    "{http://www.xplanung.de/xplangml/6/0}inkrafttretenDatum"
                )
            )
            if len(datum) > 0:
                if rechtsstand_key == "1000":
                    aufstellungsbeschlussDatum_element.text = datum
                    lp_plan_element.remove(untergangsDatum_element)
                    lp_plan_element.remove(inkrafttretenDatum_element)
                elif rechtsstand_key == "4000":
                    inkrafttretenDatum_element.text = datum
                    lp_plan_element.remove(untergangsDatum_element)
                    lp_plan_element.remove(aufstellungsbeschlussDatum_element)
                elif rechtsstand_key == "5000":
                    untergangsDatum_element.text = datum
                    lp_plan_element.remove(aufstellungsbeschlussDatum_element)
                    lp_plan_element.remove(inkrafttretenDatum_element)
            else:
                lp_plan_element.remove(aufstellungsbeschlussDatum_element)
                lp_plan_element.remove(untergangsDatum_element)
                lp_plan_element.remove(inkrafttretenDatum_element)

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
