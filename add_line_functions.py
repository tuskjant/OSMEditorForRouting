from qgis.core import QgsProject, QgsVectorLayer, QgsSnappingConfig, QgsSnappingUtils, QgsTolerance
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

# Activate snappin to ways layer
def enable_snapping_for_layer(ways_layer):
    snapping_config = QgsSnappingConfig()

    snapping_config.setEnabled(True)
    snapping_config.setType(QgsSnappingConfig.Vertex)  
    snapping_config.setTolerance(10)
    snapping_config.setMode(QgsSnappingConfig.SnappingMode.AdvancedConfiguration)
    lyr_settings = QgsSnappingConfig.IndividualLayerSettings(True, QgsSnappingConfig.SnappingType.Vertex, 10, QgsTolerance.Pixels)
    snapping_config.setIndividualLayerSettings(ways_layer, lyr_settings) 

    QgsProject.instance().setSnappingConfig(snapping_config)
