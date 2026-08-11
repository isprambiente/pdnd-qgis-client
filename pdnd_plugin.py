from qgis.PyQt.QtCore import Qt
from .pdnd_browser_panel import PdndDockWidget

class PdndPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.dock = None

    def initGui(self):
        self.dock = PdndDockWidget(self.iface)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

    def unload(self):
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock = None
