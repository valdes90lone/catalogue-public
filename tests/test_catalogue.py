import sqlite3
import unittest

from serveur import base, importation, requetes
from serveur.lecteur_xlsx import ErreurXlsx, lire_xlsx
from tests.utilitaires import ENTETES, Environnement, Serveur, creer_base_principale, fabriquer_xlsx, ligne

DONNEES = [
    ligne("Éric ADÉ", "L'audit des marchés publics", "ade.pdf", "Marchés publics", "Dr Koffi", "2019-2020", "GMP"),
    ligne("Awa SOW", "Gestion des archives", "sow.pdf", "Droit", None, "2018"),
    ligne("Paul DOSSOU", "Impôts locaux", "dossou.pdf", "Impôts", "M. Kpade", "1979/80"),
    ligne("Paul DOSSOU", "Impôts locaux", "dossou.pdf", "Impôts", "M. Kpade", "1979/80"),   # doublon exact
]


class Base(unittest.TestCase):
    def setUp(self):
        self.env = Environnement().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.xlsx = self.env.racine / "src.xlsx"
        fabriquer_xlsx(self.xlsx, [ENTETES] + DONNEES)


class TestLecteurXlsx(Base):
    def test_lecture_chaines_partagees_et_en_ligne(self):
        for partage in (True, False):
            fabriquer_xlsx(self.xlsx, [ENTETES] + DONNEES, partage=partage)
            lignes = lire_xlsx(self.xlsx)
            self.assertEqual(len(lignes), 5)
            self.assertEqual(lignes[1][0], "Éric ADÉ")

    def test_nombres_entiers_sans_decimale(self):
        fabriquer_xlsx(self.xlsx, [["Annee"], [2020.0], [2021]])
        self.assertEqual(lire_xlsx(self.xlsx)[1][0], "2020")

    def test_fichier_invalide(self):
        faux = self.env.racine / "faux.xlsx"
        faux.write_text("pas un xlsx")
        with self.assertRaises(ErreurXlsx):
            lire_xlsx(faux)


class TestImportation(Base):
    def test_import_initial_et_doublons(self):
        r = importation.importer(self.xlsx, "excel")
        self.assertEqual((r["lignes_lues"], r["total"], r["ajoutees"], r["doublons_fusionnes"]), (4, 3, 3, 1))
        self.assertTrue(r["controle_ok"])
        self.assertEqual(importation.resume_base()["doublons"], 0)

    def test_reimport_identique_ne_cree_rien(self):
        importation.importer(self.xlsx, "excel")
        r = importation.importer(self.xlsx, "excel")
        self.assertEqual((r["ajoutees"], r["mises_a_jour"], r["inchangees"], r["total"]), (0, 0, 3, 3))
        self.assertIsNotNone(r["sauvegarde"])           # sauvegarde automatique avant la mise à jour

    def test_mise_a_jour_ajout_et_conservation(self):
        importation.importer(self.xlsx, "excel")
        modif = [list(l) for l in DONNEES[:3]]
        modif[0][3] = "Dr Nouveau"                      # fiche modifiée (même signature)
        modif.append(ligne("Nouvel AUTEUR", "Nouveau thème", "n.pdf"))
        fabriquer_xlsx(self.xlsx, [ENTETES] + modif[1:] + [modif[0]] + modif[3:])
        r = importation.importer(self.xlsx, "excel")
        self.assertEqual((r["ajoutees"], r["mises_a_jour"], r["inchangees"], r["total"]), (1, 1, 2, 4))

    def test_absentes_conservees_sauf_synchronisation(self):
        importation.importer(self.xlsx, "excel")
        fabriquer_xlsx(self.xlsx, [ENTETES, DONNEES[0]])
        r = importation.importer(self.xlsx, "excel")
        self.assertEqual((r["absentes_de_la_source"], r["supprimees"], r["total"]), (2, 0, 3))
        r = importation.importer(self.xlsx, "excel", synchroniser=True)
        self.assertEqual((r["supprimees"], r["total"], r["controle_ok"]), (2, 1, True))

    def test_fusion_garde_la_version_la_plus_complete(self):
        pauvre = ligne("Zoé KONE", "Thème X", "z.pdf", directeur=None)
        riche = ligne("Zoé KONE", "Thème X", "z.pdf", directeur="Dr Complet")
        fabriquer_xlsx(self.xlsx, [ENTETES, pauvre, riche])
        r = importation.importer(self.xlsx, "excel")
        self.assertEqual((r["doublons_fusionnes"], r["fusions_avec_differences"]), (1, 1))
        conn = base.ouvrir_lecture()
        self.assertEqual(conn.execute("SELECT directeur FROM memoires").fetchone()[0], "Dr Complet")

    def test_lignes_sans_identite_rejetees_et_totaux_ignores(self):
        fabriquer_xlsx(self.xlsx, [ENTETES, DONNEES[0], [None, None, "Droit"], ["Total", "12"]])
        r = importation.importer(self.xlsx, "excel")
        self.assertEqual((r["total"], r["lignes_rejetees"], r["lignes_ignorees"]), (1, 1, 1))

    def test_source_vide_ou_invalide_refusee_sans_effet(self):
        fabriquer_xlsx(self.xlsx, [["Truc", "Machin"], ["a", "b"]])
        with self.assertRaises(importation.ErreurImport):
            importation.importer(self.xlsx, "excel")
        with self.assertRaises(importation.ErreurImport):
            importation.importer(self.env.racine / "absent.xlsx", "excel")

    def test_import_depuis_la_base_principale_sans_la_modifier(self):
        src = self.env.racine / "principale.db"
        creer_base_principale(src, [tuple(l) for l in DONNEES[:3]], corbeille=[tuple(ligne("Supprimé", "Corbeille", "c.pdf"))])
        avant = src.read_bytes()
        r = importation.importer(src, "base")
        self.assertEqual((r["lignes_lues"], r["total"]), (3, 3))   # la corbeille n'est pas importée
        self.assertEqual(src.read_bytes(), avant)                  # fichier source intact
        with self.assertRaises(importation.ErreurImport):          # une autre base SQLite est refusée
            autre = self.env.racine / "autre.db"
            sqlite3.connect(autre).execute("CREATE TABLE t(x)").connection.close()
            importation.importer(autre, "base")


