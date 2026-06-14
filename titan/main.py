"""TITAN AIO -- application entry point."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Database.connection import init_db, close_db
from titan.config import settings

# FastAPI app for health + admin
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Autonomous Affiliate Intelligence Operating System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    """Initialize database and services on startup."""
    await init_db()


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up resources on shutdown."""
    await close_db()


@app.get("/")
async def root() -> dict:
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health_endpoint() -> dict:
    return {"status": "ok", "version": "0.1.0"}


def main() -> None:
    """Run the TITAN AIO server."""
    uvicorn.run(
        "titan.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
