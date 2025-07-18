from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from ..models.sql_models import AnalysisJob, AgentLog, FinalReport


class DatabaseService:
    """Service class for database operations related to analysis jobs."""
    
    @staticmethod
    def create_analysis_job(
        db: Session, 
        task_id: str, 
        input_source_type: str, 
        input_source_path: str
    ) -> AnalysisJob:
        """
        Create a new analysis job in the database.
        
        Args:
            db: Database session
            task_id: Unique task identifier
            input_source_type: Type of input (git_url, zip_upload)
            input_source_path: Source path or URL
            
        Returns:
            AnalysisJob: Created analysis job object
        """
        job = AnalysisJob(
            task_id=task_id,
            status="PENDING",
            input_source_type=input_source_type,
            input_source_path=input_source_path
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def get_analysis_job(db: Session, task_id: str) -> Optional[AnalysisJob]:
        """
        Retrieve an analysis job by task ID.
        
        Args:
            db: Database session
            task_id: Task identifier
            
        Returns:
            AnalysisJob or None: Analysis job if found, None otherwise
        """
        return db.query(AnalysisJob).filter(AnalysisJob.task_id == task_id).first()
    
    @staticmethod
    def update_job_status(
        db: Session, 
        task_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> Optional[AnalysisJob]:
        """
        Update the status of an analysis job.
        
        Args:
            db: Database session
            task_id: Task identifier
            status: New status
            error_message: Error message if status is FAILED
            
        Returns:
            AnalysisJob or None: Updated job if found, None otherwise
        """
        job = db.query(AnalysisJob).filter(AnalysisJob.task_id == task_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if status in ["COMPLETE", "FAILED"]:
                job.completed_at = datetime.now()
            db.commit()
            db.refresh(job)
        return job
    
    @staticmethod
    def create_agent_log(
        db: Session,
        task_id: str,
        step_index: int,
        thought: str,
        action_tool: str,
        action_input: str,
        observation: str
    ) -> AgentLog:
        """
        Create a new agent log entry.
        
        Args:
            db: Database session
            task_id: Task identifier
            step_index: Step sequence number
            thought: Agent's reasoning
            action_tool: Tool used
            action_input: Input to the tool
            observation: Tool's output
            
        Returns:
            AgentLog: Created agent log entry
        """
        log = AgentLog(
            task_id=task_id,
            step_index=step_index,
            thought=thought,
            action_tool=action_tool,
            action_input=action_input,
            observation=observation
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def create_final_report(
        db: Session,
        task_id: str,
        report_content: Dict[str, Any]
    ) -> FinalReport:
        """
        Create a final report for an analysis job.
        
        Args:
            db: Database session
            task_id: Task identifier
            report_content: Analysis report as dictionary
            
        Returns:
            FinalReport: Created report object
        """
        report = FinalReport(
            task_id=task_id,
            report_content=report_content
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_final_report(db: Session, task_id: str) -> Optional[FinalReport]:
        """
        Retrieve the final report for an analysis job.
        
        Args:
            db: Database session
            task_id: Task identifier
            
        Returns:
            FinalReport or None: Report if found, None otherwise
        """
        return db.query(FinalReport).filter(FinalReport.task_id == task_id).first() 