import type { NextConfig } from 'next';

// Where the store API runs. Read when the app is built or started, so set it in production too.
const apiUrl = process.env.API_URL ?? 'http://localhost:8000';

const nextConfig: NextConfig = {
  async rewrites() {
    // The browser talks only to this site; /api/* is passed on to the backend. That keeps the
    // session cookie same-origin and avoids CORS.
    return [{ source: '/api/:path*', destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
