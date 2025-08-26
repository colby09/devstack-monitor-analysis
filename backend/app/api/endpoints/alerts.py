"""
Alerts API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

router = APIRouter()


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class Alert(BaseModel):
    """Alert model"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@router.get("/", response_model=List[Alert])
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of alerts")
):
    """Get alerts with optional filtering"""
    try:
        # Sample alerts data
        sample_alerts = [
            Alert(
                id="1",
                title="High CPU Usage",
                message="Instance cirros-test-1 CPU usage is above 80%",
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                source="instance:cirros-test-1",
                created_at=datetime.now()
            ),
            Alert(
                id="2",
                title="Service Down",
                message="Swift object storage service is not responding",
                severity=AlertSeverity.CRITICAL,
                status=AlertStatus.ACTIVE,
                source="service:swift",
                created_at=datetime.now()
            ),
            Alert(
                id="3",
                title="New Instance Created",
                message="Instance ubuntu-server-1 has been created successfully",
                severity=AlertSeverity.INFO,
                status=AlertStatus.RESOLVED,
                source="instance:ubuntu-server-1",
                created_at=datetime.now()
            )
        ]
        
        alerts = sample_alerts
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return alerts[:limit]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    """Get specific alert details"""
    try:
        # Sample alert lookup
        if alert_id == "1":
            return Alert(
                id="1",
                title="High CPU Usage",
                message="Instance cirros-test-1 CPU usage is above 80%",
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                source="instance:cirros-test-1",
                created_at=datetime.now()
            )
        
        raise HTTPException(status_code=404, detail="Alert not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_at": datetime.now()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_at": datetime.now()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_alerts_summary():
    """Get alerts summary statistics"""
    try:
        return {
            "total": 15,
            "active": 3,
            "critical": 1,
            "warning": 2,
            "info": 0,
            "resolved_today": 5
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))