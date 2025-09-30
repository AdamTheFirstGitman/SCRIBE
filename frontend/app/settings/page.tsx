'use client'

import { useState } from 'react'
import { useTheme } from '../../components/theme/ThemeProvider'
import { ThemeToggle } from '../../components/theme/ThemeToggle'
import { Feather, Brain, Trash2, Download, Info } from 'lucide-react'
import { toast } from 'sonner'

export default function SettingsPage() {
  const { theme } = useTheme()
  const [defaultAgent, setDefaultAgent] = useState<'plume' | 'mimir'>('plume')
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)

  const handleClearCache = () => {
    if (confirm('Êtes-vous sûr de vouloir vider le cache ?')) {
      localStorage.clear()
      toast.success('Cache vidé avec succès')
    }
  }

  const handleExportData = () => {
    const data = {
      settings: {
        theme,
        defaultAgent,
        voiceEnabled,
        notificationsEnabled,
      },
      exportDate: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `scribe-settings-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Paramètres exportés')
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-50 dark:text-gray-50 light:text-gray-900">
            Paramètres
          </h1>
          <p className="text-gray-400 dark:text-gray-400 light:text-gray-600 mt-2">
            Configure ton expérience avec Plume & Mimir
          </p>
        </div>

        {/* Appearance Section */}
        <section className="card p-6 space-y-4">
          <h2 className="text-xl font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-plume-500/20 dark:bg-plume-500/20 light:bg-plume-100 flex items-center justify-center">
              🎨
            </div>
            Apparence
          </h2>

          <div className="space-y-4">
            {/* Theme Toggle */}
            <div className="flex items-center justify-between py-3 border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
              <div>
                <label className="text-sm font-medium text-gray-200 dark:text-gray-200 light:text-gray-900">
                  Thème
                </label>
                <p className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600 mt-1">
                  Choisis entre dark, light, ou system
                </p>
              </div>
              <ThemeToggle />
            </div>

            {/* Current Theme Info */}
            <div className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600">
              Thème actuel: <span className="font-medium capitalize">{theme}</span>
            </div>
          </div>
        </section>

        {/* Agents Section */}
        <section className="card p-6 space-y-4">
          <h2 className="text-xl font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-mimir-500/20 dark:bg-mimir-500/20 light:bg-mimir-100 flex items-center justify-center">
              🤖
            </div>
            Agents
          </h2>

          <div className="space-y-4">
            {/* Default Agent */}
            <div className="py-3 border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
              <label className="text-sm font-medium text-gray-200 dark:text-gray-200 light:text-gray-900 block mb-3">
                Agent par défaut
              </label>
              <div className="flex gap-3">
                <button
                  onClick={() => setDefaultAgent('plume')}
                  className={`flex-1 flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                    defaultAgent === 'plume'
                      ? 'border-plume-500 bg-plume-500/10 dark:bg-plume-500/10 light:bg-plume-50'
                      : 'border-gray-800 dark:border-gray-800 light:border-gray-200 hover:border-gray-700 dark:hover:border-gray-700 light:hover:border-gray-300'
                  }`}
                >
                  <Feather className="w-5 h-5 text-plume-500" />
                  <div className="text-left">
                    <div className="font-medium text-gray-50 dark:text-gray-50 light:text-gray-900">
                      Plume
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600">
                      Restitution
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => setDefaultAgent('mimir')}
                  className={`flex-1 flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                    defaultAgent === 'mimir'
                      ? 'border-mimir-500 bg-mimir-500/10 dark:bg-mimir-500/10 light:bg-mimir-50'
                      : 'border-gray-800 dark:border-gray-800 light:border-gray-200 hover:border-gray-700 dark:hover:border-gray-700 light:hover:border-gray-300'
                  }`}
                >
                  <Brain className="w-5 h-5 text-mimir-500" />
                  <div className="text-left">
                    <div className="font-medium text-gray-50 dark:text-gray-50 light:text-gray-900">
                      Mimir
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600">
                      Recherche
                    </div>
                  </div>
                </button>
              </div>
            </div>

            {/* Voice Transcription */}
            <div className="flex items-center justify-between py-3 border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
              <div>
                <label className="text-sm font-medium text-gray-200 dark:text-gray-200 light:text-gray-900">
                  Transcription vocale
                </label>
                <p className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600 mt-1">
                  Active la transcription automatique
                </p>
              </div>
              <button
                onClick={() => setVoiceEnabled(!voiceEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  voiceEnabled
                    ? 'bg-plume-500'
                    : 'bg-gray-700 dark:bg-gray-700 light:bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    voiceEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Notifications */}
            <div className="flex items-center justify-between py-3">
              <div>
                <label className="text-sm font-medium text-gray-200 dark:text-gray-200 light:text-gray-900">
                  Notifications
                </label>
                <p className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600 mt-1">
                  Reçois des notifications pour les événements
                </p>
              </div>
              <button
                onClick={() => setNotificationsEnabled(!notificationsEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  notificationsEnabled
                    ? 'bg-plume-500'
                    : 'bg-gray-700 dark:bg-gray-700 light:bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    notificationsEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </section>

        {/* Data Management Section */}
        <section className="card p-6 space-y-4">
          <h2 className="text-xl font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 dark:bg-blue-500/20 light:bg-blue-100 flex items-center justify-center">
              💾
            </div>
            Données
          </h2>

          <div className="space-y-3">
            {/* Export Settings */}
            <button
              onClick={handleExportData}
              className="w-full flex items-center justify-between p-4 rounded-lg border border-gray-800 dark:border-gray-800 light:border-gray-200 hover:border-gray-700 dark:hover:border-gray-700 light:hover:border-gray-300 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <Download className="w-5 h-5 text-blue-500" />
                <div>
                  <div className="text-sm font-medium text-gray-200 dark:text-gray-200 light:text-gray-900">
                    Exporter les paramètres
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600">
                    Télécharge tes préférences
                  </div>
                </div>
              </div>
            </button>

            {/* Clear Cache */}
            <button
              onClick={handleClearCache}
              className="w-full flex items-center justify-between p-4 rounded-lg border border-red-900/30 dark:border-red-900/30 light:border-red-200 hover:border-red-800 dark:hover:border-red-800 light:hover:border-red-300 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <Trash2 className="w-5 h-5 text-red-500" />
                <div>
                  <div className="text-sm font-medium text-red-400 dark:text-red-400 light:text-red-600">
                    Vider le cache
                  </div>
                  <div className="text-xs text-red-400/60 dark:text-red-400/60 light:text-red-600/70">
                    Supprime toutes les données locales
                  </div>
                </div>
              </div>
            </button>
          </div>
        </section>

        {/* About Section */}
        <section className="card p-6 space-y-4">
          <h2 className="text-xl font-semibold text-gray-50 dark:text-gray-50 light:text-gray-900 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gray-700/50 dark:bg-gray-700/50 light:bg-gray-200 flex items-center justify-center">
              <Info className="w-4 h-4" />
            </div>
            À propos
          </h2>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
              <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">
                Application
              </span>
              <span className="text-gray-200 dark:text-gray-200 light:text-gray-900 font-medium">
                Plume & Mimir
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
              <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">
                Version
              </span>
              <span className="text-gray-200 dark:text-gray-200 light:text-gray-900 font-medium">
                2.0.0 (Chapitre 2)
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
              <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">
                Développé par
              </span>
              <span className="text-gray-200 dark:text-gray-200 light:text-gray-900 font-medium">
                EMPYR Team
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">
                Architecte
              </span>
              <span className="text-gray-200 dark:text-gray-200 light:text-gray-900 font-medium">
                Leo
              </span>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}