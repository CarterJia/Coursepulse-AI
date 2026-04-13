from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.reports import router as reports_router

app = FastAPI(title="CoursePulse API")
app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
