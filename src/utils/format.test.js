import test from 'node:test'
import assert from 'node:assert/strict'
import { anneeAffichee, fenetrePages, filiereAffichee, valeurAffichable } from './format.js'

test('valeurAffichable masque les textes de remplissage', () => {
  assert.equal(valeurAffichable('Inconnu'), null)
  assert.equal(valeurAffichable('  N/A '), null)
  assert.equal(valeurAffichable(''), null)
  assert.equal(valeurAffichable(null), null)
  assert.equal(valeurAffichable('Non spécifié'), null)
  assert.equal(valeurAffichable(' Dr Adé '), 'Dr Adé')
})

test('anneeAffichee préfère annee_llm puis annee_ref', () => {
  assert.equal(anneeAffichee({ annee_llm: '2020-2021', annee_ref: 2021 }), '2020-2021')
  assert.equal(anneeAffichee({ annee_llm: 'Inconnu', annee_ref: 2019 }), '2019')
  assert.equal(anneeAffichee({ annee_llm: null, annee_ref: null }), null)
})

test('filiereAffichee ignore « Non classée »', () => {
  assert.equal(filiereAffichee({ filiere: 'Non classée' }), null)
  assert.equal(filiereAffichee({ filiere: 'Bibliothéconomie' }), 'Bibliothéconomie')
})

test('fenetrePages', () => {
  assert.deepEqual(fenetrePages(1, 1), [1])
  assert.deepEqual(fenetrePages(1, 5), [1, 2, null, 5])
  assert.deepEqual(fenetrePages(2, 5), [1, 2, 3, 4, 5])
  assert.deepEqual(fenetrePages(3, 5), [1, 2, 3, 4, 5])
  assert.deepEqual(fenetrePages(1, 20), [1, 2, null, 20])
  assert.deepEqual(fenetrePages(10, 20), [1, null, 9, 10, 11, null, 20])
  assert.deepEqual(fenetrePages(20, 20), [1, null, 19, 20])
  assert.deepEqual(fenetrePages(4, 20), [1, 2, 3, 4, 5, null, 20])
})
