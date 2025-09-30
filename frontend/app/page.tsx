'use client'

import Link from 'next/link'
import { Feather, Brain, MessageSquare, Upload, Search, ArrowRight } from 'lucide-react'
import { motion } from 'framer-motion'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-6xl">
      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center py-16 space-y-8"
      >
        <div className="flex items-center justify-center gap-4">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="w-16 h-16 rounded-2xl bg-plume-500/20 dark:bg-plume-500/20 light:bg-plume-100 flex items-center justify-center"
          >
            <Feather className="w-8 h-8 text-plume-500" />
          </motion.div>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
            className="w-16 h-16 rounded-2xl bg-mimir-500/20 dark:bg-mimir-500/20 light:bg-mimir-100 flex items-center justify-center"
          >
            <Brain className="w-8 h-8 text-mimir-500" />
          </motion.div>
        </div>

        <div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900 mb-4">
            Plume & Mimir
          </h1>
          <p className="text-xl md:text-2xl text-gray-400 dark:text-gray-400 light:text-gray-600 max-w-2xl mx-auto">
            Ton système intelligent de gestion de connaissances
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/chat"
            className="btn-primary group flex items-center gap-2 text-lg px-8 py-4"
          >
            Commencer
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/upload"
            className="btn-secondary group flex items-center gap-2 text-lg px-8 py-4"
          >
            <Upload className="w-5 h-5" />
            Upload Document
          </Link>
        </div>
      </motion.section>

      {/* Agents Cards */}
      <motion.section
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="grid md:grid-cols-2 gap-6 py-12"
      >
        {/* Plume Card */}
        <Link href="/chat?agent=plume" className="card-hover p-8 space-y-4">
          <div className="w-14 h-14 rounded-xl bg-plume-500/20 dark:bg-plume-500/20 light:bg-plume-100 flex items-center justify-center">
            <Feather className="w-7 h-7 text-plume-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900">
            Plume
          </h2>
          <p className="text-gray-400 dark:text-gray-400 light:text-gray-600">
            Agent de restitution intelligent. Transcription vocale, reformulation et capture de tes
            idées en temps réel.
          </p>
          <div className="flex items-center gap-2 text-plume-500 font-medium text-sm">
            Parler à Plume
            <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        {/* Mimir Card */}
        <Link href="/chat?agent=mimir" className="card-hover p-8 space-y-4">
          <div className="w-14 h-14 rounded-xl bg-mimir-500/20 dark:bg-mimir-500/20 light:bg-mimir-100 flex items-center justify-center">
            <Brain className="w-7 h-7 text-mimir-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900">
            Mimir
          </h2>
          <p className="text-gray-400 dark:text-gray-400 light:text-gray-600">
            Agent archiviste et recherche. RAG avancé, recherche hybride et accès instantané à tes
            connaissances.
          </p>
          <div className="flex items-center gap-2 text-mimir-500 font-medium text-sm">
            Parler à Mimir
            <ArrowRight className="w-4 h-4" />
          </div>
        </Link>
      </motion.section>

      {/* Features Grid */}
      <motion.section
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="py-12"
      >
        <h2 className="text-3xl font-bold text-center text-gray-50 dark:text-gray-50 light:text-gray-900 mb-8">
          Fonctionnalités
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="card p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/20 dark:bg-blue-500/20 light:bg-blue-100 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-blue-500" />
            </div>
            <h3 className="font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900">
              Chat Intelligent
            </h3>
            <p className="text-sm text-gray-400 dark:text-gray-400 light:text-gray-600">
              Converse avec Plume et Mimir en texte ou voix
            </p>
          </div>

          <div className="card p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 dark:bg-purple-500/20 light:bg-purple-100 flex items-center justify-center">
              <Upload className="w-5 h-5 text-purple-500" />
            </div>
            <h3 className="font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900">
              Upload Documents
            </h3>
            <p className="text-sm text-gray-400 dark:text-gray-400 light:text-gray-600">
              Importe et analyse tes documents automatiquement
            </p>
          </div>

          <div className="card p-6 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 dark:bg-emerald-500/20 light:bg-emerald-100 flex items-center justify-center">
              <Search className="w-5 h-5 text-emerald-500" />
            </div>
            <h3 className="font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900">
              Recherche Avancée
            </h3>
            <p className="text-sm text-gray-400 dark:text-gray-400 light:text-gray-600">
              RAG hybride avec recherche vectorielle et fulltext
            </p>
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="py-12 text-center"
      >
        <div className="card p-12 space-y-6 bg-gradient-plume">
          <h2 className="text-3xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900">
            Prêt à commencer ?
          </h2>
          <p className="text-gray-300 dark:text-gray-300 light:text-gray-700 max-w-xl mx-auto">
            Transforme ta façon de gérer tes connaissances avec l'intelligence artificielle
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 bg-plume-500 hover:bg-plume-600 text-white font-medium px-8 py-4 rounded-lg transition-colors shadow-lg hover:shadow-xl"
          >
            Lancer une conversation
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </motion.section>
    </div>
  )
}