"""
Enhanced analysis models with detailed progress tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

Base = declarative_base()


class AnalysisStatus(str, Enum):
    """Analysis status enumeration with detailed states."""
    PENDING = "PENDING"
    INITIALIZING = "INITIALIZING"
    CLONING_REPO = "CLONING_REPO"
    PROCESSING_FILES = "PROCESSING_FILES"
    BUILDING_RAG = "BUILDING_RAG"
    RUNNING_TOOLS = "RUNNING_TOOLS"
    GENERATING_REPORT = "GENERATING_REPORT"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AnalysisJob(Base):
    """Enhanced analysis job model with detailed tracking."""
    
    __tablename__ = "analysis_jobs"
    
    # Core fields
    task_id = Column(String(36), primary_key=True, index=True, nullable=False)  # UUID format
    
    # Source information
    input_source_type = Column(String, nullable=False)  # 'git_url' or 'zip_file'
    input_source_path = Column(String, nullable=False)  # URL or filename
    
    # Status tracking
    status = Column(String, nullable=False, default=AnalysisStatus.PENDING)
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String, nullable=True)
    
    # Timing information
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress details
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_tools = Column(Integer, default=13)  # We have 13 analysis tools
    completed_tools = Column(Integer, default=0)
    
    # Results and errors
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Metadata
    analysis_metadata = Column(JSON, nullable=True)  # Store additional info
    
    def get_duration(self) -> Optional[float]:
        """Get analysis duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    def get_progress_details(self) -> Dict[str, Any]:
        """Get detailed progress information."""
        return {
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "files_progress": f"{self.processed_files}/{self.total_files}",
            "tools_progress": f"{self.completed_tools}/{self.total_tools}",
            "duration": self.get_duration(),
            "estimated_remaining": self.estimate_remaining_time(),
        }
    
    def estimate_remaining_time(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.progress_percentage > 0 and self.started_at:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
            estimated_total = elapsed / (self.progress_percentage / 100)
            return max(0, estimated_total - elapsed)
        return None


class AnalysisStep(Base):
    """Individual analysis step tracking."""
    
    __tablename__ = "analysis_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, nullable=False, index=True)
    
    step_name = Column(String, nullable=False)
    step_type = Column(String, nullable=False)  # 'rag', 'tool', 'playbook'
    
    status = Column(String, nullable=False)  # 'pending', 'running', 'completed', 'failed'
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Metrics
    execution_time = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    
    def get_duration(self) -> Optional[float]:
        """Get step duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None 