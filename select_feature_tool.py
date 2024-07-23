from qgis.gui import QgsMapToolIdentifyFeature
from qgis.PyQt.QtCore import Qt

class SelectFeatureTool(QgsMapToolIdentifyFeature):
    def __init__(self, canvas, layer):
        super().__init__(canvas)
        print("soc al constructor")
        self.canvas = canvas
        self.layer = layer

    def canvasReleaseEvent(self, event):
        print("se ha clicado en un punto")
        if event.button() == Qt.LeftButton:
            features = self.identify(event.x(), event.y(), [self.layer])
            if features:
                for feature in features:
                    fid = feature.mFeature.id()
                    self.layer.selectByIds([fid])
            else:
                self.layer.removeSelection()
