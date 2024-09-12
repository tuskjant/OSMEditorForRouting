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
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem
from qgis.PyQt.QtWidgets import QAction, QTableView
from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsProject, Qgis, QgsMapLayer, QgsWkbTypes
from qgis.gui import QgsMessageBar

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .osm_routing_editor_dialog import EditorForRoutingDialog
import os.path
# tool for select feature
from .select_feature_tool import SelectFeatureTool
# subprocess to execute cmd commands
import subprocess
# osrm feature data to edit features
from .osrm_feature_data import OsrmFeatureData
# database funcions
from .database_functions import *

class EditorForRouting:
    """QGIS Plugin Implementation."""
    segment_layer_name = "ways"
    tags_field_name = "tags"
    ways_style_file = "ways_style.qml"

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
        self.dlg = EditorForRoutingDialog(routing_editor=self)
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
            self.dlg.pushButtonOneWay.clicked.connect(lambda: self.change_oneway("oneway"))
            self.dlg.pushButton_BothDirections.clicked.connect(lambda: self.change_oneway("bothways"))
            self.dlg.pushButtonMaxSpeed.clicked.connect(self.change_speed)
            self.dlg.pushButtonDirection.clicked.connect(self.change_direction)
            self.dlg.pushButtonUndoChanges.clicked.connect(self.undo_segment_changes)
            self.dlg.pushButtonToPbf.clicked.connect(self.convert_to_pbf)
            self.dlg.pushButtonLoadPbf.clicked.connect(self.load_pbf)
            self.dlg.button_box.clicked.connect(self.close)

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
        self.host = self.settings.value('host')
        if self.host is not None:
            self.dlg.lineEditHost.setText(self.host)
        self.port = self.settings.value('port')
        if self.port is not None:
            self.dlg.lineEditPort.setText(self.port)
        self.user = self.settings.value('user')
        if self.user is not None:
            self.dlg.lineEditUser.setText(self.user)
        self.database = self.settings.value('database')
        if self.database is not None:
            self.dlg.lineEditDB.setText(self.database)
        self.schema = self.settings.value('schema')
        if self.schema is not None:
            self.dlg.lineEditSchema.setText(self.schema)

    def add_layer(self):
        """ Method to load ways layer from database
        """
        # get user connection parameters
        self.host = self.dlg.lineEditHost.text()
        self.port = self.dlg.lineEditPort.text()
        self.user = self.dlg.lineEditUser.text()
        self.password = self.dlg.lineEditPassword.text()
        self.database = self.dlg.lineEditDB.text()
        self.schema = self.dlg.lineEditSchema.text()

        # save connection parameters to settings
        self.settings.setValue('host', self.host)
        self.settings.setValue('port', self.port)
        self.settings.setValue('user', self.user)
        self.settings.setValue('database', self.database)
        self.settings.setValue('schema', self.schema)

        # set connection
        uri = QgsDataSourceUri()
        uri.setConnection(self.host, self.port, self.database, self.user, self.password)

        # fetch ways layer
        where = "tags ? 'highway' or tags ? 'junction'"
        uri.setDataSource(self.schema, "ways", "linestring", where)
        self.ways_layer = QgsVectorLayer(uri.uri(), "ways", "postgres")

        # add ways layer
        if not self.ways_layer.isValid():
            self.iface.messageBar().pushMessage("Error", "Error when retriveing the layer.", Qgis.Warning, 10)
            return
        else:
            QgsProject.instance().addMapLayer(self.ways_layer)
            self.iface.setActiveLayer(self.ways_layer)
            self.iface.zoomToActiveLayer()
            # apply symbology
            qml_path = os.path.join(os.path.dirname(__file__), self.ways_style_file)
            self.ways_layer.loadNamedStyle(qml_path)
            self.ways_layer.triggerRepaint()

    def handle_feature_selection(self, checked):
        """Method to handle checkable button: checked select, unchecked unselect"""
        if checked:
            self.select_features()
        else:
            self.perform_cleanup()
            self.display_segments()

    def perform_cleanup(self):
        """Method to unselect all features """
        ways_layer = self.check_layer(self.segment_layer_name)
        if ways_layer is not None:
            ways_layer.removeSelection()
        self.display_segments()
        self.iface.actionIdentify().trigger() #activar la herramienta info

    def select_features(self):
        """Method to activate select feature tool for ways layer if layer is valid
        """
        # Get layer by name and check if exist
        ways_layer = self.check_layer(self.segment_layer_name)

        # Select features from ways layer
        if ways_layer is not None:
            self.tool = SelectFeatureTool(self.canvas, ways_layer)
            self.tool.feature_selected.connect(self.display_segments)
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

        for feature in selected_features:
            osrm_feature = OsrmFeatureData(feature, self.iface)
            osrm_feature.change_access(option)
            ways_layer.updateFeature(osrm_feature.feature)
        ways_layer.commitChanges()
        ways_layer.triggerRepaint()
        self.display_segments()

    def change_oneway(self, option):
        """Method to edit the segments of 'ways' to convert them to one-way or two-way circulation.
        """
        ways_layer = self.check_layer(self.segment_layer_name)        
        selected_features = ways_layer.selectedFeatures()
        if len(selected_features) < 1:
            self.iface.messageBar().pushMessage(
                "Error", "There are no selected features", Qgis.Warning, 10
            )
            return
        ways_layer.startEditing()

        for feature in selected_features:
            osrm_feature = OsrmFeatureData(feature, self.iface)
            osrm_feature.change_one_way(option)
            ways_layer.updateFeature(osrm_feature.feature)
        ways_layer.commitChanges()
        ways_layer.triggerRepaint()
        self.display_segments()

    def change_speed(self):
        """Method to change speed to selected"""
        speed = self.dlg.spinBoxSpeed.value()
        ways_layer = self.check_layer(self.segment_layer_name)
        selected_features = ways_layer.selectedFeatures()
        if len(selected_features) < 1:
            self.iface.messageBar().pushMessage(
                "Error", "There are no selected features", Qgis.Warning, 10
            )
            return
        ways_layer.startEditing()
        for feature in selected_features:
            osrm_feature = OsrmFeatureData(feature, self.iface)
            osrm_feature.change_speed(speed)
            ways_layer.updateFeature(osrm_feature.feature)
        ways_layer.commitChanges()
        ways_layer.triggerRepaint()
        self.display_segments()

    def change_direction(self):
        ways_layer = self.check_layer(self.segment_layer_name)

        # select features
        selected_features = ways_layer.selectedFeatures()
        if len(selected_features) < 1:
            self.iface.messageBar().pushMessage(
                "Error", "There are no selected features", Qgis.Warning, 10
            )
            return

        # create connection
        parameters = self.get_db_parameters()
        if parameters == None:
            return
        connection, cursor = connect_to_database(parameters)
        if connection is None or cursor is None:
            self.iface.messageBar().pushMessage(
                "Warning", "Can not connect to database", Qgis.Warning, 10
            )
            return

        # change direction of each feature
        for feature in selected_features:
            way_id = feature["id"]
            # Change direction
            reversed = change_line_direction(connection, cursor, way_id)
            if not reversed:
                self.iface.messageBar().pushMessage(
                    "Warning", f"Can not reverse {way_id} segment", Qgis.Warning, 10
                )

        # close connection
        closed = close_connection(connection, cursor)
        if not closed:
            self.iface.messageBar().pushMessage(
                "Warning", "An error occurred while closing database", Qgis.Warning, 10
            )
        return

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
        for feature in selected_features:
            osrm_feature = OsrmFeatureData(feature, self.iface)
            osrm_feature.change_edited("undo",None)
            ways_layer.updateFeature(osrm_feature.feature)
        ways_layer.commitChanges()
        ways_layer.triggerRepaint()
        self.display_segments()

    def display_segments(self):
        """Method to display attributes of selected segments in a table"""
        self.tableView = self.dlg.tableView
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
            ["Id", "Name", "Access", "Oneway", "MaxSpeed", "Edited"]
        )

        # Get selected features and attributes
        ways_layer = self.check_layer(self.segment_layer_name)
        selected_features = ways_layer.selectedFeatures()
        table_data = []
        if selected_features:
            for feature in selected_features:
                osrm_feature = OsrmFeatureData(feature, self.iface)
                table_data.append(osrm_feature.get_table_row())

        for data_row in table_data:
            items = [QStandardItem(data) for data in data_row]
            model.appendRow(items)

        self.tableView.setModel(model)
        self.tableView.setColumnWidth(1, 200)

    def run_command(self, command):
        """Method to run a subprocess for pbf generation"""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout = stdout.decode('cp1252')
        stderr = stderr.decode('cp1252')
        return stdout, stderr

    def convert_to_pbf(self):
        """Method for exporting from database to pbf files"""
        pbf_folder = self.dlg.mQgsFileWidget_pbfFolder.filePath()
        osmosis_folder = self.dlg.mQgsFileWidgetOsmosis.filePath()
        password = self.dlg.lineEditPassword.text()
        if self.db is not None and self.user is not None and password is not None:
            try: 
                command = f'cd /d "{osmosis_folder}" && osmosis --read-pgsql database={self.db} user={self.user} password={password} --dataset-dump --write-pbf file={os.path.join(pbf_folder,"output.osm.pbf")}'
                stdout, stderr = self.run_command(command)
                print("Salida", stdout)
                print("Errores", stderr)
                self.iface.messageBar().pushMessage(
                    "Info", "Database converted to pbf file", Qgis.Success, 10
                )
            except:
                self.iface.messageBar().pushMessage(
                    "Error", "An error ocurred while converting to pbf", Qgis.Warning, 10
                )

    def load_pbf(self):
        # Comprobar si existe la bbdd y si no existe crearla
        pass

    def close(self):
        self.perform_cleanup()
        self.iface.messageBar().pushMessage(
            "Info", "Exited OSM Editor for Routing pluggin", Qgis.Info, 10
        )

    def get_db_parameters(self):
        # get user connection parameters
        self.host = self.dlg.lineEditHost.text()
        self.port = self.dlg.lineEditPort.text()
        self.user = self.dlg.lineEditUser.text()
        self.password = self.dlg.lineEditPassword.text()
        self.database = self.dlg.lineEditDB.text()
        self.schema = self.dlg.lineEditSchema.text()
        if self.host and self.port and self.user and self.password and self.database:
            return {
                'dbname': self.database, 
                'user': self.user, 
                'password': self.password, 
                'host': self.host, 
                'port': self.port
            }
        else:
            self.iface.messageBar().pushMessage(
                "Warning", "Missing connection parameters", Qgis.Warning, 10
            )
            return None
