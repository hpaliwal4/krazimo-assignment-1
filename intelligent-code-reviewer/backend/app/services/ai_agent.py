"""
AI Agent for Intelligent Code Analysis.

This module implements the core AI agent that orchestrates code analysis
using various tools and playbooks through LLM-powered decision making.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import openai
from pydantic import BaseModel

from ..core.config import settings
from .rag_pipeline import RAGIngestionPipeline
from .vector_store import VectorStore


logger = logging.getLogger(__name__)


class AnalysisStatus(str, Enum):
    """Analysis task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, Enum):
    """Issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisResult(BaseModel):
    """Result of a single analysis."""
    tool_name: str
    playbook_name: Optional[str] = None
    status: AnalysisStatus
    severity: SeverityLevel
    title: str
    description: str
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float
    execution_time: float
    metadata: Dict[str, Any] = {}


class AgentContext(BaseModel):
    """Context information for the AI agent."""
    task_id: str
    project_info: Dict[str, Any]
    vector_store_collection: str
    analysis_requirements: List[str]
    user_preferences: Dict[str, Any] = {}
    previous_analyses: List[AnalysisResult] = []


class AIAgent:
    """
    Core AI Agent for intelligent code analysis.
    
    The agent uses LLM-powered decision making to:
    1. Select appropriate analysis tools and playbooks
    2. Coordinate tool execution based on code context
    3. Synthesize results into comprehensive reports
    4. Learn from analysis patterns for better recommendations
    """
    
    def __init__(
        self,
        rag_pipeline: RAGIngestionPipeline,
        vector_store: VectorStore,
        openai_api_key: Optional[str] = None
    ):
        """Initialize the AI agent."""
        self.rag_pipeline = rag_pipeline
        self.vector_store = vector_store
        self.openai_client = openai.AsyncOpenAI(
            api_key=openai_api_key or settings.openai_api_key
        )
        
        # Tool registry - initialize with all available tools
        self.tools = self._initialize_tools()
        self.playbooks = self._initialize_playbooks()
        
        # Analysis history for learning
        self.analysis_history = []
        
        logger.info("AI Agent initialized")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize all available analysis tools."""
        from ..tools import (
            StaticAnalyzer, DependencyAnalyzer, SecurityScanner, ComplexityAnalyzer,
            CodeQualityChecker, PerformanceAnalyzer, ArchitectureAnalyzer
        )
        
        tools = {
            "static_analyzer": StaticAnalyzer(),
            "dependency_analyzer": DependencyAnalyzer(),
            "security_scanner": SecurityScanner(),
            "complexity_analyzer": ComplexityAnalyzer(),
            "code_quality_checker": CodeQualityChecker(),
            "performance_analyzer": PerformanceAnalyzer(),
            "architecture_analyzer": ArchitectureAnalyzer()
        }
        
        logger.info(f"Initialized {len(tools)} analysis tools")
        return tools
    
    def _initialize_playbooks(self) -> Dict[str, Any]:
        """Initialize all available analysis playbooks."""
        from ..playbooks import (
            GodClassesPlaybook, CircularDependenciesPlaybook, HighComplexityPlaybook,
            DependencyHealthPlaybook, HardcodedSecretsPlaybook, IdorVulnerabilitiesPlaybook
        )
        
        playbooks = {
            "god_classes": GodClassesPlaybook(),
            "circular_dependencies": CircularDependenciesPlaybook(),
            "high_complexity": HighComplexityPlaybook(),
            "dependency_health": DependencyHealthPlaybook(),
            "hardcoded_secrets": HardcodedSecretsPlaybook(),
            "idor_vulnerabilities": IdorVulnerabilitiesPlaybook()
        }
        
        logger.info(f"Initialized {len(playbooks)} analysis playbooks")
        return playbooks
    
    async def analyze_codebase(
        self,
        context: AgentContext,
        db_service: Any = None
    ) -> List[AnalysisResult]:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            context: Analysis context with task info and requirements
            db_service: Database service for progress tracking
            
        Returns:
            List of analysis results from executed tools/playbooks
        """
        logger.info(f"Starting codebase analysis for task {context.task_id}")
        
        try:
            # Update status
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {"stage": "agent_analysis", "step": "planning"}
                )
            
            # Step 1: Analyze project context and select tools
            selected_tools = await self._select_analysis_tools(context)
            logger.info(f"Selected tools: {[tool['name'] for tool in selected_tools]}")
            
            # Step 2: Execute selected tools and playbooks
            results = []
            for i, tool_config in enumerate(selected_tools):
                if db_service:
                    await db_service.update_job_status(
                        context.task_id,
                        "in_progress",
                        {
                            "stage": "agent_analysis",
                            "step": f"executing_tool_{i+1}",
                            "tool": tool_config["name"],
                            "progress": f"{i+1}/{len(selected_tools)}"
                        }
                    )
                
                tool_result = await self._execute_tool(tool_config, context)
                if tool_result:
                    results.append(tool_result)
            
            # Step 3: Synthesize and prioritize findings
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {"stage": "agent_analysis", "step": "synthesizing_results"}
                )
            
            prioritized_results = await self._synthesize_results(results, context)
            
            # Step 4: Generate final recommendations
            final_recommendations = await self._generate_recommendations(
                prioritized_results, context
            )
            
            # Update analysis history for learning
            self.analysis_history.extend(prioritized_results)
            
            logger.info(
                f"Analysis completed for task {context.task_id}. "
                f"Found {len(prioritized_results)} issues across {len(selected_tools)} tools."
            )
            
            return prioritized_results
            
        except Exception as e:
            logger.error(f"Analysis failed for task {context.task_id}: {e}")
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "failed",
                    {"error": str(e), "stage": "agent_analysis"}
                )
            raise
    
    async def _select_analysis_tools(self, context: AgentContext) -> List[Dict[str, Any]]:
        """
        Use LLM to intelligently select appropriate analysis tools.
        
        Args:
            context: Analysis context
            
        Returns:
            List of tool configurations to execute
        """
        # Gather project context from vector store
        project_context = await self._gather_project_context(context)
        
        # Prepare LLM prompt for tool selection
        selection_prompt = f"""
        You are an expert code analysis agent. Based on the project context below, select the most appropriate analysis tools and playbooks.

        PROJECT CONTEXT:
        - Languages: {project_context.get('languages', [])}
        - File count: {project_context.get('file_count', 0)}
        - Project size: {project_context.get('total_size', 0)} bytes
        - Architecture patterns: {project_context.get('architecture_patterns', [])}
        - Complexity indicators: {project_context.get('complexity_indicators', [])}

        AVAILABLE TOOLS:
        1. static_analyzer - Detects code quality issues, complexity, maintainability
        2. dependency_analyzer - Analyzes dependencies, circular imports, version conflicts
        3. security_scanner - Identifies security vulnerabilities, hardcoded secrets
        4. complexity_analyzer - Measures cyclomatic complexity, cognitive load
        5. code_quality_checker - Validates coding standards and best practices
        6. performance_analyzer - Identifies performance bottlenecks and inefficiencies
        7. architecture_analyzer - Evaluates architectural patterns and design quality

        AVAILABLE PLAYBOOKS:
        1. god_classes - Detects oversized classes violating Single Responsibility Principle
        2. circular_dependencies - Identifies circular imports and dependency cycles
        3. high_complexity - Finds functions with excessive cyclomatic complexity
        4. dependency_health - Analyzes dependency versions and security issues
        5. hardcoded_secrets - Detects exposed credentials and sensitive information
        6. idor_vulnerabilities - Identifies Insecure Direct Object Reference vulnerabilities
        5. code_quality_checker - Checks coding standards, best practices
        6. performance_analyzer - Identifies performance bottlenecks, inefficiencies
        7. architecture_analyzer - Evaluates architectural patterns, design issues

        AVAILABLE PLAYBOOKS:
        1. god_classes - Detects overly complex classes (God Class anti-pattern)
        2. circular_dependencies - Finds circular import/dependency chains
        3. high_complexity - Identifies functions/methods with high complexity
        4. dependency_health - Analyzes dependency freshness and security
        5. hardcoded_secrets - Scans for exposed credentials and secrets
        6. idor_vulnerabilities - Checks for Insecure Direct Object References

        ANALYSIS REQUIREMENTS:
        {context.analysis_requirements}

        Please select 3-5 tools and 2-3 playbooks that would be most valuable for this project.
        Return a JSON array with tool/playbook configurations.

        Example format:
        [
            {{"name": "static_analyzer", "type": "tool", "priority": "high", "config": {{}}}},
            {{"name": "god_classes", "type": "playbook", "priority": "medium", "config": {{}}}}
        ]
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert code analysis tool selector."},
                    {"role": "user", "content": selection_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            selection_text = response.choices[0].message.content
            
            # Parse JSON response
            import re
            json_match = re.search(r'\[(.*?)\]', selection_text, re.DOTALL)
            if json_match:
                selection_json = '[' + json_match.group(1) + ']'
                selected_tools = json.loads(selection_json)
                return selected_tools
            else:
                # Fallback to default tool selection
                return self._get_default_tool_selection(project_context)
                
        except Exception as e:
            logger.warning(f"LLM tool selection failed: {e}. Using default selection.")
            return self._get_default_tool_selection(project_context)
    
    async def _gather_project_context(self, context: AgentContext) -> Dict[str, Any]:
        """Gather comprehensive project context from various sources."""
        project_context = context.project_info.copy()
        
        # Query vector store for code patterns
        try:
            # Search for common architectural patterns
            arch_queries = [
                "class definition inheritance",
                "import statements dependencies",
                "function complexity loops conditions",
                "database queries connections",
                "authentication authorization security"
            ]
            
            architecture_patterns = []
            complexity_indicators = []
            
            for query in arch_queries:
                results = self.vector_store.search(
                    context.vector_store_collection,
                    query,
                    k=5
                )
                
                if results:
                    if "class" in query or "inheritance" in query:
                        architecture_patterns.extend([r['metadata'].get('chunk_type', 'unknown') for r in results])
                    elif "complexity" in query:
                        complexity_indicators.extend([r['metadata'].get('file_path', '') for r in results])
            
            project_context.update({
                'architecture_patterns': list(set(architecture_patterns)),
                'complexity_indicators': list(set(complexity_indicators))
            })
            
        except Exception as e:
            logger.warning(f"Failed to gather extended project context: {e}")
        
        return project_context
    
    def _get_default_tool_selection(self, project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Provide default tool selection based on project characteristics."""
        languages = project_context.get('languages', [])
        file_count = project_context.get('file_count', 0)
        
        default_tools = [
            {"name": "static_analyzer", "type": "tool", "priority": "high", "config": {}},
            {"name": "complexity_analyzer", "type": "tool", "priority": "high", "config": {}},
            {"name": "god_classes", "type": "playbook", "priority": "medium", "config": {}}
        ]
        
        # Add language-specific tools
        if 'python' in languages:
            default_tools.extend([
                {"name": "dependency_analyzer", "type": "tool", "priority": "medium", "config": {}},
                {"name": "circular_dependencies", "type": "playbook", "priority": "medium", "config": {}}
            ])
        
        if 'javascript' in languages or 'typescript' in languages:
            default_tools.append(
                {"name": "security_scanner", "type": "tool", "priority": "high", "config": {}}
            )
        
        # Add security-focused tools for larger projects
        if file_count > 20:
            default_tools.extend([
                {"name": "security_scanner", "type": "tool", "priority": "high", "config": {}},
                {"name": "hardcoded_secrets", "type": "playbook", "priority": "high", "config": {}}
            ])
        
        return default_tools
    
    async def _execute_tool(
        self,
        tool_config: Dict[str, Any],
        context: AgentContext
    ) -> Optional[AnalysisResult]:
        """Execute a single analysis tool or playbook."""
        tool_name = tool_config["name"]
        tool_type = tool_config["type"]
        
        logger.info(f"Executing {tool_type}: {tool_name}")
        
        start_time = datetime.now()
        
        try:
            if tool_type == "tool":
                if tool_name in self.tools:
                    result = await self.tools[tool_name].analyze(context, tool_config.get("config", {}))
                else:
                    logger.warning(f"Tool {tool_name} not found in registry")
                    result = None
            elif tool_type == "playbook":
                if tool_name in self.playbooks:
                    result = await self.playbooks[tool_name].execute(context, tool_config.get("config", {}))
                else:
                    # Placeholder for playbook implementation
                    result = await self._mock_playbook_execution(tool_name, context)
            else:
                logger.warning(f"Unknown tool type: {tool_type}")
                return None
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result:
                result.execution_time = execution_time
                logger.info(f"Tool {tool_name} completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool {tool_name} failed after {execution_time:.2f}s: {e}")
            
            return AnalysisResult(
                tool_name=tool_name,
                playbook_name=tool_name if tool_type == "playbook" else None,
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title=f"{tool_name} execution failed",
                description=f"Tool execution failed: {str(e)}",
                findings=[],
                recommendations=[],
                confidence_score=0.0,
                execution_time=execution_time,
                metadata={"error": str(e), "tool_type": tool_type}
            )
    
    async def _mock_tool_execution(self, tool_name: str, context: AgentContext) -> AnalysisResult:
        """Mock tool execution for development purposes."""
        # This will be replaced by actual tool implementations
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return AnalysisResult(
            tool_name=tool_name,
            status=AnalysisStatus.COMPLETED,
            severity=SeverityLevel.MEDIUM,
            title=f"{tool_name} analysis completed",
            description=f"Mock analysis result from {tool_name}",
            findings=[
                {
                    "type": "mock_finding",
                    "file": "example.py",
                    "line": 42,
                    "message": f"Mock finding from {tool_name}"
                }
            ],
            recommendations=[
                f"Consider refactoring based on {tool_name} findings",
                f"Follow best practices recommended by {tool_name}"
            ],
            confidence_score=0.8,
            execution_time=0.0,
            metadata={"mock": True, "tool": tool_name}
        )
    
    async def _mock_playbook_execution(self, playbook_name: str, context: AgentContext) -> AnalysisResult:
        """Mock playbook execution for development purposes."""
        # This will be replaced by actual playbook implementations
        await asyncio.sleep(0.3)  # Simulate processing time
        
        return AnalysisResult(
            tool_name="playbook_executor",
            playbook_name=playbook_name,
            status=AnalysisStatus.COMPLETED,
            severity=SeverityLevel.HIGH,
            title=f"{playbook_name} playbook completed",
            description=f"Mock analysis result from {playbook_name} playbook",
            findings=[
                {
                    "type": "mock_playbook_finding",
                    "file": "example.py",
                    "class": "ExampleClass",
                    "message": f"Mock finding from {playbook_name} playbook"
                }
            ],
            recommendations=[
                f"Address {playbook_name} issues immediately",
                f"Review code patterns detected by {playbook_name}"
            ],
            confidence_score=0.9,
            execution_time=0.0,
            metadata={"mock": True, "playbook": playbook_name}
        )
    
    async def _synthesize_results(
        self,
        results: List[AnalysisResult],
        context: AgentContext
    ) -> List[AnalysisResult]:
        """Synthesize and prioritize analysis results."""
        if not results:
            return []
        
        # Sort by severity and confidence
        severity_order = {
            SeverityLevel.CRITICAL: 4,
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1
        }
        
        sorted_results = sorted(
            results,
            key=lambda r: (severity_order.get(r.severity, 0), r.confidence_score),
            reverse=True
        )
        
        # Add synthesis metadata
        for i, result in enumerate(sorted_results):
            result.metadata.update({
                "priority_rank": i + 1,
                "total_results": len(results),
                "synthesis_timestamp": datetime.now().isoformat()
            })
        
        return sorted_results
    
    async def _generate_recommendations(
        self,
        results: List[AnalysisResult],
        context: AgentContext
    ) -> List[str]:
        """Generate high-level recommendations based on all analysis results."""
        if not results:
            return ["No issues found. Code appears to be in good condition."]
        
        high_severity_count = sum(1 for r in results if r.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL])
        
        recommendations = []
        
        if high_severity_count > 0:
            recommendations.append(
                f"🚨 Priority: Address {high_severity_count} high/critical severity issues first"
            )
        
        # Tool-specific recommendations
        tool_counts = {}
        for result in results:
            tool_counts[result.tool_name] = tool_counts.get(result.tool_name, 0) + 1
        
        most_problematic_tool = max(tool_counts.items(), key=lambda x: x[1])
        if most_problematic_tool[1] > 1:
            recommendations.append(
                f"📊 Focus area: {most_problematic_tool[0]} found {most_problematic_tool[1]} issues"
            )
        
        recommendations.extend([
            "🔄 Regular code reviews and automated testing recommended",
            "📚 Consider establishing coding standards and guidelines",
            "🛠️ Implement continuous integration with code quality checks"
        ])
        
        return recommendations
    
    def register_tool(self, name: str, tool_instance: Any):
        """Register an analysis tool."""
        self.tools[name] = tool_instance
        logger.info(f"Registered analysis tool: {name}")
    
    def register_playbook(self, name: str, playbook_instance: Any):
        """Register an analysis playbook."""
        self.playbooks[name] = playbook_instance
        logger.info(f"Registered analysis playbook: {name}") 