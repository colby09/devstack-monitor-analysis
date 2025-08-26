"""
Memory dump model for digital forensics
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class DumpStatus(str, Enum):
    """Dump status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DumpType(str, Enum):
    """Dump type enumeration"""
    PHYSICAL_RAM = "physical_ram"
    PROCESS_SPECIFIC = "process_specific"


class MemoryDump(BaseModel):
    """Memory dump model"""
    id: str
    instance_id: str
    instance_name: str
    os_type: str
    dump_type: DumpType
    status: DumpStatus
    file_path: str
    file_size: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    ssh_host: Optional[str] = None
    checksum: Optional[str] = None


class DumpRequest(BaseModel):
    """Memory dump request model"""
    instance_id: str
    dump_type: DumpType = DumpType.PHYSICAL_RAM
    ssh_key_path: Optional[str] = None
    ssh_user: str = "root"


class DumpRequestBody(BaseModel):
    """Memory dump request body model (without instance_id for endpoints)"""
    dump_type: DumpType = DumpType.PHYSICAL_RAM
    ssh_key_path: Optional[str] = None
    ssh_user: str = "root"


class DumpResponse(BaseModel):
    """Memory dump response model"""
    dump_id: str
    message: str
    status: DumpStatus
