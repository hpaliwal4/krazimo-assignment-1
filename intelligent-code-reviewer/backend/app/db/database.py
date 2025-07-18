"""
Database service for managing analysis jobs, logs, and reports.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, desc
from ..models.database import Base, AnalysisJob, AgentLog, FinalReport
from ..core.config import settings


logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.debug
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class DatabaseService:
    """Database service for managing analysis jobs and results."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_job(
        self,
        task_id: str,
        source_type: str,
        source_location: str,
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisJob:
        """Create a new analysis job."""
        try:
            job = AnalysisJob(
                task_id=task_id,
                source_type=source_type,
                source_location=source_location,
                status=status,
                metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            
            logger.info(f"Created analysis job: {task_id}")
            return job
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create job {task_id}: {e}")
            raise
    
    async def get_job(self, task_id: str) -> Optional[AnalysisJob]:
        """Get an analysis job by task ID."""
        try:
            stmt = select(AnalysisJob).where(AnalysisJob.task_id == task_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get job {task_id}: {e}")
            return None
    
    async def update_job_status(
        self,
        task_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update job status and metadata."""
        try:
            stmt = select(AnalysisJob).where(AnalysisJob.task_id == task_id)
            result = await self.session.execute(stmt)
            job = result.scalar_one_or_none()
            
            if not job:
                logger.warning(f"Job {task_id} not found for status update")
                return False
            
            job.status = status
            job.updated_at = datetime.now()
            
            if metadata:
                # Merge with existing metadata
                existing_metadata = {}
                if job.metadata:
                    try:
                        existing_metadata = json.loads(job.metadata)
                    except json.JSONDecodeError:
                        pass
                
                existing_metadata.update(metadata)
                job.metadata = json.dumps(existing_metadata)
            
            await self.session.commit()
            logger.info(f"Updated job {task_id} status to {status}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update job {task_id}: {e}")
            return False
    
    async def list_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[AnalysisJob]:
        """List analysis jobs with optional filtering."""
        try:
            stmt = select(AnalysisJob).order_by(desc(AnalysisJob.created_at))
            
            if status_filter:
                stmt = stmt.where(AnalysisJob.status == status_filter)
            
            stmt = stmt.limit(limit).offset(offset)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    async def log_agent_action(
        self,
        task_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> AgentLog:
        """Log an agent action."""
        try:
            log_entry = AgentLog(
                task_id=task_id,
                action_type=action_type,
                action_data=json.dumps(action_data),
                tool_name=tool_name,
                timestamp=datetime.now()
            )
            
            self.session.add(log_entry)
            await self.session.commit()
            await self.session.refresh(log_entry)
            
            return log_entry
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to log agent action for {task_id}: {e}")
            raise
    
    async def get_agent_logs(
        self,
        task_id: str,
        action_type: Optional[str] = None
    ) -> List[AgentLog]:
        """Get agent logs for a task."""
        try:
            stmt = select(AgentLog).where(AgentLog.task_id == task_id)
            
            if action_type:
                stmt = stmt.where(AgentLog.action_type == action_type)
            
            stmt = stmt.order_by(AgentLog.timestamp)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get agent logs for {task_id}: {e}")
            return []
    
    async def create_final_report(
        self,
        task_id: str,
        report_data: Dict[str, Any]
    ) -> FinalReport:
        """Create a final analysis report."""
        try:
            report = FinalReport(
                task_id=task_id,
                report_data=json.dumps(report_data),
                generated_at=datetime.now()
            )
            
            self.session.add(report)
            await self.session.commit()
            await self.session.refresh(report)
            
            logger.info(f"Created final report for task: {task_id}")
            return report
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create final report for {task_id}: {e}")
            raise
    
    async def get_final_report(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get final report by task ID."""
        try:
            stmt = select(FinalReport).where(FinalReport.task_id == task_id)
            result = await self.session.execute(stmt)
            report = result.scalar_one_or_none()
            
            if report and report.report_data:
                try:
                    return json.loads(report.report_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in final report for {task_id}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get final report for {task_id}: {e}")
            return None
    
    async def delete_job(self, task_id: str) -> bool:
        """Delete a job and all related data."""
        try:
            # Delete agent logs
            await self.session.execute(
                select(AgentLog).where(AgentLog.task_id == task_id)
            )
            
            # Delete final report
            await self.session.execute(
                select(FinalReport).where(FinalReport.task_id == task_id)
            )
            
            # Delete job
            stmt = select(AnalysisJob).where(AnalysisJob.task_id == task_id)
            result = await self.session.execute(stmt)
            job = result.scalar_one_or_none()
            
            if job:
                await self.session.delete(job)
                await self.session.commit()
                logger.info(f"Deleted job and related data: {task_id}")
                return True
            
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete job {task_id}: {e}")
            return False


# Database session dependency
async def get_db_session() -> AsyncSession:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_service() -> DatabaseService:
    """Get database service instance."""
    async with async_session_factory() as session:
        try:
            yield DatabaseService(session)
        finally:
            await session.close()


async def create_tables():
    """Create database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise 