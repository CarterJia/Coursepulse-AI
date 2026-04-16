from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.assignments import router as assignments_router
from app.api.routes.documents import router as documents_router
from app.api.routes.files import router as files_router
from app.api.routes.glossary import router as glossary_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.reports import router as reports_router
from app.api.routes.videos import router as videos_router
from app.middleware.byok import BYOKMiddleware

app = FastAPI(title="CoursePulse API")


@app.middleware("http")
async def reject_path_traversal(request: Request, call_next):
    raw = request.url.path
    # Reject encoded slashes or literal dot-dot in any /api/files/ request
    if raw.startswith("/api/files/") and ("%2f" in raw.lower() or ".." in raw):
        return JSONResponse(status_code=400, content={"detail": "Path traversal rejected"})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BYOKMiddleware)

app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(assignments_router, prefix="/api")
app.include_router(glossary_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(videos_router, prefix="/api")
