"""
Services API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.openstack import OpenStackClient
from app.models.service import Service, ServiceStatus

router = APIRouter()


class ServiceResponse(BaseModel):
    """Service response model"""
    name: str
    status: ServiceStatus
    description: str
    port: int
    uptime: str
    response_time: float
    last_check: str


@router.get("", response_model=List[ServiceResponse])
async def get_services(
    status: Optional[ServiceStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name")
):
    """Get all OpenStack services"""
    try:
        openstack_client = OpenStackClient()
        services = await openstack_client.get_services()
        
        # Apply filters
        if status:
            services = [s for s in services if s.status == status]
        
        if search:
            search_lower = search.lower()
            services = [
                s for s in services 
                if search_lower in s.name.lower() or search_lower in s.description.lower()
            ]
        
        return services
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_name}", response_model=ServiceResponse)
async def get_service(service_name: str):
    """Get specific service details"""
    try:
        openstack_client = OpenStackClient()
        service = await openstack_client.get_service(service_name)
        
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return service
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{service_name}/health-check")
async def check_service_health(service_name: str):
    """Force health check for specific service"""
    try:
        openstack_client = OpenStackClient()
        health_status = await openstack_client.check_service_health(service_name)
        
        return {
            "service_name": service_name,
            "health_status": health_status,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_services_summary():
    """Get services summary statistics"""
    try:
        openstack_client = OpenStackClient()
        summary = await openstack_client.get_services_summary()
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))