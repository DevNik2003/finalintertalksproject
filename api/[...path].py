from app.main import app

# Vercel Python runtime expects an ASGI/WSGI-compatible `app` object.
# This file catches all requests under /api/* and forwards them to FastAPI.

__all__ = ["app"]
