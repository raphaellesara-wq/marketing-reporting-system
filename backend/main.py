from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import engine, Base
from app.routes import auth, clients, integrations, reports

# Create tables on startup (use Alembic migrations in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Marketing Reporting SaaS",
    description="Automated marketing performance reporting with 50+ integrations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated reports as static files
os.makedirs(settings.reports_dir, exist_ok=True)
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=settings.reports_dir), name="reports")

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0", "app": settings.app_name}


@app.get("/")
def root():
    return {
        "message": "Marketing Reporting SaaS API",
        "docs": "/docs",
        "health": "/health",
    }
