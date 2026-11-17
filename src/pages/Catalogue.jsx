import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import CarteMemoire from '../components/CarteMemoire.jsx'
import ChampTexte from '../components/ChampTexte.jsx'
import { AucunResultat, CatalogueVide, Chargement, ErreurConnexion } from '../components/Etats.jsx'
import Pagination from '../components/Pagination.jsx'
import { facettes as chargerFacettes, lister } from '../services/catalogue.js'
import { nombre, pluriel } from '../utils/format.js'
import { ETAT_INITIAL, TRIS, lireEtat, nombreFiltres, versParamsApi, versUrl } from '../utils/query.js'

const Etiquette = ({ id, children }) => <label htmlFor={id} className="mb-1 block text-xs font-medium text-encre/70">{children}</label>

export default function Catalogue() {
  const [sp, setSp] = useSearchParams()
  const etat = useMemo(() => lireEtat(sp), [sp])
  const [donnees, setDonnees] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState(null)
  const [essai, setEssai] = useState(0)
  const [facettes, setFacettes] = useState({ filieres: [], annees: [] })
  const [totalCatalogue, setTotalCatalogue] = useState(null)
  const [filtresOuverts, setFiltresOuverts] = useState(false)

  useEffect(() => { document.title = 'Catalogue des mémoires' }, [])

  // Valeurs des filtres et total du catalogue (échec toléré : la liste principale signale l'erreur).
  useEffect(() => {
    const ctrl = new AbortController()
    chargerFacettes(ctrl.signal).then(setFacettes).catch(() => {})
    lister({ taille: 1 }, ctrl.signal).then((r) => setTotalCatalogue(r.total)).catch(() => {})
    return () => ctrl.abort()
  }, [essai])

  const cle = JSON.stringify(versParamsApi(etat))
  useEffect(() => {
    const ctrl = new AbortController()
    setChargement(true)
    setErreur(null)
    lister(JSON.parse(cle), ctrl.signal)
      .then((r) => { setDonnees(r); setChargement(false) })
      .catch((e) => { if (e.name !== 'AbortError') { setErreur(e.message); setChargement(false) } })
    return () => ctrl.abort()
  }, [cle, essai])

  const maj = useCallback((changements, { remplacer = false } = {}) => {
    const suivant = { ...etat, ...changements }
    if (!('page' in changements)) suivant.page = 1
    setSp(versUrl(suivant), { replace: remplacer })
  }, [etat, setSp])

  const changerPage = (page) => { maj({ page }); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const reinitialiser = () => setSp(versUrl(ETAT_INITIAL))

  const nbFiltres = nombreFiltres(etat)
  const filieres = useMemo(() => {
    const noms = facettes.filieres.map((f) => f.valeur)
    return etat.filiere && !noms.includes(etat.filiere) ? [etat.filiere, ...noms] : noms
  }, [facettes, etat.filiere])
  const annees = useMemo(() => {
    const vals = facettes.annees.map((a) => String(a.valeur))
    return etat.annee && !vals.includes(etat.annee) ? [etat.annee, ...vals] : vals
  }, [facettes, etat.annee])

  const total = donnees?.total ?? 0
  const catalogueVide = !erreur && !chargement && donnees && total === 0 && nbFiltres === 0

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <section>
        <h1 className="font-serif text-3xl font-semibold tracking-tight text-vert">Catalogue des mémoires</h1>
        <p className="mt-2 max-w-2xl text-encre/75">
          Parcourez les mémoires de la bibliothèque : recherchez par thème, auteur ou directeur, filtrez par filière
          ou par année, puis ouvrez une fiche pour voir toutes les informations disponibles.
        </p>
        {totalCatalogue !== null && (
          <p className="mt-3 text-sm font-medium text-encre/80">
            <span className="text-2xl font-semibold text-vert">{nombre(totalCatalogue)}</span>{' '}
            {pluriel(totalCatalogue, 'mémoire disponible', 'mémoires disponibles')}
          </p>
        )}
      </section>

      <section aria-label="Recherche et filtres" className="rounded-lg border border-ligne bg-white p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-encre/65" aria-hidden="true" />
            <ChampTexte type="search" className="champ pl-9" aria-label="Rechercher un mémoire"
              placeholder="Rechercher un thème, un auteur, un directeur…" valeur={etat.q}
              onValider={(q) => maj({ q }, { remplacer: true })} />
          </div>
          <button className="btn btn-contour md:hidden" aria-expanded={filtresOuverts} aria-controls="filtres"
            onClick={() => setFiltresOuverts((o) => !o)}>
            <SlidersHorizontal size={16} aria-hidden="true" />Filtres{nbFiltres > 0 ? ` (${nbFiltres})` : ''}
          </button>
        </div>

        <div id="filtres" className={`${filtresOuverts ? 'grid' : 'hidden'} mt-4 gap-3 sm:grid-cols-2 md:grid md:grid-cols-5`}>
          <div>
            <Etiquette id="f-filiere">Filière</Etiquette>
            <select id="f-filiere" className="champ" value={etat.filiere} onChange={(e) => maj({ filiere: e.target.value })}>
              <option value="">Toutes les filières</option>
              {filieres.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div>
            <Etiquette id="f-annee">Année</Etiquette>
            <select id="f-annee" className="champ" value={etat.annee} onChange={(e) => maj({ annee: e.target.value })}>
              <option value="">Toutes les années</option>
              {annees.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <Etiquette id="f-auteur">Auteur</Etiquette>
            <ChampTexte id="f-auteur" className="champ" placeholder="Nom de l’auteur" valeur={etat.auteur}
              onValider={(auteur) => maj({ auteur }, { remplacer: true })} />
          </div>
          <div>
            <Etiquette id="f-tri">Trier par</Etiquette>
            <select id="f-tri" className="champ" value={etat.tri} onChange={(e) => maj({ tri: e.target.value })}>
              {TRIS.map((t) => <option key={t.valeur} value={t.valeur}>{t.libelle}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn btn-contour w-full" onClick={reinitialiser} disabled={nbFiltres === 0 && etat.tri === 'titre'}>
              <X size={15} aria-hidden="true" />Réinitialiser
            </button>
          </div>
        </div>
      </section>

      <section aria-label="Résultats" className="space-y-5">
        {!erreur && donnees && (
          <p className="text-sm text-encre/75" role="status" aria-live="polite">
            <strong className="font-semibold text-encre">{nombre(total)}</strong> {pluriel(total, 'résultat', 'résultats')}
            {nbFiltres > 0 && totalCatalogue !== null ? <> sur {nombre(totalCatalogue)}</> : null}
            {donnees.pages > 1 ? <> · page {donnees.page} sur {donnees.pages}</> : null}
          </p>
        )}

        {erreur ? <ErreurConnexion message={erreur} onRetry={() => setEssai((n) => n + 1)} />
          : chargement && !donnees ? <Chargement />
          : catalogueVide ? <CatalogueVide />
          : donnees && total === 0 ? <AucunResultat onReset={reinitialiser} />
          : donnees && (
            <div className={chargement ? 'opacity-60 transition-opacity' : 'transition-opacity'} aria-busy={chargement}>
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {donnees.items.map((m) => <li key={m.id} className="flex"><div className="flex w-full flex-col [&>article]:flex-1"><CarteMemoire m={m} /></div></li>)}
              </ul>
            </div>
          )}

        {!erreur && donnees && total > 0 && <Pagination page={donnees.page} pages={donnees.pages} onChange={changerPage} />}
      </section>
    </div>
  )
}
