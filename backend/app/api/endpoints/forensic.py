"""
Integrated Forensic Analysis API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...services.integrated_forensic import integrated_forensic_service, AnalysisStatus

router = APIRouter()


class ForensicAnalysisRequest(BaseModel):
    """Request to start forensic analysis"""
    instance_id: str
    instance_name: str


class ForensicAnalysisFromDumpRequest(BaseModel):
    """Request to start forensic analysis from existing dump"""
    dump_id: str
    instance_id: str
    instance_name: str


class ForensicAnalysisResponse(BaseModel):
    """Response for forensic analysis request"""
    analysis_id: str
    message: str


class ForensicAnalysisStatus(BaseModel):
    """Forensic analysis status response"""
    id: str
    status: str
    progress: int
    current_step: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]


class ForensicAnalysisResults(BaseModel):
    """Forensic analysis results"""
    id: str
    instance_id: str
    instance_name: str
    status: str
    dump_info: Dict[str, Any]
    summary: Dict[str, Any]
    report_available: bool


@router.post("/start", response_model=ForensicAnalysisResponse)
async def start_forensic_analysis(request: ForensicAnalysisRequest):
    """Start complete forensic analysis pipeline"""
    try:
        analysis_id = await integrated_forensic_service.start_analysis(
            instance_id=request.instance_id,
            instance_name=request.instance_name
        )
        
        return ForensicAnalysisResponse(
            analysis_id=analysis_id,
            message=f"Forensic analysis started for instance {request.instance_name}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start forensic analysis: {str(e)}")


@router.post("/start-from-dump", response_model=ForensicAnalysisResponse)
async def start_forensic_analysis_from_dump(request: ForensicAnalysisFromDumpRequest):
    """Start forensic analysis from existing memory dump"""
    try:
        analysis_id = await integrated_forensic_service.start_analysis_from_dump(
            dump_id=request.dump_id,
            instance_id=request.instance_id,
            instance_name=request.instance_name
        )
        
        return ForensicAnalysisResponse(
            analysis_id=analysis_id,
            message=f"Forensic analysis started from existing dump for instance {request.instance_name}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start forensic analysis from dump: {str(e)}")


@router.get("/status/{analysis_id}", response_model=ForensicAnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """Get forensic analysis status and progress"""
    try:
        status = integrated_forensic_service.get_analysis_status(analysis_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return ForensicAnalysisStatus(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis status: {str(e)}")


@router.get("/results/{analysis_id}", response_model=ForensicAnalysisResults)
async def get_analysis_results(analysis_id: str):
    """Get forensic analysis results"""
    try:
        analysis = integrated_forensic_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.status != AnalysisStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Analysis not completed yet")
        
        return ForensicAnalysisResults(
            id=analysis.id,
            instance_id=analysis.instance_id,
            instance_name=analysis.instance_name,
            status=analysis.status.value,
            dump_info=analysis.results.dump_info,
            summary=analysis.results.summary,
            report_available=analysis.report_path is not None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis results: {str(e)}")


@router.get("/report/{analysis_id}")
async def download_report(analysis_id: str):
    """Download PDF forensic report"""
    try:
        report_path = integrated_forensic_service.get_report_path(analysis_id)
        
        if not report_path:
            raise HTTPException(status_code=404, detail="Report not found or not available")
        
        return FileResponse(
            path=report_path,
            media_type="application/pdf",
            filename=f"forensic_report_{analysis_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")


@router.get("", response_model=List[ForensicAnalysisStatus])
async def get_all_analyses():
    """Get all forensic analyses"""
    try:
        analyses = integrated_forensic_service.get_all_analyses()
        
        return [
            ForensicAnalysisStatus(
                id=analysis.id,
                status=analysis.status.value,
                progress=analysis.progress,
                current_step=analysis.current_step,
                created_at=analysis.created_at.isoformat(),
                started_at=analysis.started_at.isoformat() if analysis.started_at else None,
                completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
                error_message=analysis.error_message
            )
            for analysis in analyses
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyses: {str(e)}")


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete forensic analysis"""
    try:
        analysis = integrated_forensic_service.get_analysis(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Stop active analysis if running
        if analysis_id in integrated_forensic_service.active_analyses:
            task = integrated_forensic_service.active_analyses[analysis_id]
            task.cancel()
            del integrated_forensic_service.active_analyses[analysis_id]
        
        # Remove from database
        del integrated_forensic_service.analyses_db[analysis_id]
        
        return {"message": f"Analysis {analysis_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")
