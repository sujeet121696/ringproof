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

# Safe for every response: they only stop old browser behaviours (MIME sniffing, framing, leaking
# the full URL, with the "Is this you?" token, to other sites).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}


class DashboardFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        # `path` uses the OS separator (a backslash on Windows), so compare with "/" normalised.
        immutable = path.replace("\\", "/").startswith("assets/") and response.status_code == 200
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable" if immutable else "no-cache"
        return response
