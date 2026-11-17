import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink, FileText } from 'lucide-react'
import { Chargement, ErreurConnexion } from '../components/Etats.jsx'
import { obtenir, urlDocument } from '../services/catalogue.js'
import { anneeAffichee, filiereAffichee, valeurAffichable } from '../utils/format.js'

function Ligne({ libelle, valeur }) {
  if (!valeur) return null
  return (
    <div className="grid gap-1 border-b border-ligne/70 py-3 last:border-0 sm:grid-cols-3">
      <dt className="text-sm text-encre/65">{libelle}</dt>
      <dd className="sm:col-span-2">{valeur}</dd>
    </div>
  )
}

const Lien = ({ retour }) => (
  <Link to={`/${retour || ''}`} className="btn btn-contour"><ArrowLeft size={15} aria-hidden="true" />Retour au catalogue</Link>
)

export default function Fiche() {
  const { id } = useParams()
  const { state } = useLocation()
  const retour = state?.retour
  const [m, setM] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [introuvable, setIntrouvable] = useState(false)

  const charger = useCallback((signal) => {
    setM(null); setErreur(null); setIntrouvable(false)
    obtenir(id, signal).then(setM).catch((e) => {
      if (e.name === 'AbortError') return
      if (e.code === 'introuvable') setIntrouvable(true)
      else setErreur(e.message)
    })
  }, [id])

  useEffect(() => {
    const ctrl = new AbortController()
    charger(ctrl.signal)
    window.scrollTo({ top: 0 })
    return () => ctrl.abort()
  }, [charger])

  useEffect(() => {
    document.title = m?.theme ? `${m.theme} — Catalogue des mémoires` : 'Fiche du mémoire'
  }, [m])

  const cadre = (contenu) => <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">{contenu}</div>

  if (introuvable) {
    return cadre(<>
      <Lien retour={retour} />
      <div className="rounded-lg border border-ligne bg-white px-6 py-12 text-center">
        <h1 className="font-serif text-xl font-semibold">Mémoire introuvable</h1>
        <p className="mt-2 text-sm text-encre/70">Cette fiche n’existe pas ou n’est plus disponible.</p>
      </div>
    </>)
  }
  if (erreur) return cadre(<><Lien retour={retour} /><ErreurConnexion message={erreur} onRetry={() => charger()} /></>)
  if (!m) return cadre(<><Lien retour={retour} /><Chargement nombre={1} /></>)

  const titre = valeurAffichable(m.theme)
  const auteur = valeurAffichable(m.auteur)
  const annee = anneeAffichee(m)
  const filiere = filiereAffichee(m)
  const fichier = valeurAffichable(m.fichier)

  return cadre(<>
    <Lien retour={retour} />

    <article className="rounded-lg border border-ligne bg-white p-5 sm:p-8">
      {filiere && <p><span className="inline-block rounded bg-vert-clair px-2 py-0.5 text-xs font-medium text-vert">{filiere}</span></p>}
      <h1 className="mt-3 font-serif text-2xl font-semibold leading-snug sm:text-3xl">
        {titre || <span className="italic text-encre/65">Thème non renseigné</span>}
      </h1>
      <p className="mt-2 text-lg text-encre/75">{auteur || 'Auteur non renseigné'}</p>

      <h2 className="mb-1 mt-8 font-serif text-lg font-semibold text-vert">Informations</h2>
      <dl>
        <Ligne libelle="Auteur(s)" valeur={auteur} />
        <Ligne libelle="Directeur de mémoire" valeur={valeurAffichable(m.directeur)} />
        <Ligne libelle="Année" valeur={annee} />
        <Ligne libelle="Filière" valeur={filiere} />
        <Ligne libelle="Sous-filière" valeur={valeurAffichable(m.sous_filiere)} />
      </dl>

      {(valeurAffichable(m.filiere_llm) || valeurAffichable(m.filiere_chemin) || valeurAffichable(m.annee_chemin)) && (
        <>
          <h2 className="mb-1 mt-8 font-serif text-lg font-semibold text-vert">Autres informations du catalogue</h2>
          <dl>
            <Ligne libelle="Filière déclarée" valeur={valeurAffichable(m.filiere_llm)} />
            <Ligne libelle="Filière (dossier de classement)" valeur={valeurAffichable(m.filiere_chemin)} />
            <Ligne libelle="Année (dossier de classement)" valeur={valeurAffichable(m.annee_chemin)} />
          </dl>
        </>
      )}

      {fichier && (
        <>
          <h2 className="mb-2 mt-8 font-serif text-lg font-semibold text-vert">Document</h2>
          <p className="flex items-start gap-2 break-all text-sm text-encre/80"><FileText size={16} className="mt-0.5 shrink-0" aria-hidden="true" />{fichier}</p>
          {m.document_disponible && (
            <a className="btn btn-plein mt-4" href={urlDocument(m.id)} target="_blank" rel="noreferrer">
              <ExternalLink size={15} aria-hidden="true" />Ouvrir le document
            </a>
          )}
        </>
      )}
    </article>
  </>)
}
