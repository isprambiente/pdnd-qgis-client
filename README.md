# PDND QGIS Client

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![QGIS Plugin](https://img.shields.io/badge/QGIS-Plugin-green.svg)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![pdnd-python-client](https://img.shields.io/badge/uses-pdnd--python--client-orange.svg)](https://github.com/isprambiente/pdnd-python-client)
[![PublicCode](https://img.shields.io/badge/publiccode.yml-Compliant-0A66C2.svg)]()

---

## Descrizione

**PDND QGIS Client** è un plugin QGIS che permette di:

- configurare connessioni PDND tramite file JSON  
- generare automaticamente JWT e token PDND  
- interrogare API OAS3  
- estrarre endpoint WMS
- estrarre endpoint GeoJSON
- caricare layer WMS e GeoJSON protetti direttamente in QGIS  

È pensato per enti pubblici, ricercatori e sviluppatori che devono integrare servizi geospaziali protetti tramite la **Piattaforma Digitale Nazionale Dati (PDND)**.

---

## Dipendenze

Questo plugin include e utilizza in riuso il client Python PDND sviluppato dallo stesso ente (ISPRA):

| Libreria | Repository | Descrizione |
|---|---|---|
| `pdnd-python-client` | [isprambiente/pdnd-python-client](https://github.com/isprambiente/pdnd-python-client) | Client Python ISPRA per autenticazione PDND (JWT + token) — riuso interno |

---

## Funzionalità

- Gestione connessioni PDND (clientId, privateKey, kid, apiUrl)
- Generazione JWT + richiesta token PDND
- Parsing automatico del documento OAS3
- Individuazione degli endpoint WMS e GeoJSON
- Caricamento dei layer nel progetto QGIS
- Messaggi colorati tramite QGIS MessageBar
- Gestione errori PDND (token, API, OAS3)
- Compatibile con QGIS LTR 3.44+

---

## Screenshot

| Pannello PDND | Menu contestuale |
|:---:|:---:|
| ![Pannello PDND](docs/images/01_browser_panel.png) | ![Menu contestuale](docs/images/02_browser_panel_menu.png) |

| Nuova connessione | Modifica connessione |
|:---:|:---:|
| ![Nuova connessione](docs/images/03_config_panel_new.png) | ![Modifica connessione](docs/images/04_config_panel_edit.png) |

| Importa configurazione | Layer caricati in QGIS |
|:---:|:---:|
| ![Importa configurazione](docs/images/05_import_panel.png) | ![Layer caricati](docs/images/06_view_layers.png) |

---

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/isprambiente/pdnd-qgis-client.git
```
### 2. Copia il plugin nella cartella dei plugin QGIS

Windows
```bash
C:\Users\<utente>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
```
Linux
```bash
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

MacOS
```bash
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

### 3. Attiva il plugin QGIS

Apri QGIS  
Vai su `Plugin` → `Gestione e installazione dei plugin...`  
Cerca `PDND QGIS Client`  
Seleziona `Abilita plugin`

---

## Configurazione

### 1. Aggiungi una nuova connessione

Apri il pannello PDND: `Browser` → `PDND`

Clicca su `Nuova connessione`

Inserisci i parametri:

- Nome connessione: nome descrittivo  
- clientId: ID del tuo client PDND  
- privateKey: percorso del file JSON  
- kid: ID della chiave  
- apiUrl: URL API PDND (es. https://pdnd.developers.italia.it/api/v1)  
- ambiente: produzione | collaudo | attestazione

### 2. Crea il file JSON della configurazione

Il file JSON deve contenere la configurazione nel formato richiesto da PDND:

```json
{
  "<enviroment>": {
    "clientId": "…",
    "privateKey": "…",
    "kid": "…",
    "apiUrl": "https://api.pdnd/.../oas",
    "debug": false,
    "pretty": false,
    "cache": false
  }
}

```

---

## Riuso e PublicCode

Questo repository è conforme ai requisiti di PublicCode per il riuso nel settore pubblico italiano.

---

## Licenza

Questo progetto è rilasciato con licenza **MIT**.

Vedi il file `LICENSE` per i dettagli completi.

---

## Contributi

Pull request e segnalazioni sono benvenute.
Apri una issue o una PR nel repository GitHub.
