"""Serveur web du catalogue : API de LECTURE SEULE + fichiers du site (dossier dist/).

Bibliothèque standard uniquement. Seules les méthodes GET et HEAD sont acceptées, et la base est
ouverte en lecture seule : ce serveur ne peut modifier aucune donnée.
"""
import json
import mimetypes
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from . import base, config, requetes

TRIS_VALIDES = set(requetes.TRIS)
_RE_ID = re.compile(r"^/api/memoires/(\d{1,12})(/document)?$")

PAGE_SANS_SITE = """<!doctype html><html lang="fr"><meta charset="utf-8"><title>Catalogue</title>
<body style="font-family:system-ui;max-width:40rem;margin:3rem auto;padding:0 1rem;line-height:1.5">
<h1>Le site n'est pas encore construit</h1>
<p>Le serveur du catalogue fonctionne (<a href="/api/sante">/api/sante</a>), mais le dossier <code>dist</code> est absent.</p>
<p>Construisez le site une fois : <code>npm install</code> puis <code>npm run build</code> (ou relancez <code>start.bat</code>).</p>
</body></html>"""


class Erreur(Exception):
    def __init__(self, statut, message, code="erreur"):
        super().__init__(message)
        self.statut, self.message, self.code = statut, message, code


def _entier(valeurs, nom, defaut=None, mini=None, maxi=None):
    brut = valeurs.get(nom, [None])[0]
    if brut in (None, ""):
        return defaut
    try:
        n = int(brut)
    except ValueError:
        raise Erreur(422, f"Paramètre « {nom} » invalide.", "parametre_invalide")
    if (mini is not None and n < mini) or (maxi is not None and n > maxi):
        raise Erreur(422, f"Paramètre « {nom} » hors limites.", "parametre_invalide")
    return n


def _texte(valeurs, nom, maxi=255):
    brut = valeurs.get(nom, [None])[0]
    if brut is None:
        return None
    if len(brut) > maxi:
        raise Erreur(422, f"Paramètre « {nom} » trop long.", "parametre_invalide")
    return brut.strip() or None


class _Index:
    """Index des PDF (nom de fichier -> chemin), construit à la demande si un dossier est configuré."""
    chemins = None

    @classmethod
    def trouver(cls, nom):
        if config.DOCUMENTS_DIR is None or not nom or not config.DOCUMENTS_DIR.is_dir():
            return None
        if cls.chemins is None:
            cls.chemins = {}
            for p in config.DOCUMENTS_DIR.rglob("*"):
                if p.is_file():
                    cls.chemins.setdefault(p.name.casefold(), p)
        return cls.chemins.get(Path(nom).name.casefold())


class Gestionnaire(BaseHTTPRequestHandler):
    server_version = "Catalogue"
    protocol_version = "HTTP/1.1"

    # ------------------------------------------------------------ utilitaires
    def log_message(self, *_):   # journal d'accès désactivé (seules les erreurs sont affichées)
        pass

    def _envoyer(self, statut, corps: bytes, type_="application/json; charset=utf-8", extra=None):
        self.send_response(statut)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corps)

    def _json(self, statut, objet):
        self._envoyer(statut, json.dumps(objet, ensure_ascii=False).encode("utf-8"), extra={"Cache-Control": "no-store"})

    # ---------------------------------------------------------------- routage
    def do_GET(self):
        try:
            chemin = urlsplit(self.path)
            url = unquote(chemin.path)
            if url.startswith("/api/") or url == "/api":
                self._api(url, parse_qs(chemin.query))
            else:
                self._site(url)
        except Erreur as e:
            self._json(e.statut, {"detail": {"code": e.code, "message": e.message}})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # erreur inattendue : jamais de trace envoyée au navigateur
            print(f"Erreur interne : {e!r}", file=sys.stderr)
            try:
                self._json(500, {"detail": {"code": "erreur_interne", "message": "Erreur interne du serveur."}})
            except Exception:
                pass

    do_HEAD = do_GET

    def _refuser(self):
        corps = json.dumps({"detail": {"code": "lecture_seule",
                                       "message": "Ce catalogue est en lecture seule."}}).encode("utf-8")
        self._envoyer(405, corps, extra={"Allow": "GET, HEAD"})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _refuser

    # -------------------------------------------------------------------- API
    def _api(self, url, valeurs):
        if not base.existe():
            raise Erreur(503, "Base de données absente : lancez l'importation.", "base_absente")
        conn = base.ouvrir_lecture()
        try:
            if url == "/api/sante":
                return self._json(200, {"statut": "ok", "memoires": requetes.total(conn)})
            if url == "/api/memoires":
                tri = _texte(valeurs, "tri", 20) or "titre"
                if tri not in TRIS_VALIDES:
                    raise Erreur(422, "Tri inconnu.", "parametre_invalide")
                return self._json(200, requetes.lister(
                    conn, q=_texte(valeurs, "q", 200), filiere=_texte(valeurs, "filiere"),
                    annee=_entier(valeurs, "annee", None, 1900, 2100), auteur=_texte(valeurs, "auteur", 200),
                    tri=tri, page=_entier(valeurs, "page", 1, 1), taille=_entier(valeurs, "taille", 24, 1, 100)))
            if url == "/api/memoires/facettes":
                return self._json(200, requetes.facettes(conn))
            m = _RE_ID.match(url)
            if m:
                fiche = requetes.obtenir(conn, int(m.group(1)))
                if fiche is None:
                    raise Erreur(404, "Mémoire introuvable.", "introuvable")
                pdf = _Index.trouver(fiche["fichier"])
                if m.group(2):
                    if pdf is None:
                        raise Erreur(404, "Document introuvable.", "document_introuvable")
                    return self._envoyer(200, pdf.read_bytes(), "application/pdf",
                                         {"Content-Disposition": "inline"})
                fiche["document_disponible"] = pdf is not None
                return self._json(200, fiche)
            raise Erreur(404, "Adresse inconnue.", "introuvable")
        finally:
            conn.close()

    # ------------------------------------------------------------------- site
    def _site(self, url):
        dist = config.DIST_DIR
        if not (dist / "index.html").is_file():
            return self._envoyer(200, PAGE_SANS_SITE.encode("utf-8"), "text/html; charset=utf-8")
        racine = dist.resolve()
        cible = (racine / url.lstrip("/")).resolve()
        if cible.is_file() and (cible == racine or racine in cible.parents):
            type_ = mimetypes.guess_type(cible.name)[0] or "application/octet-stream"
            if type_.startswith("text/") or type_ in ("application/javascript", "application/json"):
                type_ += "; charset=utf-8"
            cache = "public, max-age=31536000, immutable" if "/assets/" in url else "no-cache"
            return self._envoyer(200, cible.read_bytes(), type_, {"Cache-Control": cache})
        if Path(url).suffix and "/assets/" in url:   # fichier de ressource réellement absent
            return self._envoyer(404, b"Not found", "text/plain; charset=utf-8")
        # routes de l'application (/memoire/12, etc.) : on renvoie la page d'accueil du site
        self._envoyer(200, (dist / "index.html").read_bytes(), "text/html; charset=utf-8", {"Cache-Control": "no-cache"})


def creer_serveur(host=None, port=None) -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((host or config.HOST, config.PORT if port is None else port), Gestionnaire)
    srv.daemon_threads = True
    return srv
