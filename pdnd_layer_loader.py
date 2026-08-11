from qgis.core import QgsRasterLayer, QgsProject
from .api_client import ApiClient
from .pdnd_logger import log_info, log_error
import requests
import os
import json

class PdndLayerLoader:

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def load(self, name):
        log_info(f"Caricamento layer PDND: {name}")

        # 1) Percorso del JSON
        json_path = self.config_manager.get_json_path(name)

        # 2) Carica la configurazione corretta
        cfg = self.config_manager.load_configuration(name)

        apiUrl = cfg.get("apiUrl")
        if not apiUrl:
            raise Exception("apiUrl mancante nella configurazione.")

        # 3) Ottieni token PDND
        api = ApiClient()
        token = api.get_token_from_file(json_path)

        # 4) Chiama API PDND (OAS3)
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(apiUrl, headers=headers)

        if resp.status_code != 200:
            raise Exception(f"Errore API PDND: {resp.status_code}")

        oas = resp.json()

        # 5) Estrai URL WMS dal JSON OAS3
        wms_urls = []

        for path, methods in oas.get("paths", {}).items():
            get = methods.get("get")
            if not get:
                continue

            servers = get.get("servers", [])
            for srv in servers:
                url = srv.get("url")
                if url and "wms" in url.lower():
                    wms_urls.append(url)

        if not wms_urls:
            raise Exception("Nessun URL WMS trovato nell'OAS3.")

        # 6) Crea layer WMS in QGIS
        for url in wms_urls:
            layer = QgsRasterLayer(
                f"url={url}&format=image/png&crs=EPSG:3857",
                f"{name} - WMS",
                "wms"
            )

            if not layer.isValid():
                log_error(f"Layer non valido: {url}")
                continue

            QgsProject.instance().addMapLayer(layer)
            log_info(f"Layer WMS caricato: {url}")

        return True


