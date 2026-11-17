const PLACEHOLDERS = ['inconnu', 'inconnue', 'non specifie', 'non specifiee', 'n/a', '-', '0']
const FILIERE_INCONNUE = 'Non classée'

const sansAccent = (s) => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()

/** Retourne la valeur, ou null si elle est vide ou n'est qu'un texte de remplissage (« Inconnu », « N/A »…). */
export function valeurAffichable(v) {
  if (v == null || String(v).trim() === '') return null
  return PLACEHOLDERS.includes(sansAccent(v)) ? null : String(v).trim()
}

export function anneeAffichee(m) {
  return valeurAffichable(m.annee_llm) || (m.annee_ref ? String(m.annee_ref) : null)
}

export function filiereAffichee(m) {
  return m.filiere && m.filiere !== FILIERE_INCONNUE ? m.filiere : null
}

export const nombre = (n) => new Intl.NumberFormat('fr-FR').format(n ?? 0)
export const pluriel = (n, un, plusieurs) => (n > 1 ? plusieurs : un)

/** Pages à afficher : 1 … 4 5 [6] 7 8 … 20 (null = points de suspension). */
export function fenetrePages(page, pages, voisines = 1) {
  if (pages <= 1) return [1]
  const voulues = new Set([1, pages])
  for (let i = page - voisines; i <= page + voisines; i++) if (i >= 1 && i <= pages) voulues.add(i)
  const tri = [...voulues].sort((a, b) => a - b)
  const sortie = []
  tri.forEach((p, i) => {
    if (i > 0 && p - tri[i - 1] > 1) sortie.push(p - tri[i - 1] === 2 ? p - 1 : null)
    sortie.push(p)
  })
  return sortie
}
