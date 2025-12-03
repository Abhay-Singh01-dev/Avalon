from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from .routes import chat, graph, reports, upload, projects, admin, settings, llm, data_sources
from .db.mongo import init_db

logger = logging.getLogger(__name__)

app = FastAPI(title="Pharma Research AI",
             description="Backend for Pharma Research AI Platform",
             version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on application shutdown"""
    try:
        from .db.mongo import close_connection
        await close_connection()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(data_sources.router, tags=["Data Sources"])

# Mount uploads directory for serving report files
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
