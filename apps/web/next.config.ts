import type { NextConfig } from 'next';

// Where the store API runs. Read when the app is built or started, so set it in production too.
// No fallback: a missing API_URL used to fall back to localhost, which then quietly shipped to
// production and made every request fail there. Failing the build here is the fix - it surfaces
// a missing or wrong API_URL immediately, in the deploy log, instead of as a broken live site.
const apiUrl = process.env.API_URL;
if (!apiUrl) {
  throw new Error(
    'API_URL is not set. Add it as an environment variable before building (see .env.example); ' +
      'for local development, put it in .env.',
  );
}

const nextConfig: NextConfig = {
  async rewrites() {
    // The browser talks only to this site; /api/* is passed on to the backend. That keeps the
    // session cookie same-origin and avoids CORS.
    return [{ source: '/api/:path*', destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
