import { ChevronLeft, ChevronRight } from 'lucide-react'
import { fenetrePages } from '../utils/format.js'

export default function Pagination({ page, pages, onChange }) {
  if (pages <= 1) return null
  return (
    <nav aria-label="Pagination" className="flex flex-wrap items-center justify-center gap-1.5">
      <button className="btn btn-contour" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Page précédente">
        <ChevronLeft size={16} aria-hidden="true" /><span className="hidden sm:inline">Précédent</span>
      </button>
      {/* Numéros de page : masqués sur petit écran, remplacés par « Page X sur Y » */}
      <ul className="hidden items-center gap-1.5 sm:flex">
        {fenetrePages(page, pages).map((p, i) => (
          <li key={p ?? `e${i}`}>
            {p === null ? <span className="px-1 text-encre/65" aria-hidden="true">…</span> : (
              <button className={`btn min-w-[2.5rem] ${p === page ? 'btn-plein' : 'btn-contour'}`}
                aria-current={p === page ? 'page' : undefined} aria-label={`Page ${p}`} onClick={() => onChange(p)}>{p}</button>
            )}
          </li>
        ))}
      </ul>
      <span className="px-2 text-sm text-encre/70 sm:hidden">Page {page} sur {pages}</span>
      <button className="btn btn-contour" disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Page suivante">
        <span className="hidden sm:inline">Suivant</span><ChevronRight size={16} aria-hidden="true" />
      </button>
    </nav>
  )
}
