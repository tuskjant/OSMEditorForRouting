# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EditorForRouting
                                 A QGIS plugin
 This plugin allow to edit OSM layer for routing purpouses
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-07-18
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Gemma Riu
        email                : gemmariup@gmail.com
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsProject, Qgis, QgsMapLayer, QgsWkbTypes
from qgis.gui import QgsMessageBar

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .osm_routing_editor_dialog import EditorForRoutingDialog
import os.path
# import tools
from .select_feature_tool import SelectFeatureTool


class EditorForRouting:
    """QGIS Plugin Implementation."""
    segment_layer_name = "ways"
    tags_field_name = "tags"

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'EditorForRouting_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.canvas = iface.mapCanvas()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&OSM Editor for Routing')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        # Load settings
        self.settings = QSettings('OSMRoutingEditor', 'OSMRE_settings')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('EditorForRouting', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/osm_routing_editor/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'OSM editor'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

        # create dialog and load settings
        self.dlg = EditorForRoutingDialog()
        self.load_settings()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&OSM Editor for Routing'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg.pushButtonAddLayers.clicked.connect(self.add_layer)
            self.dlg.pushButtonSelectTram.toggled.connect(self.handle_feature_selection)
            self.dlg.pushButtonActiva.clicked.connect(lambda: self.change_segment_access("allow_access"))
            self.dlg.pushButtonDesactiva.clicked.connect(lambda: self.change_segment_access("restrict_access"))
            self.dlg.pushButtonUndoChanges.clicked.connect(self.undo_segment_changes)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def load_settings(self):
        """ Method to load and set saved parameters (host, port, user, database, schema).
        """
        host = self.settings.value('host')
        if host is not None:
            self.dlg.lineEditHost.setText(host)
        port = self.settings.value('port')
        if port is not None:
            self.dlg.lineEditPort.setText(port)
        user = self.settings.value('user')
        if user is not None:
            self.dlg.lineEditUser.setText(user)
        db = self.settings.value('database')
        if db is not None:
            self.dlg.lineEditDB.setText(db)
        schema = self.settings.value('schema')
        if schema is not None:
            self.dlg.lineEditSchema.setText(schema)

    def add_layer(self):
        """ Method to load ways layer from database
        """
        # get user connection parameters
        host = self.dlg.lineEditHost.text()
        port = self.dlg.lineEditPort.text()
        user = self.dlg.lineEditUser.text()
        password = self.dlg.lineEditPassword.text()
        database = self.dlg.lineEditDB.text()
        schema = self.dlg.lineEditSchema.text()

        # save connection parameters to settings
        self.settings.setValue('host', host)
        self.settings.setValue('port', port)
        self.settings.setValue('user', user)
        self.settings.setValue('database', database)
        self.settings.setValue('schema', schema)

        # set connection
        uri = QgsDataSourceUri()
        uri.setConnection(host, port, database, user, password)

        # fetch ways layer
        where = "tags ? 'highway' or tags ? 'junction'"
        uri.setDataSource(schema, "ways", "linestring", where)
        self.ways_layer = QgsVectorLayer(uri.uri(), "ways", "postgres")

        # add ways layer
        if not self.ways_layer.isValid():
            self.iface.messageBar().pushMessage("Error", "Error when retriveing the layer.", Qgis.Warning, 10)
            return
        else:
            QgsProject.instance().addMapLayer(self.ways_layer)
            self.iface.setActiveLayer(self.ways_layer)
            self.iface.zoomToActiveLayer()

    def handle_feature_selection(self, checked):
        if checked:
            self.select_features()
        else:
            ways_layer = self.check_layer(self.segment_layer_name)
            if ways_layer is not None:
                ways_layer.removeSelection()
            self.iface.actionIdentify().trigger() #activar la herramienta info

    def select_features(self):
        """Method to activate select feature tool for ways layer if layer is valid
        """
        # Get layer by name and check if exist
        ways_layer = self.check_layer(self.segment_layer_name)

        # Select features from ways layer
        if ways_layer is not None:
            self.tool = SelectFeatureTool(self.canvas, ways_layer)
            self.canvas.setMapTool(self.tool)
        else:
            self.iface.messageBar().pushMessage("Error", "No layer available", Qgis.Warning, 10)

    def check_layer(self, layer_name):
        """Check if layer exist in type and format defined
        """
        # Get layer by name and check if exists
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if len(layers) < 1:
            self.iface.messageBar().pushMessage(
                "Error", "Ways layer is not loaded", Qgis.Warning, 10
            )
            return
        ways_layer = layers[0]

        # Check layer type, geometry = linestring (2)
        if (
            ways_layer.type() != QgsMapLayer.VectorLayer
            or ways_layer.wkbType() != 2
        ):
            self.iface.messageBar().pushMessage(
                "Error", "Ways layer is not valid", Qgis.Warning, 10
            )
            return

        # Check layer attributes
        hasAttribute = False
        for field in ways_layer.fields():
            if field.name() == "tags":
                if field.type() == 8:  # hstore
                    hasAttribute = True
        if not hasAttribute:
            self.iface.messageBar().pushMessage(
                "Error",
                "Ways layer is not valid. Missing tags attribute",
                Qgis.Warning,
                10,
            )
            return
        return ways_layer

    def change_segment_access(self, option):
        """ Method to edit ways segment to allow or restrict segment access
        """
        ways_layer = self.check_layer(self.segment_layer_name)
        selected_features = ways_layer.selectedFeatures()
        if len(selected_features) < 1:
            self.iface.messageBar().pushMessage(
                "Error", "There are no selected features", Qgis.Warning, 10
            )
            return
        ways_layer.startEditing()

        edited_segments = 0
        for feature in selected_features:
            tags_value = feature[self.tags_field_name]
            if tags_value:
                new_tags_value = self.edit_access_segments(tags_value, option)
                feature[self.tags_field_name] = new_tags_value
                ways_layer.updateFeature(feature)
                edited_segments += 1
        ways_layer.commitChanges()
        ways_layer.triggerRepaint()
        self.iface.messageBar().pushMessage(
            "Info", f"{edited_segments} segments have been edited", Qgis.Info, 10
        )

    def edit_access_segments(self, tags_value, option):
        """Method to modify tags field depending on option. Option can be "allow_access" or 
        "restrict_access". If "allow_access", "access" tag is "yes". If "restrict_access", "access"
        tag is "no". Before been edited previous state will be stored in osmredited tag.
        In case segement has been edited before, just change the access state. 
        """
        # tags_dict = dict(item.split("=>") for item in tags_value.split(", "))
        tags_dict = tags_value
        # When it has not been edited before:
        if "osmredited" not in tags_dict.keys():
            # if access tag exist save value in osmredited
            if "access" in tags_dict.keys():
                tags_dict["osmredited"] = tags_dict["access"]
            # if access tag does not exist mark as no_access_key
            else:
                tags_dict["osmredited"] = "No_Access_Key"
            # if option selected is restrict access -> no, else if allow access ->yes
        # In any case change state
        if option == "restrict_access":
            tags_dict["access"] = "no"
        elif option == "allow_access":
            tags_dict["access"] = "yes"
        # Convert to hstore tags = ", ".join(f"{k}=>{v}" for k, v in tags_dict.items())
        print(tags_dict)
        return tags_dict

    def undo_segment_changes(self):
        """Method to undo all previous changes (access or restrict) in segments"""
        ways_layer = self.check_layer(self.segment_layer_name)
        selected_features = ways_layer.selectedFeatures()
        if len(selected_features) < 1:
            self.iface.messageBar().pushMessage(
                "Error", "There are no selected features", Qgis.Warning, 10
            )
            return

        ways_layer.startEditing()
        edited_segments = 0
        for feature in selected_features:
            tags_value = feature[self.tags_field_name]
            if tags_value:
                if "osmredited" in tags_value.keys():
                    edited_segments += 1
                    if tags_value["osmredited"] == "No_Access_Key":
                        del tags_value["osmredited"]
                        del tags_value["access"]
                    else:
                        tags_value["access"] = tags_value.pop("osmredited")

        if edited_segments == 0:
            self.iface.messageBar().pushMessage(
                "Alert", "There aren't any previously edited segments", Qgis.Warning, 10
            )
        else:
            self.iface.messageBar().pushMessage(
                "Info", f"{edited_segments} segments have been restored", Qgis.Info, 10
            )

        feature[self.tags_field_name] = tags_value
        ways_layer.updateFeature(feature)
        ways_layer.commitChanges()
        ways_layer.triggerRepaint()
