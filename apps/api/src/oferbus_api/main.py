from fastapi import FastAPI
from pydantic import BaseModel


class HealthStatus(BaseModel):
    service: str
    status: str
    version: str


app = FastAPI(
    title="OferBus API",
    version="0.1.0",
    description="Application boundary for the OferBus 2026 planning platform.",
)


@app.get("/health", response_model=HealthStatus, tags=["platform"])
def health() -> HealthStatus:
    return HealthStatus(service="oferbus-api", status="ok", version="0.1.0")
