import test from 'node:test'
import assert from 'node:assert/strict'
import { ETAT_INITIAL, lireEtat, nombreFiltres, versParamsApi, versUrl } from './query.js'

test('lireEtat : valeurs par défaut', () => {
  assert.deepEqual(lireEtat(new URLSearchParams('')), ETAT_INITIAL)
})

test('lireEtat : valeurs invalides ramenées au défaut', () => {
  const e = lireEtat(new URLSearchParams('annee=abc&page=-3&tri=hack&q=x'))
  assert.equal(e.annee, '')
  assert.equal(e.page, 1)
  assert.equal(e.tri, 'titre')
  assert.equal(e.q, 'x')
})

test('aller-retour état <-> URL', () => {
  const etat = { q: 'archives', filiere: 'Bibliothéconomie', annee: '2020', auteur: 'Kon', tri: 'annee_desc', page: 3 }
  assert.deepEqual(lireEtat(versUrl(etat)), etat)
  assert.equal(versUrl(ETAT_INITIAL).toString(), '')
})

test('versParamsApi : GET /memoires uniquement avec des filtres lisibles', () => {
  const p = versParamsApi({ ...ETAT_INITIAL, q: '  a  ', page: 2 })
  assert.equal(p.q, 'a')
  assert.equal(p.filiere, undefined)
  assert.equal(p.page, 2)
  assert.equal(p.taille, 24)
})

test('nombreFiltres', () => {
  assert.equal(nombreFiltres(ETAT_INITIAL), 0)
  assert.equal(nombreFiltres({ ...ETAT_INITIAL, q: 'x', annee: '2020' }), 2)
})
