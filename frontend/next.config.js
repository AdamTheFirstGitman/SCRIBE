/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  images: {
    domains: [
      'scribe-api.onrender.com',
      'eytfiohvhlqokikemlfn.supabase.co'
    ]
  },

  // Disable x-powered-by header
  poweredByHeader: false,

  // Optimize production build
  compress: true,

  // Generate unique build ID to prevent stale cache issues
  generateBuildId: async () => {
    // Use git commit hash + timestamp for cache busting
    return `${process.env.RENDER_GIT_COMMIT || 'local'}-${Date.now()}`
  },

  // CRITICAL: Configure headers to prevent Render CDN from caching HTML/JSON aggressively
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate',
          },
        ],
      },
      {
        source: '/_next/data/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=0, must-revalidate',
          },
        ],
      },
    ]
  }
}

module.exports = nextConfig