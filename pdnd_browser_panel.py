import os
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QMenu, QDockWidget, QPushButton, QHBoxLayout
)
from qgis.PyQt.QtCore import Qt
from .config_manager import ConfigManager
from .pdnd_connection_dialog import PdndConnectionDialog
from .pdnd_layer_loader import PdndLayerLoader
from .api_client import ApiClient
from .pdnd_logger import log_info, log_error


class PdndBrowserPanel(QWidget):

    def __init__(self, plugin_dir, iface):
        super().__init__()

        self.plugin_dir = plugin_dir
        self.iface = iface
        self.config_manager = ConfigManager(plugin_dir)
        self.api = ApiClient()

        layout = QVBoxLayout()

        # Barra comandi
        btn_layout = QHBoxLayout()

        btn_new = QPushButton("Nuova Connessione")
        btn_new.clicked.connect(self.new_connection)
        btn_layout.addWidget(btn_new)

        btn_refresh = QPushButton("Aggiorna")
        btn_refresh.clicked.connect(self.refresh)
        btn_layout.addWidget(btn_refresh)

        btn_test = QPushButton("Test Connessione")
        btn_test.clicked.connect(self.test_connection)
        btn_layout.addWidget(btn_test)

        layout.addLayout(btn_layout)

        # Albero connessioni
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Connessioni PDND")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_menu)
        self.tree.itemDoubleClicked.connect(self.double_click_load)

        layout.addWidget(self.tree)
        self.setLayout(layout)

        self.refresh()

    def double_click_load(self, item, column):
        name = item.text(0)
        loader = PdndLayerLoader(self.config_manager)
        try:
            loader.load(name)
            self.msg_success(self.iface, "PDND", f"Layer '{name}' caricato correttamente.")
        except Exception as e:
            self.msg_critical(self.iface, "PDND", str(e))

    def refresh(self):
        self.tree.clear()
        for name in self.config_manager.list_configurations():
            item = QTreeWidgetItem([name])
            self.tree.addTopLevelItem(item)

    def open_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu()

        if item is None:
            menu.addAction("Nuova Connessione…", self.new_connection)
            menu.addAction("Salva Connessioni…", self.save_connections)
            menu.addAction("Carica Connessioni…", self.load_connections)
        else:
            name = item.text(0)
            menu.addAction("Carica Layer", lambda: PdndLayerLoader(self.config_manager))
            menu.addAction("Test Connessione", lambda: self.test_connection(name))
            menu.addAction("Modifica Connessione…", lambda: self.edit_connection(name))
            menu.addAction("Elimina Connessione", lambda: self.delete_connection(name))

        menu.exec(self.tree.mapToGlobal(pos))

    def new_connection(self):
        dlg = PdndConnectionDialog(self.plugin_dir, self.iface, self)
        dlg.exec()
        self.refresh()
    
    def edit_connection(self, name):
        json_path = self.config_manager.get_json_path(name)
        if not json_path:
            self.iface.messageBar().pushCritical("PDND", f"Connessione '{name}' non trovata.")
            return

        # Carica configurazione esistente
        cfg = self.config_manager.load_configuration(name)
        ambiente = self.config_manager.get_environment(name)

        # Apri dialog in modalità modifica
        dlg = PdndConnectionDialog(self.plugin_dir, self.iface, self, edit_mode=True, name=name, ambiente=ambiente, cfg=cfg)
        dlg.exec()

        self.refresh()


    def save_connections(self):
        self.config_manager.export_connections()

    def load_connections(self):
        self.config_manager.import_connections()
        self.refresh()

    def delete_connection(self, name):
        self.config_manager.delete_configuration(name)
        self.refresh()

    def test_connection(self, name=None):
        # Se non viene passato il nome, usa l'elemento selezionato
        if name is None or name is False or name == "":
            item = self.tree.currentItem()
            if not item:
                self.iface.messageBar().pushWarning("PDND", "Seleziona una connessione da testare.")
                return
            name = item.text(0)

        # Percorso JSON
        json_path = self.config_manager.get_json_path(name)
        if not json_path:
            self.iface.messageBar().pushCritical("PDND", f"Connessione '{name}' non trovata nell'index.json.")
            return

        try:
            # Log
            log_info(f"TEST CONNESSIONE: {name}")
            log_info(f"JSON path: {json_path}")

            # Genera token
            token = self.api.get_token_from_file(json_path)

            # Riscontro visivo
            self.iface.messageBar().pushSuccess("PDND", f"Connessione '{name}' OK — token generato.")

            # Log token
            log_info(f"Token generato correttamente per '{name}'.")
            log_info(f"Token (primi 50 caratteri): {token[:50]}...")

        except Exception as e:
            msg = str(e)
            self.iface.messageBar().pushCritical("PDND", f"Errore: {msg}")
            log_error(f"Errore test connessione '{name}': {msg}")

    def load_pdnd_layer(self, name):
        loader = PdndLayerLoader(self.config_manager)
        try:
            loader.load(name)
            self.iface.messageBar().pushSuccess("PDND", f"Layer '{name}' caricato.")
        except Exception as e:
            self.iface.messageBar().pushCritical("PDND", str(e))

    def msg_success(self, iface, title, text):
        iface.messageBar().pushSuccess(title, text)

    def msg_warning(self, iface, title, text):
        iface.messageBar().pushWarning(title, text)

    def msg_critical(self, iface, title, text):
        iface.messageBar().pushCritical(title, text)


class PdndDockWidget(QDockWidget):

    def __init__(self, iface):
        super().__init__("PDND")
        plugin_dir = os.path.dirname(__file__)
        self.panel = PdndBrowserPanel(plugin_dir, iface)
        self.setWidget(self.panel)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
