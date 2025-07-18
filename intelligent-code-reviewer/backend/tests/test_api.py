import pytest
import json
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.sql_models import AnalysisJob, FinalReport
from app.services.database import DatabaseService


class TestAnalyzeUrlEndpoint:
    """Test the /api/analyze/url endpoint."""
    
    def test_analyze_url_success(self, client: TestClient, test_db: Session, sample_git_url: str):
        """Test successful URL analysis request."""
        payload = {"git_url": sample_git_url}
        
        response = client.post("/api/analyze/url", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "task_id" in data
        assert "message" in data
        assert sample_git_url in data["message"]
        
        # Verify task was created in database
        task_id = data["task_id"]
        job = test_db.query(AnalysisJob).filter(AnalysisJob.task_id == task_id).first()
        
        assert job is not None
        assert job.task_id == task_id
        assert job.status == "PENDING"
        assert job.input_source_type == "git_url"
        assert job.input_source_path == sample_git_url
    
    def test_analyze_url_invalid_url(self, client: TestClient):
        """Test URL analysis with invalid URL."""
        payload = {"git_url": "not-a-valid-url"}
        
        response = client.post("/api/analyze/url", json=payload)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_analyze_url_missing_field(self, client: TestClient):
        """Test URL analysis with missing git_url field."""
        payload = {}
        
        response = client.post("/api/analyze/url", json=payload)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_analyze_url_wrong_content_type(self, client: TestClient, sample_git_url: str):
        """Test URL analysis with wrong content type."""
        # Send as form data instead of JSON
        response = client.post("/api/analyze/url", data={"git_url": sample_git_url})
        
        # Should return validation error
        assert response.status_code == 422


class TestAnalyzeZipEndpoint:
    """Test the /api/analyze/zip endpoint."""
    
    def test_analyze_zip_success(self, client: TestClient, test_db: Session):
        """Test successful ZIP file analysis request."""
        # Create a mock ZIP file
        zip_content = b"PK\x03\x04"  # Basic ZIP file header
        zip_file = ("test.zip", io.BytesIO(zip_content), "application/zip")
        
        response = client.post("/api/analyze/zip", files={"file": zip_file})
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "task_id" in data
        assert "message" in data
        assert "test.zip" in data["message"]
        
        # Verify task was created in database
        task_id = data["task_id"]
        job = test_db.query(AnalysisJob).filter(AnalysisJob.task_id == task_id).first()
        
        assert job is not None
        assert job.task_id == task_id
        assert job.status == "PENDING"
        assert job.input_source_type == "zip_upload"
        assert job.input_source_path == "test.zip"
    
    def test_analyze_zip_invalid_extension(self, client: TestClient):
        """Test ZIP analysis with non-ZIP file."""
        # Create a file with wrong extension
        file_content = b"some content"
        file_obj = ("test.txt", io.BytesIO(file_content), "text/plain")
        
        response = client.post("/api/analyze/zip", files={"file": file_obj})
        
        assert response.status_code == 400
        assert "Only ZIP files are allowed" in response.json()["detail"]
    
    def test_analyze_zip_no_file(self, client: TestClient):
        """Test ZIP analysis without file."""
        response = client.post("/api/analyze/zip")
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_analyze_zip_no_filename(self, client: TestClient):
        """Test ZIP analysis with file that has no filename."""
        zip_content = b"PK\x03\x04"
        zip_file = (None, io.BytesIO(zip_content), "application/zip")
        
        response = client.post("/api/analyze/zip", files={"file": zip_file})
        
        assert response.status_code == 400
        assert "Only ZIP files are allowed" in response.json()["detail"]


class TestReportEndpoint:
    """Test the /api/report/{task_id} endpoint."""
    
    def test_get_report_pending_job(self, client: TestClient, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test getting report for a pending job."""
        # Create a pending job
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        
        response = client.get(f"/api/report/{sample_task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == sample_task_id
        assert data["job_status"]["status"] == "PENDING"
        assert data["job_status"]["created_at"] is not None
        assert data["job_status"]["completed_at"] is None
        assert data["report_content"] is None
        assert data["error_message"] is None
    
    def test_get_report_processing_job(self, client: TestClient, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test getting report for a processing job."""
        # Create and update job status
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        DatabaseService.update_job_status(test_db, sample_task_id, "PROCESSING_RAG")
        
        response = client.get(f"/api/report/{sample_task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == sample_task_id
        assert data["job_status"]["status"] == "PROCESSING_RAG"
        assert data["report_content"] is None
    
    def test_get_report_complete_job_with_report(self, client: TestClient, test_db: Session, sample_task_id: str, sample_git_url: str, sample_report_content: dict):
        """Test getting report for a completed job with final report."""
        # Create job, complete it, and add final report
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        DatabaseService.update_job_status(test_db, sample_task_id, "COMPLETE")
        DatabaseService.create_final_report(
            db=test_db,
            task_id=sample_task_id,
            report_content=sample_report_content
        )
        
        response = client.get(f"/api/report/{sample_task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == sample_task_id
        assert data["job_status"]["status"] == "COMPLETE"
        assert data["job_status"]["completed_at"] is not None
        assert data["report_content"] == sample_report_content
        assert data["error_message"] is None
    
    def test_get_report_complete_job_without_report(self, client: TestClient, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test getting report for a completed job without final report."""
        # Create job and mark complete but don't add final report
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        DatabaseService.update_job_status(test_db, sample_task_id, "COMPLETE")
        
        response = client.get(f"/api/report/{sample_task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == sample_task_id
        assert data["job_status"]["status"] == "COMPLETE"
        assert data["report_content"] is not None  # Should have fallback content
        assert "Analysis complete" in data["report_content"]["summary"]
    
    def test_get_report_failed_job(self, client: TestClient, test_db: Session, sample_task_id: str, sample_git_url: str):
        """Test getting report for a failed job."""
        error_message = "Repository not found"
        
        # Create job and mark as failed
        DatabaseService.create_analysis_job(
            db=test_db,
            task_id=sample_task_id,
            input_source_type="git_url",
            input_source_path=sample_git_url
        )
        DatabaseService.update_job_status(test_db, sample_task_id, "FAILED", error_message)
        
        response = client.get(f"/api/report/{sample_task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == sample_task_id
        assert data["job_status"]["status"] == "FAILED"
        assert data["job_status"]["completed_at"] is not None
        assert data["report_content"] is None
        assert data["error_message"] == error_message
    
    def test_get_report_nonexistent_task(self, client: TestClient):
        """Test getting report for non-existent task."""
        response = client.get("/api/report/nonexistent-task-id")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "service" in data


class TestAPIIntegration:
    """Test end-to-end API workflows."""
    
    def test_full_workflow_url_analysis(self, client: TestClient, test_db: Session, sample_git_url: str):
        """Test a complete workflow from URL submission to report retrieval."""
        # 1. Submit URL for analysis
        payload = {"git_url": sample_git_url}
        response = client.post("/api/analyze/url", json=payload)
        
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # 2. Check initial status
        response = client.get(f"/api/report/{task_id}")
        assert response.status_code == 200
        assert response.json()["job_status"]["status"] == "PENDING"
        
        # 3. Simulate status updates (normally done by background processes)
        DatabaseService.update_job_status(test_db, task_id, "PROCESSING_RAG")
        
        response = client.get(f"/api/report/{task_id}")
        assert response.json()["job_status"]["status"] == "PROCESSING_RAG"
        
        # 4. Simulate completion with report
        DatabaseService.update_job_status(test_db, task_id, "COMPLETE")
        sample_report = {
            "summary": "Analysis completed successfully",
            "findings": [{"type": "info", "message": "No issues found"}],
            "recommendations": []
        }
        DatabaseService.create_final_report(test_db, task_id, sample_report)
        
        # 5. Check final status
        response = client.get(f"/api/report/{task_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_status"]["status"] == "COMPLETE"
        assert data["report_content"] == sample_report
    
    def test_full_workflow_zip_analysis(self, client: TestClient, test_db: Session):
        """Test a complete workflow from ZIP submission to report retrieval."""
        # 1. Submit ZIP for analysis
        zip_content = b"PK\x03\x04"
        zip_file = ("project.zip", io.BytesIO(zip_content), "application/zip")
        
        response = client.post("/api/analyze/zip", files={"file": zip_file})
        
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # 2. Check initial status
        response = client.get(f"/api/report/{task_id}")
        assert response.status_code == 200
        assert response.json()["job_status"]["status"] == "PENDING"
        
        # 3. Simulate failure
        DatabaseService.update_job_status(test_db, task_id, "FAILED", "Invalid ZIP file")
        
        # 4. Check failure status
        response = client.get(f"/api/report/{task_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_status"]["status"] == "FAILED"
        assert data["error_message"] == "Invalid ZIP file"
        assert data["report_content"] is None 