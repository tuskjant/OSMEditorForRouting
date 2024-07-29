from qgis.gui import QgsMapToolIdentifyFeature
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer


class SelectFeatureTool(QgsMapToolIdentifyFeature):
    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            features = self.identify(event.x(), event.y(), [self.layer])
            if features:
                for feature in features:
                    fid = feature.mFeature.id()
                    self.layer.selectByIds([fid], QgsVectorLayer.AddToSelection)
            else:
                self.layer.removeSelection()
