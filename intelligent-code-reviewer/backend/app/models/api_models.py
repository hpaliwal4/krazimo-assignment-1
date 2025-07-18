from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


# Request Models
class AnalyzeUrlRequest(BaseModel):
    """Request model for analyzing a Git repository URL."""
    git_url: HttpUrl = Field(..., description="The Git repository URL to analyze")


class AnalyzeZipRequest(BaseModel):
    """Request model for analyzing an uploaded ZIP file."""
    # This will be handled as multipart/form-data in the endpoint
    pass


# Response Models
class AnalyzeResponse(BaseModel):
    """Response model for both analyze endpoints."""
    task_id: str = Field(..., description="Unique identifier for the analysis task")
    message: str = Field(..., description="Success message")


class JobStatus(BaseModel):
    """Model representing the current status of an analysis job."""
    status: Literal["PENDING", "PROCESSING_RAG", "PROCESSING_AGENT", "COMPLETE", "FAILED"]
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReportResponse(BaseModel):
    """Response model for the report endpoint."""
    task_id: str
    job_status: JobStatus
    report_content: Optional[dict] = Field(None, description="Analysis report (only present when status is COMPLETE)")
    error_message: Optional[str] = Field(None, description="Error details (only present when status is FAILED)")


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    detail: Optional[str] = None 