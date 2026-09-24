// Cloudflare Pages Function: forwards /api/* to the API on Fly.io.
//
// Pages cannot proxy to an external origin through _redirects (200 rewrites
// are same-site only), so this Function does it instead. Keeping the call
// same-origin means the React code goes on using relative URLs and no CORS
// preflight is involved.
//
// The target is overridable per environment: set API_ORIGIN in the Pages
// project settings to point a preview branch at a different API.

// The custom domain, not the fly.dev name: moving hosts later is then a DNS
// edit rather than a code change.
const DEFAULT_API_ORIGIN = "https://orders-api.mauriceneme.com";

export async function onRequest({ env, params, request }) {
  const origin = env.API_ORIGIN || DEFAULT_API_ORIGIN;
  const path = Array.isArray(params.path) ? params.path.join("/") : params.path;
  const { search } = new URL(request.url);

  return fetch(new Request(`${origin}/api/${path}${search}`, request));
}
