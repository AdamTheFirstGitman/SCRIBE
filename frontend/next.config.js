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
  compress: true
}

module.exports = nextConfig