"""Base de données propre au catalogue (SQLite, fichier data/catalogue.db)."""
import sqlite3
from pathlib import Path

from . import config

VERSION_SCHEMA = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS memoires (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signature       TEXT NOT NULL UNIQUE,   -- clé anti-doublon : sha1(auteur|thème|fichier normalisés)
    empreinte       TEXT NOT NULL,          -- sha1 des 9 champs d'origine (détecte les changements)
    auteur          TEXT,
    theme           TEXT,
    filiere_llm     TEXT,
    directeur       TEXT,
    annee_llm       TEXT,
    filiere_chemin  TEXT,
    sous_filiere    TEXT,
    annee_chemin    TEXT,
    fichier         TEXT,
    filiere         TEXT,                   -- calculé : filière normalisée
    annee_ref       INTEGER,                -- calculé : année de référence
    auteur_norm     TEXT,
    theme_norm      TEXT,
    recherche       TEXT,
    cree_le         TEXT NOT NULL,
    maj_le          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memoires_filiere ON memoires(filiere);
CREATE INDEX IF NOT EXISTS idx_memoires_annee ON memoires(annee_ref);
CREATE INDEX IF NOT EXISTS idx_memoires_theme ON memoires(theme_norm);

CREATE TABLE IF NOT EXISTS imports (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    date_import        TEXT NOT NULL,
    source             TEXT NOT NULL,
    type_source        TEXT NOT NULL,
    sha256_source      TEXT,
    lignes_lues        INTEGER NOT NULL,
    lignes_rejetees    INTEGER NOT NULL,
    doublons_fusionnes INTEGER NOT NULL,
    ajoutees           INTEGER NOT NULL,
    mises_a_jour       INTEGER NOT NULL,
    inchangees         INTEGER NOT NULL,
    absentes_source    INTEGER NOT NULL,
    supprimees         INTEGER NOT NULL,
    total_apres        INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT NOT NULL);
"""


def existe(chemin: Path = None) -> bool:
    chemin = chemin or config.DB_PATH
    return chemin.is_file() and chemin.stat().st_size > 0


def ouvrir_ecriture(chemin: Path = None) -> sqlite3.Connection:
    """Connexion en écriture : réservée à l'initialisation et à l'importation."""
    chemin = chemin or config.DB_PATH
    chemin.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(chemin, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def initialiser(chemin: Path = None) -> bool:
    """Crée la base et son schéma si elle n'existe pas. Retourne True si elle vient d'être créée."""
    chemin = chemin or config.DB_PATH
    creee = not existe(chemin)
    conn = ouvrir_ecriture(chemin)
    try:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO meta(cle, valeur) VALUES ('version_schema', ?)", (str(VERSION_SCHEMA),))
    finally:
        conn.close()
    return creee


def ouvrir_lecture(chemin: Path = None) -> sqlite3.Connection:
    """Connexion en LECTURE SEULE (mode=ro) : le serveur web ne peut rien écrire dans la base."""
    chemin = (chemin or config.DB_PATH).resolve()
    conn = sqlite3.connect(f"{chemin.as_uri()}?mode=ro", uri=True, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn
