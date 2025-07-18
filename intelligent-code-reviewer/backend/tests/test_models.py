import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.sql_models import AnalysisJob, AgentLog, FinalReport


class TestAnalysisJob:
    """Test the AnalysisJob model."""
    
    def test_create_analysis_job(self, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test creating a new analysis job."""
        job = AnalysisJob(
            task_id=sample_task_id,
            status="PENDING",
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        
        # Verify the job was created correctly
        assert job.task_id == sample_task_id
        assert job.status == "PENDING"
        assert job.input_source_type == "git_url"
        assert job.input_source_path == sample_git_url
        assert job.created_at is not None
        assert job.completed_at is None
        assert job.error_message is None
    
    def test_analysis_job_default_status(self, test_db: Session, sample_task_id: str):
        """Test that analysis job has default status of PENDING."""
        job = AnalysisJob(
            task_id=sample_task_id,
            input_source_type="zip_upload",
            input_source_path="test.zip"
        )
        
        test_db.add(job)
        test_db.commit()
        
        assert job.status == "PENDING"
    
    def test_analysis_job_repr(self, sample_task_id: str):
        """Test the string representation of AnalysisJob."""
        job = AnalysisJob(
            task_id=sample_task_id,
            status="COMPLETE",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        
        expected = f"<AnalysisJob(task_id='{sample_task_id}', status='COMPLETE')>"
        assert repr(job) == expected
    
    def test_query_analysis_job_by_task_id(self, test_db: Session, sample_task_id: str):
        """Test querying analysis job by task_id."""
        # Create job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="PENDING",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Query by task_id
        found_job = test_db.query(AnalysisJob).filter(AnalysisJob.task_id == sample_task_id).first()
        
        assert found_job is not None
        assert found_job.task_id == sample_task_id
        assert found_job.status == "PENDING"


class TestAgentLog:
    """Test the AgentLog model."""
    
    def test_create_agent_log(self, test_db: Session, sample_task_id: str):
        """Test creating a new agent log."""
        # First create an analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="PROCESSING_AGENT",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create agent log
        log = AgentLog(
            task_id=sample_task_id,
            step_index=1,
            thought="I need to analyze the code structure",
            action_tool="list_project_files",
            action_input="{}",
            observation="Found 5 Python files"
        )
        
        test_db.add(log)
        test_db.commit()
        test_db.refresh(log)
        
        # Verify the log was created correctly
        assert log.task_id == sample_task_id
        assert log.step_index == 1
        assert log.thought == "I need to analyze the code structure"
        assert log.action_tool == "list_project_files"
        assert log.action_input == "{}"
        assert log.observation == "Found 5 Python files"
        assert log.timestamp is not None
    
    def test_agent_log_relationship(self, test_db: Session, sample_task_id: str):
        """Test the relationship between AgentLog and AnalysisJob."""
        # Create analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="PROCESSING_AGENT",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create multiple agent logs
        for i in range(3):
            log = AgentLog(
                task_id=sample_task_id,
                step_index=i + 1,
                thought=f"Step {i + 1} thought",
                action_tool="test_tool",
                action_input="{}",
                observation=f"Step {i + 1} result"
            )
            test_db.add(log)
        
        test_db.commit()
        
        # Test the relationship
        test_db.refresh(job)
        assert len(job.agent_logs) == 3
        assert all(log.task_id == sample_task_id for log in job.agent_logs)
    
    def test_agent_log_repr(self, sample_task_id: str):
        """Test the string representation of AgentLog."""
        log = AgentLog(
            task_id=sample_task_id,
            step_index=5,
            thought="Test thought",
            action_tool="test_tool",
            action_input="{}",
            observation="Test observation"
        )
        log.log_id = 123  # Simulate assigned ID
        
        expected = f"<AgentLog(log_id=123, task_id='{sample_task_id}', step=5)>"
        assert repr(log) == expected


class TestFinalReport:
    """Test the FinalReport model."""
    
    def test_create_final_report(self, test_db: Session, sample_task_id: str, sample_report_content: dict):
        """Test creating a final report."""
        # First create an analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="COMPLETE",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create final report
        report = FinalReport(
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        
        test_db.add(report)
        test_db.commit()
        test_db.refresh(report)
        
        # Verify the report was created correctly
        assert report.task_id == sample_task_id
        assert report.report_content == sample_report_content
        assert report.generated_at is not None
    
    def test_final_report_relationship(self, test_db: Session, sample_task_id: str, sample_report_content: dict):
        """Test the relationship between FinalReport and AnalysisJob."""
        # Create analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="COMPLETE",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create final report
        report = FinalReport(
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        test_db.add(report)
        test_db.commit()
        
        # Test the relationship
        test_db.refresh(job)
        assert job.final_report is not None
        assert job.final_report.task_id == sample_task_id
        assert job.final_report.report_content == sample_report_content
    
    def test_final_report_unique_constraint(self, test_db: Session, sample_task_id: str, sample_report_content: dict):
        """Test that only one final report can exist per task."""
        # Create analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="COMPLETE",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create first final report
        report1 = FinalReport(
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        test_db.add(report1)
        test_db.commit()
        
        # Try to create second final report for same task
        report2 = FinalReport(
            task_id=sample_task_id,
            report_content={"different": "content"}
        )
        test_db.add(report2)
        
        # This should raise an integrity error due to unique constraint
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            test_db.commit()
    
    def test_final_report_repr(self, sample_task_id: str):
        """Test the string representation of FinalReport."""
        report = FinalReport(
            task_id=sample_task_id,
            report_content={"test": "content"}
        )
        report.report_id = 456  # Simulate assigned ID
        
        expected = f"<FinalReport(report_id=456, task_id='{sample_task_id}')>"
        assert repr(report) == expected


class TestModelRelationships:
    """Test the relationships between all models."""
    
    def test_cascade_delete_agent_logs(self, test_db: Session, sample_task_id: str):
        """Test that deleting an analysis job cascades to delete agent logs."""
        # Create analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="PROCESSING_AGENT",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create agent logs
        for i in range(2):
            log = AgentLog(
                task_id=sample_task_id,
                step_index=i + 1,
                thought=f"Step {i + 1}",
                action_tool="test_tool",
                action_input="{}",
                observation="test result"
            )
            test_db.add(log)
        test_db.commit()
        
        # Verify logs exist
        log_count = test_db.query(AgentLog).filter(AgentLog.task_id == sample_task_id).count()
        assert log_count == 2
        
        # Delete the job
        test_db.delete(job)
        test_db.commit()
        
        # Verify logs were cascaded deleted
        log_count = test_db.query(AgentLog).filter(AgentLog.task_id == sample_task_id).count()
        assert log_count == 0
    
    def test_cascade_delete_final_report(self, test_db: Session, sample_task_id: str, sample_report_content: dict):
        """Test that deleting an analysis job cascades to delete final report."""
        # Create analysis job
        job = AnalysisJob(
            task_id=sample_task_id,
            status="COMPLETE",
            input_source_type="git_url",
            input_source_path="https://github.com/test/repo.git"
        )
        test_db.add(job)
        test_db.commit()
        
        # Create final report
        report = FinalReport(
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        test_db.add(report)
        test_db.commit()
        
        # Verify report exists
        report_count = test_db.query(FinalReport).filter(FinalReport.task_id == sample_task_id).count()
        assert report_count == 1
        
        # Delete the job
        test_db.delete(job)
        test_db.commit()
        
        # Verify report was cascaded deleted
        report_count = test_db.query(FinalReport).filter(FinalReport.task_id == sample_task_id).count()
        assert report_count == 0 