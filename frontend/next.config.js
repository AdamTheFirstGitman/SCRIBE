/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: false, // Temporarily disabled to force chunk regeneration

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
  }
}

module.exports = nextConfig