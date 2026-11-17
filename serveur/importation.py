"""Importation (initiale ou mise à jour) des mémoires dans la base du catalogue.

Deux sources, lues SANS jamais les modifier et sans lancer l'application principale :
  * le fichier de base de données SQLite de l'application principale (copié dans un dossier
    temporaire avant lecture) ;
  * un fichier Excel .xlsx (les 9 colonnes d'origine).

Anti-doublons : chaque fiche a une signature (auteur + thème + fichier normalisés) UNIQUE dans la base.
Réimporter la même source ne crée donc aucun doublon : les fiches identiques sont « inchangées »,
les fiches modifiées sont mises à jour, les nouvelles sont ajoutées.
"""
import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import base, config
from .champs import (CHAMPS_ANNEE, CHAMPS_IDENTIFIANTS, CHAMPS_ORIGINAUX, LONGUEURS_MAX, SYNONYMES)
from .lecteur_xlsx import ErreurXlsx, lire_xlsx
from .normalisation import calculer_champs, fold, nettoyer

_INDEX_SYNONYMES = {fold(s): champ for champ, liste in SYNONYMES.items() for s in liste}
_RE_TOTAL = re.compile(r"^(total|sous-total|nombre)\b")


class ErreurImport(Exception):
    """Source inutilisable ou import refusé (message destiné à l'utilisateur)."""


def maintenant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


# ------------------------------------------------------------------ sources

def _nettoyer_annee(valeur):
    if valeur and re.fullmatch(r"\d{4}\.0+", valeur):
        return valeur.split(".")[0]
    return valeur


def _detecter_entete(lignes, max_scan: int = 15) -> int:
    meilleur, score_max = 0, 0
    for i, ligne in enumerate(lignes[:max_scan]):
        score = sum(1 for c in ligne if c and fold(c) in _INDEX_SYNONYMES)
        if score > score_max:
            meilleur, score_max = i, score
    return meilleur


def lire_excel(chemin: Path, feuille=None) -> dict:
    """-> {'enregistrements': [dict], 'lues': n, 'rejetees': n, 'ignorees': n}"""
    try:
        lignes = lire_xlsx(chemin, feuille)
    except ErreurXlsx as exc:
        raise ErreurImport(str(exc)) from exc
    if not lignes:
        raise ErreurImport("La feuille est vide.")
    lignes = [[nettoyer(c) for c in ligne] for ligne in lignes]
    i_entete = _detecter_entete(lignes)
    entetes = lignes[i_entete]
    positions, utilisees = {}, set()
    for champ in CHAMPS_ORIGINAUX:
        for syn in SYNONYMES[champ]:
            for pos, nom in enumerate(entetes):
                if nom and fold(nom) == fold(syn) and pos not in utilisees:
                    positions[champ] = pos
                    utilisees.add(pos)
                    break
            if champ in positions:
                break
    if not any(c in positions for c in CHAMPS_IDENTIFIANTS):
        raise ErreurImport("Colonnes introuvables : le fichier doit contenir au moins « Auteur », « Theme » ou « Fichier ».")

    sortie, rejetees, ignorees = [], 0, 0
    for brut in lignes[i_entete + 1:]:
        remplies = [c for c in brut if c]
        if not remplies:
            ignorees += 1
            continue
        if len(remplies) <= 2 and any(_RE_TOTAL.match(fold(c)) for c in remplies):
            ignorees += 1
            continue
        data = {}
        for champ in CHAMPS_ORIGINAUX:
            pos = positions.get(champ)
            valeur = brut[pos] if pos is not None and pos < len(brut) else None
            if champ in CHAMPS_ANNEE:
                valeur = _nettoyer_annee(valeur)
            if valeur and len(valeur) > LONGUEURS_MAX[champ]:
                valeur = valeur[:LONGUEURS_MAX[champ]]
            data[champ] = valeur
        if not any(data[c] for c in CHAMPS_IDENTIFIANTS):
            rejetees += 1
            continue
        sortie.append(data)
    return {"enregistrements": sortie, "lues": len(sortie) + rejetees, "rejetees": rejetees, "ignorees": ignorees}


