'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, MessageSquare, Upload, Search, Settings, Feather, Brain } from 'lucide-react'
import { ThemeToggle } from '../theme/ThemeToggle'
import { motion } from 'framer-motion'

const navItems = [
  { href: '/', icon: Home, label: 'Accueil' },
  { href: '/chat', icon: MessageSquare, label: 'Chat' },
  { href: '/upload', icon: Upload, label: 'Upload' },
  { href: '/search', icon: Search, label: 'Recherche' },
  { href: '/settings', icon: Settings, label: 'Paramètres' },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <>
      {/* Desktop Navigation - Top Navbar */}
      <nav className="hidden lg:block fixed top-0 left-0 right-0 z-50 bg-gray-900/80 dark:bg-gray-900/80 light:bg-white/80 backdrop-blur-md border-b border-gray-800 dark:border-gray-800 light:border-gray-200">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="flex items-center gap-2">
              <Feather className="w-5 h-5 text-plume-500" />
              <span className="font-semibold text-lg text-gray-50 dark:text-gray-50 light:text-gray-900">
                Plume
              </span>
            </div>
            <span className="text-gray-500">&</span>
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-mimir-500" />
              <span className="font-semibold text-lg text-gray-50 dark:text-gray-50 light:text-gray-900">
                Mimir
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="flex items-center gap-6">
            {navItems.slice(0, -1).map(({ href, icon: Icon, label }) => {
              const isActive = pathname === href
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-plume-400 dark:text-plume-400 light:text-plume-600 bg-plume-500/10 dark:bg-plume-500/10 light:bg-plume-50'
                      : 'text-gray-400 dark:text-gray-400 light:text-gray-600 hover:text-gray-200 dark:hover:text-gray-200 light:hover:text-gray-900 hover:bg-gray-800/50 dark:hover:bg-gray-800/50 light:hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </Link>
              )
            })}
          </div>

          {/* Right section - Theme Toggle & Settings */}
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link
              href="/settings"
              className={`p-2 rounded-lg transition-colors ${
                pathname === '/settings'
                  ? 'text-plume-400 dark:text-plume-400 light:text-plume-600 bg-plume-500/10 dark:bg-plume-500/10 light:bg-plume-50'
                  : 'text-gray-400 dark:text-gray-400 light:text-gray-600 hover:text-gray-200 dark:hover:text-gray-200 light:hover:text-gray-900 hover:bg-gray-800/50 dark:hover:bg-gray-800/50 light:hover:bg-gray-100'
              }`}
              aria-label="Paramètres"
            >
              <Settings className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation - Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-gray-900/95 dark:bg-gray-900/95 light:bg-white/95 backdrop-blur-md border-t border-gray-800 dark:border-gray-800 light:border-gray-200 safe-bottom">
        <div className="flex items-center justify-around px-2 py-2">
          {navItems.map(({ href, icon: Icon, label }) => {
            const isActive = pathname === href

            return (
              <Link
                key={href}
                href={href}
                className="relative flex flex-col items-center justify-center w-full py-2 px-1"
              >
                {isActive && (
                  <motion.div
                    layoutId="mobile-active-indicator"
                    className="absolute inset-0 bg-plume-500/10 dark:bg-plume-500/10 light:bg-plume-50 rounded-xl"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon
                  className={`relative w-6 h-6 mb-1 transition-colors ${
                    isActive
                      ? 'text-plume-400 dark:text-plume-400 light:text-plume-600'
                      : 'text-gray-400 dark:text-gray-400 light:text-gray-600'
                  }`}
                />
                <span
                  className={`relative text-xs font-medium transition-colors ${
                    isActive
                      ? 'text-plume-400 dark:text-plume-400 light:text-plume-600'
                      : 'text-gray-400 dark:text-gray-400 light:text-gray-600'
                  }`}
                >
                  {label}
                </span>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Spacer for fixed navigation */}
      <div className="hidden lg:block h-16" />
      <div className="lg:hidden h-20" />
    </>
  )
}