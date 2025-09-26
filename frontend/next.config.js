/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  images: {
    domains: [
      'scribe-api.onrender.com',
      'eytfiohvhlqokikemlfn.supabase.co'
    ]
  }
}

module.exports = nextConfig