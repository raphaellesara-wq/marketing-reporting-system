from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every HTTP response.
    Protects against XSS, clickjacking, MIME sniffing, and data leakage.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Deny embedding in iframes (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS filter for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Force HTTPS for 1 year (only meaningful behind TLS in production)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Control referrer information sent to other sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser feature access
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Content Security Policy — tight for an API; frontend has its own CSP via meta tag
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'none';"
        )

        # Remove server fingerprinting header if present
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        return response
