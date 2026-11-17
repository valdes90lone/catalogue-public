import { Link, useLocation } from 'react-router-dom'
import { CalendarDays, User, UserCheck } from 'lucide-react'
import { anneeAffichee, filiereAffichee, valeurAffichable } from '../utils/format.js'

export default function CarteMemoire({ m }) {
  const { search } = useLocation()
  const filiere = filiereAffichee(m)
  const annee = anneeAffichee(m)
  const auteur = valeurAffichable(m.auteur)
  const directeur = valeurAffichable(m.directeur)
  return (
    <article className="group relative flex flex-col rounded-lg border border-ligne bg-white p-4 transition-shadow focus-within:shadow-md hover:shadow-md">
      {filiere && <p className="mb-2"><span className="inline-block rounded bg-vert-clair px-2 py-0.5 text-xs font-medium text-vert">{filiere}</span></p>}
      <h3 className="clamp-3 font-serif text-base font-semibold leading-snug">
        <Link to={`/memoire/${m.id}`} state={{ retour: search }} className="text-encre after:absolute after:inset-0 hover:text-vert hover:underline">
          {valeurAffichable(m.theme) || <span className="italic text-encre/65">Thème non renseigné</span>}
        </Link>
      </h3>
      <dl className="mt-3 space-y-1.5 text-sm text-encre/80">
        <div className="flex gap-2"><dt className="sr-only">Auteur</dt><User size={15} className="mt-0.5 shrink-0 text-encre/65" aria-hidden="true" />
          <dd className="line-clamp-2">{auteur || <span className="italic text-encre/65">Auteur non renseigné</span>}</dd></div>
        <div className="flex gap-2"><dt className="sr-only">Année</dt><CalendarDays size={15} className="mt-0.5 shrink-0 text-encre/65" aria-hidden="true" />
          <dd>{annee || <span className="italic text-encre/65">Année non renseignée</span>}</dd></div>
        {directeur && <div className="flex gap-2"><dt className="sr-only">Directeur</dt><UserCheck size={15} className="mt-0.5 shrink-0 text-encre/65" aria-hidden="true" />
          <dd className="line-clamp-1">{directeur}</dd></div>}
      </dl>
    </article>
  )
}
