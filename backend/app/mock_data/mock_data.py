import asyncio
from datetime import datetime
from app.models.instance import Instance, InstanceStatus
from app.models.service import Service, ServiceStatus

async def get_mock_instances():
    """Return empty list when no OpenStack connection - don't show mock data in instances page"""
    await asyncio.sleep(0.1)
    return []

async def get_mock_services():
    """Return connection error service when no OpenStack connection"""
    await asyncio.sleep(0.1)
    return [
        Service(
            name="openstack-connection",
            status=ServiceStatus.CRITICAL,
            description="OpenStack Connection Failed - DevStack not running on localhost:5000",
            port=5000,
            uptime="0h 0m",
            response_time=0.0,
            last_check=datetime.now().isoformat()
        )
    ]
