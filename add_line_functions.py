from qgis.core import QgsProject, QgsVectorLayer
from qgis.utils import iface

# Create temporary layer
def create_temporary_line_layer():
    layer = QgsVectorLayer("LineString?crs=EPSG:4326", "Temporary way", "memory")
    if not layer.isValid():
        return None

    # Add layer to project
    QgsProject.instance().addMapLayer(layer)

    return layer

# Start layer editing
def start_editing_layer(layer):
    if layer is not None:
        if not layer.isEditable():
            layer.startEditing()

# Activate tool to add lines
def activate_add_line_tool(iface, layer):
    iface.setActiveLayer(layer)
    add_feature_action = iface.actionAddFeature()
    if add_feature_action:
        add_feature_action.trigger()
        return True
    else:
        return False

# Finish line edition
def finish_editing_layer(layer):
    layer.commitChanges()

