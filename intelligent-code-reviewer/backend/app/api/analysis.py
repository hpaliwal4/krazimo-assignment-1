"""
Code Analysis API endpoints.

This module provides REST API endpoints for submitting code analysis jobs
and retrieving results using the integrated RAG + AI Agent pipeline.
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from ..models.api import AnalyzeURLRequest, AnalyzeZipRequest, AnalysisResponse
from ..db.database import get_db_service, DatabaseService
from ..services.agent_integration import AgentIntegrationService
import tempfile
import shutil
from pathlib import Path
import uuid


router = APIRouter()
logger = logging.getLogger(__name__)

# Global agent integration service instance
agent_service = AgentIntegrationService()


async def run_analysis_job(
    task_id: str,
    source_type: str,
    source_location: str,
    db_service: DatabaseService,
    analysis_requirements: list = None
):
    """Background task to run the analysis job."""
    try:
        logger.info(f"Starting background analysis job {task_id}")
        
        # Run the integrated analysis
        result = await agent_service.process_analysis_job(
            task_id=task_id,
            source_type=source_type,
            source_location=source_location,
            db_service=db_service,
            analysis_requirements=analysis_requirements
        )
        
        logger.info(f"Analysis job {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Background analysis job {task_id} failed: {e}")
        # Error handling is done in the agent service


@router.post("/analyze/url", response_model=AnalysisResponse)
async def analyze_git_repository(
    request: AnalyzeURLRequest,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_db_service)
) -> AnalysisResponse:
    """
    Analyze a Git repository from URL.
    
    This endpoint starts an asynchronous analysis job that:
    1. Clones the repository using the RAG pipeline
    2. Processes and indexes the code
    3. Runs intelligent analysis using the AI agent
    4. Generates a comprehensive report
    """
    try:
        # Generate unique task ID
        task_id = f"git_{uuid.uuid4().hex[:8]}"
        
        # Create initial job record
        await db_service.create_job(
            task_id=task_id,
            source_type="git_url",
            source_location=request.git_url,
            status="pending",
            metadata={
                "git_url": request.git_url,
                "branch": getattr(request, 'branch', 'main'),
                "analysis_requirements": getattr(request, 'analysis_requirements', []),
                "created_at": "now"
            }
        )
        
        # Start background analysis
        background_tasks.add_task(
            run_analysis_job,
            task_id=task_id,
            source_type="url",
            source_location=request.git_url,
            db_service=db_service,
            analysis_requirements=getattr(request, 'analysis_requirements', None)
        )
        
        logger.info(f"Started analysis job {task_id} for URL: {request.git_url}")
        
        return AnalysisResponse(
            task_id=task_id,
            status="started",
            message="Analysis job started. Use the task_id to check progress and get results.",
            estimated_completion_time="5-10 minutes"
        )
        
    except Exception as e:
        logger.error(f"Failed to start Git repository analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.post("/analyze/zip", response_model=AnalysisResponse)
async def analyze_zip_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db_service: DatabaseService = Depends(get_db_service)
) -> AnalysisResponse:
    """
    Analyze a ZIP file containing source code.
    
    This endpoint:
    1. Receives and validates the ZIP file
    2. Extracts and processes the code using the RAG pipeline
    3. Runs intelligent analysis using the AI agent
    4. Generates a comprehensive report
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="Only ZIP files are supported"
            )
        
        # Generate unique task ID
        task_id = f"zip_{uuid.uuid4().hex[:8]}"
        
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp(prefix=f"upload_{task_id}_")
        temp_file_path = Path(temp_dir) / file.filename
        
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()
        
        # Create initial job record
        await db_service.create_job(
            task_id=task_id,
            source_type="zip_file",
            source_location=str(temp_file_path),
            status="pending",
            metadata={
                "original_filename": file.filename,
                "file_size": temp_file_path.stat().st_size,
                "temp_path": str(temp_file_path),
                "created_at": "now"
            }
        )
        
        # Start background analysis
        background_tasks.add_task(
            run_analysis_job,
            task_id=task_id,
            source_type="zip",
            source_location=str(temp_file_path),
            db_service=db_service,
            analysis_requirements=None
        )
        
        logger.info(f"Started analysis job {task_id} for ZIP file: {file.filename}")
        
        return AnalysisResponse(
            task_id=task_id,
            status="started",
            message="ZIP file analysis job started. Use the task_id to check progress and get results.",
            estimated_completion_time="3-8 minutes"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start ZIP file analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/report/{task_id}")
async def get_analysis_report(
    task_id: str,
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """
    Get analysis report by task ID.
    
    Returns the current status and results of an analysis job.
    If the job is complete, returns the full analysis report.
    If in progress, returns current status and progress information.
    """
    try:
        # Get report from agent service
        report = await agent_service.get_analysis_report(task_id, db_service)
        
        if report is None:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis job {task_id} not found"
            )
        
        logger.info(f"Retrieved report for task {task_id}, status: {report.get('status', 'unknown')}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report for task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_analysis_status(
    task_id: str,
    db_service: DatabaseService = Depends(get_db_service)
) -> Dict[str, Any]:
    """
    Get quick status check for an analysis job.
    
    Returns just the status and progress information without the full report.
    """
    try:
        # Get job from database
        job = await db_service.get_job(task_id)
        
        if job is None:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis job {task_id} not found"
            )
        
        response = {
            "task_id": task_id,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }
        
        # Add progress information if available
        if job.metadata:
            if isinstance(job.metadata, dict):
                response["progress"] = job.metadata
            else:
                try:
                    import json
                    response["progress"] = json.loads(job.metadata)
                except:
                    response["progress"] = {"raw": job.metadata}
        
        # Add status-specific information
        if job.status == "completed":
            response["message"] = "Analysis completed successfully. Use /report/{task_id} to get full results."
        elif job.status == "failed":
            response["message"] = "Analysis failed. Check progress details for error information."
        elif job.status == "in_progress":
            stage = response.get("progress", {}).get("stage", "unknown")
            response["message"] = f"Analysis in progress - {stage}"
        else:
            response["message"] = f"Job status: {job.status}"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the analysis service."""
    try:
        # Quick health check of components
        # This could be expanded to check database, vector store, etc.
        return {
            "status": "healthy",
            "agent_service": "initialized",
            "timestamp": "now"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        ) 