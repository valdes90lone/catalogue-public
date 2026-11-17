import { lire, urlApi } from './api.js'

export const lister = (params, signal) => lire('/memoires', { params, signal })
export const obtenir = (id, signal) => lire(`/memoires/${encodeURIComponent(id)}`, { signal })
export const facettes = (signal) => lire('/memoires/facettes', { signal })
export const urlDocument = (id) => urlApi(`/memoires/${encodeURIComponent(id)}/document`)
