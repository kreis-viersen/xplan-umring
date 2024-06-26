# -*- coding: utf-8 -*-

"""
/***************************************************************************
 XPlan-Umring
                                 A QGIS plugin
 Umringpolygon eines Bebauungsplans aus QGIS nach XPlanung konvertieren
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-05-22
        copyright            : (C) 2023 by Kreis Viersen
        email                : open@kreis-viersen.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = "Kreis Viersen"
__date__ = "2023-05-22"
__copyright__ = "(C) 2023 by Kreis Viersen"

import inspect
import json
import os
import sys

from qgis import processing
from qgis.core import QgsApplication, QgsSettings

from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QCompleter, QDialog, QMenu, QMessageBox

from .xplan_umring_provider import XPlanUmringProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class LoadDialog(QDialog):
    def __init__(self, caller):
        super(LoadDialog, self).__init__()
        uic.loadUi(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "xplan_umring.ui"),
            self,
        )


class XPlanUmringPlugin(object):
    def __init__(self):
        self.iface = iface
        self.provider = None
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = XPlanUmringProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

        self.action = QAction(
            QIcon(os.path.join(self.plugin_dir, "xplan_umring_icon.png")),
            "&XPlan-Umring",
            self.iface.mainWindow(),
        )
        self.aboutAction = QAction(
            QIcon(os.path.join(self.plugin_dir, "info_icon.png")),
            "&Über XPlan-Umring",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.runXplanUmring)
        self.aboutAction.triggered.connect(self.about)

        self.menu = QMenu("&XPlan-Umring")
        self.menu.setIcon(QIcon(os.path.join(self.plugin_dir, "xplan_umring_icon.png")))
        self.menu.addActions([self.action, self.aboutAction])

        self.iface.pluginMenu().addMenu(self.menu)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

        self.iface.removePluginMenu("&XPlan-Umring", self.action)
        self.iface.removePluginMenu("&XPlan-Umring", self.aboutAction)
        self.iface.removeToolBarIcon(self.action)

        del self.action
        del self.aboutAction

    def about(self):
        aboutString = (
            "XPlan-Umring<br>QGIS-Plugin zum Erstellen einer XPlanGML-Datei für ein Umringszenario <br>"
            + 'Author: Kreis Viersen<br>Mail: <a href="mailto:open@kreis-viersen.de?subject=XPlan&#8208;Umring">'
            + "open@kreis-viersen.de</a><br>Web: "
            + '<a href="https://github.com/kreis-viersen/xplan-umring">'
            + "https://github.com/kreis-viersen/xplan-umring</a>"
        )
        QMessageBox.information(
            self.iface.mainWindow(), "Über XPlan-Umring", aboutString
        )

    def on_combo_box_changed(self, text):
        opening_parenthesis_index = text.find("(")

        if opening_parenthesis_index != -1:
            self.kommune = text[:opening_parenthesis_index].strip()

            closing_parenthesis_index = text.find(")", opening_parenthesis_index + 1)

            if closing_parenthesis_index != -1:
                self.ags = text[
                    opening_parenthesis_index + 1 : closing_parenthesis_index
                ]
            else:
                self.ags = ""
        else:
            self.kommune = text
            self.ags = ""

    def runXplanUmring(self):
        self.dlg = LoadDialog(self)
        self.settings = QgsSettings()
        self.selectedTool = self.settings.value(
            "xplan-umring/mytool", "bebauungsplan60"
        )

        self.kommune = self.settings.value("xplan-umring/kommune", "")
        self.ags = self.settings.value("xplan-umring/ags", "")

        self.selected_bezeichnung_ags = self.kommune + " (" + self.ags + ")"

        ags_data_source = os.path.join(self.plugin_dir, "ags/AGS_2024-02-29.json")

        with open(ags_data_source, encoding="UTF-8") as json_file:
            ags_data = json.load(json_file)

        self.bezeichnung_ags = sorted(
            [f"{entry[1]} ({entry[0]})" for entry in ags_data["daten"]]
        )

        if self.selected_bezeichnung_ags in self.bezeichnung_ags:
            selected_index = self.bezeichnung_ags.index(self.selected_bezeichnung_ags)
        else:
            custom_string = self.kommune
            if len(self.ags) > 0:
                custom_string = custom_string + " (" + self.ags + ")"
            self.bezeichnung_ags.append(custom_string)
            selected_index = self.bezeichnung_ags.index(custom_string)

        self.dlg.cb_ags.blockSignals(True)
        self.dlg.cb_ags.clear()
        self.dlg.cb_ags.addItems(self.bezeichnung_ags)
        self.dlg.cb_ags.setCurrentIndex(selected_index)
        self.dlg.cb_ags.blockSignals(False)
        self.dlg.cb_ags.setEditable(True)
        completer = QCompleter(self.bezeichnung_ags, self.dlg.cb_ags)
        self.dlg.cb_ags.setCompleter(completer)
        self.dlg.cb_ags.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.dlg.cb_ags.completer().setCaseSensitivity(Qt.CaseInsensitive)
        self.dlg.cb_ags.currentTextChanged.connect(self.on_combo_box_changed)

        def saveTool(tool):
            self.settings.setValue("xplan-umring/mytool", tool)
            self.selectedTool = tool

        self.dlg.rb_bp_54.toggled.connect(lambda: saveTool("bebauungsplan54"))
        self.dlg.rb_bp_60.toggled.connect(lambda: saveTool("bebauungsplan60"))
        self.dlg.rb_fp_60.toggled.connect(lambda: saveTool("flaechennutzungsplan60"))
        self.dlg.rb_lp_60.toggled.connect(lambda: saveTool("landschaftsplan60"))
        self.dlg.rb_replace.toggled.connect(lambda: saveTool("replacegeometry"))
        self.dlg.rb_clip.toggled.connect(lambda: saveTool("clipraster"))
        self.dlg.rb_difference.toggled.connect(lambda: saveTool("differenceraster"))

        if self.selectedTool == "bebauungsplan54":
            self.dlg.rb_bp_54.setChecked(True)
        elif self.selectedTool == "bebauungsplan60":
            self.dlg.rb_bp_60.setChecked(True)
        elif self.selectedTool == "flaechennutzungsplan60":
            self.dlg.rb_fp_60.setChecked(True)
        elif self.selectedTool == "landschaftsplan60":
            self.dlg.rb_lp_60.setChecked(True)
        elif self.selectedTool == "replacegeometry":
            self.dlg.rb_replace.setChecked(True)
        elif self.selectedTool == "clipraster":
            self.dlg.rb_clip.setChecked(True)
        elif self.selectedTool == "differenceraster":
            self.dlg.rb_difference.setChecked(True)

        result = self.dlg.exec_()

        # check if confirmed with OK
        if result == 1:
            self.settings.setValue("xplan-umring/kommune", self.kommune)
            self.settings.setValue("xplan-umring/ags", self.ags)

            processing.execAlgorithmDialog("xplanumring:" + self.selectedTool)
