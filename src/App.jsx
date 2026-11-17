import { Link, Route, Routes } from 'react-router-dom'
import Entete from './components/Entete.jsx'
import PiedDePage from './components/PiedDePage.jsx'
import Catalogue from './pages/Catalogue.jsx'
import Fiche from './pages/Fiche.jsx'

function PageIntrouvable() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16 text-center">
      <h1 className="font-serif text-2xl font-semibold">Page introuvable</h1>
      <p className="mt-2 text-encre/70">Cette adresse ne correspond à aucune page du catalogue.</p>
      <Link to="/" className="btn btn-plein mt-6">Retour au catalogue</Link>
    </div>
  )
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Entete />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Catalogue />} />
          <Route path="/memoire/:id" element={<Fiche />} />
          <Route path="*" element={<PageIntrouvable />} />
        </Routes>
      </main>
      <PiedDePage />
    </div>
  )
}
