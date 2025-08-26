"""
Forensic analysis models for memory dump analysis
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class AnalysisStatus(str, Enum):
    """Status of forensic analysis"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, Enum):
    """Types of forensic analysis"""
    PROCESSES = "processes"
    NETWORK = "network"
    FILES = "files"
    MODULES = "modules"
    SYSTEM_INFO = "system_info"
    BASH_HISTORY = "bash_history"


class ProcessInfo(BaseModel):
    """Process information from pslist"""
    pid: int
    ppid: int
    name: str
    state: str
    uid: int
    gid: int
    start_time: Optional[str] = None
    memory: Optional[str] = None


class NetworkConnection(BaseModel):
    """Network connection information"""
    protocol: str
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    state: str
    pid: Optional[int] = None
    process: Optional[str] = None


class OpenFile(BaseModel):
    """Open file information"""
    pid: int
    process: str
    fd: str
    path: str
    file_type: str


class KernelModule(BaseModel):
    """Kernel module information"""
    name: str
    size: int
    instances: int
    dependencies: List[str] = []
    offset: Optional[str] = None


class SystemInfo(BaseModel):
    """System information from banner/info"""
    kernel_version: str
    architecture: str
    hostname: Optional[str] = None
    uptime: Optional[str] = None
    memory_total: Optional[str] = None


class AnalysisResults(BaseModel):
    """Complete analysis results"""
    processes: List[ProcessInfo] = []
    network: List[NetworkConnection] = []
    files: List[OpenFile] = []
    modules: List[KernelModule] = []
    system_info: Optional[SystemInfo] = None
    bash_history: List[str] = []


class ForensicAnalysis(BaseModel):
    """Forensic analysis record"""
    id: str
    dump_id: str
    instance_id: str
    instance_name: str
    status: AnalysisStatus
    progress: int = 0  # 0-100%
    current_step: Optional[str] = None
    results: Optional[AnalysisResults] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dump_file_path: str
    volatility_path: str = "/tmp/volatility3-2.26.0"
    # Campi per identificazione OS/kernel
    os_type: Optional[str] = None
    kernel_version: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request to start forensic analysis"""
    dump_id: str
    analysis_types: List[AnalysisType] = [
        AnalysisType.PROCESSES,
        AnalysisType.NETWORK, 
        AnalysisType.FILES,
        AnalysisType.MODULES,
        AnalysisType.SYSTEM_INFO
    ]
