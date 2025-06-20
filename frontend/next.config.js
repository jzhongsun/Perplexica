/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/locales/:path*',
        destination: '/public/locales/:path*'
      },
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*'
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ]
  }
}

module.exports = nextConfig