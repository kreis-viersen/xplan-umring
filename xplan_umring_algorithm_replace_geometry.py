"""
***************************************************************************
XPlan-Umring - Replace Geometry

        begin                : November 2023
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

import processing
import uuid

from lxml import etree

from qgis.core import (
    QgsFeatureRequest,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterVectorLayer,
    QgsProcessingUtils,
)

from qgis.PyQt.QtXml import QDomDocument


class XPlanUmringAlgorithmReplaceGeometry(QgsProcessingAlgorithm):
    def createInstance(self):
        return XPlanUmringAlgorithmReplaceGeometry()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def name(self):
        return "replacegeometry"

    def displayName(self):
        return "Geometrie-Update"

    def group(self):
        return self.groupId()

    def groupId(self):
        return ""

    def shortHelpString(self):
        return (
            "Umringgeometrie (räumlichen Geltungsbereich) einer XPlanGML ersetzen (alle anderen Attribute bleiben erhalten)"
            + "\n\n"
            + "Neuen Geltungsbereich in QGIS digitalisieren oder vorhandenen(e) Umring(e) laden."
            + "\n\n"
            + "Wichtig: Der Eingabelayer muss ein Polygonlayer sein."
            + "\n\n"
            + "Eingabelayer für das Skript ist der Vektorlayer mit dem/den Umring(en)."
            + "\n\n"
            + "Dazu noch die zu verändernde XPlanGML und den Speicherort und Name für die erzeugte XPlanGML festlegen."
            + "\n\n"
            + "Es werden nur XPlan-GML mit maximal einem *_Bereich unterstützt."
            + "\n\n"
            + "Autor: Kreis Viersen"
            + "\n\n"
            + "Kontakt: open@kreis-viersen.de"
            + "\n\n"
            + "GitHub: https://github.com/kreis-viersen/xplan-umring"
        )

    def shortDescription(self):
        return "Umringgeometrie (räumlichen Geltungsbereich) einer XPlanGML ersetzen."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "Umring",
                "Vektorlayer mit Umringpolygon(en)",
                optional=False,
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                "eingabeXplanGml",
                "XPlanGML bei welcher die Umring-Geometrie(en) ersetzt werden sollen",
                behavior=QgsProcessingParameterFile.File,
                fileFilter="GML-Dateien (*.gml *.GML)",
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name="speicherpfad",
                description="Speicherpfad für erzeugte XPlanGML",
                fileFilter="GML-Dateien (*.gml *.GML)",
                createByDefault=False,
            )
        )

    feedback = QgsProcessingFeedback()

    def processAlgorithm(self, parameters, context, feedback):
        input_file = self.parameterAsString(parameters, "eingabeXplanGml", context)
        output_file = self.parameterAsString(parameters, "speicherpfad", context)

        try:
            tree = etree.parse(input_file)
        except:
            raise QgsProcessingException(
                'Datei: "'
                + input_file
                + '" konnte nicht gelesen werden, bitte Datei überprüfen.'
            )

        gml_root = tree.getroot()

        try:
            xplan_ns_uri = gml_root.nsmap["xplan"]
        except:
            try:
                xplan_ns_uri = gml_root.nsmap[None]
            except:
                raise QgsProcessingException(
                    'Datei: "'
                    + input_file
                    + '": XPlanung-Namespace konnte nicht gefunden werden, bitte Datei überprüfen.'
                )

        xplan_version = xplan_ns_uri.split("http://www.xplanung.de/xplangml/")[
            1
        ].replace("/", ".")
        feedback.pushInfo("XPlanung Version: " + xplan_version)

        plan_category = None
        plan_category_short = None
        plan_element = None
        bereich_element = None
        raeumlicherGeltungsbereich_element = None
        kbs = None

        for elem in ("BP_Plan", "FP_Plan", "LP_Plan", "RP_Plan", "SO_Plan"):
            try:
                if next(gml_root.iter("{" + xplan_ns_uri + "}" + elem)).tag:
                    plan_category = elem
                    plan_category_short = plan_category.split("_")[0]
                    feedback.pushInfo("Plankategorie: " + plan_category)
                    plan_element = next(
                        gml_root.iter("{" + xplan_ns_uri + "}" + plan_category)
                    )
                    break
            except:
                raise QgsProcessingException(
                    "Kein *_Plan gefunden, dies wird nicht unterstützt!"
                )

        bereich_count = 0
        try:
            for bereich_element in gml_root.iter(
                "{" + xplan_ns_uri + "}" + plan_category_short + "_Bereich"
            ):
                bereich_count += 1
        except:
            raise QgsProcessingException(
                "Fehler beim ermitteln der Anzahl von "
                + plan_category_short
                + "_Bereich"
            )

        feedback.pushInfo(
            "Anzahl " + plan_category_short + "_Bereich: " + str(bereich_count)
        )
        if bereich_count > 1:
            raise QgsProcessingException(
                "Mehr als 1 Bereich gefunden, dies wird nicht unterstützt!"
            )

        try:
            raeumlicherGeltungsbereich_element = next(
                plan_element.iter("{" + xplan_ns_uri + "}raeumlicherGeltungsbereich")
            )
            if len(raeumlicherGeltungsbereich_element.text) > 0:
                pass
        except:
            raise QgsProcessingException(
                elem
                + " hat keinen räumlichen Geltungsbereich, dies wird nicht unterstützt!"
            )

        try:
            first_element = next(
                raeumlicherGeltungsbereich_element.iter(
                    "{http://www.opengis.net/gml/3.2}*"
                )
            )
            kbs = first_element.attrib["srsName"]
            feedback.pushInfo("KBS der Eingabe-XPlanGML: " + kbs)
        except:
            raise QgsProcessingException(
                "Der räumliche Geltungsbereich von "
                + plan_category
                + "hat kein srsName-Attribut, dies wird nicht unterstützt!"
            )

        outputs = {}

        # Zu erhaltende Felder
        alg_params = {
            "FIELDS": [""],
            "INPUT": parameters["Umring"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["ZuErhaltendeFelder"] = processing.run(
            "native:retainfields",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Mehr- zu einteilig
        alg_params = {
            "INPUT": outputs["ZuErhaltendeFelder"]["OUTPUT"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["GeometrienSammeln"] = processing.run(
            "native:collect",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        # Layer reprojizieren in KBS der Eingabe XPlan-GML
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
                .replace('xmlns="gml"', 'xmlns:gml="http://www.opengis.net/gml/3.2"')
            )

            bbox = feature.geometry().boundingBox()
            lower_corner = str(bbox.xMinimum()) + " " + str(bbox.yMinimum())
            upper_corner = str(bbox.xMaximum()) + " " + str(bbox.yMaximum())

        def updateBoundedBy():
            for envelope_element in boundedby_element.iter(
                "{http://www.opengis.net/gml/3.2}Envelope"
            ):
                envelope_element.attrib["srsName"] = kbs
            for lowerCorner_element in boundedby_element.iter(
                "{http://www.opengis.net/gml/3.2}lowerCorner"
            ):
                lowerCorner_element.text = lower_corner

            for upperCorner_element in boundedby_element.iter(
                "{http://www.opengis.net/gml/3.2}upperCorner"
            ):
                upperCorner_element.text = upper_corner

        try:
            for boundedby_element in gml_root.iterchildren(
                "{http://www.opengis.net/gml/3.2}boundedBy"
            ):
                updateBoundedBy()
        except:
            raise QgsProcessingException("Fehler beim Update des boundedBy-Elements!")

        try:
            for boundedby_element in plan_element.iterchildren(
                "{http://www.opengis.net/gml/3.2}boundedBy"
            ):
                updateBoundedBy()
        except:
            raise QgsProcessingException(
                "Fehler beim Update des boundedBy-Elements von " + plan_category + " !"
            )

        new_geltungsbereich_element = etree.Element(
            "{" + xplan_ns_uri + "}raeumlicherGeltungsbereich"
        )

        new_geltungsbereich_element.append(etree.fromstring(gml_geometry_string))

        for MultiSurface_element in new_geltungsbereich_element.iter(
            "{http://www.opengis.net/gml/3.2}MultiSurface"
        ):
            MultiSurface_element.attrib["{http://www.opengis.net/gml/3.2}id"] = (
                "ID_" + str(uuid.uuid4())
            )
            MultiSurface_element.attrib["srsName"] = kbs

        for polygon_element in new_geltungsbereich_element.iter(
            "{http://www.opengis.net/gml/3.2}Polygon"
        ):
            polygon_element.attrib["{http://www.opengis.net/gml/3.2}id"] = "ID_" + str(
                uuid.uuid4()
            )
            polygon_element.attrib["srsName"] = kbs

        for linestring_element in new_geltungsbereich_element.iter(
            "{http://www.opengis.net/gml/3.2}LineString"
        ):
            linestring_element.attrib["{http://www.opengis.net/gml/3.2}id"] = (
                "ID_" + str(uuid.uuid4())
            )
            linestring_element.attrib["srsName"] = kbs

        for curve_element in new_geltungsbereich_element.iter(
            "{http://www.opengis.net/gml/3.2}Curve"
        ):
            curve_element.attrib["{http://www.opengis.net/gml/3.2}id"] = "ID_" + str(
                uuid.uuid4()
            )
            curve_element.attrib["srsName"] = kbs

        raeumlicherGeltungsbereich_element.getparent().replace(
            raeumlicherGeltungsbereich_element, new_geltungsbereich_element
        )

        try:
            geltungsbereich_element_bereich = next(
                bereich_element.iter("{" + xplan_ns_uri + "}geltungsbereich")
            )
            geltungsbereich_element_bereich.getparent().remove(
                geltungsbereich_element_bereich
            )
        except:
            pass
        try:
            boundedby_element_bereich = next(
                bereich_element.iterchildren(
                    "{http://www.opengis.net/gml/3.2}boundedBy"
                )
            )
            boundedby_element_bereich.getparent().remove(boundedby_element_bereich)
        except:
            pass

        etree.indent(gml_root, space="\t", level=0)

        etree.ElementTree(gml_root).write(
            output_file, encoding="UTF-8", xml_declaration=True
        )

        return {"XPlanGML mit neuem Geltungsbereich wurde erstellt": output_file}
