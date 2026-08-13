import re
import os
import json
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from .config_manager import ConfigManager

class PdndLoadConfigDialog(QDialog):

    REQUIRED_KEYS = [
        "apiUrl", "cache", "clientId", "debug",
        "issuer", "kid", "pretty", "privKeyPath", "purposeId"
    ]

    def __init__(self, plugin_dir, iface):
        super().__init__()
        self.setWindowTitle("Importa configurazione PDND")

        self.plugin_dir = plugin_dir
        self.iface = iface
        self.config_manager = ConfigManager(plugin_dir)

        self.loaded_data = None
        self.environment = None
        self.valid = False
        self.resize(650, 700)

        # ------------------------------
        # Layout principale
        # ------------------------------
        layout = QVBoxLayout(self)

        # File selector
        file_layout = QHBoxLayout()
        self.fileEdit = QLineEdit()
        self.fileEdit.setPlaceholderText("Seleziona file JSON...")
        btnBrowse = QPushButton("Sfoglia")
        btnBrowse.clicked.connect(self.browse_file)
        file_layout.addWidget(self.fileEdit)
        file_layout.addWidget(btnBrowse)
        layout.addLayout(file_layout)

        # ------------------------------
        # Anteprima campi
        # ------------------------------
        self.previewEnv = QLabel("-")
        self.previewApiUrl = QLabel("-")
        self.previewPrivKey = QLabel("-")
        self.previewKid = QLabel("-")
        self.previewIssuer = QLabel("-")
        self.previewClientId = QLabel("-")
        self.previewPurposeId = QLabel("-")
        self.previewCache = QLabel("-")
        self.previewDebug = QLabel("-")
        self.previewPretty = QLabel("-")

        def row(label, widget):
            r = QHBoxLayout()
            r.addWidget(QLabel(label))
            r.addWidget(widget)
            return r

        layout.addLayout(row("Ambiente:", self.previewEnv))
        layout.addLayout(row("API URL:", self.previewApiUrl))
        layout.addLayout(row("Chiave privata:", self.previewPrivKey))
        layout.addLayout(row("KID:", self.previewKid))
        layout.addLayout(row("Issuer:", self.previewIssuer))
        layout.addLayout(row("Client ID:", self.previewClientId))
        layout.addLayout(row("Purpose ID:", self.previewPurposeId))
        layout.addLayout(row("Cache:", self.previewCache))
        layout.addLayout(row("Debug:", self.previewDebug))
        layout.addLayout(row("Pretty:", self.previewPretty))

        # ------------------------------
        # Pulsanti OK / Annulla
        # ------------------------------
        btns = QHBoxLayout()
        btnOk = QPushButton("Importa")
        btnCancel = QPushButton("Annulla")
        btnOk.clicked.connect(self.on_import)
        btnCancel.clicked.connect(self.reject)
        btns.addWidget(btnOk)
        btns.addWidget(btnCancel)
        layout.addLayout(btns)

    # ---------------------------------------------------------
    # Selezione file
    # ---------------------------------------------------------
    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file di configurazione",
            "",
            "Configurazioni PDND (*.json);;Tutti i file (*)"
        )
        if not path:
            return

        self.fileEdit.setText(path)

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile leggere il file:\n{e}")
            return

        # Validazione struttura
        if not isinstance(raw, dict) or len(raw.keys()) != 1:
            QMessageBox.warning(self, "Errore", "Il file deve contenere un solo nodo radice (es: 'produzione').")
            return

        env = list(raw.keys())[0]
        data = raw[env]

        # Completa i campi mancanti
        for key in self.REQUIRED_KEYS:
            if key not in data:
                if key in ["cache", "debug", "pretty"]:
                    data[key] = False
                else:
                    data[key] = ""

        self.environment = env
        self.loaded_data = data

        # Anteprima
        self.previewEnv.setText(env)
        self.previewApiUrl.setText(data["apiUrl"])
        self.previewPrivKey.setText(data["privKeyPath"])
        self.previewKid.setText(data["kid"])
        self.previewIssuer.setText(data["issuer"])
        self.previewClientId.setText(data["clientId"])
        self.previewPurposeId.setText(data["purposeId"])
        self.previewCache.setText("Sì" if data["cache"] else "No")
        self.previewDebug.setText("Sì" if data["debug"] else "No")
        self.previewPretty.setText("Sì" if data["pretty"] else "No")

    # ---------------------------------------------------------
    # Importa
    # ---------------------------------------------------------
    def on_import(self):
        if not self.loaded_data:
            QMessageBox.warning(self, "Errore", "Nessuna configurazione caricata.")
            return

        self.valid = True
        self.save()

    # ---------------------------------------------------------
    # Restituisce i dati caricati
    # ---------------------------------------------------------
    def get_data(self):
        if not self.valid:
            return None

        return {
            "environment": self.environment,
            **self.loaded_data
        }

    def save(self):
        full_path = self.fileEdit.text().strip()
        filename = os.path.basename(full_path)
        name = self.sanitize_filename(os.path.splitext(filename)[0])

        if not name:
            QMessageBox.warning(self, "PDND", "Impossibile ricavare il nome dal file.")
            return
        
        ambiente = self.environment

        cfg = {
            "kid": self.previewKid.text().strip(),
            "issuer": self.previewIssuer.text().strip(),
            "clientId": self.previewClientId.text().strip(),
            "purposeId": self.previewPurposeId.text().strip(),
            "privKeyPath": self.previewPrivKey.text().strip(),
            "apiUrl": self.previewApiUrl.text().strip(),
            "debug": self.previewDebug.text().strip() == "Sì",
            "pretty": self.previewPretty.text().strip() == "Sì",
            "cache": self.previewCache.text().strip() == "Sì"
        }

        self.config_manager.create_configuration(name, cfg, ambiente)
        self.close()
    
    def sanitize_filename(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"[^\w]+", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")

        return name