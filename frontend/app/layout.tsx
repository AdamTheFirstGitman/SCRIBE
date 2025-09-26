import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { PWAInstallPrompt } from '@/components/pwa/InstallPrompt'
import OfflineStatus from '@/components/OfflineStatus'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL(process.env['NEXT_PUBLIC_APP_URL'] || 'https://scribe-frontend.onrender.com'),
  title: {
    default: 'Plume & Mimir',
    template: '%s | Plume & Mimir'
  },
  description: 'AI-powered knowledge management system with intelligent agents',
  keywords: ['AI', 'knowledge management', 'agents', 'notes', 'search', 'transcription'],
  authors: [{ name: 'EMPYR Team' }],
  creator: 'Leo - EMPYR Architect',

  // PWA Configuration
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Plume & Mimir',
  },

  // Open Graph
  openGraph: {
    type: 'website',
    locale: 'fr_FR',
    url: process.env['NEXT_PUBLIC_APP_URL'] || 'https://scribe-frontend.onrender.com',
    title: 'Plume & Mimir - Gestion de Connaissances IA',
    description: 'Système intelligent de gestion de connaissances avec agents IA spécialisés',
    siteName: 'Plume & Mimir',
  },

  // Twitter Card
  twitter: {
    card: 'summary',
    title: 'Plume & Mimir',
    description: 'Gestion de connaissances avec IA',
  },

  // Icons
  icons: {
    icon: [
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'mask-icon', url: '/safari-pinned-tab.svg', color: '#8B5CF6' },
    ],
  },

  // Security
  robots: {
    index: false, // Private app
    follow: false,
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#8B5CF6' },
    { media: '(prefers-color-scheme: dark)', color: '#0F0F0F' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr" className="dark" suppressHydrationWarning>
      <head>
        {/* Preconnect to external domains */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />

        {/* Additional PWA meta tags */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="application-name" content="Plume & Mimir" />
        <meta name="format-detection" content="telephone=no" />

        {/* iOS specific */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Plume & Mimir" />

        {/* Microsoft */}
        <meta name="msapplication-TileColor" content="#8B5CF6" />
        <meta name="msapplication-config" content="/browserconfig.xml" />

        {/* Performance hints */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="dns-prefetch" href="//fonts.gstatic.com" />
      </head>
      <body
        className={`${inter.className} bg-gray-950 text-gray-50 antialiased`}
        suppressHydrationWarning
      >
        <Providers>
          {/* Main Application Layout */}
          <div className="min-h-screen flex flex-col">
            {/* Skip to main content for accessibility */}
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-plume-500 text-white px-4 py-2 rounded-lg"
            >
              Aller au contenu principal
            </a>

            {/* Main Content */}
            <main id="main-content" className="flex-1 flex flex-col">
              {children}
            </main>
          </div>

          {/* PWA Install Prompt */}
          <PWAInstallPrompt />

          {/* Offline Status Indicator */}
          <OfflineStatus />
        </Providers>

        {/* Service Worker Registration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js')
                  .then(function(registration) {
                    console.log('Service Worker enregistré');

                    // Update available
                    registration.addEventListener('updatefound', () => {
                      const newWorker = registration.installing;
                      newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                          // Show update notification
                          if (confirm('Nouvelle version disponible. Actualiser ?')) {
                            window.location.reload();
                          }
                        }
                      });
                    });
                  })
                  .catch(function(registrationError) {
                    console.log('Échec enregistrement SW:', registrationError);
                  });
              }
            `,
          }}
        />
      </body>
    </html>
  )
}