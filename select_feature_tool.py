from qgis.gui import QgsMapToolIdentifyFeature
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer
from PyQt5.QtCore import pyqtSignal


class SelectFeatureTool(QgsMapToolIdentifyFeature):
    feature_selected = pyqtSignal() #signal to update table

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
                self.feature_selected.emit() #emit signal when selected
            else:
                self.layer.removeSelection()
                self.feature_selected.emit()  # emit signal when unselected
