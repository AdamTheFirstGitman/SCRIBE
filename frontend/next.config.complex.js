/** @type {import('next').NextConfig} */

const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'google-fonts',
        expiration: {
          maxEntries: 4,
          maxAgeSeconds: 365 * 24 * 60 * 60 // 365 days
        }
      }
    },
    {
      urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'google-fonts-static',
        expiration: {
          maxEntries: 4,
          maxAgeSeconds: 365 * 24 * 60 * 60 // 365 days
        }
      }
    },
    {
      urlPattern: /\.(?:js|css|woff|woff2|eot|ttf|otf)$/i,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'static-assets'
      }
    },
    {
      urlPattern: /^\/api\/.*/i,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        networkTimeoutSeconds: 10,
        expiration: {
          maxEntries: 16,
          maxAgeSeconds: 24 * 60 * 60 // 24 hours
        }
      }
    }
  ],
  buildExcludes: [/middleware-manifest\.json$/]
})

const nextConfig = {
  // Use standalone for Render.com deployment (better compatibility)
  output: 'standalone',
  trailingSlash: false,

  // Enable image optimization for production (Render compatible)
  images: {
    unoptimized: process.env.NODE_ENV === 'production',
    domains: ['eytfiohvhlqokikemlfn.supabase.co'],
    formats: ['image/webp', 'image/avif'],
  },

  // Compiler options
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Experimental features
  experimental: {
    // Enable server components logging
    serverComponentsExternalPackages: ['@supabase/supabase-js'],
    // Enable modern bundling
    esmExternals: true,
  },

  // TypeScript configuration
  typescript: {
    // Allow builds to complete for Render deploy
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    // Allow ESLint during builds for better code quality
    ignoreDuringBuilds: false,
    dirs: ['app', 'components', 'lib', 'hooks'],
  },

  // Headers for security and performance
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Security headers
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(self), microphone=(self), geolocation=(), interest-cohort=()'
          },
          // Performance headers
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          }
        ],
      },
      {
        source: '/sw.js',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate'
          }
        ]
      }
    ]
  },

  // Redirects for better UX
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/chat',
        permanent: true,
      },
      {
        source: '/dashboard',
        destination: '/chat',
        permanent: true,
      }
    ]
  },

  // Rewrites for API proxy (development only)
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`
        }
      ]
    }
    return []
  },

  // Environment variables to expose to browser
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '1.0.0',
    NEXT_PUBLIC_BUILD_TIME: new Date().toISOString(),
  },

  // Bundle analyzer (conditional)
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config, { dev, isServer }) => {
      if (!dev && !isServer) {
        const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer')
        config.plugins.push(
          new BundleAnalyzerPlugin({
            analyzerMode: 'static',
            openAnalyzer: false,
            reportFilename: '../analyze/client.html'
          })
        )
      }
      return config
    }
  }),

  // Custom webpack configuration
  webpack: (config, { dev, isServer }) => {
    // Fix for 'fs' module error
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      }
    }

    // Force alias resolution for Render.com deployment
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': require('path').resolve(__dirname),
      '@/components': require('path').resolve(__dirname, 'components'),
      '@/lib': require('path').resolve(__dirname, 'lib'),
      '@/app': require('path').resolve(__dirname, 'app'),
      '@/hooks': require('path').resolve(__dirname, 'hooks'),
      '@/styles': require('path').resolve(__dirname, 'styles'),
      '@/types': require('path').resolve(__dirname, 'types'),
      '@/utils': require('path').resolve(__dirname, 'utils'),
    }

    // Optimize chunks in production
    if (!dev) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
            chunks: 'all',
          },
          common: {
            minChunks: 2,
            priority: 5,
            chunks: 'all',
            reuseExistingChunk: true,
          },
        },
      }
    }

    return config
  },

  // Performance budgets
  onDemandEntries: {
    // Period (in ms) where the server will keep pages in the buffer
    maxInactiveAge: 25 * 1000,
    // Number of pages that should be kept simultaneously without being disposed
    pagesBufferLength: 2,
  },
}

// Only wrap with PWA in production or when explicitly enabled
const shouldUsePWA = process.env.NODE_ENV === 'production' || process.env.ENABLE_PWA === 'true'

module.exports = shouldUsePWA ? withPWA(nextConfig) : nextConfig