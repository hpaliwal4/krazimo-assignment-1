from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
import uuid

from ..models.api_models import (
    AnalyzeUrlRequest,
    AnalyzeResponse,
    ReportResponse,
    JobStatus,
    ErrorResponse,
)
from ..db.session import get_db
from ..services.database import DatabaseService
from . import analyze
from . import admin

router = APIRouter(prefix="/api")

router.include_router(analyze.router)
router.include_router(admin.router)


@router.post("/analyze/url", response_model=AnalyzeResponse)
async def analyze_repository_url(request: AnalyzeUrlRequest, db: Session = Depends(get_db)):
    """
    Analyze a Git repository by URL.
    
    This endpoint accepts a Git repository URL and creates a new analysis task.
    Returns a task_id that can be used to check the status and retrieve results.
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create job in database
        DatabaseService.create_analysis_job(
            db=db,
            task_id=task_id,
            input_source_type="git_url",
            input_source_path=str(request.git_url)
        )
        
        return AnalyzeResponse(
            task_id=task_id,
            message=f"Analysis task created successfully. Repository: {request.git_url}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis task: {str(e)}")


@router.post("/analyze/zip", response_model=AnalyzeResponse)
async def analyze_zip_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Analyze a codebase from an uploaded ZIP file.
    
    This endpoint accepts a ZIP file upload and creates a new analysis task.
    Returns a task_id that can be used to check the status and retrieve results.
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create job in database
        DatabaseService.create_analysis_job(
            db=db,
            task_id=task_id,
            input_source_type="zip_upload",
            input_source_path=file.filename
        )
        
        return AnalyzeResponse(
            task_id=task_id,
            message=f"Analysis task created successfully. File: {file.filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis task: {str(e)}")


@router.get("/report/{task_id}", response_model=ReportResponse)
async def get_analysis_report(task_id: str, db: Session = Depends(get_db)):
    """
    Get the status and results of an analysis task.
    
    This endpoint returns the current status of the analysis job.
    When the job is complete, it also returns the full analysis report.
    """
    try:
        # Get job from database
        job = DatabaseService.get_analysis_job(db, task_id)
        if not job:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Create job status object
        job_status = JobStatus(
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        
        # Create response
        response = ReportResponse(
            task_id=task_id,
            job_status=job_status
        )
        
        # If job is complete, include the actual report
        if job_status.status == "COMPLETE":
            final_report = DatabaseService.get_final_report(db, task_id)
            if final_report:
                response.report_content = final_report.report_content
            else:
                # Fallback if no report found but job is marked complete
                response.report_content = {
                    "summary": "Analysis complete",
                    "findings": [],
                    "recommendations": []
                }
        
        # If job failed, include error message
        if job_status.status == "FAILED" and job.error_message:
            response.error_message = job.error_message
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}") 