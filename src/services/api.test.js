import test from 'node:test'
import assert from 'node:assert/strict'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { ApiError, lire } from './api.js'
import { facettes, lister, obtenir, urlDocument } from './catalogue.js'

const reponse = (status, corps) => ({ ok: status >= 200 && status < 300, status, json: async () => corps })

function simuler(rep) {
  const appels = []
  globalThis.fetch = async (url, options) => { appels.push({ url, options }); return typeof rep === 'function' ? rep(url) : rep }
  return appels
}

test('chaque requête est un GET sans clé ni corps', async () => {
  const appels = simuler(reponse(200, { items: [], total: 0 }))
  await lister({ q: 'archives', page: 2, taille: 24, filiere: undefined })
  await obtenir(12)
  await facettes()
  assert.equal(appels.length, 3)
  for (const a of appels) {
    assert.equal(a.options.method, 'GET')
    assert.equal(a.options.body, undefined)
    assert.deepEqual(Object.keys(a.options.headers), ['Accept'])
  }
  assert.equal(appels[0].url, '/api/memoires?q=archives&page=2&taille=24')
  assert.equal(appels[1].url, '/api/memoires/12')
  assert.equal(appels[2].url, '/api/memoires/facettes')
  assert.equal(urlDocument(12), '/api/memoires/12/document')
})

test('erreurs : réseau, 404, 500', async () => {
  globalThis.fetch = async () => { throw new TypeError('fetch failed') }
  await assert.rejects(lire('/memoires'), (e) => e instanceof ApiError && e.code === 'reseau')
  simuler(reponse(404, {}))
  await assert.rejects(lire('/memoires/9'), (e) => e.code === 'introuvable')
  simuler(reponse(500, {}))
  await assert.rejects(lire('/memoires'), (e) => e.code === 'serveur' && e.status === 500)
})

test('le code source ne contient aucune opération d’écriture', () => {
  const fichiers = []
  const parcourir = (d) => readdirSync(d).forEach((n) => {
    const p = join(d, n)
    if (statSync(p).isDirectory()) parcourir(p)
    else if (/\.(jsx?|html)$/.test(n) && !n.endsWith('.test.js')) fichiers.push(p)
  })
  parcourir(new URL('..', import.meta.url).pathname)
  assert.ok(fichiers.length > 10)
  const interdits = /\b(POST|PUT|PATCH|DELETE)\b|X-API-Key|FormData|localStorage|\/import|\/export|\/auth|\/sauvegardes/
  for (const f of fichiers) assert.doesNotMatch(readFileSync(f, 'utf8'), interdits, f)
})
