"""
Instance data models
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional


class InstanceStatus(str, Enum):
    """Instance status enumeration"""
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"
    BUILDING = "building"
    UNKNOWN = "unknown"


class Instance(BaseModel):
    """Instance model"""
    id: str
    name: str
    status: InstanceStatus
    flavor: str
    image: str
    ip_address: Optional[str] = None
    uptime: str = "0h 0m"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_rx: float = 0.0
    network_tx: float = 0.0
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        use_enum_values = True