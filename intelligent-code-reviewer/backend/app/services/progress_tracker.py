"""
Real-time progress tracking service for analysis jobs.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..models.analysis import AnalysisJob, AnalysisStep, AnalysisStatus

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Real-time progress tracking for analysis jobs."""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.start_time = time.time()
        
    def update_status(self, status: AnalysisStatus, progress: float = None, step: str = None):
        """Update the analysis status with optional progress and step info."""
        try:
            with get_session() as db:
                job = db.query(AnalysisJob).filter(AnalysisJob.task_id == self.task_id).first()
                if job:
                    job.status = status.value
                    job.updated_at = datetime.utcnow()
                    
                    if progress is not None:
                        job.progress_percentage = min(100.0, max(0.0, progress))
                    
                    if step:
                        job.current_step = step
                    
                    # Set started_at on first non-pending status
                    if status != AnalysisStatus.PENDING and not job.started_at:
                        job.started_at = datetime.utcnow()
                    
                    # Set completed_at on final status
                    if status in [AnalysisStatus.COMPLETE, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
                        job.completed_at = datetime.utcnow()
                    
                    db.commit()
                    
                    logger.info(f"Task {self.task_id}: {status.value} - {progress:.1f}% - {step}")
                else:
                    logger.error(f"Task {self.task_id} not found in database")
                    
        except Exception as e:
            logger.error(f"Failed to update status for task {self.task_id}: {e}")
    
    def update_file_progress(self, processed: int, total: int):
        """Update file processing progress."""
        try:
            with get_session() as db:
                job = db.query(AnalysisJob).filter(AnalysisJob.task_id == self.task_id).first()
                if job:
                    job.processed_files = processed
                    job.total_files = total
                    db.commit()
        except Exception as e:
            logger.error(f"Failed to update file progress for task {self.task_id}: {e}")
    
    def update_tool_progress(self, completed_tools: int):
        """Update tool execution progress."""
        try:
            with get_session() as db:
                job = db.query(AnalysisJob).filter(AnalysisJob.task_id == self.task_id).first()
                if job:
                    job.completed_tools = completed_tools
                    
                    # Calculate overall progress based on tools completed
                    if job.total_tools > 0:
                        tool_progress = (completed_tools / job.total_tools) * 100
                        # Tools are typically 50-90% of the total analysis
                        overall_progress = 50 + (tool_progress * 0.4)
                        job.progress_percentage = min(90.0, overall_progress)
                    
                    db.commit()
        except Exception as e:
            logger.error(f"Failed to update tool progress for task {self.task_id}: {e}")
    
    def log_step_start(self, step_name: str, step_type: str = "tool"):
        """Log the start of an analysis step."""
        try:
            with get_session() as db:
                step = AnalysisStep(
                    task_id=self.task_id,
                    step_name=step_name,
                    step_type=step_type,
                    status="running",
                    started_at=datetime.utcnow()
                )
                db.add(step)
                db.commit()
                logger.info(f"Task {self.task_id}: Started {step_type} - {step_name}")
        except Exception as e:
            logger.error(f"Failed to log step start for task {self.task_id}: {e}")
    
    def log_step_complete(self, step_name: str, success: bool = True, error: str = None, output: Dict = None):
        """Log the completion of an analysis step."""
        try:
            with get_session() as db:
                step = db.query(AnalysisStep).filter(
                    AnalysisStep.task_id == self.task_id,
                    AnalysisStep.step_name == step_name
                ).first()
                
                if step:
                    step.status = "completed" if success else "failed"
                    step.completed_at = datetime.utcnow()
                    step.success = success
                    step.execution_time = step.get_duration()
                    
                    if error:
                        step.error_message = error
                    
                    if output:
                        step.output_data = output
                    
                    db.commit()
                    
                    status_text = "✅ Completed" if success else "❌ Failed"
                    logger.info(f"Task {self.task_id}: {status_text} {step_name}")
                    
        except Exception as e:
            logger.error(f"Failed to log step completion for task {self.task_id}: {e}")
    
    def log_error(self, error_message: str, error_details: Dict = None):
        """Log an error for the analysis job."""
        try:
            with get_session() as db:
                job = db.query(AnalysisJob).filter(AnalysisJob.task_id == self.task_id).first()
                if job:
                    job.status = AnalysisStatus.FAILED.value
                    job.error_message = error_message
                    job.error_details = error_details
                    job.completed_at = datetime.utcnow()
                    db.commit()
                    
                    logger.error(f"Task {self.task_id}: ERROR - {error_message}")
        except Exception as e:
            logger.error(f"Failed to log error for task {self.task_id}: {e}")
    
    def add_warning(self, warning_message: str):
        """Add a warning to the analysis job."""
        try:
            with get_session() as db:
                job = db.query(AnalysisJob).filter(AnalysisJob.task_id == self.task_id).first()
                if job:
                    warnings = job.warnings or []
                    warnings.append({
                        "message": warning_message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    job.warnings = warnings
                    db.commit()
                    
                    logger.warning(f"Task {self.task_id}: WARNING - {warning_message}")
        except Exception as e:
            logger.error(f"Failed to add warning for task {self.task_id}: {e}")

    def get_current_status(self) -> Dict[str, Any]:
        """Get the current status and progress of the analysis."""
        try:
            with get_session() as db:
                job = db.query(AnalysisJob).filter(AnalysisJob.task_id == self.task_id).first()
                if job:
                    return job.get_progress_details()
                return {"error": "Job not found"}
        except Exception as e:
            logger.error(f"Failed to get status for task {self.task_id}: {e}")
            return {"error": str(e)}
    
    def get_step_history(self) -> List[Dict[str, Any]]:
        """Get the history of all analysis steps."""
        try:
            with get_session() as db:
                steps = db.query(AnalysisStep).filter(
                    AnalysisStep.task_id == self.task_id
                ).order_by(AnalysisStep.started_at).all()
                
                return [{
                    "step_name": step.step_name,
                    "step_type": step.step_type,
                    "status": step.status,
                    "duration": step.get_duration(),
                    "success": step.success,
                    "error": step.error_message,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                } for step in steps]
        except Exception as e:
            logger.error(f"Failed to get step history for task {self.task_id}: {e}")
            return []


def get_all_active_jobs() -> List[Dict[str, Any]]:
    """Get all currently active analysis jobs."""
    try:
        with get_session() as db:
            active_jobs = db.query(AnalysisJob).filter(
                AnalysisJob.status.notin_([
                    AnalysisStatus.COMPLETE.value,
                    AnalysisStatus.FAILED.value,
                    AnalysisStatus.CANCELLED.value
                ])
            ).all()
            
            return [{
                "task_id": job.task_id,
                "status": job.status,
                "progress": job.progress_percentage,
                "current_step": job.current_step,
                "duration": job.get_duration(),
                "source": job.input_source_path,
                "created_at": job.created_at.isoformat(),
            } for job in active_jobs]
    except Exception as e:
        logger.error(f"Failed to get active jobs: {e}")
        return [] 