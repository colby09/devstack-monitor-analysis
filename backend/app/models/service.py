"""
Service data models
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class Service(BaseModel):
    """Service model"""
    name: str
    status: ServiceStatus
    description: str
    port: int
    uptime: str = "0h 0m"
    response_time: float = 0.0
    last_check: str
    endpoint_url: Optional[str] = None
    version: Optional[str] = None
    
    class Config:
        use_enum_values = True