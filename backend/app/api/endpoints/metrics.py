"""
Metrics API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
import psutil
import os
import logging

# Import services
from ...services.openstack import OpenStackClient
from ...services.memory_dump import memory_dump_service
from ...services.integrated_forensic import integrated_forensic_service

router = APIRouter()
openstack_client = OpenStackClient()
logger = logging.getLogger(__name__)


class MetricPoint(BaseModel):
    """Single metric data point"""
    timestamp: datetime
    value: float


class SystemMetrics(BaseModel):
    """System metrics response"""
    cpu_usage: List[MetricPoint]
    memory_usage: List[MetricPoint]
    disk_usage: List[MetricPoint]
    network_io: List[MetricPoint]


@router.get("/")
async def get_comprehensive_metrics() -> Dict[str, Any]:
    """Get comprehensive system and application metrics"""
    try:
        logger.info("Collecting comprehensive metrics...")
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        # Dump statistics
        try:
            all_dumps = memory_dump_service.get_all_dumps()
            completed_dumps = len([d for d in all_dumps if d.status.value == "completed"])
            failed_dumps = len([d for d in all_dumps if d.status.value == "failed"])
            in_progress_dumps = len([d for d in all_dumps if d.status.value == "in_progress"])
            
            # Calculate total dump size
            total_dump_size = 0
            for dump in all_dumps:
                if dump.status.value == "completed" and dump.file_path and os.path.exists(dump.file_path):
                    try:
                        total_dump_size += os.path.getsize(dump.file_path)
                    except Exception as e:
                        logger.warning(f"Could not get size for dump {dump.id}: {e}")
            
            dump_metrics = {
                "total": len(all_dumps),
                "completed": completed_dumps,
                "failed": failed_dumps,
                "in_progress": in_progress_dumps,
                "total_size_bytes": total_dump_size,
                "total_size_gb": round(total_dump_size / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Error collecting dump metrics: {e}")
            dump_metrics = {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "total_size_bytes": 0,
                "total_size_gb": 0,
                "error": str(e)
            }
        
        # Forensic analysis statistics
        try:
            all_analyses = integrated_forensic_service.get_all_analyses()
            completed_analyses = len([a for a in all_analyses if a.status.value == "completed"])
            failed_analyses = len([a for a in all_analyses if a.status.value == "failed"])
            in_progress_analyses = len([a for a in all_analyses if a.status.value in ["analyzing", "generating_report", "dumping_memory"]])
            
            forensic_metrics = {
                "total": len(all_analyses),
                "completed": completed_analyses,
                "failed": failed_analyses,
                "in_progress": in_progress_analyses
            }
            
        except Exception as e:
            logger.error(f"Error collecting forensic metrics: {e}")
            forensic_metrics = {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "error": str(e)
            }
        
        # OpenStack instances (if available)
        try:
            instances = await openstack_client.get_instances()
            instance_metrics = {
                "total": len(instances),
                "active": len([i for i in instances if i.status == "ACTIVE"]),
                "stopped": len([i for i in instances if i.status in ["SHUTOFF", "STOPPED"]])
            }
        except Exception as e:
            logger.warning(f"Could not get OpenStack instances: {e}")
            instance_metrics = {
                "total": 0,
                "active": 0,
                "stopped": 0,
                "error": "OpenStack not available"
            }
        
        # Disk space specific to application directories
        app_disk_usage = {}
        try:
            # Check forensic reports directory
            forensic_dir = "/home/stack/forensic"
            if os.path.exists(forensic_dir):
                forensic_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(forensic_dir)
                    for filename in filenames
                )
                app_disk_usage["forensic_reports"] = {
                    "size_bytes": forensic_size,
                    "size_mb": round(forensic_size / (1024**2), 2)
                }
        except Exception as e:
            logger.warning(f"Could not calculate forensic directory size: {e}")
        
        response = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": {
                    "percent": round(cpu_percent, 2),
                    "cores": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": round(memory.percent, 2),
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": round((disk.used / disk.total) * 100, 2)
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "total_gb": round((net_io.bytes_sent + net_io.bytes_recv) / (1024**3), 2)
                }
            },
            "application": {
                "dumps": dump_metrics,
                "forensic_analyses": forensic_metrics,
                "instances": instance_metrics,
                "disk_usage": app_disk_usage
            }
        }
        
        logger.info("Metrics collected successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error getting comprehensive metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/system")
async def get_system_metrics():
    """Get current system metrics only"""
    try:
        # Ottieni solo i valori attuali del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        # Restituisci solo i dati attuali
        current_data = {
            "timestamp": datetime.now().isoformat(),
            "cpu": round(cpu_percent, 2),
            "memory": round(memory.percent, 2),
            "disk": round((disk.used / disk.total) * 100, 2),
            "network": round((net_io.bytes_sent + net_io.bytes_recv) / (1024**3), 2)  # GB
        }
        
        return current_data
        
    except Exception as e:
        print(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}")
async def get_instance_metrics(
    instance_id: str,
    hours: int = Query(24, description="Hours of historical data")
):
    """Get metrics for specific instance"""
    try:
        # Generate sample instance metrics
        now = datetime.now()
        metrics = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            metrics.append({
                "timestamp": timestamp,
                "cpu_usage": 40.0 + (i % 35),
                "memory_usage": 55.0 + (i % 30),
                "network_rx": 20.0 + (i % 25),
                "network_tx": 15.0 + (i % 20)
            })
        
        return {
            "instance_id": instance_id,
            "metrics": metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}")
async def get_service_metrics(
    service_name: str,
    hours: int = Query(24, description="Hours of historical data")
):
    """Get metrics for specific service"""
    try:
        # Generate sample service metrics
        now = datetime.now()
        metrics = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            metrics.append({
                "timestamp": timestamp,
                "response_time": 45.0 + (i % 50),
                "requests_per_second": 100.0 + (i % 80),
                "error_rate": max(0, 2.0 + (i % 5) - 3)
            })
        
        return {
            "service_name": service_name,
            "metrics": metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_metrics_summary():
    """Get current metrics summary with error handling"""
    try:
        logger.info("Getting metrics summary...")
        
        # Ottieni solo i valori attuali del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Dati OpenStack con gestione errori
        running_instances = 0
        total_instances = 0
        active_services = 0
        total_services = 0
        
        try:
            instances = await openstack_client.get_instances()
            running_instances = len([i for i in instances if i.status == 'ACTIVE'])
            total_instances = len(instances)
            logger.info(f"OpenStack instances: {running_instances}/{total_instances}")
        except Exception as e:
            logger.warning(f"Could not get OpenStack instances: {e}")
        
        try:
            services = await openstack_client.get_services()
            active_services = len([s for s in services if s.status == 'enabled'])
            total_services = len(services)
            logger.info(f"OpenStack services: {active_services}/{total_services}")
        except Exception as e:
            logger.warning(f"Could not get OpenStack services: {e}")
        
        # Calcola i dettagli della memoria
        memory_total_gb = round(memory.total / (1024**3), 2)
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_available_gb = round(memory.available / (1024**3), 2)
        
        # Dati applicazione
        try:
            all_dumps = memory_dump_service.get_all_dumps()
            completed_dumps = len([d for d in all_dumps if d.status.value == "completed"])
            active_services += completed_dumps
            total_services += len(all_dumps)
        except Exception as e:
            logger.warning(f"Could not get dump data: {e}")
        
        try:
            all_analyses = integrated_forensic_service.get_all_analyses()
            completed_analyses = len([a for a in all_analyses if a.status.value == "completed"])
            active_services += completed_analyses
            total_services += len(all_analyses)
        except Exception as e:
            logger.warning(f"Could not get forensic data: {e}")
        
        # Restituisci solo i dati attuali
        summary = {
            "cpu": {
                "current": round(cpu_percent, 1),
                "unit": "%"
            },
            "memory": {
                "current": round(memory.percent, 1),
                "unit": "%",
                "total_gb": memory_total_gb,
                "used_gb": memory_used_gb,
                "available_gb": memory_available_gb
            },
            "disk": {
                "current": round((disk.used / disk.total) * 100, 1),
                "unit": "%"
            },
            "instances": {
                "running": running_instances,
                "total": total_instances
            },
            "services": {
                "active": active_services,
                "total": total_services
            }
        }
        
        logger.info("Metrics summary collected successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")