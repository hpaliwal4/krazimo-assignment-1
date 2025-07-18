"""
Admin API endpoints for monitoring and debugging analysis jobs.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..services.progress_tracker import get_all_active_jobs, ProgressTracker
from ..db.session import get_session
from ..models.analysis import AnalysisJob, AnalysisStep

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/jobs/active")
async def get_active_jobs() -> List[Dict[str, Any]]:
    """Get all currently active analysis jobs."""
    return get_all_active_jobs()


@router.get("/jobs/all")
async def get_all_jobs(
    limit: int = Query(50, description="Number of jobs to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    hours: Optional[int] = Query(None, description="Jobs from last N hours")
) -> List[Dict[str, Any]]:
    """Get all analysis jobs with optional filtering."""
    try:
        with get_session() as db:
            query = db.query(AnalysisJob)
            
            # Filter by status if provided
            if status:
                query = query.filter(AnalysisJob.status == status)
            
            # Filter by time if provided
            if hours:
                since = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(AnalysisJob.created_at >= since)
            
            # Order by most recent first
            jobs = query.order_by(AnalysisJob.created_at.desc()).limit(limit).all()
            
            return [{
                "task_id": job.task_id,
                "status": job.status,
                "progress": job.progress_percentage,
                "current_step": job.current_step,
                "source_type": job.input_source_type,
                "source": job.input_source_path,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "updated_at": job.updated_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "duration": job.get_duration(),
                "files_progress": f"{job.processed_files}/{job.total_files}",
                "tools_progress": f"{job.completed_tools}/{job.total_tools}",
                "error": job.error_message,
                "warnings_count": len(job.warnings) if job.warnings else 0,
            } for job in jobs]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")


@router.get("/jobs/{task_id}/details")
async def get_job_details(task_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific analysis job."""
    try:
        tracker = ProgressTracker(task_id)
        
        # Get current status
        status = tracker.get_current_status()
        
        # Get step history
        steps = tracker.get_step_history()
        
        # Get job metadata
        with get_session() as db:
            job = db.query(AnalysisJob).filter(AnalysisJob.task_id == task_id).first()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return {
                "job_info": {
                    "task_id": job.task_id,
                    "status": job.status,
                    "source_type": job.input_source_type,
                    "source_identifier": job.input_source_path,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "updated_at": job.updated_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error_message": job.error_message,
                    "error_details": job.error_details,
                    "warnings": job.warnings,
                    "metadata": job.analysis_metadata,
                },
                "progress": status,
                "steps": steps,
                "summary": {
                    "total_steps": len(steps),
                    "completed_steps": len([s for s in steps if s["status"] == "completed"]),
                    "failed_steps": len([s for s in steps if s["status"] == "failed"]),
                    "running_steps": len([s for s in steps if s["status"] == "running"]),
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job details: {str(e)}")


@router.get("/jobs/{task_id}/logs")
async def get_job_logs(task_id: str) -> List[Dict[str, Any]]:
    """Get detailed logs for a specific analysis job."""
    try:
        with get_session() as db:
            steps = db.query(AnalysisStep).filter(
                AnalysisStep.task_id == task_id
            ).order_by(AnalysisStep.started_at).all()
            
            logs = []
            for step in steps:
                log_entry = {
                    "timestamp": step.started_at.isoformat() if step.started_at else None,
                    "type": "step_start",
                    "message": f"Started {step.step_type}: {step.step_name}",
                    "level": "info"
                }
                logs.append(log_entry)
                
                if step.completed_at:
                    status = "success" if step.success else "error"
                    log_entry = {
                        "timestamp": step.completed_at.isoformat(),
                        "type": "step_complete",
                        "message": f"{'Completed' if step.success else 'Failed'} {step.step_name}",
                        "level": status,
                        "duration": step.get_duration(),
                        "error": step.error_message if not step.success else None
                    }
                    logs.append(log_entry)
            
            return logs
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.post("/jobs/{task_id}/cancel")
async def cancel_job(task_id: str) -> Dict[str, str]:
    """Cancel a running analysis job."""
    try:
        tracker = ProgressTracker(task_id)
        tracker.update_status(
            status="CANCELLED",
            progress=None,
            step="Cancelled by admin"
        )
        return {"message": f"Job {task_id} has been cancelled"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """Get system-wide analysis statistics."""
    try:
        with get_session() as db:
            # Count jobs by status
            from sqlalchemy import func
            
            status_counts = db.query(
                AnalysisJob.status,
                func.count(AnalysisJob.id).label('count')
            ).group_by(AnalysisJob.status).all()
            
            # Recent activity (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_jobs = db.query(func.count(AnalysisJob.id)).filter(
                AnalysisJob.created_at >= last_24h
            ).scalar()
            
            # Average completion time
            completed_jobs = db.query(AnalysisJob).filter(
                AnalysisJob.status == "COMPLETE",
                AnalysisJob.started_at.isnot(None),
                AnalysisJob.completed_at.isnot(None)
            ).all()
            
            avg_duration = None
            if completed_jobs:
                durations = [job.get_duration() for job in completed_jobs if job.get_duration()]
                if durations:
                    avg_duration = sum(durations) / len(durations)
            
            return {
                "status_counts": {status: count for status, count in status_counts},
                "recent_activity": {
                    "jobs_last_24h": recent_jobs,
                },
                "performance": {
                    "average_duration_seconds": avg_duration,
                    "completed_jobs_total": len(completed_jobs),
                },
                "active_jobs": len(get_all_active_jobs()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") 