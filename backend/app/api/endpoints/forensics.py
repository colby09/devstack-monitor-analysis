"""
Forensic analysis API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional

from ...models.forensic import ForensicAnalysis, AnalysisRequest, AnalysisType
from ...services.forensic_analysis import forensic_service
from ...services.memory_dump import memory_dump_service

router = APIRouter()


@router.post("/analyze", response_model=dict)
async def start_forensic_analysis(request: AnalysisRequest):
    """Start forensic analysis of a memory dump"""
    
    # Get the dump
    dump = memory_dump_service.get_dump(request.dump_id)
    if not dump:
        raise HTTPException(status_code=404, detail="Memory dump not found")
    
    # Check if dump is completed
    if dump.status.value != "completed":
        raise HTTPException(status_code=400, detail="Memory dump must be completed before analysis")
    
    # Start analysis
    try:
        analysis_id = await forensic_service.start_analysis(request, dump)
        return {
            "analysis_id": analysis_id,
            "message": "Forensic analysis started",
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@router.get("/analysis/{analysis_id}", response_model=ForensicAnalysis)
async def get_analysis(analysis_id: str):
    """Get forensic analysis by ID"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis


@router.get("/analysis/{analysis_id}/status", response_model=dict)
async def get_analysis_status(analysis_id: str):
    """Get analysis status and progress"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "analysis_id": analysis_id,
        "status": analysis.status,
        "progress": analysis.progress,
        "current_step": analysis.current_step,
        "error_message": analysis.error_message
    }


@router.get("/dump/{dump_id}/analyses", response_model=List[dict])
async def get_dump_analyses(dump_id: str):
    """Get all analyses for a specific dump"""
    
    analyses = forensic_service.get_analyses_for_dump(dump_id)
    return [analysis.model_dump() for analysis in analyses]


@router.get("/analyses", response_model=List[dict])
async def get_all_analyses():
    """Get all forensic analyses"""
    
    analyses = forensic_service.get_all_analyses()
    return [analysis.model_dump() for analysis in analyses]


@router.get("/analysis/{analysis_id}/results/processes", response_model=List)
async def get_analysis_processes(analysis_id: str):
    """Get process analysis results"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.results:
        raise HTTPException(status_code=400, detail="Analysis not completed or no results available")
    
    return [process.model_dump() for process in analysis.results.processes] if analysis.results.processes else []


@router.get("/analysis/{analysis_id}/results/network", response_model=List)
async def get_analysis_network(analysis_id: str):
    """Get network analysis results"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.results:
        raise HTTPException(status_code=400, detail="Analysis not completed or no results available")
    
    return [conn.model_dump() for conn in analysis.results.network] if analysis.results.network else []


@router.get("/analysis/{analysis_id}/results/files", response_model=List)
async def get_analysis_files(analysis_id: str):
    """Get file analysis results"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.results:
        raise HTTPException(status_code=400, detail="Analysis not completed or no results available")
    
    return [file.model_dump() for file in analysis.results.files] if analysis.results.files else []


@router.get("/analysis/{analysis_id}/results/modules", response_model=List)
async def get_analysis_modules(analysis_id: str):
    """Get module analysis results"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.results:
        raise HTTPException(status_code=400, detail="Analysis not completed or no results available")
    
    return [module.model_dump() for module in analysis.results.modules] if analysis.results.modules else []


@router.get("/analysis/{analysis_id}/results/system", response_model=dict)
async def get_analysis_system_info(analysis_id: str):
    """Get system info analysis results"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.results:
        raise HTTPException(status_code=400, detail="Analysis not completed or no results available")
    
    return analysis.results.system_info.model_dump() if analysis.results.system_info else {}


@router.get("/analysis/{analysis_id}/results/history", response_model=List[str])
async def get_analysis_bash_history(analysis_id: str):
    """Get bash history analysis results"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if not analysis.results:
        raise HTTPException(status_code=400, detail="Analysis not completed or no results available")
    
    return analysis.results.bash_history


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete a forensic analysis"""
    
    analysis = forensic_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Remove from service
    if analysis_id in forensic_service.analyses_db:
        del forensic_service.analyses_db[analysis_id]
    
    # Cancel if still running
    if analysis_id in forensic_service.active_analyses:
        task = forensic_service.active_analyses[analysis_id]
        task.cancel()
        del forensic_service.active_analyses[analysis_id]
    
    return {"message": "Analysis deleted successfully"}
