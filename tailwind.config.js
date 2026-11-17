/** @type {import('tailwindcss').Config} */
// Identité verte. Contrastes (WCAG) : blanc sur vert 7,1:1 · blanc sur vert foncé 9,9:1 ·
// vert sur blanc 7,1:1 · vert sur vert clair 6,2:1 · texte encre sur fond clair ≥ 14:1.
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        encre: '#18251d',
        papier: '#f5f8f5',
        vert: { DEFAULT: '#166534', fonce: '#0f4d2c', clair: '#e6f2e9', moyen: '#2f7d4f' },
        ligne: '#cfdad2',
        contour: '#6b8574', // bordure des champs de saisie (≥ 3:1 sur blanc)
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'system-ui', '-apple-system', 'Roboto', 'sans-serif'],
        serif: ['Georgia', '"Times New Roman"', 'serif'],
      },
    },
  },
  plugins: [],
}
