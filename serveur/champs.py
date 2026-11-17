"""Champs documentaires du catalogue : les 9 colonnes du fichier Excel d'origine."""

CHAMPS_ORIGINAUX = (
    "auteur", "theme", "filiere_llm", "directeur", "annee_llm",
    "filiere_chemin", "sous_filiere", "annee_chemin", "fichier",
)

# Une ligne n'est exploitable que si l'un de ces champs au moins est renseigné.
CHAMPS_IDENTIFIANTS = ("auteur", "theme", "fichier")
CHAMPS_ANNEE = ("annee_llm", "annee_chemin")

LONGUEURS_MAX = {
    "auteur": 1000, "theme": 2000, "filiere_llm": 500, "directeur": 500, "annee_llm": 100,
    "filiere_chemin": 255, "sous_filiere": 100, "annee_chemin": 100, "fichier": 500,
}

# En-têtes reconnus automatiquement (comparés après normalisation : minuscules, sans accents).
SYNONYMES = {
    "auteur": ["auteur", "auteurs", "auteur(s)", "nom", "author"],
    "theme": ["theme", "theme (titre)", "titre", "sujet", "title", "intitule"],
    "filiere_llm": ["filiere (llm)", "filiere llm", "filiere", "specialite"],
    "directeur": ["directeur", "directeur de memoire", "encadreur", "superviseur"],
    "annee_llm": ["annee (llm)", "annee llm", "annee", "annee de soutenance"],
    "filiere_chemin": ["filiere (chemin)", "filiere chemin"],
    "sous_filiere": ["sous-filiere", "sous filiere", "sousfiliere"],
    "annee_chemin": ["annee (chemin)", "annee chemin"],
    "fichier": ["fichier", "nom du fichier", "nom de fichier", "document", "pdf"],
}
