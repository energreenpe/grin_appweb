import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // Regla nueva (react-hooks v7 / React Compiler) que marca como error el
      // patrón estándar de cargar datos en useEffect. La app usa ese patrón en
      // todas las pantallas; la dejamos como advertencia hasta migrar el fetching
      // a React Query (ya instalado). No oculta bugs reales, solo guía de estilo.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
])
