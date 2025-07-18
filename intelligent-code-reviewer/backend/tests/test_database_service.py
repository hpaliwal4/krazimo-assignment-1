import pytest
from sqlalchemy.orm import Session

from app.services.database import DatabaseService
from app.models.sql_models import AnalysisJob, AgentLog, FinalReport


class TestDatabaseService:
    """Test the DatabaseService class."""
    
    def test_create_analysis_job(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test creating an analysis job using DatabaseService."""
        job = DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        assert job.task_id == sample_task_id
        assert job.status == "PENDING"
        assert job.input_source_type == "git_url"
        assert job.input_source_path == sample_git_url
        assert job.created_at is not None
        assert job.completed_at is None
        assert job.error_message is None
        
        # Verify it was persisted to database
        db_job = test_db.query(AnalysisJob).filter(AnalysisJob.task_id == sample_task_id).first()
        assert db_job is not None
        assert db_job.task_id == sample_task_id
    
    def test_get_analysis_job_existing(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test retrieving an existing analysis job."""
        # Create job first
        created_job = DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        # Retrieve job
        retrieved_job = DatabaseService.get_analysis_job(test_db, sample_task_id)
        
        assert retrieved_job is not None
        assert retrieved_job.task_id == sample_task_id
        assert retrieved_job.status == "PENDING"
        assert retrieved_job.input_source_type == "git_url"
    
    def test_get_analysis_job_nonexistent(self, test_db: Session):
        """Test retrieving a non-existent analysis job."""
        result = DatabaseService.get_analysis_job(test_db, "nonexistent-task-id")
        assert result is None
    
    def test_update_job_status_success(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test updating job status successfully."""
        # Create job first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        # Update status
        updated_job = DatabaseService.update_job_status(
            db=test_db,
            task_id=sample_task_id,
            status="PROCESSING_RAG"
        )
        
        assert updated_job is not None
        assert updated_job.status == "PROCESSING_RAG"
        assert updated_job.completed_at is None  # Should only be set for COMPLETE/FAILED
    
    def test_update_job_status_complete(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test updating job status to COMPLETE sets completed_at."""
        # Create job first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        # Update status to COMPLETE
        updated_job = DatabaseService.update_job_status(
            db=test_db,
            task_id=sample_task_id,
            status="COMPLETE"
        )
        
        assert updated_job is not None
        assert updated_job.status == "COMPLETE"
        assert updated_job.completed_at is not None
    
    def test_update_job_status_failed_with_error(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test updating job status to FAILED with error message."""
        # Create job first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        error_msg = "Git repository not found"
        
        # Update status to FAILED with error
        updated_job = DatabaseService.update_job_status(
            db=test_db,
            task_id=sample_task_id,
            status="FAILED",
            error_message=error_msg
        )
        
        assert updated_job is not None
        assert updated_job.status == "FAILED"
        assert updated_job.error_message == error_msg
        assert updated_job.completed_at is not None
    
    def test_update_job_status_nonexistent(self, test_db: Session):
        """Test updating status of non-existent job."""
        result = DatabaseService.update_job_status(
            db=test_db,
            task_id="nonexistent-task-id",
            status="COMPLETE"
        )
        assert result is None
    
    def test_create_agent_log(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test creating an agent log."""
        # Create job first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        # Create agent log
        log = DatabaseService.create_agent_log(
            db=test_db,
            task_id=sample_task_id,
            step_index=1,
            thought="I need to analyze the code",
            action_tool="list_project_files",
            action_input="{}",
            observation="Found 5 files"
        )
        
        assert log.task_id == sample_task_id
        assert log.step_index == 1
        assert log.thought == "I need to analyze the code"
        assert log.action_tool == "list_project_files"
        assert log.action_input == "{}"
        assert log.observation == "Found 5 files"
        assert log.timestamp is not None
        
        # Verify it was persisted
        db_log = test_db.query(AgentLog).filter(AgentLog.task_id == sample_task_id).first()
        assert db_log is not None
        assert db_log.step_index == 1
    
    def test_create_multiple_agent_logs(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test creating multiple agent logs for the same job."""
        # Create job first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        # Create multiple logs
        for i in range(3):
            DatabaseService.create_agent_log(
                db=test_db,
                task_id=sample_task_id,
                step_index=i + 1,
                thought=f"Step {i + 1} thought",
                action_tool="test_tool",
                action_input="{}",
                observation=f"Step {i + 1} result"
            )
        
        # Verify all logs were created
        logs = test_db.query(AgentLog).filter(AgentLog.task_id == sample_task_id).all()
        assert len(logs) == 3
        assert [log.step_index for log in logs] == [1, 2, 3]
    
    def test_create_final_report(self, test_db: Session, sample_task_id: str, sample_git_url: str, sample_report_content: dict):
        """Test creating a final report."""
        # Create job first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        # Create final report
        report = DatabaseService.create_final_report(
            db=test_db,
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        
        assert report.task_id == sample_task_id
        assert report.report_content == sample_report_content
        assert report.generated_at is not None
        
        # Verify it was persisted
        db_report = test_db.query(FinalReport).filter(FinalReport.task_id == sample_task_id).first()
        assert db_report is not None
        assert db_report.report_content == sample_report_content
    
    def test_get_final_report_existing(self, test_db: Session, sample_task_id: str, sample_git_url: str, sample_report_content: dict):
        """Test retrieving an existing final report."""
        # Create job and report first
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        created_report = DatabaseService.create_final_report(
            db=test_db,
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        
        # Retrieve report
        retrieved_report = DatabaseService.get_final_report(test_db, sample_task_id)
        
        assert retrieved_report is not None
        assert retrieved_report.task_id == sample_task_id
        assert retrieved_report.report_content == sample_report_content
    
    def test_get_final_report_nonexistent(self, test_db: Session):
        """Test retrieving a non-existent final report."""
        result = DatabaseService.get_final_report(test_db, "nonexistent-task-id")
        assert result is None
    
    def test_end_to_end_workflow(self, test_db: Session, sample_task_id: str, sample_git_url: str, sample_report_content: dict):
        """Test a complete end-to-end workflow using DatabaseService."""
        # 1. Create analysis job
        job = DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        assert job.status == "PENDING"
        
        # 2. Update status to processing RAG
        job = DatabaseService.update_job_status(test_db, sample_task_id, "PROCESSING_RAG")
        assert job.status == "PROCESSING_RAG"
        
        # 3. Update status to processing agent
        job = DatabaseService.update_job_status(test_db, sample_task_id, "PROCESSING_AGENT")
        assert job.status == "PROCESSING_AGENT"
        
        # 4. Create agent logs
        for i in range(3):
            DatabaseService.create_agent_log(
                db=test_db,
                task_id=sample_task_id,
                step_index=i + 1,
                thought=f"Agent step {i + 1}",
                action_tool="test_tool",
                action_input="{}",
                observation=f"Result {i + 1}"
            )
        
        # 5. Create final report
        report = DatabaseService.create_final_report(
            db=test_db,
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        
        # 6. Update status to complete
        job = DatabaseService.update_job_status(test_db, sample_task_id, "COMPLETE")
        assert job.status == "COMPLETE"
        assert job.completed_at is not None
        
        # 7. Verify everything exists
        final_job = DatabaseService.get_analysis_job(test_db, sample_task_id)
        final_report = DatabaseService.get_final_report(test_db, sample_task_id)
        agent_logs = test_db.query(AgentLog).filter(AgentLog.task_id == sample_task_id).all()
        
        assert final_job.status == "COMPLETE"
        assert final_report.report_content == sample_report_content
        assert len(agent_logs) == 3 