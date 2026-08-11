import os
import json

class ConfigManager:

    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.conn_dir = os.path.join(plugin_dir, "connections")
        self.index_path = os.path.join(self.conn_dir, "index.json")

        if not os.path.exists(self.conn_dir):
            os.makedirs(self.conn_dir)

        if not os.path.exists(self.index_path):
            with open(self.index_path, "w") as f:
                json.dump({}, f)

    def _load_index(self):
        with open(self.index_path, "r") as f:
            return json.load(f)

    def _save_index(self, index):
        with open(self.index_path, "w") as f:
            json.dump(index, f, indent=2)

    def list_configurations(self):
        return list(self._load_index().keys())

    def get_json_path(self, name):
        index = self._load_index()
        return index.get(name)

    def get_environment(self, name):
        json_path = self.get_json_path(name)
        with open(json_path, "r") as f:
            wrapper = json.load(f)
        return list(wrapper.keys())[0]


    def create_configuration(self, name, cfg, ambiente):
        json_path = os.path.join(self.conn_dir, f"{name}.json")

        wrapper = { ambiente: cfg }

        with open(json_path, "w") as f:
            if cfg.get("pretty", False):
                json.dump(wrapper, f, indent=2, sort_keys=True)
            else:
                json.dump(wrapper, f)

        # aggiorna index
        index = self._load_index()
        index[name] = json_path
        self._save_index(index)

    def delete_configuration(self, name):
        index = self._load_index()

        if name not in index:
            return

        # elimina file JSON
        json_path = index[name]
        if os.path.exists(json_path):
            os.remove(json_path)

        # elimina voce da index
        del index[name]
        self._save_index(index)

    def export_connections(self):
        path, _ = QFileDialog.getSaveFileName(None, "Esporta Connessioni", "", "JSON (*.json)")
        if not path:
            return

        index = self._load_index()
        with open(path, "w") as f:
            json.dump(index, f, indent=2)

    def import_connections(self):
        path, _ = QFileDialog.getOpenFileName(None, "Importa Connessioni", "", "JSON (*.json)")
        if not path:
            return

        with open(path, "r") as f:
            index = json.load(f)

        # index deve essere: { "rendis": "path/to/rendis.json", ... }
        self._save_index(index)

    def load_configuration(self, name):
        """
        Carica il contenuto del file JSON PDND relativo alla connessione 'name'.
        Restituisce il dict interno (es: {"kid": "...", "issuer": "...", ...}).
        """
        json_path = self.get_json_path(name)
        if not json_path:
            raise Exception(f"Connessione '{name}' non trovata nell'index.json")

        if not isinstance(json_path, str):
            raise Exception(f"Percorso JSON non valido per '{name}': {json_path}")

        if not os.path.exists(json_path):
            raise Exception(f"File JSON non trovato: {json_path}")

        with open(json_path, "r") as f:
            wrapper = json.load(f)

        # wrapper = { "produzione": { ... } } oppure { "collaudo": { ... } }
        if len(wrapper.keys()) != 1:
            raise Exception("Formato JSON PDND non valido: wrapper deve avere una sola chiave")

        ambiente = list(wrapper.keys())[0]
        cfg = wrapper[ambiente]

        return cfg
