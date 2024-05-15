"""
***************************************************************************
XPlan-Umring - Difference Raster

        begin                : April 2024
        Copyright            : (C) 2024 by Kreis Viersen
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

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingFeedback,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
)


class XPlanUmringAlgorithmDifferenceRaster(QgsProcessingAlgorithm):
    def createInstance(self):
        return XPlanUmringAlgorithmDifferenceRaster()

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def name(self):
        return "differenceraster"

    def displayName(self):
        return "Polygon von Rasterplan abziehen"

    def group(self):
        return self.groupId()

    def groupId(self):
        return ""

    def shortHelpString(self):
        return (
            "Polygon von Rasterplan abziehen"
            + "\n\n"
            + "Eingabelayer für das Skript sind:"
            + "\n"
            + "1. Rasterlayer mit dem Plan, von welchem die Fläche des Polygons abgezogen werden soll."
            + "\n"
            + "2. Vektorlayer mit dem Polygon, welches zum Abziehen verwendet werden soll."
            + "\n"
            + "Wichtig: Der Vektorlayer muss ein Polygonlayer sein."
            + "\n"
            + "3. Optional kann die Farbe auf Farbpalettenindex 0 als Leerwert gesetzt werden. "
            + "\n"
            + "Für die Verwendung des Rasterplans in der KRZN-XPlanBox sollte dies die Regel und "
            + "die Farbe auf Index 0 'Reinweiß' RGB(255,255,255) sein."
            + "\n\n"
            + "Dazu den Speicherort und Name für den erzeugten Rasterplan festlegen."
            + "\n\n"
            + "Autor: Kreis Viersen"
            + "\n\n"
            + "Kontakt: open@kreis-viersen.de"
            + "\n\n"
            + "GitHub: https://github.com/kreis-viersen/xplan-umring"
        )

    def shortDescription(self):
        return "Polygon von Rasterplan abziehen"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "alter_plan_raster", "Alter Plan (Raster)", defaultValue=None
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "polygon_zum_abziehen",
                "Polygon zum Abziehen (Vektor)",
                optional=False,
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                "no_data",
                "Farbpalettenindex 0 als Leerwert setzen",
                optional=True,
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                "ErzeugterRasterplan",
                "erzeugter Rasterplan",
                createByDefault=True,
                defaultValue=None,
            )
        )

    feedback = QgsProcessingFeedback()

    def processAlgorithm(self, parameters, context, feedback):
        feedback = QgsProcessingMultiStepFeedback(4, feedback)
        results = {}
        outputs = {}

        no_data = self.parameterAsBool(parameters, "no_data", context)

        palett_index = None
        if no_data:
            palett_index = 0

        # Layer aus Ausdehnung erzeugen
        alg_params = {
            "INPUT": parameters["alter_plan_raster"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["LayerAusAusdehnungErzeugen"] = processing.run(
            "native:extenttolayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Durch maximalen Abstand segmentieren
        alg_params = {
            "DISTANCE": 0.01,
            "INPUT": parameters["polygon_zum_abziehen"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["DurchMaximalenAbstandSegmentieren"] = processing.run(
            "native:segmentizebymaxdistance",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Differenz
        alg_params = {
            "GRID_SIZE": None,
            "INPUT": outputs["LayerAusAusdehnungErzeugen"]["OUTPUT"],
            "OVERLAY": outputs["DurchMaximalenAbstandSegmentieren"]["OUTPUT"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        }
        outputs["Differenz"] = processing.run(
            "native:difference",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Raster auf Layermaske zuschneiden
        alg_params = {
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "DATA_TYPE": 0,  # Eingabelayerdatentyp verwenden
            "EXTRA": "",
            "INPUT": parameters["alter_plan_raster"],
            "KEEP_RESOLUTION": False,
            "MASK": outputs["Differenz"]["OUTPUT"],
            "MULTITHREADING": False,
            "NODATA": palett_index,
            "OPTIONS": "COMPRESS=DEFLATE",
            "SET_RESOLUTION": False,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "TARGET_EXTENT": None,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "OUTPUT": parameters["ErzeugterRasterplan"],
        }
        outputs["RasterAufLayermaskeZuschneiden"] = processing.run(
            "gdal:cliprasterbymasklayer",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )
        results["ErzeugterRasterplan"] = outputs[
            "RasterAufLayermaskeZuschneiden"
        ]["OUTPUT"]
        return results
