"""Normalisation des données documentaires (fonctions pures, bibliothèque standard uniquement).

COPIE AUTONOME des règles de normalisation de l'application Bibliothèque Mémoires, figée
au moment du développement du catalogue : le catalogue n'importe jamais le code de l'application
principale. Les valeurs ORIGINALES ne sont jamais modifiées : tout ce qui est calculé ici alimente
des colonnes séparées (filiere, annee_ref, recherche, signature).
"""
import hashlib
import re
import unicodedata

FILIERE_INCONNUE = "Non classée"

# Valeurs « bouche-trou » présentes dans le fichier source : conservées telles
# quelles, mais considérées comme des informations manquantes.
PLACEHOLDERS = {
    "inconnu", "inconnue", "non specifie", "non specifiee", "non renseigne",
    "non renseignee", "n/a", "na", "nc", "-", "--", "0",
}


def fold(valeur) -> str:
    """Minuscules, sans accents, apostrophes unifiées, espaces compactés."""
    if valeur is None:
        return ""
    s = str(valeur)
    s = (s.replace("’", "'").replace("‘", "'").replace("œ", "oe").replace("Œ", "oe")
          .replace("æ", "ae").replace("Æ", "ae"))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().casefold()


def est_vide(valeur) -> bool:
    """Vrai si la valeur est absente ou n'est qu'un « bouche-trou » (Inconnu...)."""
    f = fold(valeur)
    return f == "" or f in PLACEHOLDERS


def nettoyer(valeur):
    """Retire uniquement les espaces de bord et les caractères nuls. ``None`` si vide."""
    if valeur is None:
        return None
    s = str(valeur).replace("\x00", "").strip()
    return s or None


# ---------------------------------------------------------------- années

_RE_ABREGE = re.compile(r"((?:19|20)\d{2})\s*/\s*(\d{2})")
_RE_ANNEE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")


def parse_annees(texte):
    """Retourne ``(annee_min, annee_max)`` ou ``None``.

    Exemples : ``2020`` -> (2020, 2020) ; ``2008-2009`` -> (2008, 2009) ;
    ``1979/80`` -> (1979, 1980) ; ``Non spécifié`` -> None ; ``AFT 2017`` -> (2017, 2017).
    """
    if not texte:
        return None
    t = str(texte).strip()
    m = _RE_ABREGE.fullmatch(t)
    if m:
        debut = int(m.group(1))
        fin = (debut // 100) * 100 + int(m.group(2))
        if fin < debut:
            fin += 100
        return debut, fin
    annees = [int(a) for a in _RE_ANNEE.findall(t)]
    if not annees:
        return None
    return min(annees), max(annees)


def annee_reference(annee_llm, annee_chemin):
    """Année utilisée pour filtrer/trier : fin de la période ``annee_llm`` si lisible,
    sinon année trouvée dans ``annee_chemin``, sinon ``None``."""
    p = parse_annees(annee_llm) or parse_annees(annee_chemin)
    return p[1] if p else None


# --------------------------------------------------------------- filières

# Libellés dérivés des codes de sous-filière présents dans le fichier (colonne
# « Sous-Filiere », issue du chemin des dossiers).
LIBELLES_CODES = {
    "AFT": "Administration des Finances et du Trésor",
    "GMP": "Gestion des Marchés Publics",
    "AI": "Administration des Impôts",
    "AHUI": "Administration Hospitalière, Universitaire et d'Intendance",
    "PDL": "Planification et Développement Local",
    "GFCL": "Gestion Financière des Collectivités Locales",
    "AAS": "Administration de l'Action Sociale",
    "ATSS": "Administration du Travail et de la Sécurité Sociale",
    "AGT": "Administration Générale et Territoriale",
    "GE": "Gestion des Entreprises",
    "AB": "Banque",
    "COMMERCE": "Commerce",
    "ACFT": "Administration Centrale des Finances et du Trésor",
}

# Règles appliquées au texte « Filiere (LLM) » normalisé, DANS CET ORDRE
# (les plus spécifiques d'abord, car le texte source mélange parfois plusieurs filières).
REGLES_FILIERES = [
    (("marches publics",), LIBELLES_CODES["GMP"]),
    (("impots",), LIBELLES_CODES["AI"]),
    (("hospitaliere",), LIBELLES_CODES["AHUI"]),
    (("developpement local",), LIBELLES_CODES["PDL"]),
    (("collectivites locales",), LIBELLES_CODES["GFCL"]),
    (("action sociale",), LIBELLES_CODES["AAS"]),
    (("securite sociale",), LIBELLES_CODES["ATSS"]),
    (("diplomatie",), "Diplomatie et Relations Internationales"),
    (("territoriale",), LIBELLES_CODES["AGT"]),
    (("ressources humaines", "(grh)", "(g.r.h)"), "Gestion des Ressources Humaines"),
    (("projet",), "Gestion des Projets"),
    (("patrimoine culturel",), "Gestion du Patrimoine Culturel"),
    (("magistrat", "justice", "greffe", "judiciaire"), "Magistrature et carrières judiciaires"),
    (("politiques publiques", "(epp)"), "Évaluation des Politiques Publiques"),
    (("tresor",), LIBELLES_CODES["AFT"]),
    (("banque",), LIBELLES_CODES["AB"]),
    (("gestion des entreprises", "gistion des entreprises"), LIBELLES_CODES["GE"]),
    (("commerce",), LIBELLES_CODES["COMMERCE"]),
    (("administration des finances",), "Administration des Finances (non précisée)"),
    (("administration generale",), "Administration Générale (non précisée)"),
]


def classer_filiere(filiere_llm, sous_filiere) -> str:
    """Filière normalisée. Le code de sous-filière (issu du dossier) prime ;
    à défaut, règles de mots-clés sur « Filiere (LLM) » ; sinon « Non classée »."""
    code = (sous_filiere or "").strip().upper()
    if code in LIBELLES_CODES:
        return LIBELLES_CODES[code]
    texte = fold(filiere_llm)
    if texte and texte not in PLACEHOLDERS:
        for mots, libelle in REGLES_FILIERES:
            if any(m in texte for m in mots):
                return libelle
        if texte == "droit":
            return "Magistrature et carrières judiciaires"
    return FILIERE_INCONNUE



# ------------------------------------------------------- champs calculés


def calculer_champs(data: dict) -> dict:
    """À partir des 9 champs originaux, produit les champs calculés du catalogue."""
    auteur_norm = fold(data.get("auteur"))
    theme_norm = fold(data.get("theme"))
    directeur_norm = fold(data.get("directeur"))
    fichier_norm = fold(data.get("fichier"))
    filiere = classer_filiere(data.get("filiere_llm"), data.get("sous_filiere"))
    annee_ref = annee_reference(data.get("annee_llm"), data.get("annee_chemin"))
    morceaux = [auteur_norm, theme_norm, directeur_norm, fichier_norm, fold(filiere),
                fold(data.get("sous_filiere")), fold(data.get("filiere_llm"))]
    recherche = " ".join(m for m in morceaux if m)
    signature = hashlib.sha1(f"{auteur_norm}|{theme_norm}|{fichier_norm}".encode("utf-8")).hexdigest()
    return {
        "auteur_norm": auteur_norm or None,
        "theme_norm": theme_norm or None,
        "filiere": filiere,
        "annee_ref": annee_ref,
        "recherche": recherche,
        "signature": signature,
    }
