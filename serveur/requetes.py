"""Requêtes de lecture sur la base du catalogue (recherche, filtres, tri, pagination, fiches)."""
import math

from .normalisation import fold

CHAMPS_SORTIE = ("id", "auteur", "theme", "filiere_llm", "directeur", "annee_llm",
                 "filiere_chemin", "sous_filiere", "annee_chemin", "fichier", "filiere", "annee_ref")

TRIS = {
    "titre": "(theme_norm IS NULL OR theme_norm = ''), theme_norm, id",
    "auteur": "(auteur_norm IS NULL OR auteur_norm = ''), auteur_norm, id",
    "annee_desc": "annee_ref IS NULL, annee_ref DESC, theme_norm, id",
    "annee_asc": "annee_ref IS NULL, annee_ref ASC, theme_norm, id",
}


def _motif(texte: str) -> str:
    """Motif LIKE « contient » (les caractères spéciaux de LIKE sont échappés)."""
    return "%" + texte.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _conditions(q=None, filiere=None, annee=None, auteur=None):
    cond, params = [], []
    for mot in fold(q).split()[:10]:                      # tous les mots doivent être présents
        cond.append("recherche LIKE ? ESCAPE '\\'")
        params.append(_motif(mot))
    if filiere:
        cond.append("filiere = ?")
        params.append(filiere)
    if annee is not None:
        cond.append("annee_ref = ?")
        params.append(annee)
    for mot in fold(auteur).split()[:10]:
        cond.append("auteur_norm LIKE ? ESCAPE '\\'")
        params.append(_motif(mot))
    return (" WHERE " + " AND ".join(cond)) if cond else "", params


def _sortie(ligne) -> dict:
    return {c: ligne[c] for c in CHAMPS_SORTIE}


def lister(conn, q=None, filiere=None, annee=None, auteur=None, tri="titre", page=1, taille=24) -> dict:
    where, params = _conditions(q, filiere, annee, auteur)
    total = conn.execute(f"SELECT COUNT(*) FROM memoires{where}", params).fetchone()[0]
    pages = max(1, math.ceil(total / taille))
    page = min(max(1, page), pages)
    lignes = conn.execute(
        f"SELECT {', '.join(CHAMPS_SORTIE)} FROM memoires{where} ORDER BY {TRIS.get(tri, TRIS['titre'])} LIMIT ? OFFSET ?",
        params + [taille, (page - 1) * taille]).fetchall()
    return {"items": [_sortie(r) for r in lignes], "total": total, "page": page, "taille": taille, "pages": pages}


def facettes(conn) -> dict:
    filieres = conn.execute("SELECT filiere AS valeur, COUNT(*) AS total FROM memoires WHERE filiere IS NOT NULL "
                            "GROUP BY filiere ORDER BY total DESC, valeur").fetchall()
    annees = conn.execute("SELECT annee_ref AS valeur, COUNT(*) AS total FROM memoires WHERE annee_ref IS NOT NULL "
                          "GROUP BY annee_ref ORDER BY valeur").fetchall()
    return {"filieres": [dict(r) for r in filieres], "annees": [dict(r) for r in annees]}


def obtenir(conn, memoire_id: int):
    ligne = conn.execute(f"SELECT {', '.join(CHAMPS_SORTIE)} FROM memoires WHERE id = ?", (memoire_id,)).fetchone()
    return _sortie(ligne) if ligne else None


def total(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM memoires").fetchone()[0]