class TestRequetes(Base):
    def setUp(self):
        super().setUp()
        importation.importer(self.xlsx, "excel")
        self.conn = base.ouvrir_lecture()
        self.addCleanup(self.conn.close)

    def test_recherche_sans_accent_ni_casse(self):
        self.assertEqual(requetes.lister(self.conn, q="ERIC ade")["total"], 1)
        self.assertEqual(requetes.lister(self.conn, q="marches publics audit")["total"], 1)
        self.assertEqual(requetes.lister(self.conn, q="introuvable")["total"], 0)

    def test_caracteres_speciaux_de_like(self):
        self.assertEqual(requetes.lister(self.conn, q="%")["total"], 0)
        self.assertEqual(requetes.lister(self.conn, q="_")["total"], 0)

    def test_filtres_et_tri_pagination(self):
        self.assertEqual(requetes.lister(self.conn, annee=2020)["total"], 1)
        self.assertEqual(requetes.lister(self.conn, auteur="dossou")["total"], 1)
        fac = requetes.facettes(self.conn)
        self.assertEqual({a["valeur"] for a in fac["annees"]}, {1980, 2018, 2020})
        filiere = fac["filieres"][0]["valeur"]
        self.assertGreaterEqual(requetes.lister(self.conn, filiere=filiere)["total"], 1)
        titres = [m["theme"] for m in requetes.lister(self.conn, tri="titre")["items"]]
        self.assertEqual(titres, sorted(titres, key=str.casefold))
        annees = [m["annee_ref"] for m in requetes.lister(self.conn, tri="annee_desc")["items"]]
        self.assertEqual(annees, sorted(annees, reverse=True))
        page = requetes.lister(self.conn, taille=2, page=2)
        self.assertEqual((page["pages"], len(page["items"])), (2, 1))
        self.assertEqual(requetes.lister(self.conn, taille=2, page=99)["page"], 2)   # page hors limite ramenée


class TestServeur(Base):
    def setUp(self):
        super().setUp()
        importation.importer(self.xlsx, "excel")

    def test_api_lecture(self):
        with Serveur() as s:
            self.assertEqual(s.json("/api/sante"), (200, {"statut": "ok", "memoires": 3}))
            statut, page = s.json("/api/memoires?q=archives&taille=10")
            self.assertEqual((statut, page["total"], page["items"][0]["auteur"]), (200, 1, "Awa SOW"))
            self.assertNotIn("signature", page["items"][0])     # aucun champ technique exposé
            ident = page["items"][0]["id"]
            statut, fiche = s.json(f"/api/memoires/{ident}")
            self.assertEqual((statut, fiche["document_disponible"]), (200, False))
            self.assertEqual(s.json("/api/memoires/99999")[0], 404)
            self.assertEqual(s.json("/api/memoires?annee=abc")[0], 422)
            self.assertEqual(s.json("/api/memoires?tri=drop")[0], 422)
            self.assertEqual(s.json("/api/memoires?taille=1000")[0], 422)
            self.assertEqual(len(s.json("/api/memoires/facettes")[1]["filieres"]) > 0, True)
            self.assertEqual(s.json("/api/inconnu")[0], 404)

    def test_aucune_ecriture_possible(self):
        with Serveur() as s:
            for methode in ("POST", "PUT", "PATCH", "DELETE"):
                statut, entetes, _ = s.requete("/api/memoires", methode)
                self.assertEqual(statut, 405, methode)
                self.assertEqual(entetes["Allow"], "GET, HEAD")
        conn = base.ouvrir_lecture()                              # et la connexion du serveur est en lecture seule
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("DELETE FROM memoires")

    def test_donnees_persistantes_apres_redemarrage(self):
        with Serveur() as s:
            avant = s.json("/api/memoires?taille=100")[1]
        with Serveur() as s:                                      # nouveau serveur, même fichier
            self.assertEqual(s.json("/api/memoires?taille=100")[1], avant)

    def test_base_absente(self):
        self.env.patchs[1].stop()
        try:
            from unittest import mock
            from serveur import config
            with mock.patch.object(config, "DB_PATH", self.env.racine / "vide" / "x.db"):
                with Serveur() as s:
                    self.assertEqual(s.json("/api/sante")[0], 503)
        finally:
            self.env.patchs[1].start()

    def test_site_et_routes_spa(self):
        with Serveur() as s:                                       # dist absent : page d'explication
            statut, _, corps = s.requete("/")
            self.assertIn(b"pas encore construit", corps)
        dist = self.env.racine / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<html>SITE</html>")
        (dist / "assets" / "app.js").write_text("x=1")
        (self.env.racine / "secret.txt").write_text("SECRET")
        with Serveur() as s:
            self.assertIn(b"SITE", s.requete("/memoire/12")[2])            # route de l'application
            self.assertEqual(s.requete("/assets/app.js")[2], b"x=1")
            self.assertEqual(s.requete("/assets/absent.js")[0], 404)
            for piege in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
                self.assertNotIn(b"SECRET", s.requete(piege)[2], piege)


if __name__ == "__main__":
    unittest.main()
