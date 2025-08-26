"""
Memory dump API endpoints for digital forensics
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...models.dump import DumpRequest, DumpResponse, MemoryDump, DumpStatus
from ...services.memory_dump import memory_dump_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[MemoryDump])
async def get_all_dumps():
    """Get all memory dumps"""
    try:
        dumps = memory_dump_service.get_all_dumps()
        return dumps
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dumps: {str(e)}")


class DumpStats(BaseModel):
    """Dump statistics"""
    total_dumps: int
    completed_dumps: int
    failed_dumps: int
    in_progress_dumps: int
    total_size_gb: float


@router.get("/stats", response_model=DumpStats)
async def get_dump_stats():
    """Get memory dump statistics"""
    try:
        logger.info("Getting dump statistics...")
        dumps = memory_dump_service.get_all_dumps()
        logger.info(f"Found {len(dumps)} dumps")
        
        if not dumps:
            logger.info("No dumps found, returning empty stats")
            return DumpStats(
                total_dumps=0,
                completed_dumps=0,
                failed_dumps=0,
                in_progress_dumps=0,
                total_size_gb=0.0
            )
        
        # Debug dump statuses
        for i, dump in enumerate(dumps):
            logger.info(f"Dump {i}: status={dump.status}, type={type(dump.status)}")
        
        total_dumps = len(dumps)
        completed_dumps = len([d for d in dumps if d.status == DumpStatus.COMPLETED])
        failed_dumps = len([d for d in dumps if d.status == DumpStatus.FAILED])
        in_progress_dumps = len([d for d in dumps if d.status == DumpStatus.IN_PROGRESS])
        
        logger.info(f"Stats: total={total_dumps}, completed={completed_dumps}, failed={failed_dumps}, in_progress={in_progress_dumps}")
        
        total_size_bytes = sum([d.file_size or 0 for d in dumps if d.file_size])
        total_size_gb = round(total_size_bytes / (1024**3), 2)
        
        logger.info(f"Total size: {total_size_bytes} bytes = {total_size_gb} GB")
        
        result = DumpStats(
            total_dumps=total_dumps,
            completed_dumps=completed_dumps,
            failed_dumps=failed_dumps,
            in_progress_dumps=in_progress_dumps,
            total_size_gb=total_size_gb
        )
        
        logger.info(f"Returning stats: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting dump stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get dump statistics: {str(e)}")


@router.get("/{dump_id}", response_model=MemoryDump)
async def get_dump(dump_id: str):
    """Get specific memory dump"""
    try:
        dump = memory_dump_service.get_dump(dump_id)
        if not dump:
            raise HTTPException(status_code=404, detail="Dump not found")
        return dump
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dump: {str(e)}")


@router.get("/{dump_id}/download")
async def download_dump(dump_id: str):
    """Download memory dump file"""
    try:
        file_path = memory_dump_service.get_dump_file_path(dump_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Dump file not found or not ready")
        
        dump = memory_dump_service.get_dump(dump_id)
        filename = f"{dump.instance_name}_{dump_id}.dump"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download dump: {str(e)}")


@router.delete("/{dump_id}")
async def delete_dump(dump_id: str):
    """Delete memory dump and file"""
    try:
        dump = memory_dump_service.get_dump(dump_id)
        if not dump:
            raise HTTPException(status_code=404, detail="Dump not found")
        
        # Delete file if exists
        import os
        if os.path.exists(dump.file_path):
            os.remove(dump.file_path)
        
        # Remove from database
        del memory_dump_service.dumps_db[dump_id]
        
        return {"message": f"Dump {dump_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dump: {str(e)}")
