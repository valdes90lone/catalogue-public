import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const racine = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')

function fichiers(dossier, sortie = []) {
  for (const n of readdirSync(dossier)) {
    if (['node_modules', 'dist', 'data', '.git', '__pycache__'].includes(n)) continue
    const p = join(dossier, n)
    if (statSync(p).isDirectory()) fichiers(p, sortie)
    else if (/\.(jsx?|html|json|css|bat|example|py)$/.test(n) || n === '.env.example') sortie.push(p)
  }
  return sortie
}

test('le site et le serveur ne référencent plus l’application principale (port 8000, backend, 5173)', () => {
  const exceptions = ['catalogue.py', 'autonomie.test.js', 'tests'] // suggestions de fichiers à importer, hors exécution du site
  const cibles = fichiers(racine).filter((f) => !exceptions.some((e) => f.includes(e)) && !f.endsWith('package-lock.json'))
  assert.ok(cibles.length > 15)
  for (const f of cibles) {
    const texte = readFileSync(f, 'utf8')
    assert.doesNotMatch(texte, /:8000\b|127\.0\.0\.1:8000|bibliotheque-memoires|backend\/app/, f)
  }
})

test('les pages n’utilisent aucune couleur bleue de l’ancienne identité', () => {
  for (const f of fichiers(join(racine, 'src')).filter((x) => /\.(jsx|css)$/.test(x)))
    assert.doesNotMatch(readFileSync(f, 'utf8'), /marine|#1f3a5f|\b(bg|text|border|ring)-(blue|indigo|sky)/, f)
})
