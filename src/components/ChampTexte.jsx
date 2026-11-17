import { useEffect, useRef, useState } from 'react'
import { useDebounce } from '../hooks/useDebounce.js'

/**
 * Champ de saisie dont la valeur est « validée » après une courte pause (ou avec Entrée).
 * `valeur` vient de l'adresse (source de vérité) ; une réinitialisation extérieure vide donc bien le champ.
 */
export default function ChampTexte({ valeur, onValider, delai = 350, ...props }) {
  const [saisie, setSaisie] = useState(valeur)
  const derniere = useRef(valeur)
  const rappel = useRef(onValider)
  rappel.current = onValider
  const differee = useDebounce(saisie, delai)

  useEffect(() => {
    if (differee !== derniere.current) { derniere.current = differee; rappel.current(differee) }
  }, [differee])

  useEffect(() => {
    if (valeur !== derniere.current) { derniere.current = valeur; setSaisie(valeur) }
  }, [valeur])

  return (
    <input {...props} value={saisie}
      onChange={(e) => setSaisie(e.target.value)}
      onKeyDown={(e) => { if (e.key === 'Enter') { derniere.current = saisie; rappel.current(saisie) } }} />
  )
}