def lire_base_principale(chemin: Path) -> dict:
    """Lit les fiches actives (hors corbeille) de la base de l'application principale.

    La base est d'abord COPIÉE dans un dossier temporaire puis ouverte en lecture seule : le fichier
    d'origine n'est jamais ouvert en écriture ni verrouillé, et peut être en cours d'utilisation."""
    with tempfile.TemporaryDirectory(prefix="catalogue-src-") as tmp:
        copie = Path(tmp) / "source.db"
        shutil.copyfile(chemin, copie)
        for suffixe in ("-wal", "-shm"):
            annexe = Path(str(chemin) + suffixe)
            if annexe.is_file():
                shutil.copyfile(annexe, Path(str(copie) + suffixe))
        try:
            conn = sqlite3.connect(f"{copie.as_uri()}?mode=ro", uri=True)
            colonnes = {r[1] for r in conn.execute("PRAGMA table_info(memoires)")}
            manquantes = [c for c in CHAMPS_ORIGINAUX if c not in colonnes]
            if not colonnes or manquantes:
                conn.close()
                raise ErreurImport("Ce fichier n'est pas la base de l'application Bibliothèque Mémoires "
                                   "(table « memoires » ou colonnes d'origine absentes).")
            filtre = "WHERE deleted_at IS NULL" if "deleted_at" in colonnes else ""
            lignes = conn.execute(f"SELECT {', '.join(CHAMPS_ORIGINAUX)} FROM memoires {filtre} ORDER BY id").fetchall()
            conn.close()
        except sqlite3.DatabaseError as exc:
            raise ErreurImport(f"Base illisible : {exc}") from exc
    sortie, rejetees = [], 0
    for ligne in lignes:
        data = {c: nettoyer(v) for c, v in zip(CHAMPS_ORIGINAUX, ligne)}
        if not any(data[c] for c in CHAMPS_IDENTIFIANTS):
            rejetees += 1
            continue
        sortie.append(data)
    return {"enregistrements": sortie, "lues": len(lignes), "rejetees": rejetees, "ignorees": 0}


# --------------------------------------------------------------- sauvegarde

def sauvegarder_avant_import() -> "Path | None":
    """Copie cohérente de la base actuelle (si elle contient des données) avant toute modification."""
    if not base.existe():
        return None
    conn = base.ouvrir_lecture()
    try:
        if not conn.execute("SELECT COUNT(*) FROM memoires").fetchone()[0]:
            return None
        config.SAUVEGARDES_DIR.mkdir(parents=True, exist_ok=True)
        cible = config.SAUVEGARDES_DIR / f"catalogue-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
        dest = sqlite3.connect(cible)
        conn.backup(dest)
        dest.close()
    finally:
        conn.close()
    anciennes = sorted(config.SAUVEGARDES_DIR.glob("catalogue-*.db"))
    for vieille in anciennes[:-config.SAUVEGARDES_A_GARDER]:
        vieille.unlink()
    return cible


# --------------------------------------------------------------- importation

def _completude(data: dict) -> int:
    return sum(1 for c in CHAMPS_ORIGINAUX if data.get(c))


def _empreinte(data: dict) -> str:
    return hashlib.sha1(json.dumps([data.get(c) for c in CHAMPS_ORIGINAUX], ensure_ascii=False).encode("utf-8")).hexdigest()


