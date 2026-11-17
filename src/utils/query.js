export const PAR_PAGE = 24

export const TRIS = [
  { valeur: 'titre', libelle: 'Titre (A → Z)' },
  { valeur: 'auteur', libelle: 'Auteur (A → Z)' },
  { valeur: 'annee_desc', libelle: 'Année (récentes d’abord)' },
  { valeur: 'annee_asc', libelle: 'Année (anciennes d’abord)' },
]
const TRIS_VALIDES = TRIS.map((t) => t.valeur)

export const ETAT_INITIAL = { q: '', filiere: '', annee: '', auteur: '', tri: 'titre', page: 1 }

/** URLSearchParams -> état (valeurs invalides ramenées aux valeurs par défaut). */
export function lireEtat(sp) {
  const annee = Number(sp.get('annee'))
  const page = Number(sp.get('page'))
  const tri = sp.get('tri')
  return {
    q: (sp.get('q') || '').slice(0, 200),
    filiere: (sp.get('filiere') || '').slice(0, 255),
    annee: Number.isInteger(annee) && annee >= 1900 && annee <= 2100 ? String(annee) : '',
    auteur: (sp.get('auteur') || '').slice(0, 200),
    tri: TRIS_VALIDES.includes(tri) ? tri : 'titre',
    page: Number.isInteger(page) && page >= 1 ? page : 1,
  }
}

/** État -> URLSearchParams (les valeurs par défaut sont omises pour garder des adresses courtes). */
export function versUrl(etat) {
  const sp = new URLSearchParams()
  for (const cle of ['q', 'filiere', 'annee', 'auteur']) if (etat[cle]) sp.set(cle, etat[cle])
  if (etat.tri !== 'titre') sp.set('tri', etat.tri)
  if (etat.page > 1) sp.set('page', String(etat.page))
  return sp
}

/** État -> paramètres de GET /api/memoires. */
export function versParamsApi(etat) {
  return {
    q: etat.q.trim() || undefined,
    filiere: etat.filiere || undefined,
    annee: etat.annee || undefined,
    auteur: etat.auteur.trim() || undefined,
    tri: etat.tri,
    page: etat.page,
    taille: PAR_PAGE,
  }
}

export const nombreFiltres = (etat) =>
  ['q', 'filiere', 'annee', 'auteur'].filter((c) => String(etat[c]).trim() !== '').length
