import re
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QCheckBox
)
from qgis.PyQt.QtCore import Qt
from .config_manager import ConfigManager
from qgis.PyQt.QtWidgets import QMessageBox

class PdndConnectionDialog(QDialog):

    def __init__(self, plugin_dir, iface, parent_panel, edit_mode=False, name=None, ambiente=None, cfg=None):
        super().__init__()
        self.iface = iface
        self.parent_panel = parent_panel

        self.setWindowTitle("Connessione PDND")

        self.plugin_dir = plugin_dir
        self.config_manager = ConfigManager(plugin_dir)

        self.edit_mode = edit_mode
        self.original_name = name

        layout = QVBoxLayout()

        self.resize(650, 700)

        # Nome connessione
        layout.addWidget(QLabel("Nome connessione"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        # Ambiente
        layout.addWidget(QLabel("Ambiente"))
        self.env_combo = QComboBox()
        self.env_combo.addItems(["produzione", "collaudo"])
        layout.addWidget(self.env_combo)

        # Campi PDND
        self.kid_edit = QLineEdit()
        self.issuer_edit = QLineEdit()
        self.client_edit = QLineEdit()
        self.purpose_edit = QLineEdit()
        self.key_edit = QLineEdit()
        self.api_edit = QLineEdit()

        for label, widget in [
            ("kid", self.kid_edit),
            ("issuer", self.issuer_edit),
            ("clientId", self.client_edit),
            ("purposeId", self.purpose_edit),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        # Chiave privata con pulsante Sfoglia
        layout.addWidget(QLabel("Chiave privata"))
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.key_edit)
        key_btn = QPushButton("Sfoglia…")
        key_btn.clicked.connect(self.select_key)
        key_layout.addWidget(key_btn)
        layout.addLayout(key_layout)

        # API URL
        layout.addWidget(QLabel("API URL"))
        layout.addWidget(self.api_edit)

        # Checkbox debug + pretty JSON + mantieni in cache
        self.debug_checkbox = QCheckBox("Abilita debug PDND")
        self.pretty_checkbox = QCheckBox("Salva JSON in formato leggibile (pretty)")
        self.cache_checkbox = QCheckBox("Mantieni in cache")
        layout.addWidget(self.debug_checkbox)
        layout.addWidget(self.pretty_checkbox)
        layout.addWidget(self.cache_checkbox)

        # Se siamo in modalità modifica, precompila i campi
        if edit_mode and cfg is not None:
            self.name_edit.setText(name)
            self.env_combo.setCurrentText(ambiente)

            self.kid_edit.setText(cfg.get("kid", ""))
            self.issuer_edit.setText(cfg.get("issuer", ""))
            self.client_edit.setText(cfg.get("clientId", ""))
            self.purpose_edit.setText(cfg.get("purposeId", ""))
            self.key_edit.setText(cfg.get("privKeyPath", ""))
            self.api_edit.setText(cfg.get("apiUrl", ""))

            self.debug_checkbox.setChecked(cfg.get("debug", False))
            self.pretty_checkbox.setChecked(cfg.get("pretty", False))
            self.cache_checkbox.setChecked(cfg.get("cache", False))

        # Pulsanti OK / Annulla
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Salva")
        ok_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        btn_test = QPushButton("Test Connessione")
        btn_test.clicked.connect(self.run_test_from_dialog)
        btn_layout.addWidget(btn_test)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def select_key(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona chiave privata",
            "",
            "Key Files (*.priv *.pem *.key);;Tutti i file (*)"
        )
        if path:
            self.key_edit.setText(path)

    def save(self):
        raw_name = self.name_edit.text().strip()
        name = self.sanitize_filename(raw_name)

        if not name:
            QMessageBox.warning(self, "PDND", "Il nome inserito non è valido.")
            self.name_edit.setStyleSheet("border: 1px solid red;")
            return
        
        ambiente = self.env_combo.currentText()

        cfg = {
            "kid": self.kid_edit.text().strip(),
            "issuer": self.issuer_edit.text().strip(),
            "clientId": self.client_edit.text().strip(),
            "purposeId": self.purpose_edit.text().strip(),
            "privKeyPath": self.key_edit.text().strip(),
            "apiUrl": self.api_edit.text().strip(),
            "debug": self.debug_checkbox.isChecked(),
            "pretty": self.pretty_checkbox.isChecked(),
            "cache": self.cache_checkbox.isChecked()
        }

        # Modalità modifica
        if self.edit_mode:
            # Se il nome è cambiato, elimina la vecchia configurazione
            if name != self.original_name:
                self.config_manager.delete_configuration(self.original_name)

            self.config_manager.create_configuration(name, cfg, ambiente)

        else:
            # Nuova configurazione
            self.config_manager.create_configuration(name, cfg, ambiente)

        self.close()
    
    def run_test_from_dialog(self):
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "PDND", "Inserisci un nome connessione prima di testare.")
            return

        self.parent_panel.test_connection(name)

    def sanitize_filename(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"[^\w]+", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")

        return name




