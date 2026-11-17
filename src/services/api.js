// Client API en LECTURE SEULE : une seule fonction, qui n'émet que des requêtes GET.
// Aucune clé d'accès n'est envoyée et aucune méthode d'écriture n'existe dans cette application.
const BASE = (import.meta.env?.VITE_API_URL || '/api').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, code, status = 0) {
    super(message)
    this.code = code // 'reseau' | 'introuvable' | 'serveur'
    this.status = status
  }
}

export function construireQuery(params = {}) {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    sp.set(k, String(v))
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export async function lire(chemin, { params, signal } = {}) {
  let reponse
  try {
    reponse = await fetch(`${BASE}${chemin}${construireQuery(params)}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Impossible de joindre le serveur du catalogue.', 'reseau')
  }
  if (reponse.status === 404) throw new ApiError('Ressource introuvable.', 'introuvable', 404)
  if (!reponse.ok) throw new ApiError(`Le serveur a répondu avec une erreur (${reponse.status}).`, 'serveur', reponse.status)
  try {
    return await reponse.json()
  } catch {
    throw new ApiError('Réponse inattendue du serveur.', 'serveur', reponse.status)
  }
}

export const urlApi = (chemin) => `${BASE}${chemin}`
