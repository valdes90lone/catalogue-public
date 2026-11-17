"""Catalogue public — commandes : demarrer, importer, verifier.

    python catalogue.py demarrer                       lance le catalogue (crée la base vide au premier lancement)
    python catalogue.py importer --excel FICHIER.xlsx  importe / met à jour depuis un fichier Excel
    python catalogue.py importer --base memoires.db    importe / met à jour depuis la base de l'application principale
    python catalogue.py verifier                       contrôle l'état de la base du catalogue

Bibliothèque standard uniquement : aucune installation Python n'est nécessaire.
"""
import argparse
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from serveur import api, base, config, importation  # noqa: E402


def _console_utf8():
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def candidats() -> list:
    """Sources plausibles, à titre indicatif (aucune n'est utilisée sans demande explicite)."""
    r = config.RACINE
    trouves = []
    for dossier in (r.parent / "bibliotheque-memoires" / "data", r / "data"):
        for nom, type_ in (("memoires.db", "--base"), ("memoires.xlsx", "--excel"), ("resultats_memoires.xlsx", "--excel")):
            if (dossier / nom).is_file():
                trouves.append((type_, dossier / nom))
    src = r.parent / "bibliotheque-memoires" / "data" / "source" / "resultats_memoires.xlsx"
    if src.is_file():
        trouves.append(("--excel", src))
    return trouves


def message_import_requis():
    print("\n  La base du catalogue vient d'être créée ; elle est VIDE.")
    print("  Pour importer les mémoires (une seule fois), utilisez l'un de ces deux fichiers :")
    print(r"    importer.bat chemin\vers\memoires.xlsx          (fichier Excel)")
    print(r"    importer.bat chemin\vers\memoires.db            (base de l'application principale)")
    print("  ou : python catalogue.py importer --excel FICHIER.xlsx   /   --base FICHIER.db")
    trouves = candidats()
    if trouves:
        print("  Fichiers trouvés sur cet ordinateur :")
        for option, chemin in trouves:
            print(f"    python catalogue.py importer {option} \"{chemin}\"")
    print()


def cmd_demarrer(args) -> int:
    nouvelle = base.initialiser()
    if nouvelle:
        message_import_requis()
    else:
        resume = importation.resume_base()
        print(f"  Base existante : {resume['total']} mémoires ({config.DB_PATH})")
        if resume["total"] == 0:
            message_import_requis()
    if args.port:
        config.PORT = args.port
    try:
        serveur = api.creer_serveur(port=config.PORT)
    except OSError as exc:
        print(f"  Impossible d'ouvrir le port {config.PORT} : {exc}\n  Un autre programme l'utilise peut-être déjà "
              f"(catalogue déjà lancé ?). Essayez : python catalogue.py demarrer --port 5180")
        return 1
    adresse = f"http://{config.HOST}:{config.PORT}"
    if not (config.DIST_DIR / "index.html").is_file():
        print("  Le site n'est pas construit (dossier dist absent) : npm install puis npm run build.")
    print(f"  Catalogue disponible : {adresse}   (Ctrl+C pour arrêter)\n")
    if not args.sans_navigateur:
        threading.Timer(1.0, lambda: webbrowser.open(adresse)).start()
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\n  Catalogue arrêté.")
    finally:
        serveur.server_close()
    return 0


def cmd_importer(args) -> int:
    if not (args.excel or args.base):
        print("Indiquez la source à importer : --excel FICHIER.xlsx  ou  --base FICHIER.db")
        for option, chemin in candidats():
            print(f"  python catalogue.py importer {option} \"{chemin}\"")
        return 2
    source, type_ = (Path(args.excel), "excel") if args.excel else (Path(args.base), "base")
    try:
        r = importation.importer(source, type_, synchroniser=args.synchroniser, feuille=args.feuille)
    except importation.ErreurImport as exc:
        print(f"Importation impossible : {exc}")
        return 1
    print(f"Source               : {r['source']}")
    print(f"Lignes lues          : {r['lignes_lues']}  (rejetées : {r['lignes_rejetees']}, ignorées : {r['lignes_ignorees']})")
    print(f"Fiches uniques       : {r['fiches_uniques_source']}  (doublons fusionnés : {r['doublons_fusionnes']}, dont {r['fusions_avec_differences']} aux champs secondaires différents : version la plus complète gardée)")
    print(f"Avant l'import       : {r['avant']} fiches")
    print(f"Ajoutées             : {r['ajoutees']}")
    print(f"Mises à jour         : {r['mises_a_jour']}")
    print(f"Inchangées           : {r['inchangees']}")
    if r["absentes_de_la_source"]:
        print(f"Absentes de la source: {r['absentes_de_la_source']}  "
              + (f"(supprimées : {r['supprimees']})" if args.synchroniser else "(conservées ; utilisez --synchroniser pour les retirer)"))
    print(f"TOTAL dans le catalogue : {r['total']}")
    if r["sauvegarde"]:
        print(f"Sauvegarde préalable : {r['sauvegarde']}")
    print("Contrôle (toutes les fiches de la source sont dans la base) : " + ("OK" if r["controle_ok"] else "ÉCHEC"))
    return 0 if r["controle_ok"] else 1


def cmd_verifier(_args) -> int:
    if not base.existe():
        print(f"Aucune base de données ({config.DB_PATH}). Lancez le catalogue puis importez les données.")
        return 1
    r = importation.resume_base()
    print(f"Base : {config.DB_PATH}")
    print(f"Mémoires : {r['total']} · filières : {r['filieres']} · sans année : {r['sans_annee']}")
    print(f"Intégrité SQLite : {r['integrite']} · signatures en double : {r['doublons']}")
    d = r["dernier_import"]
    if d:
        print(f"Dernier import : {d['date_import']} ({d['type_source']}) {d['source']}")
        print(f"  lues {d['lignes_lues']} · ajoutées {d['ajoutees']} · mises à jour {d['mises_a_jour']} · "
              f"inchangées {d['inchangees']} · fusionnées {d['doublons_fusionnes']}")
    else:
        print("Aucun import effectué : la base est vide.")
    return 0 if r["integrite"] == "ok" and r["doublons"] == 0 else 1


def main(argv=None) -> int:
    _console_utf8()
    p = argparse.ArgumentParser(description="Catalogue public — autonome et en lecture seule.")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demarrer", help="lance le catalogue")
    d.add_argument("--port", type=int)
    d.add_argument("--sans-navigateur", action="store_true")
    i = sub.add_parser("importer", help="importe ou met à jour les mémoires")
    i.add_argument("--excel", help="fichier .xlsx (colonnes d'origine)")
    i.add_argument("--base", help="fichier de base SQLite de l'application principale")
    i.add_argument("--feuille", help="nom de la feuille Excel (défaut : la première)")
    i.add_argument("--synchroniser", action="store_true", help="retire aussi les fiches absentes de la source")
    sub.add_parser("verifier", help="contrôle la base")
    args = p.parse_args(argv)
    return {"demarrer": cmd_demarrer, "importer": cmd_importer, "verifier": cmd_verifier}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
