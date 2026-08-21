import os
import gc
import json
import requests
from qgis.PyQt.QtCore import QTimer
from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProject
)
from .api_client import ApiClient
from .pdnd_logger import log_info, log_error


class PdndLayerLoader:

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.cache_root = os.path.join(config_manager.plugin_dir, "cache")
        os.makedirs(self.cache_root, exist_ok=True)

    # ---------------------------------------------------------
    # CACHE
    # ---------------------------------------------------------
    def get_cache_dir(self, name):
        path = os.path.join(self.cache_root, name)
        os.makedirs(path, exist_ok=True)
        return path

    def clear_cache(self, name):
        """Cancella SOLO file non-GeoJSON (Windows blocca i GeoJSON)."""
        cache_dir = self.get_cache_dir(name)
        for f in os.listdir(cache_dir):
            if f.endswith(".geojson"):
                continue  # NON cancellare GeoJSON
            try:
                os.remove(os.path.join(cache_dir, f))
            except Exception as e:
                log_error(f"Errore cancellazione cache: {e}")

    def cache_write(self, name, filename, data):
        """Sovrascrive SEMPRE il file, anche se QGIS lo sta usando."""
        cache_dir = self.get_cache_dir(name)
        path = os.path.join(cache_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

        return path

    def cache_read_json(self, name, filename):
        cache_dir = self.get_cache_dir(name)
        path = os.path.join(cache_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------------------------------------------------------
    # GROUP MANAGEMENT
    # ---------------------------------------------------------
    def get_or_create_group(self, name):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(name)

        if group:
            # Svuota il gruppo esistente
            for child in list(group.children()):
                group.removeChildNode(child)
            return group

        return root.addGroup(name)

    # ---------------------------------------------------------
    # MAIN LOAD
    # ---------------------------------------------------------
    def load(self, name, refresh=False):
        log_info(f"Caricamento layer PDND: {name}")

        json_path = self.config_manager.get_json_path(name)
        cfg = self.config_manager.load_configuration(name)

        apiUrl = cfg.get("apiUrl")
        if not apiUrl:
            raise Exception("apiUrl mancante nella configurazione.")

        cache = cfg.get("cache", False)

        # Refresh
        if refresh:
            log_info(f"Refresh richiesto: elimino gruppo '{name}' e tutti i layer contenuti")
            self.remove_group_and_layers(name)

            if not cache:
                log_info("Pulizia cache (solo file non-GeoJSON)")
                QTimer.singleShot(300, lambda: self.clear_cache(name))

        # Token PDND
        api = ApiClient()
        token = api.get_token_from_file(json_path)

        # Scarica dati API
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(apiUrl, headers=headers)

        if resp.status_code != 200:
            raise Exception(f"Errore API PDND: {resp.status_code}")

        data = resp.json()

        # ---------------------------------------------------------
        # CASO 1: GeoJSON diretto
        # ---------------------------------------------------------
        if data.get("type") == "FeatureCollection":
            log_info("GeoJSON diretto rilevato.")
            cache_path = self.cache_write(name, "data.geojson", json.dumps(data))

            group = self.get_or_create_group(name)
            layer = self.load_geojson_layer(name, cache_path)

            if layer:
                QgsProject.instance().addMapLayer(layer, False)
                group.addLayer(layer)

            return True

        # ---------------------------------------------------------
        # CASO 2: OAS3
        # ---------------------------------------------------------
        oas_json = None
        oas_cached = self.cache_read_json(name, "oas.json")

        if cache and oas_cached:
            log_info("Uso OAS dalla cache.")
            oas_json = oas_cached
        else:
            oas_json = data
            self.cache_write(name, "oas.json", json.dumps(oas_json, indent=2))

        wms_urls = self.detect_wms_endpoints(oas_json)
        geojson_endpoints = self.detect_geojson_endpoints(oas_json)

        if not wms_urls and not geojson_endpoints:
            raise Exception("Nessun endpoint WMS o GeoJSON trovato.")

        group = self.get_or_create_group(name)

        # WMS
        for url in wms_urls:
            layer = self.load_wms_layer(name, url)
            if layer:
                QgsProject.instance().addMapLayer(layer, False)
                group.addLayer(layer)

        # GeoJSON da endpoint
        for endpoint in geojson_endpoints:
            geojson_path = self.download_geojson(name, endpoint, token)
            layer = self.load_geojson_layer(name, geojson_path)
            if layer:
                QgsProject.instance().addMapLayer(layer, False)
                group.addLayer(layer)

        return True

    # ---------------------------------------------------------
    # DETECTORS
    # ---------------------------------------------------------
    def detect_wms_endpoints(self, oas):
        urls = []
        for path, methods in oas.get("paths", {}).items():
            get = methods.get("get")
            if not get:
                continue

            servers = get.get("servers", [])
            for srv in servers:
                url = srv.get("url")
                if url and "wms" in url.lower():
                    urls.append(url)

        log_info(f"Endpoint WMS trovati: {len(urls)}")
        return urls

    def detect_geojson_endpoints(self, oas):
        endpoints = []
        for path, methods in oas.get("paths", {}).items():
            get = methods.get("get")
            if not get:
                continue

            responses = get.get("responses", {})
            r200 = responses.get("200", {})
            content = r200.get("content", {})

            if "application/geo+json" in content:
                endpoints.append(path)
                continue

            if "application/json" in content:
                endpoints.append(path)

        log_info(f"Endpoint GeoJSON trovati: {len(endpoints)}")
        return endpoints

    # ---------------------------------------------------------
    # DOWNLOAD GEOJSON
    # ---------------------------------------------------------
    def download_geojson(self, name, endpoint, token):
        cfg = self.config_manager.load_configuration(name)
        base_url = cfg.get("apiUrl").rstrip("/")

        url = f"{base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        log_info(f"Scarico GeoJSON da: {url}")
        resp = requests.get(url, headers=headers)

        if resp.status_code != 200:
            raise Exception(f"Errore GeoJSON {endpoint}: {resp.status_code}")

        geojson_text = resp.text
        filename = f"geojson_{endpoint.strip('/').replace('/', '_')}.geojson"

        # Sovrascrive SEMPRE
        return self.cache_write(name, filename, geojson_text)

    # ---------------------------------------------------------
    # LOADERS
    # ---------------------------------------------------------
    def load_wms_layer(self, name, url):
        layer = QgsRasterLayer(
            f"url={url}&format=image/png&crs=EPSG:3857",
            f"{name} - WMS",
            "wms"
        )

        if not layer.isValid():
            log_error(f"Layer WMS non valido: {url}")
            return None

        log_info(f"Layer WMS pronto: {url}")
        return layer

    def load_geojson_layer(self, name, path):
        layer = QgsVectorLayer(path, f"{name} - GeoJSON", "ogr")

        if not layer.isValid():
            log_error(f"Layer GeoJSON non valido: {path}")
            return None

        log_info(f"Layer GeoJSON pronto: {path}")
        return layer

    # ---------------------------------------------------------
    # REMOVE GROUP + LAYERS
    # ---------------------------------------------------------
    def remove_group_and_layers(self, name):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(name)

        if not group:
            return

        # Rimuovi tutti i layer del gruppo
        for child in list(group.children()):
            if hasattr(child, "layerId"):
                layer_id = child.layerId()
                layer = QgsProject.instance().mapLayer(layer_id)

                log_info(f"Layer rimosso: {layer.name()}")

                QgsProject.instance().removeMapLayer(layer_id)

                # Elimina riferimenti Python
                del layer

        # Rimuovi il gruppo
        parent = group.parent()
        parent.removeChildNode(group)

        log_info(f"Gruppo rimosso: {name}")

        gc.collect()
