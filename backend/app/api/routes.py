"""
Main API router
"""

from fastapi import APIRouter

from .endpoints import instances, services, metrics, alerts, system, dumps, forensics, forensic

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(instances.router, prefix="/instances", tags=["instances"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(dumps.router, prefix="/dumps", tags=["memory-dumps"])
api_router.include_router(forensics.router, prefix="/forensics", tags=["forensics"])
api_router.include_router(forensic.router, prefix="/integrated-forensic", tags=["integrated-forensic"])