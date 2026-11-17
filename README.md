# Catalogue public — Bibliothèque Mémoires

Application **autonome et en lecture seule** pour consulter les mémoires : recherche, filtres, pagination, fiches détaillées.
Elle possède **sa propre base de données** et **son propre serveur** ; elle n'a besoin ni de l'API ni du backend d'une autre application.

## Démarrer (Windows)

Double-cliquez sur **`start.bat`** (ou lancez-le dans PowerShell / cmd : `.\start.bat`). Puis ouvrez **http://127.0.0.1:5174** (le navigateur s'ouvre seul).

- Prérequis : **Python 3** (aucune bibliothèque à installer). **Node.js** n'est nécessaire qu'au tout premier lancement, pour construire le site (`dist/`) ; ensuite il n'est plus utilisé.
- À chaque lancement : si la base `data\catalogue.db` n'existe pas, elle est créée **vide** et le message explique comment importer ; si elle existe, elle est utilisée telle quelle. **Aucun import automatique.**

## Importer les mémoires (une seule fois)

```powershell
.\importer.bat chemin\vers\memoires.xlsx
.\importer.bat chemin\vers\memoires.db
```

Deux sources possibles, lues sans jamais être modifiées et sans lancer l'autre application :

| Source | Ce qui est lu |
| --- | --- |
| Fichier Excel `.xlsx` | les 9 colonnes d'origine (Auteur, Theme, Filiere (LLM), Directeur, Annee (LLM), Filiere (Chemin), Sous-Filiere, Annee (Chemin), Fichier) |
| Fichier de base SQLite de l'application principale (`memoires.db`) | les mêmes 9 champs des fiches actives (la corbeille est ignorée) ; le fichier est d'abord copié dans un dossier temporaire |

Le rapport affiche : lignes lues, fiches uniques, doublons fusionnés, ajoutées / mises à jour / inchangées, total, et un **contrôle** (« toutes les fiches de la source sont dans la base : OK »).

### Doublons

Chaque fiche a une signature (auteur + thème + fichier, normalisés) **unique** dans la base. Une fiche répétée dans la source n'est gardée qu'une fois (la version la plus complète). Réimporter ne crée jamais de doublon.

### Mettre à jour plus tard

Relancez la même commande avec le fichier à jour :

- fiches nouvelles → ajoutées ; fiches modifiées → mises à jour ; fiches identiques → inchangées ;
- fiches absentes de la source → **conservées** par défaut ; ajoutez `--synchroniser` pour les retirer (miroir exact) :
  `.\importer.bat memoires.xlsx --synchroniser`
- une **sauvegarde automatique** de la base est faite avant chaque import (`data\sauvegardes\`, 10 conservées).
- Si une fiche est retouchée dans la source de façon à changer son auteur, son thème ou son fichier, elle est vue comme une nouvelle fiche : utilisez `--synchroniser` pour retirer l'ancienne version.

Contrôler la base à tout moment : `python catalogue.py verifier`.
Restaurer une sauvegarde : fermez le catalogue, puis copiez le fichier de `data\sauvegardes\` vers `data\catalogue.db`.

## Données et fichiers

- Base : `data\catalogue.db` (SQLite, conservée sur le disque ; jamais versionnée).
- Le serveur ouvre la base en **lecture seule** et refuse toute requête autre que GET/HEAD (erreur 405).
- Champs affichés : thème, auteur, directeur, année, filière, sous-filière, filière et année du dossier de classement, nom du fichier. Il n'existe ni « mots-clés » ni « établissement » dans les données.
- Lien « Ouvrir le document » : uniquement si la variable `CATALOGUE_DOCUMENTS_DIR` désigne un dossier contenant les PDF.

## Configuration (variables d'environnement facultatives)

| Variable | Défaut |
| --- | --- |
| `CATALOGUE_PORT` | `5174` |
| `CATALOGUE_HOST` | `127.0.0.1` (visible seulement depuis cet ordinateur ; `0.0.0.0` pour le réseau local) |
| `CATALOGUE_DATA_DIR` | `data` |
| `CATALOGUE_DOCUMENTS_DIR` | aucun |

## Structure

```
catalogue.py        commandes : demarrer · importer · verifier
start.bat           lancement en un clic
importer.bat        importation
serveur/            serveur web, requêtes, importation, lecteur .xlsx (Python standard)
src/                interface React (Vite + Tailwind), thème vert
tests/              tests Python (unittest) ; src/*.test.js : tests Node
data/               base catalogue.db et sauvegardes (créés au premier lancement)
```

## Tests et développement

```powershell
python -m unittest discover -s tests -t .     # serveur, import, recherche
npm test                                       # utilitaires du site, lecture seule, autonomie
npm run build                                  # reconstruire le site après une modification de src\
npm run dev                                    # interface en mode développement (port 5176, relaie /api vers le serveur du catalogue)
```

Après une modification de l'interface, relancez `npm run build` puis `start.bat`.
