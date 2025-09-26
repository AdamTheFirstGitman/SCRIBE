/** @type {import('next').NextConfig} */

// Configuration simplifiée pour build rapide sur Render
const nextConfig = {
  // Basic settings
  reactStrictMode: true,
  swcMinify: true,

  // Performance optimizations
  // experimental: {
  //   optimizeCss: true, // Causes 'critters' module error
  // },

  // Disable PWA temporarily for faster builds
  // PWA can be re-enabled after deployment works

  // Images optimization
  images: {
    domains: [
      'scribe-api.onrender.com',
      'eytfiohvhlqokikemlfn.supabase.co'
    ],
    formats: ['image/webp', 'image/avif']
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '1.0.0',
    NEXT_PUBLIC_BUILD_TIME: new Date().toISOString(),
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig