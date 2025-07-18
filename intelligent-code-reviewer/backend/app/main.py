from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.main import router as api_router
from .core.config import settings
from .db.session import create_tables


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: The configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Include API router
    app.include_router(api_router)
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize database on startup."""
        create_tables()
    
    @app.get("/")
    async def root():
        """Root endpoint for health check."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "status": "healthy"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": settings.app_version}
    
    return app


# Create the application instance
app = create_application() 