from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from oferbus_db import check_database

from .ai import router as ai_router
from .computations import router as computations_router
from .edits import router as edits_router
from .history import router as history_router
from .identity import router as identity_router
from .march import router as march_router
from .planning import router as planning_router
from .recalculation import router as recalculation_router
from .results import router as results_router


class HealthStatus(BaseModel):
    service: str
    status: str
    version: str


class DatabaseStatus(BaseModel):
    status: str
    database: str
    schema_name: str
    server_version: str
    migration: str


app = FastAPI(
    title="OferBus API",
    version="0.15.0",
    description="Application boundary for the OferBus 2026 planning platform.",
)
app.include_router(identity_router)
app.include_router(computations_router)
app.include_router(ai_router)
app.include_router(planning_router)
app.include_router(results_router)
app.include_router(march_router)
app.include_router(edits_router)
app.include_router(recalculation_router)
app.include_router(history_router)


@app.get("/health", response_model=HealthStatus, tags=["platform"])
def health() -> HealthStatus:
    return HealthStatus(service="oferbus-api", status="ok", version="0.15.0")


@app.get("/ready", response_model=DatabaseStatus, tags=["platform"])
def ready() -> DatabaseStatus:
    try:
        database = check_database()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="PostgreSQL is not ready") from exc

    if database["migration"] == "unversioned":
        raise HTTPException(status_code=503, detail="PostgreSQL is reachable but migrations are not applied")

    return DatabaseStatus(
        status="ready",
        database=database["database"],
        schema_name="oferbus",
        server_version=database["server_version"],
        migration=database["migration"],
    )
