import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.config import settings
from app.db.database import engine, Base
from app.api import health, projects, scenes, story_state, issues, claims, research, retrieval, reasoning, unified, timeline, settings as settings_api, documents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("script_supervisor.main")

app = FastAPI(
    title="Script Supervisor API",
    description="Backend API for AI-powered Screenplay Story World Engine (Day 6 Hybrid Retrieval & Reasoning Refinement System)",
    version="6.0.0"
)

# CORS setup
cors_list = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_list:
    cors_list.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

from app.services.rate_limiter import limiter

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method.upper()

    # Skip health check from rate limiting
    if path in ("/api/health", "/health"):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    category = "cheap"
    if "/documents" in path and ("import" in path or "confirm-import" in path):
        category = "import"
    elif "/research" in path and method in ("POST", "PUT"):
        category = "research"
    elif ("/analyze" in path or "/reason" in path or "/timeline/extract" in path) and method in ("POST", "PUT"):
        category = "analysis"
    elif method in ("POST", "PUT", "DELETE", "PATCH"):
        category = "write"

    try:
        limiter.check_rate_limit(request, category=category)
    except HTTPException as he:
        res = JSONResponse(status_code=he.status_code, content={"detail": he.detail})
        if he.headers:
            for k, v in he.headers.items():
                res.headers[k] = v
        return res

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Include Routers
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(scenes.router)
app.include_router(story_state.router)
app.include_router(issues.router)
app.include_router(claims.router)
app.include_router(research.router)
app.include_router(retrieval.router)
app.include_router(reasoning.router)
app.include_router(unified.router)
app.include_router(timeline.router)
app.include_router(settings_api.router)
app.include_router(documents.router)


@app.on_event("startup")
def startup_event():
    logger.info("Initializing database tables & schema migrations...")
    try:
        Base.metadata.create_all(bind=engine)

        # Ensure Day 4 & Day 5 columns exist on SQLite tables
        inspector = inspect(engine)
        if "issues" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("issues")]
            with engine.begin() as conn:
                if "reviewed_at" not in columns:
                    conn.execute(text("ALTER TABLE issues ADD COLUMN reviewed_at DATETIME"))
                if "reviewed_by" not in columns:
                    conn.execute(text("ALTER TABLE issues ADD COLUMN reviewed_by VARCHAR(50) DEFAULT 'writer'"))
                if "resolution_type" not in columns:
                    conn.execute(text("ALTER TABLE issues ADD COLUMN resolution_type VARCHAR(50)"))
                if "resolution_note" not in columns:
                    conn.execute(text("ALTER TABLE issues ADD COLUMN resolution_note TEXT"))
                if "issue_fingerprint" not in columns:
                    conn.execute(text("ALTER TABLE issues ADD COLUMN issue_fingerprint VARCHAR(64)"))

        if "scenes" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("scenes")]
            with engine.begin() as conn:
                if "source_document_id" not in columns:
                    conn.execute(text("ALTER TABLE scenes ADD COLUMN source_document_id VARCHAR(36)"))
                if "source_page_start" not in columns:
                    conn.execute(text("ALTER TABLE scenes ADD COLUMN source_page_start INTEGER"))
                if "source_page_end" not in columns:
                    conn.execute(text("ALTER TABLE scenes ADD COLUMN source_page_end INTEGER"))
                if "source_type" not in columns:
                    conn.execute(text("ALTER TABLE scenes ADD COLUMN source_type VARCHAR(50) DEFAULT 'MANUAL'"))

        logger.info("Database schema initialized and verified successfully.")
    except Exception as e:
        logger.warning(f"Notice on database schema initialization: {e}")

    logger.info("Script Supervisor Backend started (Day 6 Hybrid Retrieval & Reasoning Refinement System active).")
    logger.info(f"Target FRONTEND_URL: {settings.FRONTEND_URL}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
