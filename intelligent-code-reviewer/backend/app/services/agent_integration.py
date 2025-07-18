"""
Agent Integration Service.

This module provides integration between the AI Agent and the existing
API infrastructure, connecting RAG pipeline results with intelligent analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ai_agent import AIAgent, AgentContext, AnalysisResult
from .agent_orchestrator import AgentOrchestrator, ExecutionStrategy
from .rag_pipeline import RAGIngestionPipeline
from .vector_store import VectorStore
from ..core.config import settings
from ..db.database import DatabaseService


logger = logging.getLogger(__name__)


class AgentIntegrationService:
    """
    Service that integrates AI Agent with the existing infrastructure.
    
    This service handles:
    1. Setting up agent context from job information
    2. Coordinating RAG pipeline and agent execution
    3. Converting agent results to database format
    4. Managing the full analysis workflow
    """
    
    def __init__(self):
        """Initialize the integration service."""
        # Initialize RAG pipeline
        self.rag_pipeline = RAGIngestionPipeline()
        
        # Initialize vector store
        self.vector_store = VectorStore()
        
        # Initialize AI agent
        self.ai_agent = AIAgent(
            rag_pipeline=self.rag_pipeline,
            vector_store=self.vector_store,
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize Agent Orchestrator
        self.orchestrator = AgentOrchestrator(self.ai_agent)
        
        logger.info("Agent Integration Service initialized")
    
    async def process_analysis_job(
        self,
        task_id: str,
        source_type: str,
        source_location: str,
        db_service: DatabaseService,
        analysis_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a complete analysis job using RAG + AI Agent.
        
        Args:
            task_id: Unique task identifier
            source_type: Type of source ('url' or 'zip')
            source_location: Git URL or file path
            db_service: Database service for progress tracking
            analysis_requirements: Specific analysis requirements
            
        Returns:
            Dictionary with analysis results and metadata
        """
        logger.info(f"Starting integrated analysis for task {task_id}")
        
        try:
            # Phase 1: RAG Pipeline Processing
            await db_service.update_job_status(
                task_id,
                "in_progress",
                {"stage": "rag_processing", "step": "initializing"}
            )
            
            # Process with RAG pipeline
            if source_type == "url":
                rag_result = await self.rag_pipeline.process_git_repository(
                    task_id, source_location, db_service
                )
            else:  # zip file
                rag_result = await self.rag_pipeline.process_zip_file(
                    task_id, source_location, db_service
                )
            
            if rag_result["status"] != "completed":
                raise Exception(f"RAG pipeline failed: {rag_result.get('error', 'Unknown error')}")
            
            # Phase 2: AI Agent Analysis
            await db_service.update_job_status(
                task_id,
                "in_progress",
                {"stage": "ai_analysis", "step": "preparing_context"}
            )
            
            # Create agent context
            agent_context = AgentContext(
                task_id=task_id,
                project_info=rag_result.get("project_info", {}),
                vector_store_collection=task_id,
                analysis_requirements=analysis_requirements or [
                    "code_quality", 
                    "security_vulnerabilities", 
                    "architectural_issues",
                    "performance_bottlenecks"
                ]
            )
            
            # Execute orchestrated AI agent analysis
            analysis_results, orchestration_metrics = await self.orchestrator.orchestrate_analysis(
                agent_context, 
                execution_strategy=ExecutionStrategy.ADAPTIVE,
                db_service=db_service
            )
            
            # Phase 3: Result Processing
            await db_service.update_job_status(
                task_id,
                "in_progress",
                {"stage": "result_processing", "step": "formatting_results"}
            )
            
            # Convert results to API format
            formatted_results = self._format_analysis_results(
                analysis_results, rag_result, task_id, orchestration_metrics
            )
            
            # Store final report in database
            await self._store_final_report(
                task_id, formatted_results, db_service
            )
            
            # Mark job as completed
            await db_service.update_job_status(
                task_id,
                "completed",
                {
                    "stage": "completed",
                    "total_issues": len(analysis_results),
                    "critical_issues": sum(1 for r in analysis_results if r.severity == "critical"),
                    "completion_time": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Integrated analysis completed for task {task_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Integrated analysis failed for task {task_id}: {e}")
            
            await db_service.update_job_status(
                task_id,
                "failed",
                {
                    "error": str(e),
                    "stage": "integration_service",
                    "failure_time": datetime.now().isoformat()
                }
            )
            
            raise
    
    def _format_analysis_results(
        self,
        analysis_results: List[AnalysisResult],
        rag_result: Dict[str, Any],
        task_id: str,
        orchestration_metrics: Any = None
    ) -> Dict[str, Any]:
        """Format analysis results for API response."""
        
        # Group results by severity
        results_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for result in analysis_results:
            severity = result.severity.value
            formatted_result = {
                "id": f"{task_id}_{result.tool_name}_{hash(result.title) % 10000}",
                "tool": result.tool_name,
                "playbook": result.playbook_name,
                "title": result.title,
                "description": result.description,
                "severity": severity,
                "confidence": result.confidence_score,
                "findings": result.findings,
                "recommendations": result.recommendations,
                "execution_time": result.execution_time,
                "metadata": result.metadata
            }
            results_by_severity[severity].append(formatted_result)
        
        # Calculate summary statistics
        total_issues = len(analysis_results)
        critical_count = len(results_by_severity["critical"])
        high_count = len(results_by_severity["high"])
        
        # Determine overall health score
        if critical_count > 0:
            health_score = max(0, 40 - (critical_count * 10))
        elif high_count > 3:
            health_score = max(40, 70 - (high_count * 5))
        elif total_issues > 10:
            health_score = max(60, 85 - total_issues)
        else:
            health_score = min(95, 90 + (5 - total_issues))
        
        # Generate overall recommendations
        overall_recommendations = []
        if critical_count > 0:
            overall_recommendations.append(
                f"🚨 URGENT: {critical_count} critical security/architectural issues require immediate attention"
            )
        if high_count > 0:
            overall_recommendations.append(
                f"⚠️ HIGH PRIORITY: {high_count} high-severity issues should be addressed soon"
            )
        
        # Add tool-specific insights
        tool_counts = {}
        for result in analysis_results:
            tool_counts[result.tool_name] = tool_counts.get(result.tool_name, 0) + 1
        
        if tool_counts:
            most_issues = max(tool_counts.items(), key=lambda x: x[1])
            overall_recommendations.append(
                f"📊 FOCUS AREA: {most_issues[0]} identified {most_issues[1]} issues - prioritize these fixes"
            )
        
        overall_recommendations.extend([
            "🔄 Implement automated code quality checks in CI/CD pipeline",
            "📚 Consider team training on identified code quality patterns",
            "🛡️ Regular security audits and dependency updates recommended"
        ])
        
        # Add orchestration metrics if available
        orchestration_data = {}
        if orchestration_metrics:
            orchestration_data = {
                "execution_time": orchestration_metrics.execution_time,
                "tool_success_rate": orchestration_metrics.tool_success_rate,
                "finding_quality_score": orchestration_metrics.finding_quality_score,
                "coverage_score": orchestration_metrics.coverage_score
            }

        return {
            "task_id": task_id,
            "status": "completed",
            "analysis_summary": {
                "total_issues": total_issues,
                "critical_issues": critical_count,
                "high_priority_issues": high_count,
                "health_score": health_score,
                "health_grade": self._get_health_grade(health_score),
                "analysis_timestamp": datetime.now().isoformat(),
                "tools_executed": list(tool_counts.keys()),
                "processing_time": rag_result.get("processing_time", 0)
            },
            "project_info": rag_result.get("project_info", {}),
            "results_by_severity": results_by_severity,
            "overall_recommendations": overall_recommendations,
            "rag_metrics": {
                "files_processed": rag_result.get("files_processed", 0),
                "chunks_created": rag_result.get("chunks_created", 0),
                "languages_detected": rag_result.get("project_info", {}).get("languages", [])
            },
            "orchestration_metrics": orchestration_data
        }
    
    def _get_health_grade(self, health_score: int) -> str:
        """Convert health score to letter grade."""
        if health_score >= 90:
            return "A"
        elif health_score >= 80:
            return "B"
        elif health_score >= 70:
            return "C"
        elif health_score >= 60:
            return "D"
        else:
            return "F"
    
    async def _store_final_report(
        self,
        task_id: str,
        formatted_results: Dict[str, Any],
        db_service: DatabaseService
    ):
        """Store the final analysis report in the database."""
        try:
            # Create final report record
            report_data = {
                "task_id": task_id,
                "analysis_summary": formatted_results["analysis_summary"],
                "results": formatted_results["results_by_severity"],
                "recommendations": formatted_results["overall_recommendations"],
                "project_info": formatted_results["project_info"],
                "rag_metrics": formatted_results["rag_metrics"],
                "generated_at": datetime.now().isoformat()
            }
            
            # Store in database (assuming we have a final_reports table)
            await db_service.create_final_report(task_id, report_data)
            
            logger.info(f"Final report stored for task {task_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store final report for task {task_id}: {e}")
            # Don't fail the entire process if report storage fails
    
    async def get_analysis_report(
        self,
        task_id: str,
        db_service: DatabaseService
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a stored analysis report."""
        try:
            # Get final report from database
            report = await db_service.get_final_report(task_id)
            
            if report:
                return {
                    "task_id": task_id,
                    "status": "completed",
                    **report
                }
            else:
                # Check if job is still in progress
                job = await db_service.get_job(task_id)
                if job:
                    return {
                        "task_id": task_id,
                        "status": job.status,
                        "progress": job.metadata or {},
                        "message": "Analysis in progress" if job.status == "in_progress" else f"Job status: {job.status}"
                    }
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to retrieve analysis report for task {task_id}: {e}")
            return None 