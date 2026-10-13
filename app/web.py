"""Production: the API server also serves the built dashboard (web/dist), so a deploy is one
process on one port behind the tunnel. In development Vite serves the dashboard instead.

Caching: files under assets/ have a content hash in their name, so they never change and can be
kept for a year. Everything else (index.html, sw.js, manifest, icons) is re-checked on each load,
so a new deploy is picked up at once, including by Cloudflare's cache.
"""

from pathlib import Path

from starlette.staticfiles import StaticFiles
from starlette.types import Scope

DIST = Path(__file__).resolve().parent.parent / "web" / "dist"

# Content Security Policy: everything comes from this site (no CDNs, analytics or outside fonts),
# so the browser refuses any script, style or connection injected from elsewhere. Inline styles are
# allowed for the "Is this you?" page (app/main.py). Adding a third party means adding it here and
# on the privacy page (docs/RULES.md §5).
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "manifest-src 'self'",
    "worker-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

# Safe for every response: they stop old browser behaviours (MIME sniffing, framing, leaking the
# full URL, with the "Is this you?" token, to other sites) and keep the site on HTTPS. HSTS is
# ignored over plain http (localhost), and leaves out other kharidwise.com subdomains.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": CSP,
    "Strict-Transport-Security": "max-age=15552000",
}


class DashboardFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        # `path` uses the OS separator (a backslash on Windows), so compare with "/" normalised.
        immutable = path.replace("\\", "/").startswith("assets/") and response.status_code == 200
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable" if immutable else "no-cache"
        return response
