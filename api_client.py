import os
import json
import time
from .pdnd_token_cache import TokenCache
from .vendor.pdnd_client.config import Config
from .vendor.pdnd_client.jwt_generator import JWTGenerator
from .pdnd_logger import log_info, log_error


class ApiClient:

    def __init__(self):
        self.cache = TokenCache()

    def get_token_from_file(self, json_path):
        log_info(f"Caricamento configurazione da: {json_path}", json_path)

        if not os.path.exists(json_path):
            raise Exception(f"File JSON non trovato: {json_path}", json_path)

        # Carica JSON PDND
        with open(json_path, "r") as f:
            wrapper = json.load(f)

        # wrapper = { "produzione": { ... } }
        ambiente = list(wrapper.keys())[0]
        cfg = wrapper[ambiente]

        # Costruisci Config PDND (solo path!)
        config = Config(json_path)

        log_info(f"Ambiente PDND: {ambiente}", json_path, config)

        # Debug PDND
        if cfg.get("debug", False):
            config.debug = True
            log_info("DEBUG PDND attivato.", json_path, config)

        # Pretty JSON
        if cfg.get("pretty", False):
            config.pretty = True
            log_info("Pretty JSON attivato.", json_path, config)

        # Cache token
        cached = self.cache.get(json_path)
        if cached:
            log_info("Token recuperato dalla cache.", json_path, config)
            return cached

        # Generazione token
        log_info("Generazione nuovo token PDND...", json_path, config)
        jwt_gen = JWTGenerator(config)

        try:
            token, exp = jwt_gen.request_token()
        except Exception as e:
            log_error(f"Errore generazione token: {e}")
            raise Exception("Impossibile generare token PDND.")

        log_info(f"Token generato. Scadenza UNIX: {exp}", json_path, config)
        log_info(f"Token (primi 50 caratteri): {token[:50]}...", json_path, config)

        self.cache.store(json_path, token, exp)
        return token
