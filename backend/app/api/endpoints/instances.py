"""
Instances API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.openstack import OpenStackClient
from app.models.instance import Instance, InstanceStatus
from app.models.dump import DumpRequest, DumpRequestBody, DumpResponse
from app.services.memory_dump import memory_dump_service
from app.services.multi_tool_forensics import create_multi_tool_analysis

router = APIRouter()


class InstanceResponse(BaseModel):
    """Instance response model"""
    id: str
    name: str
    status: InstanceStatus
    flavor: str
    image: str
    ip_address: Optional[str]
    uptime: str
    cpu_usage: float
    memory_usage: float
    created_at: str


@router.get("", response_model=List[InstanceResponse])
async def get_instances(
    status: Optional[InstanceStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or image")
):
    """Get all instances with optional filtering"""
    try:
        openstack_client = OpenStackClient()
        instances = await openstack_client.get_instances()
        
        # Don't show instances if no real OpenStack connection
        if not openstack_client.connection:
            return []
        
        # Apply filters
        if status:
            instances = [i for i in instances if i.status == status]
        
        if search:
            search_lower = search.lower()
            instances = [
                i for i in instances 
                if search_lower in i.name.lower() or search_lower in i.image.lower()
            ]
        
        return instances
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(instance_id: str):
    """Get specific instance details"""
    try:
        openstack_client = OpenStackClient()
        instance = await openstack_client.get_instance(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        return instance
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/health-check")
async def check_instance_health(instance_id: str):
    """Force health check for specific instance"""
    try:
        openstack_client = OpenStackClient()
        health_status = await openstack_client.check_instance_health(instance_id)
        
        return {
            "instance_id": instance_id,
            "health_status": health_status,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/metrics")
async def get_instance_metrics(instance_id: str):
    """Get instance performance metrics"""
    try:
        openstack_client = OpenStackClient()
        metrics = await openstack_client.get_instance_metrics(instance_id)
        
        return metrics
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/dump", response_model=DumpResponse)
async def create_memory_dump(instance_id: str, request_body: DumpRequestBody):
    """Create a memory dump for a specific instance"""
    try:
        # Get instance data from OpenStack
        openstack_client = OpenStackClient()
        instances = await openstack_client.get_instances()
        instance_data = None
        
        for instance in instances:
            if instance.id == instance_id:
                # Convert OpenStack objects to dictionaries properly
                addresses_dict = {}
                if hasattr(instance, 'addresses') and instance.addresses:
                    addresses_dict = dict(instance.addresses)
                
                image_dict = {}
                if hasattr(instance, 'image') and instance.image:
                    if isinstance(instance.image, dict):
                        image_dict = instance.image
                    else:
                        image_dict = {'id': str(instance.image)}
                
                flavor_dict = {}
                if hasattr(instance, 'flavor') and instance.flavor:
                    if isinstance(instance.flavor, dict):
                        flavor_dict = instance.flavor
                    else:
                        flavor_dict = {'id': str(instance.flavor)}
                
                instance_data = {
                    'id': instance.id,
                    'name': instance.name,
                    'status': instance.status,
                    'ip_address': instance.ip_address,  # Use the IP from the instance directly
                    'addresses': addresses_dict,
                    'image': image_dict,
                    'flavor': flavor_dict
                }
                break
        
        if not instance_data:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Create full request with instance_id from URL
        request = DumpRequest(
            instance_id=instance_id,
            dump_type=request_body.dump_type,
            ssh_key_path=request_body.ssh_key_path,
            ssh_user=request_body.ssh_user
        )
        
        # Create the dump
        dump_id = await memory_dump_service.create_dump(request, instance_data)
        
        return DumpResponse(
            dump_id=dump_id,
            message=f"Memory dump initiated for instance {instance_id}",
            status="pending"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/forensic-analysis")
async def create_forensic_analysis(
    instance_id: str,
    tools: Optional[List[str]] = Query(None, description="Specific tools to use (binwalk, foremost, bulk_extractor, yara, strings, hexdump)")
):
    """
    Create comprehensive forensic analysis using multiple tools
    
    This endpoint:
    1. Creates a memory dump of the specified instance
    2. Runs multiple forensic analysis tools on the dump
    3. Returns comprehensive analysis results including:
       - File carving and recovery (foremost)
       - Firmware analysis (binwalk) 
       - Data extraction (bulk_extractor)
       - Pattern matching (yara)
       - String analysis
       - Hex pattern analysis
    """
    try:
        # Get instance name from OpenStack
        openstack_client = OpenStackClient()
        instances = await openstack_client.get_instances()
        
        instance_name = None
        for instance in instances:
            if instance.id == instance_id:
                instance_name = instance.name
                break
                
        if not instance_name:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Run multi-tool forensic analysis
        analysis_results = await create_multi_tool_analysis(instance_name, tools)
        
        if 'error' in analysis_results:
            raise HTTPException(status_code=500, detail=analysis_results['error'])
            
        return {
            "analysis_id": analysis_results['multi_tool_analysis']['analysis_directory'].split('/')[-1],
            "instance_id": instance_id,
            "instance_name": instance_name,
            "message": "Multi-tool forensic analysis completed successfully",
            "results": analysis_results,
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory dump: {str(e)}")