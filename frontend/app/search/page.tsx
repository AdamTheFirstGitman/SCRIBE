'use client'

import { Search as SearchIcon, Filter, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

export default function SearchPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-3xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900">
            Recherche
          </h1>
          <p className="text-gray-400 dark:text-gray-400 light:text-gray-600 mt-2">
            Explore tes connaissances avec Mimir
          </p>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="relative"
        >
          <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-400 light:text-gray-600" />
          <input
            type="search"
            placeholder="Rechercher dans tes documents..."
            className="input-primary w-full pl-12 pr-4 py-4 text-lg"
            disabled
          />
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap gap-3"
        >
          <button
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800/50 dark:bg-gray-800/50 light:bg-gray-100 text-gray-400 dark:text-gray-400 light:text-gray-600 text-sm"
            disabled
          >
            <Filter className="w-4 h-4" />
            Filtres
          </button>
          <button
            className="px-4 py-2 rounded-lg bg-gray-800/50 dark:bg-gray-800/50 light:bg-gray-100 text-gray-400 dark:text-gray-400 light:text-gray-600 text-sm"
            disabled
          >
            Tous
          </button>
          <button
            className="px-4 py-2 rounded-lg bg-gray-800/50 dark:bg-gray-800/50 light:bg-gray-100 text-gray-400 dark:text-gray-400 light:text-gray-600 text-sm"
            disabled
          >
            Documents
          </button>
          <button
            className="px-4 py-2 rounded-lg bg-gray-800/50 dark:bg-gray-800/50 light:bg-gray-100 text-gray-400 dark:text-gray-400 light:text-gray-600 text-sm"
            disabled
          >
            Conversations
          </button>
        </motion.div>

        {/* Empty State / Coming Soon */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-12 text-center space-y-6"
        >
          <div className="w-20 h-20 rounded-2xl bg-mimir-500/20 dark:bg-mimir-500/20 light:bg-mimir-100 flex items-center justify-center mx-auto">
            <SearchIcon className="w-10 h-10 text-mimir-500" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900">
              Recherche Avancée
            </h2>
            <p className="text-gray-400 dark:text-gray-400 light:text-gray-600">
              Cette fonctionnalité sera disponible prochainement
            </p>
          </div>

          <div className="max-w-md mx-auto space-y-3 text-sm text-gray-400 dark:text-gray-400 light:text-gray-600">
            <p>Fonctionnalités prévues :</p>
            <ul className="space-y-2">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-mimir-500" />
                Recherche hybride (vector + fulltext + BM25)
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-mimir-500" />
                Filtres avancés (date, type, tags)
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-mimir-500" />
                Preview documents avec highlights
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-mimir-500" />
                Historique des recherches
              </li>
            </ul>
          </div>

          <div className="pt-4">
            <p className="text-xs text-gray-500 dark:text-gray-500 light:text-gray-500">
              En attendant, utilise Mimir dans le chat pour rechercher dans tes documents
            </p>
          </div>
        </motion.div>

        {/* Recent Searches (Placeholder) */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-4"
        >
          <h3 className="text-lg font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-400 dark:text-gray-400 light:text-gray-600" />
            Recherches récentes
          </h3>
          <div className="card p-8 text-center text-gray-400 dark:text-gray-400 light:text-gray-600 text-sm">
            Aucune recherche récente
          </div>
        </motion.div>
      </div>
    </div>
  )
}