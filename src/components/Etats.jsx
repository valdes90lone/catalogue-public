import { AlertTriangle, Inbox, SearchX } from 'lucide-react'

export function Chargement({ nombre = 6 }) {
  return (
    <div role="status" aria-live="polite" aria-label="Chargement des mémoires">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: nombre }, (_, i) => (
          <div key={i} className="animate-pulse rounded-lg border border-ligne bg-white p-4">
            <div className="h-3 w-1/3 rounded bg-ligne" />
            <div className="mt-4 h-4 w-full rounded bg-ligne" />
            <div className="mt-2 h-4 w-5/6 rounded bg-ligne" />
            <div className="mt-6 h-3 w-1/2 rounded bg-ligne" />
          </div>
        ))}
      </div>
      <p className="mt-4 text-center text-sm text-encre/65">Chargement des mémoires… Le premier affichage peut prendre un peu de temps.</p>
    </div>
  )
}

function Bloc({ icone: Icone, titre, children, action }) {
  return (
    <div className="rounded-lg border border-ligne bg-white px-6 py-12 text-center">
      <Icone className="mx-auto text-vert" size={34} aria-hidden="true" />
      <h2 className="mt-3 font-serif text-lg font-semibold">{titre}</h2>
      <p className="mx-auto mt-1 max-w-md text-sm text-encre/70">{children}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export const ErreurConnexion = ({ message, onRetry }) => (
  <div role="alert">
    <Bloc icone={AlertTriangle} titre="Connexion au serveur impossible"
      action={onRetry && <button className="btn btn-plein" onClick={onRetry}>Réessayer</button>}>
      {message || 'Le catalogue est momentanément inaccessible.'} Vérifiez votre connexion, puis réessayez.
    </Bloc>
  </div>
)

export const CatalogueVide = () => (
  <Bloc icone={Inbox} titre="Le catalogue est vide">Aucun mémoire n’est disponible pour le moment.</Bloc>
)

export const AucunResultat = ({ onReset }) => (
  <Bloc icone={SearchX} titre="Aucun mémoire trouvé"
    action={<button className="btn btn-contour" onClick={onReset}>Réinitialiser les filtres</button>}>
    Aucun résultat ne correspond à votre recherche. Essayez d’autres mots, ou retirez un filtre.
  </Bloc>
)
