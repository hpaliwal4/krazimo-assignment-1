"""
Development server runner for the Intelligent Code Reviewer API.

This script starts the FastAPI application using uvicorn with development settings.
"""

import uvicorn
from app.core.config import settings


def main():
    """Start the development server."""
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    main() 