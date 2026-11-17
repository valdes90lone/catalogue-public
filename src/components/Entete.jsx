import { Link } from 'react-router-dom'
import { BookOpen } from 'lucide-react'

export default function Entete() {
  return (
    <header className="border-b border-ligne bg-white">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
        <Link to="/" className="flex items-center gap-2.5 text-vert">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-vert text-white"><BookOpen size={20} aria-hidden="true" /></span>
          <span className="font-serif text-lg font-semibold leading-tight">Bibliothèque Mémoires</span>
        </Link>
        <span className="ml-auto hidden text-sm text-encre/65 sm:block">Catalogue en consultation</span>
      </div>
    </header>
  )
}
