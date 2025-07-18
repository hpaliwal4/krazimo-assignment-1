from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class AnalysisJob(Base):
    """
    Tracks the high-level status of each analysis task.
    
    This table manages the lifecycle of each code analysis job,
    from creation to completion or failure.
    """
    __tablename__ = "analysis_jobs"
    
    task_id = Column(String(36), primary_key=True, index=True)  # UUID format
    status = Column(
        String(20), 
        nullable=False, 
        default="PENDING",
        comment="Job status: PENDING, PROCESSING_RAG, PROCESSING_AGENT, COMPLETE, FAILED"
    )
    input_source_type = Column(
        String(20), 
        nullable=False,
        comment="Source type: git_url, zip_upload"
    )
    input_source_path = Column(
        Text, 
        nullable=False,
        comment="Git URL or original filename"
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    completed_at = Column(
        DateTime(timezone=True), 
        nullable=True
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error details if status is FAILED"
    )
    
    # Relationships
    agent_logs = relationship("AgentLog", back_populates="analysis_job", cascade="all, delete-orphan")
    final_report = relationship("FinalReport", back_populates="analysis_job", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisJob(task_id='{self.task_id}', status='{self.status}')>"


class AgentLog(Base):
    """
    Provides a complete, auditable record of the agent's reasoning process.
    
    This table stores each step of the AI agent's thought, action, observation cycle,
    providing full transparency into the agent's decision-making process.
    """
    __tablename__ = "agent_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(
        String(36), 
        ForeignKey("analysis_jobs.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    step_index = Column(
        Integer, 
        nullable=False,
        comment="The sequence number of the step (1, 2, 3...)"
    )
    thought = Column(
        Text, 
        nullable=False,
        comment="The agent's reasoning for its next action"
    )
    action_tool = Column(
        String(50), 
        nullable=False,
        comment="The name of the tool used"
    )
    action_input = Column(
        Text, 
        nullable=False,
        comment="The specific input given to the tool"
    )
    observation = Column(
        Text, 
        nullable=False,
        comment="The result returned from the tool"
    )
    timestamp = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    analysis_job = relationship("AnalysisJob", back_populates="agent_logs")
    
    def __repr__(self):
        return f"<AgentLog(log_id={self.log_id}, task_id='{self.task_id}', step={self.step_index})>"


class FinalReport(Base):
    """
    Stores the final, user-facing analysis report.
    
    This table contains the structured JSON output from the agent
    after completing its analysis of the codebase.
    """
    __tablename__ = "final_reports"
    
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(
        String(36), 
        ForeignKey("analysis_jobs.task_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    report_content = Column(
        JSON, 
        nullable=False,
        comment="The structured JSON output from the agent"
    )
    generated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    analysis_job = relationship("AnalysisJob", back_populates="final_report")
    
    def __repr__(self):
        return f"<FinalReport(report_id={self.report_id}, task_id='{self.task_id}')>" 