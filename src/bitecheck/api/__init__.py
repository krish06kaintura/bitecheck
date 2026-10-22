"""
BiteCheck API & Web Server Package.
Exports the FastAPI application and factory.
"""

from bitecheck.api.app import app, create_app

__all__ = ["app", "create_app"]
