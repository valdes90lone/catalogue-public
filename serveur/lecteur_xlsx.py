"""Lecteur .xlsx minimal : bibliothèque standard uniquement (zipfile + XML), aucune dépendance.

Retourne les lignes sous forme de listes de chaînes (ou None), en conservant les numéros de ligne
d'Excel (les lignes vides sont conservées comme listes vides).
"""
import re
import zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
TAILLE_DECOMPRESSEE_MAX = 300 * 1024 * 1024  # protège contre les « zip bombs »
_RE_REF = re.compile(r"([A-Z]+)(\d+)")
_RE_ENTIER = re.compile(r"-?\d+\.0+")


class ErreurXlsx(Exception):
    pass


def _colonne(lettres: str) -> int:
    n = 0
    for c in lettres:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def _texte(noeud) -> str:
    """Texte d'un <si> ou <is> : <t> direct et <r><t> (texte riche), sans la phonétique."""
    morceaux = [t.text or "" for t in noeud.findall(f"{NS}t")]
    for r in noeud.findall(f"{NS}r"):
        morceaux += [t.text or "" for t in r.findall(f"{NS}t")]
    return "".join(morceaux)


def lire_xlsx(chemin, feuille=None) -> list:
    try:
        z = zipfile.ZipFile(chemin)
    except (zipfile.BadZipFile, OSError) as exc:
        raise ErreurXlsx(f"Fichier .xlsx illisible ou corrompu : {exc}") from exc
    with z:
        if sum(i.file_size for i in z.infolist()) > TAILLE_DECOMPRESSEE_MAX:
            raise ErreurXlsx("Le contenu du classeur est anormalement volumineux.")
        noms = set(z.namelist())
        if "xl/workbook.xml" not in noms:
            raise ErreurXlsx("Ce fichier n'est pas un classeur Excel (.xlsx) valide.")

        partages = []
        if "xl/sharedStrings.xml" in noms:
            with z.open("xl/sharedStrings.xml") as f:
                for _, el in ET.iterparse(f):
                    if el.tag == f"{NS}si":
                        partages.append(_texte(el))
                        el.clear()

        classeur = ET.fromstring(z.read("xl/workbook.xml"))
        feuilles = [(s.get("name"), s.get(f"{NS_REL}id")) for s in classeur.iter(f"{NS}sheet")]
        if not feuilles:
            raise ErreurXlsx("Le classeur ne contient aucune feuille.")
        if feuille is None:
            nom, rid = feuilles[0]
        else:
            trouvees = [f for f in feuilles if f[0] == feuille]
            if not trouvees:
                raise ErreurXlsx(f"Feuille introuvable : {feuille} (disponibles : {', '.join(f[0] for f in feuilles)})")
            nom, rid = trouvees[0]
        cible = None
        if "xl/_rels/workbook.xml.rels" in noms:
            for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).iter(f"{NS_PKG}Relationship"):
                if rel.get("Id") == rid:
                    cible = rel.get("Target")
        if cible is None:
            raise ErreurXlsx("Structure du classeur non reconnue.")
        cible = cible.lstrip("/") if cible.startswith("/") else "xl/" + cible
        if cible not in noms:
            raise ErreurXlsx("Feuille introuvable dans le classeur.")

        lignes = {}
        with z.open(cible) as f:
            for _, el in ET.iterparse(f):
                if el.tag != f"{NS}row":
                    continue
                numero = int(el.get("r") or (max(lignes) + 1 if lignes else 1))
                cellules = {}
                for c in el.findall(f"{NS}c"):
                    m = _RE_REF.fullmatch(c.get("r") or "")
                    if not m:
                        continue
                    t = c.get("t")
                    v = c.find(f"{NS}v")
                    if t == "inlineStr":
                        is_ = c.find(f"{NS}is")
                        valeur = _texte(is_) if is_ is not None else None
                    elif v is None or v.text is None:
                        valeur = None
                    elif t == "s":
                        i = int(v.text)
                        valeur = partages[i] if 0 <= i < len(partages) else None
                    elif t == "e":
                        valeur = None
                    elif t == "b":
                        valeur = "1" if v.text == "1" else "0"
                    else:  # nombre ou texte de formule
                        valeur = v.text
                        if t in (None, "n") and _RE_ENTIER.fullmatch(valeur):
                            valeur = valeur.split(".")[0]
                    cellules[_colonne(m.group(1))] = valeur
                lignes[numero] = cellules
                el.clear()
        if not lignes:
            return []
        resultat = []
        for numero in range(1, max(lignes) + 1):
            cel = lignes.get(numero, {})
            largeur = (max(cel) + 1) if cel else 0
            resultat.append([cel.get(i) for i in range(largeur)])
        return resultat
