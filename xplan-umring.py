                                    # -*- coding: utf-8 -*-

"""
***************************************************************************
XPlan-Umring
QGIS-Script

        Date                 : September 2022
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
import zipfile

from lxml import etree

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterDateTime,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingUtils)

import uuid

class xplanUmring(QgsProcessingAlgorithm):

    def createInstance(self):
        return xplanUmring()

    def name(self):
        return 'xplanUmring'

    def displayName(self):
        return 'XPlan-Umring v1.0-beta'

    def group(self):
        return self.groupId()

    def shortHelpString(self):
        return "Umringpolygon eines Bebauungsplans aus QGIS nach XPlanGML konvertieren." + '\n'\
        + '\n' + "Bebauungsplanumring in QGIS digitalisieren oder vorhandenen Umring laden." + '\n'\
        + '\n' + "Wichtig: Der Vektorlayer darf nur ein Objekt (= den Umring) vom Typ Polygon beinhalten." + '\n'\
        + '\n' + "Eingabelayer für das Skript ist der Vektorlayer mit dem Bebauungsplanumring, die übrigen Skripteingaben ensprechend befüllen/auswählen und Speicherort für das XPlanArchiv festlegen." + '\n'\
        + '\n' + "Autor: Kreis Viersen" + '\n'\
        + '\n' + "Kontakt: open@kreis-viersen.de" + '\n'\
        + '\n' + "GitHub: https://github.com/kreis-viersen/umringpolygon-zu-xplanung"

    def shortDescription(self):
        return "Umringpolygon eines Bebauungsplans aus QGIS nach XPlanung konvertieren."

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterVectorLayer('BPlanUmriss', 'Vektorlayer mit Umringpolygon [Pflicht]', optional=False, types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('Name', 'Name [Pflicht]', optional=False, multiLine=False, defaultValue='Name Bebauungsplan'))
        self.addParameter(QgsProcessingParameterString('Nummer', 'Nummer [Pflicht]', optional=False, multiLine=False, defaultValue='Nummer Bebaungsplan'))
        self.addParameter(QgsProcessingParameterString('Gemeindename', 'Gemeindename [Pflicht]', optional=False, multiLine=False, defaultValue='Name der Kommune'))
        self.addParameter(QgsProcessingParameterString('Ortsteilname', 'Ortsteilname [Pflicht]', optional=False, multiLine=False, defaultValue='Name der Kommune wenn nichts anderes bekannt'))
        self.addParameter(QgsProcessingParameterString('AGS8stelligPflicht', 'AGS (8-stellig) [Pflicht]', optional=False, multiLine=False, defaultValue='05166032'))
        self.addParameter(QgsProcessingParameterString('Plangeber', 'Plangeber', optional=True, multiLine=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterEnum('Planart', 'Planart [Pflicht]', options=['1000 (BPlan)','10000 (EinfacherBPlan)','10001 (QualifizierterBPlan)','3000 (VorhabenbezogenerBPlan)','4000 (InnenbereichsSatzung)','40000 (KlarstellungsSatzung)','40001 (EntwicklungsSatzung)','40002 (ErgaenzungsSatzung)','5000 (AussenbereichsSatzung)','7000 (OertlicheBauvorschrift)','9999 (Sonstiges)'], optional=False, allowMultiple=False, usesStaticStrings=False, defaultValue=[0]))
        self.addParameter(QgsProcessingParameterEnum('Rechtsstand', 'Rechtsstand [Pflicht]', options=['1000 (Aufstellungsbeschluss)','3000 (Satzung)','4000 (InkraftGetreten)'], optional=False, allowMultiple=False, usesStaticStrings=False, defaultValue=[0]))
        self.addParameter(QgsProcessingParameterDateTime('DatumAufstellungsbeschluss', 'Datum Rechtsstand [Pflicht]', optional=False, type=QgsProcessingParameterDateTime.Date, defaultValue=None))
        self.addParameter(QgsProcessingParameterFile(name="outputZip", description="Speicherpfad für erzeugtes XPlan-Archiv [Pflicht]", behavior=QgsProcessingParameterFile.Folder, fileFilter='Alle Dateien (*.*)'))

    def processAlgorithm(self, parameters, context, feedback):

        name = self.parameterAsString(parameters,'Name',context).strip()
        nummer = self.parameterAsString(parameters,'Nummer',context).strip()
        gemeindename = self.parameterAsString(parameters,'Gemeindename',context).strip()
        ortsteilname = self.parameterAsString(parameters,'Ortsteilname',context).strip()
        ags = self.parameterAsString(parameters,'AGS8stelligPflicht',context).strip()
        plangeber = self.parameterAsString(parameters,'Plangeber',context).strip()

        planart = self.parameterAsInt(parameters,'Planart',context)
        planart_keys = [1000, 10000, 10001, 3000, 4000, 40000, 40001, 40002, 5000, 7000, 9999]
        planart_key = str(planart_keys[planart])

        rechtsstand = self.parameterAsInt(parameters,'Rechtsstand',context)
        rechtsstand_keys = [1000, 3000, 4000]
        rechtsstand_key = str(rechtsstand_keys[rechtsstand])

        datum = self.parameterAsString(parameters,'DatumAufstellungsbeschluss',context).strip()

        my_output_folder = self.parameterAsString(parameters,'outputZip',context)

        outputs = {}

        # Mehr- zu einteilig
        alg_params = {
            'INPUT': parameters['BPlanUmriss'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MehrZuEinteilig'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Layer reprojizieren in EPSG 25832
        alg_params = {
            'INPUT': outputs['MehrZuEinteilig']['OUTPUT'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:25832'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LayerReprojizierenInEpsg25832'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Geometrie nach Ausdruck force_polygon_ccw
        alg_params = {
            'EXPRESSION': 'force_polygon_ccw( $geometry)',
            'INPUT': outputs['LayerReprojizierenInEpsg25832']['OUTPUT'],
            'OUTPUT_GEOMETRY': 0,  # Polygon
            'WITH_M': False,
            'WITH_Z': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GeometrieNachAusdruck'] = processing.run('native:geometrybyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Doppelte Stützpunkte entfernen
        alg_params = {
            'INPUT': outputs['GeometrieNachAusdruck']['OUTPUT'],
            'TOLERANCE': 1e-06,
            'USE_Z_VALUE': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DoppelteSttzpunkteEntfernen'] = processing.run('native:removeduplicatevertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        vlayer = QgsProcessingUtils.mapLayerFromString(outputs['DoppelteSttzpunkteEntfernen']['OUTPUT'], context)

        for feature in vlayer.getFeatures():
            wkt_geometry = feature.geometry().asWkt()

            coords = wkt_geometry.split("((")[1].split("))")[0].replace(",", "")

            bbox = feature.geometry().boundingBox()
            lower_corner = str(bbox.xMinimum()) + " " +  str(bbox.yMinimum())
            upper_corner = str(bbox.xMaximum()) + " " +  str(bbox.yMaximum())

        template = '''<xplan:XPlanAuszug xmlns:adv="http://www.adv-online.de/nas" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xplan="http://www.xplanung.de/xplangml/5/4" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:wfs="http://www.opengis.net/wfs/2.0" gml:id="GML_707064d8-687a-494c-bb3e-1f9c23af0d50">
          <gml:boundedBy>
            <gml:Envelope srsName="EPSG:25832">
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
                <gml:Envelope srsName="EPSG:25832">
                  <gml:lowerCorner>-1.36383928571428 -0.5625</gml:lowerCorner>
                  <gml:upperCorner>1.08258928571429 0.839285714285714</gml:upperCorner>
                </gml:Envelope>
              </gml:boundedBy>
              <xplan:name>Name Bebauungsplan</xplan:name>
              <xplan:nummer>Nummer Bebaungsplan</xplan:nummer>
              <xplan:raeumlicherGeltungsbereich>
                <gml:Polygon srsName="EPSG:25832" gml:id="ID_a7faf948-6db3-4dac-8f32-0e9ae0720611">
                  <gml:exterior>
                    <gml:LinearRing>
                      <gml:posList srsDimension="2">-1.36383928571428 0.25 -0.560267857142857 -0.5625 1.08258928571429 -0.151785714285714 0.037946428571429 0.839285714285714 -1.36383928571428 0.25</gml:posList>
                    </gml:LinearRing>
                  </gml:exterior>
                </gml:Polygon>
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
              <xplan:aufstellungsbeschlussDatum>2022-09-09</xplan:aufstellungsbeschlussDatum>
              <xplan:inkrafttretensDatum></xplan:inkrafttretensDatum>
              <xplan:satzungsbeschlussDatum></xplan:satzungsbeschlussDatum>
              <xplan:bereich xlink:href="#ID_f92ead39-7f9e-47f0-bfad-498ef2cb0d9f"></xplan:bereich>
            </xplan:BP_Plan>
          </gml:featureMember>
        </xplan:XPlanAuszug>'''

        tree = etree.ElementTree(etree.fromstring(template))
        root = tree.getroot()

        uuid_1 = "GML_" + str(uuid.uuid4())

        for xplanauszug_element in root.iter('{http://www.xplanung.de/xplangml/5/4}XPlanAuszug'):
            xplanauszug_element.attrib['{http://www.opengis.net/gml/3.2}id'] = uuid_1

        uuid_2 = "ID_" + str(uuid.uuid4())

        for bp_bereich_element in root.iter('{http://www.xplanung.de/xplangml/5/4}BP_Bereich'):
            bp_bereich_element.attrib['{http://www.opengis.net/gml/3.2}id'] = uuid_2

        for bereich_element in root.iter('{http://www.xplanung.de/xplangml/5/4}bereich'):
            bereich_element.attrib['{http://www.w3.org/1999/xlink}href'] = '#' + uuid_2

        uuid_3 = "ID_" + str(uuid.uuid4())

        for bp_plan_element in root.iter('{http://www.xplanung.de/xplangml/5/4}BP_Plan'):
            bp_plan_element.attrib['{http://www.opengis.net/gml/3.2}id'] = uuid_3


        for gehoertzuplan_element in root.iter('{http://www.xplanung.de/xplangml/5/4}gehoertZuPlan'):
            gehoertzuplan_element.attrib['{http://www.w3.org/1999/xlink}href'] = '#' + uuid_3

        uuid_4 = "ID_" + str(uuid.uuid4())

        for polygon_element in root.iter('{http://www.opengis.net/gml/3.2}Polygon'):
            polygon_element.attrib['{http://www.opengis.net/gml/3.2}id'] = uuid_4

        for pos_list_element in root.iter('{http://www.opengis.net/gml/3.2}posList'):
            pos_list_element.text = coords

        for lowerCorner_element in root.iter('{http://www.opengis.net/gml/3.2}lowerCorner'):
            lowerCorner_element.text = lower_corner

        for upperCorner_element in root.iter('{http://www.opengis.net/gml/3.2}upperCorner'):
            upperCorner_element.text = upper_corner

        for name_element in root.iter('{http://www.xplanung.de/xplangml/5/4}name'):
            name_element.text = name

        for bp_plan_element in root.iter('{http://www.xplanung.de/xplangml/5/4}BP_Plan'):
            for nummer_element in bp_plan_element.iter('{http://www.xplanung.de/xplangml/5/4}nummer'):
                nummer_element.text = nummer

        for gemeindename_element in root.iter('{http://www.xplanung.de/xplangml/5/4}gemeindeName'):
            gemeindename_element.text = gemeindename

        for ortsteilname_element in root.iter('{http://www.xplanung.de/xplangml/5/4}ortsteilName'):
            ortsteilname_element.text = ortsteilname

        for ags_element in root.iter('{http://www.xplanung.de/xplangml/5/4}ags'):
            ags_element.text = ags

        for plangeber_element in root.iter('{http://www.xplanung.de/xplangml/5/4}plangeber'):
            for name_element in plangeber_element.iter('{http://www.xplanung.de/xplangml/5/4}name'):
                name_element.text = plangeber

        for bp_plan_element in root.iter('{http://www.xplanung.de/xplangml/5/4}BP_Plan'):
            aufstellungsbeschlussDatum_element = next(bp_plan_element.iter('{http://www.xplanung.de/xplangml/5/4}aufstellungsbeschlussDatum'))
            satzungsbeschlussDatum_element = next(bp_plan_element.iter('{http://www.xplanung.de/xplangml/5/4}satzungsbeschlussDatum'))
            inkrafttretensDatum_element = next(bp_plan_element.iter('{http://www.xplanung.de/xplangml/5/4}inkrafttretensDatum'))
            if rechtsstand_key == "1000":
                aufstellungsbeschlussDatum_element.text = datum
                bp_plan_element.remove(satzungsbeschlussDatum_element)
                bp_plan_element.remove(inkrafttretensDatum_element)
            elif rechtsstand_key == "3000":
                satzungsbeschlussDatum_element.text = datum
                bp_plan_element.remove(aufstellungsbeschlussDatum_element)
                bp_plan_element.remove(inkrafttretensDatum_element)
            elif rechtsstand_key == "4000":
                inkrafttretensDatum_element.text = datum
                bp_plan_element.remove(aufstellungsbeschlussDatum_element)
                bp_plan_element.remove(satzungsbeschlussDatum_element)

        for planart_element in root.iter('{http://www.xplanung.de/xplangml/5/4}planArt'):
            planart_element.text = planart_key

        for rechtsstand_element in root.iter('{http://www.xplanung.de/xplangml/5/4}rechtsstand'):
            rechtsstand_element.text = rechtsstand_key

        etree.indent(tree, space="\t", level=0)

        translation_table = str.maketrans({'ä': 'ae',
                                           'Ä': 'Ae',
                                           'ö': 'oe',
                                           'Ö': 'Oe',
                                           'ü': 'ue',
                                           'Ü': 'Ue',
                                           'ß': 'ss'})

        name = name.translate(translation_table)
        name = re.sub(r"[^a-zA-Z0-9-_]","_",name)
        name = re.sub("_+","_", name)
        name =  re.sub(r'^[\_]+', '', name)
        name =  re.sub(r'[\_]+$', '', name)

        zip_name = name + '.zip'
        zip_path = os.path.join(my_output_folder, zip_name)

        with zipfile.ZipFile(zip_path, 'w') as myzip:
            with myzip.open('xplan.gml', 'w') as myfile:
                tree.write(myfile, encoding = "UTF-8", xml_declaration = True)

        return {'XPlan-Archiv wurde erstellt': zip_path}