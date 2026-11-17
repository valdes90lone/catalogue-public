"""Configuration du catalogue (variables d'environnement facultatives, valeurs par défaut sûres)."""
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("CATALOGUE_DATA_DIR") or RACINE / "data")
DB_PATH = DATA_DIR / "catalogue.db"
SAUVEGARDES_DIR = DATA_DIR / "sauvegardes"
DIST_DIR = RACINE / "dist"
HOST = os.environ.get("CATALOGUE_HOST", "127.0.0.1")
PORT = int(os.environ.get("CATALOGUE_PORT", "5174"))
# Dossier des PDF (facultatif) : sans lui, aucun lien « Ouvrir le document » n'est proposé.
DOCUMENTS_DIR = Path(os.environ["CATALOGUE_DOCUMENTS_DIR"]) if os.environ.get("CATALOGUE_DOCUMENTS_DIR") else None
SAUVEGARDES_A_GARDER = 10