def importer(source: Path, type_source: str, *, synchroniser: bool = False, feuille=None) -> dict:
    """Importe `source` ('excel' ou 'base') dans la base du catalogue. Retourne un rapport.

    synchroniser=False : ajoute les nouvelles fiches et met à jour les modifiées ; ne supprime rien.
    synchroniser=True  : en plus, retire les fiches qui ne sont plus dans la source (miroir exact).
    """
    source = Path(source)
    if not source.is_file():
        raise ErreurImport(f"Fichier introuvable : {source}")
    if type_source == "excel":
        lecture = lire_excel(source, feuille)
    elif type_source == "base":
        lecture = lire_base_principale(source)
    else:
        raise ErreurImport(f"Type de source inconnu : {type_source}")
    if not lecture["enregistrements"]:
        raise ErreurImport("Aucune fiche exploitable dans la source : rien n'a été importé.")

    base.initialiser()
    sauvegarde = sauvegarder_avant_import()
    conn = base.ouvrir_ecriture()
    maintenant_ = maintenant()
    vues, ajoutees, maj, inchangees, fusionnees, divergentes = set(), 0, 0, 0, 0, 0
    try:
        conn.execute("BEGIN IMMEDIATE")
        existantes = {r["signature"]: (r["id"], r["empreinte"])
                      for r in conn.execute("SELECT id, signature, empreinte FROM memoires")}
        avant = len(existantes)
        # 1) Regroupement par signature : une même fiche répétée dans la source n'est gardée qu'une fois.
        #    On retient la version la plus complète (à égalité : la première rencontrée).
        uniques = {}
        for data in lecture["enregistrements"]:
            sig = calculer_champs(data)["signature"]
            if sig not in uniques:
                uniques[sig] = data
                continue
            fusionnees += 1
            if any(uniques[sig][c] != data[c] for c in CHAMPS_ORIGINAUX):
                divergentes += 1
            if _completude(data) > _completude(uniques[sig]):
                uniques[sig] = data
        # 2) Ajout / mise à jour / inchangé.
        for sig, data in uniques.items():
            calc = calculer_champs(data)
            vues.add(sig)
            emp = _empreinte(data)
            valeurs = [data[c] for c in CHAMPS_ORIGINAUX] + [
                calc["filiere"], calc["annee_ref"], calc["auteur_norm"], calc["theme_norm"], calc["recherche"]]
            if sig not in existantes:
                conn.execute(
                    f"INSERT INTO memoires(signature, empreinte, {', '.join(CHAMPS_ORIGINAUX)}, filiere, annee_ref, "
                    "auteur_norm, theme_norm, recherche, cree_le, maj_le) "
                    f"VALUES ({', '.join('?' * (2 + len(valeurs) + 2))})",
                    [sig, emp] + valeurs + [maintenant_, maintenant_])
                ajoutees += 1
            elif existantes[sig][1] != emp:
                conn.execute(
                    f"UPDATE memoires SET empreinte=?, {', '.join(c + '=?' for c in CHAMPS_ORIGINAUX)}, filiere=?, "
                    "annee_ref=?, auteur_norm=?, theme_norm=?, recherche=?, maj_le=? WHERE signature=?",
                    [emp] + valeurs + [maintenant_, sig])
                maj += 1
            else:
                inchangees += 1
        absentes = [s for s in existantes if s not in vues]
        supprimees = 0
        if synchroniser and absentes:
            conn.executemany("DELETE FROM memoires WHERE signature=?", [(s,) for s in absentes])
            supprimees = len(absentes)
        total = conn.execute("SELECT COUNT(*) FROM memoires").fetchone()[0]
        conn.execute(
            "INSERT INTO imports(date_import, source, type_source, sha256_source, lignes_lues, lignes_rejetees, "
            "doublons_fusionnes, ajoutees, mises_a_jour, inchangees, absentes_source, supprimees, total_apres) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (maintenant_, str(source), type_source, sha256_fichier(source), lecture["lues"], lecture["rejetees"],
             fusionnees, ajoutees, maj, inchangees, len(absentes), supprimees, total))
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    # Contrôle indépendant après validation : toutes les fiches de la source sont bien dans la base.
    verif = base.ouvrir_lecture()
    try:
        en_base = {r[0] for r in verif.execute("SELECT signature FROM memoires")}
    finally:
        verif.close()
    controle = vues <= en_base and (not synchroniser or en_base == vues)
    return {
        "source": str(source), "type_source": type_source,
        "lignes_lues": lecture["lues"], "lignes_rejetees": lecture["rejetees"], "lignes_ignorees": lecture["ignorees"],
        "fiches_uniques_source": len(vues), "doublons_fusionnes": fusionnees, "fusions_avec_differences": divergentes,
        "avant": avant, "ajoutees": ajoutees, "mises_a_jour": maj, "inchangees": inchangees,
        "absentes_de_la_source": len(absentes), "supprimees": supprimees, "total": total,
        "controle_ok": controle, "sauvegarde": str(sauvegarde) if sauvegarde else None,
    }


def resume_base() -> dict:
    """État de la base : totaux, dernier import, intégrité."""
    conn = base.ouvrir_lecture()
    try:
        total = conn.execute("SELECT COUNT(*) FROM memoires").fetchone()[0]
        dernier = conn.execute("SELECT * FROM imports ORDER BY id DESC LIMIT 1").fetchone()
        integrite = conn.execute("PRAGMA integrity_check").fetchone()[0]
        doublons = conn.execute("SELECT COUNT(*) FROM (SELECT signature FROM memoires GROUP BY signature HAVING COUNT(*)>1)").fetchone()[0]
        sans_annee = conn.execute("SELECT COUNT(*) FROM memoires WHERE annee_ref IS NULL").fetchone()[0]
        filieres = conn.execute("SELECT COUNT(DISTINCT filiere) FROM memoires").fetchone()[0]
        return {"total": total, "integrite": integrite, "doublons": doublons, "sans_annee": sans_annee,
                "filieres": filieres, "dernier_import": dict(dernier) if dernier else None}
    finally:
        conn.close()
