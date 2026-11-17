import json
import sqlite3
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from unittest import mock
from xml.sax.saxutils import escape

from serveur import api, config

ENTETES = ["Auteur", "Theme", "Filiere (LLM)", "Directeur", "Annee (LLM)",
           "Filiere (Chemin)", "Sous-Filiere", "Annee (Chemin)", "Fichier"]


def fabriquer_xlsx(chemin: Path, lignes: list, partage: bool = True):
    """Crée un petit .xlsx valide sans aucune bibliothèque (chaînes partagées ou en ligne)."""
    partages, cellules = [], []

    def ref(i, j):
        return f"{chr(65 + j)}{i + 1}"
    for i, ligne in enumerate(lignes):
        xs = []
        for j, v in enumerate(ligne):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                xs.append(f'<c r="{ref(i, j)}"><v>{v}</v></c>')
            elif partage:
                partages.append(v)
                xs.append(f'<c r="{ref(i, j)}" t="s"><v>{len(partages) - 1}</v></c>')
            else:
                xs.append(f'<c r="{ref(i, j)}" t="inlineStr"><is><t>{escape(v)}</t></is></c>')
        cellules.append(f'<row r="{i + 1}">{"".join(xs)}</row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("xl/workbook.xml", f'<workbook {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Feuil1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="x"/></Relationships>')
        if partage:
            z.writestr("xl/sharedStrings.xml", f'<sst {ns}>' + "".join(f"<si><t>{escape(s)}</t></si>" for s in partages) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {ns}><sheetData>{"".join(cellules)}</sheetData></worksheet>')


def ligne(auteur, theme, fichier, filiere="Impôts", directeur=None, annee="2020-2021", sous=None):
    return [auteur, theme, filiere, directeur, annee, None, sous, None, fichier]


class Environnement:
    """Base et dossiers temporaires : ne touche jamais au dossier data/ du projet."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        racine = Path(self.tmp.name)
        self.racine = racine
        self.patchs = [mock.patch.object(config, "DATA_DIR", racine / "data"),
                       mock.patch.object(config, "DB_PATH", racine / "data" / "catalogue.db"),
                       mock.patch.object(config, "SAUVEGARDES_DIR", racine / "data" / "sauvegardes"),
                       mock.patch.object(config, "DIST_DIR", racine / "dist"),
                       mock.patch.object(config, "DOCUMENTS_DIR", None)]
        for p in self.patchs:
            p.start()
        api._Index.chemins = None
        return self

    def __exit__(self, *exc):
        for p in self.patchs:
            p.stop()
        self.tmp.cleanup()


class Serveur:
    def __enter__(self):
        self.srv = api.creer_serveur(host="127.0.0.1", port=0)
        self.port = self.srv.server_address[1]
        self.fil = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.fil.start()
        return self

    def __exit__(self, *exc):
        self.srv.shutdown()
        self.srv.server_close()

    def requete(self, chemin, methode="GET"):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{chemin}", method=methode)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                corps = r.read()
                return r.status, dict(r.headers), corps
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, chemin):
        statut, _, corps = self.requete(chemin)
        return statut, json.loads(corps)


def creer_base_principale(chemin: Path, fiches: list, corbeille: list = ()):
    """Imite la base de l'application principale (table `memoires`) pour tester l'import --base."""
    conn = sqlite3.connect(chemin)
    conn.execute("CREATE TABLE memoires (id INTEGER PRIMARY KEY, auteur TEXT, theme TEXT, filiere_llm TEXT, directeur TEXT, "
                 "annee_llm TEXT, filiere_chemin TEXT, sous_filiere TEXT, annee_chemin TEXT, fichier TEXT, deleted_at TEXT)")
    for supprime, groupe in ((None, fiches), ("2026-01-01", corbeille)):
        for f in groupe:
            conn.execute("INSERT INTO memoires(auteur, theme, filiere_llm, directeur, annee_llm, filiere_chemin, sous_filiere, "
                         "annee_chemin, fichier, deleted_at) VALUES (?,?,?,?,?,?,?,?,?,?)", list(f) + [supprime])
    conn.commit()
    conn.close()
