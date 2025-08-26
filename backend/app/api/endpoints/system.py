"""
System information endpoint
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.openstack import OpenStackClient

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/info", response_model=Dict[str, Any])
async def get_system_info():
    """Get DevStack system information including uptime"""
    try:
        client = OpenStackClient()
        system_info = await client.get_system_info()
        return system_info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/uptime")
async def get_system_uptime():
    """Get DevStack system uptime"""
    try:
        client = OpenStackClient()
        uptime_info = await client.get_system_uptime()
        return uptime_info
    except Exception as e:
        logger.error(f"Error getting system uptime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connection/test")
async def test_openstack_connection():
    """Test OpenStack connection and return connection details"""
    try:
        client = OpenStackClient()
        
        # Test connection
        connection_result = await client.test_connection()
        
        # Get basic info about the OpenStack environment
        info = {
            "status": "connected" if connection_result["connected"] else "disconnected",
            "auth_url": connection_result.get("auth_url", "Unknown"),
            "project_name": connection_result.get("project_name", "Unknown"),
            "user_domain": connection_result.get("user_domain", "Unknown"),
            "project_domain": connection_result.get("project_domain", "Unknown"),
            "username": connection_result.get("username", "Unknown"),
            "region": connection_result.get("region", "Unknown"),
            "identity_api_version": connection_result.get("identity_api_version", "Unknown"),
            "compute_api_version": connection_result.get("compute_api_version", "Unknown"),
            "image_api_version": connection_result.get("image_api_version", "Unknown"),
            "network_api_version": connection_result.get("network_api_version", "Unknown"),
            "last_tested": connection_result.get("last_tested"),
            "error": connection_result.get("error")
        }
        
        if connection_result["connected"]:
            logger.info("OpenStack connection test successful")
            return {"success": True, "connection": info}
        else:
            logger.warning(f"OpenStack connection test failed: {connection_result.get('error')}")
            return {"success": False, "connection": info}
            
    except Exception as e:
        logger.error(f"Error testing OpenStack connection: {e}")
        return {"success": False, "error": str(e)}
