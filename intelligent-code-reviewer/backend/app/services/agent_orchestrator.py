"""
Agent Orchestrator - Enhanced Tool Selection, Execution Coordination, and Result Aggregation.

This module provides intelligent orchestration capabilities for the AI Agent system,
including adaptive tool selection, parallel execution coordination, result synthesis,
and continuous learning from analysis patterns.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict, Counter

from .ai_agent import AIAgent, AgentContext, AnalysisResult, AnalysisStatus, SeverityLevel
from ..core.config import settings


logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """Tool execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    PRIORITY_BASED = "priority_based"


class ToolCategory(str, Enum):
    """Categories of analysis tools."""
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"
    COMPLEXITY = "complexity"


@dataclass
class ExecutionPlan:
    """Execution plan for tools and playbooks."""
    primary_tools: List[Dict[str, Any]]
    secondary_tools: List[Dict[str, Any]]
    playbooks: List[Dict[str, Any]]
    execution_strategy: ExecutionStrategy
    estimated_duration: float
    resource_requirements: Dict[str, Any]
    dependencies: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class OrchestrationMetrics:
    """Metrics for orchestration performance and learning."""
    execution_time: float
    tool_success_rate: float
    finding_quality_score: float
    user_satisfaction: Optional[float] = None
    false_positive_rate: Optional[float] = None
    coverage_score: float = 0.0


class AgentOrchestrator:
    """
    Enhanced orchestrator for intelligent tool selection, execution coordination,
    and result aggregation with learning capabilities.
    """
    
    def __init__(self, ai_agent: AIAgent):
        """Initialize the agent orchestrator."""
        self.ai_agent = ai_agent
        
        # Tool categorization and metadata
        self.tool_metadata = self._initialize_tool_metadata()
        
        # Execution history for learning
        self.execution_history: List[Dict[str, Any]] = []
        
        # Performance metrics by tool
        self.tool_performance: Dict[str, List[float]] = defaultdict(list)
        
        # Tool compatibility matrix
        self.tool_compatibility = self._initialize_tool_compatibility()
        
        # Learning weights for different factors
        self.learning_weights = {
            "historical_success": 0.3,
            "project_characteristics": 0.4,
            "tool_performance": 0.2,
            "user_feedback": 0.1
        }
        
        logger.info("Agent Orchestrator initialized with enhanced capabilities")
    
    def _initialize_tool_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive tool metadata."""
        return {
            # Analysis Tools
            "static_analyzer": {
                "category": ToolCategory.QUALITY,
                "estimated_duration": 30,
                "resource_level": "medium",
                "languages": ["python", "javascript", "typescript", "java"],
                "prerequisites": [],
                "outputs": ["code_quality", "maintainability"],
                "confidence_baseline": 0.85
            },
            "dependency_analyzer": {
                "category": ToolCategory.DEPENDENCIES,
                "estimated_duration": 15,
                "resource_level": "low",
                "languages": ["python", "javascript", "typescript", "java"],
                "prerequisites": [],
                "outputs": ["dependencies", "imports"],
                "confidence_baseline": 0.90
            },
            "security_scanner": {
                "category": ToolCategory.SECURITY,
                "estimated_duration": 45,
                "resource_level": "high",
                "languages": ["all"],
                "prerequisites": [],
                "outputs": ["vulnerabilities", "security_issues"],
                "confidence_baseline": 0.88
            },
            "complexity_analyzer": {
                "category": ToolCategory.COMPLEXITY,
                "estimated_duration": 20,
                "resource_level": "low",
                "languages": ["python", "javascript", "typescript", "java", "c++"],
                "prerequisites": [],
                "outputs": ["complexity_metrics"],
                "confidence_baseline": 0.92
            },
            "code_quality_checker": {
                "category": ToolCategory.QUALITY,
                "estimated_duration": 25,
                "resource_level": "medium",
                "languages": ["python", "javascript", "typescript"],
                "prerequisites": [],
                "outputs": ["style_issues", "best_practices"],
                "confidence_baseline": 0.87
            },
            "performance_analyzer": {
                "category": ToolCategory.PERFORMANCE,
                "estimated_duration": 35,
                "resource_level": "medium",
                "languages": ["python", "javascript", "typescript", "java"],
                "prerequisites": [],
                "outputs": ["performance_issues"],
                "confidence_baseline": 0.83
            },
            "architecture_analyzer": {
                "category": ToolCategory.ARCHITECTURE,
                "estimated_duration": 40,
                "resource_level": "high",
                "languages": ["all"],
                "prerequisites": [],
                "outputs": ["architecture_issues", "design_patterns"],
                "confidence_baseline": 0.80
            },
            
            # Analysis Playbooks
            "god_classes": {
                "category": ToolCategory.ARCHITECTURE,
                "estimated_duration": 20,
                "resource_level": "medium",
                "languages": ["python", "java", "c#"],
                "prerequisites": ["static_analyzer"],
                "outputs": ["class_violations"],
                "confidence_baseline": 0.90
            },
            "circular_dependencies": {
                "category": ToolCategory.DEPENDENCIES,
                "estimated_duration": 15,
                "resource_level": "low",
                "languages": ["python", "javascript", "typescript"],
                "prerequisites": ["dependency_analyzer"],
                "outputs": ["circular_imports"],
                "confidence_baseline": 0.95
            },
            "high_complexity": {
                "category": ToolCategory.COMPLEXITY,
                "estimated_duration": 18,
                "resource_level": "low",
                "languages": ["all"],
                "prerequisites": ["complexity_analyzer"],
                "outputs": ["complex_functions"],
                "confidence_baseline": 0.92
            },
            "dependency_health": {
                "category": ToolCategory.DEPENDENCIES,
                "estimated_duration": 25,
                "resource_level": "medium",
                "languages": ["python", "javascript", "typescript"],
                "prerequisites": [],
                "outputs": ["dependency_issues"],
                "confidence_baseline": 0.85
            },
            "hardcoded_secrets": {
                "category": ToolCategory.SECURITY,
                "estimated_duration": 30,
                "resource_level": "medium",
                "languages": ["all"],
                "prerequisites": [],
                "outputs": ["exposed_secrets"],
                "confidence_baseline": 0.95
            },
            "idor_vulnerabilities": {
                "category": ToolCategory.SECURITY,
                "estimated_duration": 35,
                "resource_level": "high",
                "languages": ["python", "javascript", "typescript", "java", "php"],
                "prerequisites": [],
                "outputs": ["authorization_issues"],
                "confidence_baseline": 0.88
            }
        }
    
    def _initialize_tool_compatibility(self) -> Dict[str, Dict[str, float]]:
        """Initialize tool compatibility matrix for parallel execution."""
        # Tools that work well together (synergy scores)
        compatibility = defaultdict(lambda: defaultdict(float))
        
        # High compatibility pairs
        high_synergy = [
            ("static_analyzer", "code_quality_checker"),
            ("dependency_analyzer", "circular_dependencies"),
            ("security_scanner", "hardcoded_secrets"),
            ("complexity_analyzer", "high_complexity"),
            ("static_analyzer", "god_classes"),
            ("security_scanner", "idor_vulnerabilities")
        ]
        
        for tool1, tool2 in high_synergy:
            compatibility[tool1][tool2] = 0.9
            compatibility[tool2][tool1] = 0.9
        
        # Medium compatibility (same category tools)
        categories = defaultdict(list)
        for tool, metadata in self.tool_metadata.items():
            categories[metadata["category"]].append(tool)
        
        for category_tools in categories.values():
            for i, tool1 in enumerate(category_tools):
                for tool2 in category_tools[i+1:]:
                    if compatibility[tool1][tool2] == 0:  # Don't override high synergy
                        compatibility[tool1][tool2] = 0.6
                        compatibility[tool2][tool1] = 0.6
        
        return compatibility
    
    async def orchestrate_analysis(
        self,
        context: AgentContext,
        execution_strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE,
        db_service: Any = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[AnalysisResult], OrchestrationMetrics]:
        """
        Orchestrate comprehensive analysis with intelligent tool selection and execution.
        
        Args:
            context: Analysis context
            execution_strategy: Strategy for tool execution
            db_service: Database service for progress tracking
            user_preferences: User-specific preferences and constraints
            
        Returns:
            Tuple of analysis results and orchestration metrics
        """
        start_time = datetime.now()
        logger.info(f"Starting orchestrated analysis for task {context.task_id}")
        
        try:
            # Phase 1: Intelligent Tool Selection
            execution_plan = await self._create_execution_plan(
                context, execution_strategy, user_preferences
            )
            
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {
                        "stage": "orchestration_planning",
                        "tools_selected": len(execution_plan.primary_tools + execution_plan.secondary_tools),
                        "playbooks_selected": len(execution_plan.playbooks),
                        "estimated_duration": execution_plan.estimated_duration
                    }
                )
            
            # Phase 2: Coordinated Execution
            results = await self._execute_coordinated_analysis(
                execution_plan, context, db_service
            )
            
            # Phase 3: Intelligent Result Aggregation
            aggregated_results = await self._aggregate_and_prioritize_results(
                results, context, execution_plan
            )
            
            # Phase 4: Calculate Orchestration Metrics
            end_time = datetime.now()
            metrics = self._calculate_orchestration_metrics(
                aggregated_results, execution_plan, start_time, end_time
            )
            
            # Phase 5: Learn from Execution
            await self._update_learning_models(
                context, execution_plan, aggregated_results, metrics
            )
            
            logger.info(
                f"Orchestrated analysis completed for task {context.task_id}. "
                f"Executed {len(results)} tools/playbooks in {metrics.execution_time:.1f}s"
            )
            
            return aggregated_results, metrics
            
        except Exception as e:
            logger.error(f"Orchestrated analysis failed for task {context.task_id}: {e}")
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "failed",
                    {"error": str(e), "stage": "orchestration"}
                )
            raise
    
    async def _create_execution_plan(
        self,
        context: AgentContext,
        strategy: ExecutionStrategy,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """Create an intelligent execution plan based on context and learning."""
        logger.info(f"Creating execution plan for task {context.task_id}")
        
        # Analyze project characteristics
        project_characteristics = self._analyze_project_characteristics(context)
        
        # Get tool recommendations from historical data
        historical_recommendations = self._get_historical_recommendations(
            project_characteristics
        )
        
        # Apply intelligent selection algorithm
        selected_tools = await self._select_optimal_tools(
            context, project_characteristics, historical_recommendations, user_preferences
        )
        
        # Categorize tools by priority
        primary_tools = [t for t in selected_tools if t.get("priority") == "high"]
        secondary_tools = [t for t in selected_tools if t.get("priority") in ["medium", "low"]]
        
        # Select complementary playbooks
        playbooks = self._select_complementary_playbooks(selected_tools, project_characteristics)
        
        # Determine execution strategy
        execution_strategy = self._determine_execution_strategy(
            strategy, selected_tools, project_characteristics
        )
        
        # Calculate resource requirements and duration
        estimated_duration = self._estimate_execution_duration(
            selected_tools + playbooks, execution_strategy
        )
        
        resource_requirements = self._calculate_resource_requirements(
            selected_tools + playbooks
        )
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(selected_tools + playbooks)
        
        return ExecutionPlan(
            primary_tools=primary_tools,
            secondary_tools=secondary_tools,
            playbooks=playbooks,
            execution_strategy=execution_strategy,
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements,
            dependencies=dependencies
        )
    
    def _analyze_project_characteristics(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze project characteristics for intelligent tool selection."""
        project_info = context.project_info
        
        characteristics = {
            "languages": project_info.get("languages", []),
            "file_count": project_info.get("file_count", 0),
            "project_size": project_info.get("total_size", 0),
            "complexity_score": self._calculate_project_complexity_score(project_info),
            "has_tests": any("test" in lang.lower() for lang in project_info.get("file_types", [])),
            "has_dependencies": any(
                dep_file in str(project_info.get("file_structure", ""))
                for dep_file in ["package.json", "requirements.txt", "pom.xml"]
            ),
            "framework_patterns": self._detect_framework_patterns(project_info),
            "architecture_patterns": self._detect_architecture_patterns(project_info)
        }
        
        return characteristics
    
    def _calculate_project_complexity_score(self, project_info: Dict[str, Any]) -> float:
        """Calculate a complexity score for the project."""
        file_count = project_info.get("file_count", 0)
        size = project_info.get("total_size", 0)
        languages = len(project_info.get("languages", []))
        
        # Normalize factors
        file_score = min(file_count / 100, 1.0)  # Cap at 100 files
        size_score = min(size / (10 * 1024 * 1024), 1.0)  # Cap at 10MB
        lang_score = min(languages / 5, 1.0)  # Cap at 5 languages
        
        return (file_score + size_score + lang_score) / 3
    
    def _detect_framework_patterns(self, project_info: Dict[str, Any]) -> List[str]:
        """Detect framework patterns in the project."""
        patterns = []
        file_structure = str(project_info.get("file_structure", "")).lower()
        
        framework_indicators = {
            "django": ["manage.py", "settings.py", "urls.py"],
            "flask": ["app.py", "flask"],
            "react": ["package.json", "react"],
            "vue": ["vue.config.js", "vue"],
            "spring": ["pom.xml", "spring"],
            "express": ["package.json", "express"]
        }
        
        for framework, indicators in framework_indicators.items():
            if any(indicator in file_structure for indicator in indicators):
                patterns.append(framework)
        
        return patterns
    
    def _detect_architecture_patterns(self, project_info: Dict[str, Any]) -> List[str]:
        """Detect architectural patterns in the project."""
        patterns = []
        file_structure = str(project_info.get("file_structure", "")).lower()
        
        arch_indicators = {
            "mvc": ["models", "views", "controllers"],
            "microservices": ["services", "api"],
            "layered": ["data", "business", "presentation"],
            "clean_architecture": ["domain", "infrastructure", "application"]
        }
        
        for pattern, indicators in arch_indicators.items():
            if sum(indicator in file_structure for indicator in indicators) >= 2:
                patterns.append(pattern)
        
        return patterns
    
    def _get_historical_recommendations(
        self, 
        project_characteristics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Get tool recommendations based on historical execution data."""
        recommendations = defaultdict(float)
        
        # Analyze historical success patterns
        for execution in self.execution_history:
            similarity = self._calculate_characteristic_similarity(
                project_characteristics, execution.get("project_characteristics", {})
            )
            
            if similarity > 0.6:  # Only consider similar projects
                for tool_result in execution.get("results", []):
                    tool_name = tool_result.get("tool_name")
                    success_score = (
                        tool_result.get("confidence_score", 0) * 
                        similarity * 
                        (1 if tool_result.get("status") == "completed" else 0)
                    )
                    recommendations[tool_name] += success_score
        
        # Normalize scores
        if recommendations:
            max_score = max(recommendations.values())
            if max_score > 0:
                recommendations = {
                    tool: score / max_score 
                    for tool, score in recommendations.items()
                }
        
        return recommendations
    
    def _calculate_characteristic_similarity(
        self, 
        char1: Dict[str, Any], 
        char2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between project characteristics."""
        similarities = []
        
        # Language similarity
        lang1 = set(char1.get("languages", []))
        lang2 = set(char2.get("languages", []))
        if lang1 or lang2:
            lang_sim = len(lang1 & lang2) / len(lang1 | lang2) if (lang1 | lang2) else 0
            similarities.append(lang_sim)
        
        # Size similarity (normalized)
        size1 = char1.get("project_size", 0)
        size2 = char2.get("project_size", 0)
        if size1 > 0 and size2 > 0:
            size_sim = 1 - abs(size1 - size2) / max(size1, size2)
            similarities.append(size_sim)
        
        # Complexity similarity
        comp1 = char1.get("complexity_score", 0)
        comp2 = char2.get("complexity_score", 0)
        comp_sim = 1 - abs(comp1 - comp2)
        similarities.append(comp_sim)
        
        return statistics.mean(similarities) if similarities else 0.0
    
    async def _select_optimal_tools(
        self,
        context: AgentContext,
        project_characteristics: Dict[str, Any],
        historical_recommendations: Dict[str, float],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Select optimal tools using intelligent scoring algorithm."""
        tool_scores = {}
        
        # Get project languages for filtering
        project_languages = [lang.lower() for lang in project_characteristics.get("languages", [])]
        
        for tool_name, metadata in self.tool_metadata.items():
            # Calculate base compatibility score
            lang_compatibility = self._calculate_language_compatibility(
                metadata["languages"], project_languages
            )
            
            if lang_compatibility == 0:
                continue  # Skip incompatible tools
            
            # Factor in historical performance
            historical_score = historical_recommendations.get(tool_name, 0.5)
            
            # Factor in tool performance metrics
            performance_score = statistics.mean(self.tool_performance.get(tool_name, [0.8]))
            
            # Factor in user preferences
            preference_score = 1.0
            if user_preferences:
                if tool_name in user_preferences.get("preferred_tools", []):
                    preference_score = 1.2
                elif tool_name in user_preferences.get("excluded_tools", []):
                    preference_score = 0.0
            
            # Calculate weighted score
            final_score = (
                lang_compatibility * 0.3 +
                historical_score * self.learning_weights["historical_success"] +
                performance_score * self.learning_weights["tool_performance"] +
                preference_score * self.learning_weights["user_feedback"]
            )
            
            tool_scores[tool_name] = final_score
        
        # Select top tools and assign priorities
        sorted_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        
        selected_tools = []
        for i, (tool_name, score) in enumerate(sorted_tools[:8]):  # Limit to 8 tools
            if score > 0.4:  # Minimum threshold
                priority = "high" if i < 3 else "medium" if i < 6 else "low"
                
                selected_tools.append({
                    "name": tool_name,
                    "type": "playbook" if tool_name in self.ai_agent.playbooks else "tool",
                    "priority": priority,
                    "score": score,
                    "config": {}
                })
        
        return selected_tools
    
    def _calculate_language_compatibility(
        self, 
        tool_languages: List[str], 
        project_languages: List[str]
    ) -> float:
        """Calculate compatibility between tool and project languages."""
        if "all" in tool_languages:
            return 1.0
        
        if not project_languages:
            return 0.5  # Neutral for unknown languages
        
        tool_langs = set(lang.lower() for lang in tool_languages)
        proj_langs = set(project_languages)
        
        if tool_langs & proj_langs:
            return len(tool_langs & proj_langs) / len(proj_langs)
        
        return 0.0
    
    def _select_complementary_playbooks(
        self, 
        selected_tools: List[Dict[str, Any]], 
        project_characteristics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select playbooks that complement the selected tools."""
        playbooks = []
        selected_tool_names = set(tool["name"] for tool in selected_tools)
        
        # Check for tools with prerequisite playbooks
        for tool in selected_tools:
            tool_name = tool["name"]
            if tool_name in self.tool_metadata:
                prerequisites = self.tool_metadata[tool_name].get("prerequisites", [])
                for prereq in prerequisites:
                    if prereq not in selected_tool_names and prereq in self.ai_agent.playbooks:
                        playbooks.append({
                            "name": prereq,
                            "type": "playbook",
                            "priority": "medium",
                            "config": {},
                            "triggered_by": tool_name
                        })
        
        # Add high-value security playbooks for any project
        security_playbooks = ["hardcoded_secrets", "idor_vulnerabilities"]
        for playbook in security_playbooks:
            if playbook not in [p["name"] for p in playbooks] and playbook not in selected_tool_names:
                playbooks.append({
                    "name": playbook,
                    "type": "playbook",
                    "priority": "high",
                    "config": {}
                })
        
        return playbooks[:4]  # Limit to 4 playbooks
    
    def _determine_execution_strategy(
        self,
        requested_strategy: ExecutionStrategy,
        selected_tools: List[Dict[str, Any]],
        project_characteristics: Dict[str, Any]
    ) -> ExecutionStrategy:
        """Determine optimal execution strategy based on context."""
        if requested_strategy == ExecutionStrategy.ADAPTIVE:
            # Choose strategy based on project characteristics
            file_count = project_characteristics.get("file_count", 0)
            complexity_score = project_characteristics.get("complexity_score", 0)
            
            if file_count > 50 or complexity_score > 0.7:
                return ExecutionStrategy.PARALLEL
            elif len(selected_tools) > 5:
                return ExecutionStrategy.PRIORITY_BASED
            else:
                return ExecutionStrategy.SEQUENTIAL
        
        return requested_strategy
    
    def _estimate_execution_duration(
        self, 
        tools: List[Dict[str, Any]], 
        strategy: ExecutionStrategy
    ) -> float:
        """Estimate total execution duration in seconds."""
        durations = []
        
        for tool in tools:
            tool_name = tool["name"]
            base_duration = self.tool_metadata.get(tool_name, {}).get("estimated_duration", 30)
            
            # Adjust based on historical performance
            avg_performance = statistics.mean(self.tool_performance.get(tool_name, [1.0]))
            adjusted_duration = base_duration * (2 - avg_performance)  # Better performance = faster
            
            durations.append(adjusted_duration)
        
        if strategy == ExecutionStrategy.PARALLEL:
            # Parallel execution: max duration + coordination overhead
            return max(durations) * 1.2 if durations else 0
        elif strategy == ExecutionStrategy.PRIORITY_BASED:
            # Priority-based: sequential for high priority, parallel for others
            high_priority = [d for tool, d in zip(tools, durations) if tool.get("priority") == "high"]
            others = [d for tool, d in zip(tools, durations) if tool.get("priority") != "high"]
            
            high_total = sum(high_priority)
            others_max = max(others) if others else 0
            
            return high_total + others_max
        else:
            # Sequential execution
            return sum(durations)
    
    def _calculate_resource_requirements(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate resource requirements for the execution plan."""
        resource_levels = Counter()
        
        for tool in tools:
            tool_name = tool["name"]
            level = self.tool_metadata.get(tool_name, {}).get("resource_level", "medium")
            resource_levels[level] += 1
        
        return {
            "memory_estimate": resource_levels["high"] * 512 + resource_levels["medium"] * 256 + resource_levels["low"] * 128,
            "cpu_estimate": resource_levels["high"] * 2 + resource_levels["medium"] * 1 + resource_levels["low"] * 0.5,
            "io_intensive": resource_levels["high"] > 2,
            "parallel_safe": resource_levels["high"] < 3
        }
    
    def _build_dependency_graph(self, tools: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build dependency graph for tool execution order."""
        dependencies = {}
        
        for tool in tools:
            tool_name = tool["name"]
            prerequisites = self.tool_metadata.get(tool_name, {}).get("prerequisites", [])
            
            # Only include prerequisites that are in the selected tools
            selected_tool_names = [t["name"] for t in tools]
            valid_prereqs = [prereq for prereq in prerequisites if prereq in selected_tool_names]
            
            if valid_prereqs:
                dependencies[tool_name] = valid_prereqs
        
        return dependencies
    
    async def _execute_coordinated_analysis(
        self,
        execution_plan: ExecutionPlan,
        context: AgentContext,
        db_service: Any = None
    ) -> List[AnalysisResult]:
        """Execute analysis using the coordination strategy."""
        logger.info(f"Executing coordinated analysis with strategy: {execution_plan.execution_strategy}")
        
        all_tools = execution_plan.primary_tools + execution_plan.secondary_tools + execution_plan.playbooks
        
        if execution_plan.execution_strategy == ExecutionStrategy.PARALLEL:
            return await self._execute_parallel(all_tools, context, db_service)
        elif execution_plan.execution_strategy == ExecutionStrategy.PRIORITY_BASED:
            return await self._execute_priority_based(execution_plan, context, db_service)
        else:
            return await self._execute_sequential(all_tools, context, db_service)
    
    async def _execute_parallel(
        self,
        tools: List[Dict[str, Any]],
        context: AgentContext,
        db_service: Any = None
    ) -> List[AnalysisResult]:
        """Execute tools in parallel with dependency resolution."""
        results = []
        
        # Group tools by dependency level
        dependency_levels = self._resolve_dependency_order(tools)
        
        for level, level_tools in enumerate(dependency_levels):
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {
                        "stage": "parallel_execution",
                        "level": level + 1,
                        "tools_in_level": len(level_tools)
                    }
                )
            
            # Execute tools in current level in parallel
            tasks = []
            for tool_config in level_tools:
                task = self._execute_single_tool(tool_config, context)
                tasks.append(task)
            
            level_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in level_results:
                if isinstance(result, Exception):
                    logger.error(f"Tool execution failed: {result}")
                elif result:
                    results.append(result)
        
        return results
    
    async def _execute_priority_based(
        self,
        execution_plan: ExecutionPlan,
        context: AgentContext,
        db_service: Any = None
    ) -> List[AnalysisResult]:
        """Execute tools based on priority levels."""
        results = []
        
        # Execute high priority tools sequentially first
        for tool_config in execution_plan.primary_tools:
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {"stage": "high_priority_execution", "tool": tool_config["name"]}
                )
            
            result = await self._execute_single_tool(tool_config, context)
            if result:
                results.append(result)
        
        # Execute medium/low priority tools in parallel
        secondary_tasks = []
        for tool_config in execution_plan.secondary_tools + execution_plan.playbooks:
            task = self._execute_single_tool(tool_config, context)
            secondary_tasks.append(task)
        
        if secondary_tasks:
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {"stage": "secondary_execution", "tools": len(secondary_tasks)}
                )
            
            secondary_results = await asyncio.gather(*secondary_tasks, return_exceptions=True)
            
            for result in secondary_results:
                if isinstance(result, Exception):
                    logger.error(f"Secondary tool execution failed: {result}")
                elif result:
                    results.append(result)
        
        return results
    
    async def _execute_sequential(
        self,
        tools: List[Dict[str, Any]],
        context: AgentContext,
        db_service: Any = None
    ) -> List[AnalysisResult]:
        """Execute tools sequentially in dependency order."""
        results = []
        ordered_tools = self._topological_sort(tools)
        
        for i, tool_config in enumerate(ordered_tools):
            if db_service:
                await db_service.update_job_status(
                    context.task_id,
                    "in_progress",
                    {
                        "stage": "sequential_execution",
                        "tool": tool_config["name"],
                        "progress": f"{i+1}/{len(ordered_tools)}"
                    }
                )
            
            result = await self._execute_single_tool(tool_config, context)
            if result:
                results.append(result)
        
        return results
    
    async def _execute_single_tool(
        self,
        tool_config: Dict[str, Any],
        context: AgentContext
    ) -> Optional[AnalysisResult]:
        """Execute a single tool and track performance."""
        tool_name = tool_config["name"]
        start_time = datetime.now()
        
        try:
            result = await self.ai_agent._execute_tool(tool_config, context)
            
            if result:
                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                confidence_score = result.confidence_score
                success = result.status == AnalysisStatus.COMPLETED
                
                performance_score = confidence_score if success else 0.0
                self.tool_performance[tool_name].append(performance_score)
                
                # Keep only recent performance data
                if len(self.tool_performance[tool_name]) > 10:
                    self.tool_performance[tool_name] = self.tool_performance[tool_name][-10:]
            
            return result
            
        except Exception as e:
            logger.error(f"Single tool execution failed for {tool_name}: {e}")
            return None
    
    def _resolve_dependency_order(self, tools: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Resolve tools into dependency levels for parallel execution."""
        levels = []
        remaining_tools = tools.copy()
        completed_tools = set()
        
        while remaining_tools:
            current_level = []
            
            for tool in remaining_tools[:]:
                tool_name = tool["name"]
                prerequisites = self.tool_metadata.get(tool_name, {}).get("prerequisites", [])
                
                if all(prereq in completed_tools for prereq in prerequisites):
                    current_level.append(tool)
                    remaining_tools.remove(tool)
                    completed_tools.add(tool_name)
            
            if not current_level and remaining_tools:
                # Circular dependency or unsatisfied dependency - add remaining tools
                current_level = remaining_tools[:]
                remaining_tools = []
                for tool in current_level:
                    completed_tools.add(tool["name"])
            
            if current_level:
                levels.append(current_level)
        
        return levels
    
    def _topological_sort(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Topologically sort tools based on dependencies."""
        from collections import deque
        
        # Build dependency graph
        graph = {tool["name"]: [] for tool in tools}
        in_degree = {tool["name"]: 0 for tool in tools}
        tool_map = {tool["name"]: tool for tool in tools}
        
        for tool in tools:
            tool_name = tool["name"]
            prerequisites = self.tool_metadata.get(tool_name, {}).get("prerequisites", [])
            
            for prereq in prerequisites:
                if prereq in graph:
                    graph[prereq].append(tool_name)
                    in_degree[tool_name] += 1
        
        # Kahn's algorithm
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(tool_map[current])
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Add any remaining tools (circular dependencies)
        remaining = [tool for tool in tools if tool["name"] not in [r["name"] for r in result]]
        result.extend(remaining)
        
        return result
    
    async def _aggregate_and_prioritize_results(
        self,
        results: List[AnalysisResult],
        context: AgentContext,
        execution_plan: ExecutionPlan
    ) -> List[AnalysisResult]:
        """Aggregate and intelligently prioritize analysis results."""
        if not results:
            return []
        
        # Remove duplicates and merge similar findings
        deduplicated_results = self._deduplicate_findings(results)
        
        # Enhance results with cross-tool correlation
        correlated_results = self._correlate_findings(deduplicated_results)
        
        # Apply intelligent prioritization
        prioritized_results = self._apply_intelligent_prioritization(
            correlated_results, context, execution_plan
        )
        
        # Add aggregation metadata
        for i, result in enumerate(prioritized_results):
            result.metadata.update({
                "aggregation_rank": i + 1,
                "total_results": len(prioritized_results),
                "correlation_score": result.metadata.get("correlation_score", 0.0),
                "aggregation_timestamp": datetime.now().isoformat()
            })
        
        return prioritized_results
    
    def _deduplicate_findings(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """Remove duplicate findings across different tools."""
        unique_results = []
        seen_findings = set()
        
        for result in results:
            unique_findings = []
            
            for finding in result.findings:
                # Create a signature for the finding
                signature = (
                    finding.get("file", ""),
                    finding.get("line", 0),
                    finding.get("type", ""),
                    finding.get("message", "")[:50]  # First 50 chars
                )
                
                if signature not in seen_findings:
                    seen_findings.add(signature)
                    unique_findings.append(finding)
            
            if unique_findings:
                result.findings = unique_findings
                unique_results.append(result)
        
        return unique_results
    
    def _correlate_findings(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """Correlate findings across different tools for enhanced insights."""
        for result in results:
            correlation_score = 0.0
            correlations = []
            
            for other_result in results:
                if other_result.tool_name != result.tool_name:
                    correlation = self._calculate_finding_correlation(result, other_result)
                    if correlation > 0.3:
                        correlations.append({
                            "tool": other_result.tool_name,
                            "correlation": correlation
                        })
                        correlation_score += correlation
            
            result.metadata.update({
                "correlation_score": correlation_score,
                "correlations": correlations[:3]  # Top 3 correlations
            })
        
        return results
    
    def _calculate_finding_correlation(
        self, 
        result1: AnalysisResult, 
        result2: AnalysisResult
    ) -> float:
        """Calculate correlation between findings from different tools."""
        # File overlap
        files1 = set(f.get("file", "") for f in result1.findings)
        files2 = set(f.get("file", "") for f in result2.findings)
        
        if not files1 or not files2:
            return 0.0
        
        file_overlap = len(files1 & files2) / len(files1 | files2)
        
        # Severity correlation
        severity_correlation = 0.0
        if result1.severity == result2.severity:
            severity_correlation = 0.5
        
        # Category correlation (if both tools are in same category)
        category1 = self.tool_metadata.get(result1.tool_name, {}).get("category")
        category2 = self.tool_metadata.get(result2.tool_name, {}).get("category")
        category_correlation = 0.3 if category1 == category2 else 0.0
        
        return file_overlap * 0.5 + severity_correlation + category_correlation
    
    def _apply_intelligent_prioritization(
        self,
        results: List[AnalysisResult],
        context: AgentContext,
        execution_plan: ExecutionPlan
    ) -> List[AnalysisResult]:
        """Apply intelligent prioritization based on multiple factors."""
        # Score each result
        scored_results = []
        
        for result in results:
            priority_score = self._calculate_priority_score(result, context, execution_plan)
            scored_results.append((result, priority_score))
        
        # Sort by priority score (descending)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [result for result, _ in scored_results]
    
    def _calculate_priority_score(
        self,
        result: AnalysisResult,
        context: AgentContext,
        execution_plan: ExecutionPlan
    ) -> float:
        """Calculate priority score for a result."""
        # Base score from severity
        severity_scores = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4
        }
        base_score = severity_scores.get(result.severity, 0.5)
        
        # Confidence modifier
        confidence_modifier = result.confidence_score
        
        # Correlation bonus
        correlation_bonus = min(result.metadata.get("correlation_score", 0.0) * 0.1, 0.2)
        
        # Tool priority modifier
        tool_metadata = self.tool_metadata.get(result.tool_name, {})
        tool_confidence = tool_metadata.get("confidence_baseline", 0.8)
        
        # Findings count modifier
        findings_modifier = min(len(result.findings) * 0.05, 0.2)
        
        # Calculate final score
        priority_score = (
            base_score * 0.4 +
            confidence_modifier * 0.3 +
            tool_confidence * 0.2 +
            correlation_bonus +
            findings_modifier
        )
        
        return priority_score
    
    def _calculate_orchestration_metrics(
        self,
        results: List[AnalysisResult],
        execution_plan: ExecutionPlan,
        start_time: datetime,
        end_time: datetime
    ) -> OrchestrationMetrics:
        """Calculate comprehensive orchestration metrics."""
        execution_time = (end_time - start_time).total_seconds()
        
        # Tool success rate
        total_tools = len(execution_plan.primary_tools + execution_plan.secondary_tools + execution_plan.playbooks)
        successful_tools = len([r for r in results if r.status == AnalysisStatus.COMPLETED])
        tool_success_rate = successful_tools / total_tools if total_tools > 0 else 0.0
        
        # Finding quality score
        if results:
            avg_confidence = statistics.mean([r.confidence_score for r in results])
            finding_quality_score = avg_confidence
        else:
            finding_quality_score = 0.0
        
        # Coverage score (categories covered)
        categories_covered = set()
        for result in results:
            tool_metadata = self.tool_metadata.get(result.tool_name, {})
            category = tool_metadata.get("category")
            if category:
                categories_covered.add(category)
        
        total_categories = len(set(metadata.get("category") for metadata in self.tool_metadata.values()))
        coverage_score = len(categories_covered) / total_categories if total_categories > 0 else 0.0
        
        return OrchestrationMetrics(
            execution_time=execution_time,
            tool_success_rate=tool_success_rate,
            finding_quality_score=finding_quality_score,
            coverage_score=coverage_score
        )
    
    async def _update_learning_models(
        self,
        context: AgentContext,
        execution_plan: ExecutionPlan,
        results: List[AnalysisResult],
        metrics: OrchestrationMetrics
    ):
        """Update learning models based on execution results."""
        # Store execution history
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": context.task_id,
            "project_characteristics": self._analyze_project_characteristics(context),
            "execution_plan": {
                "tools": [t["name"] for t in execution_plan.primary_tools + execution_plan.secondary_tools],
                "playbooks": [p["name"] for p in execution_plan.playbooks],
                "strategy": execution_plan.execution_strategy.value
            },
            "results": [
                {
                    "tool_name": r.tool_name,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "confidence_score": r.confidence_score,
                    "findings_count": len(r.findings)
                }
                for r in results
            ],
            "metrics": {
                "execution_time": metrics.execution_time,
                "tool_success_rate": metrics.tool_success_rate,
                "finding_quality_score": metrics.finding_quality_score,
                "coverage_score": metrics.coverage_score
            }
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only recent history (last 100 executions)
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        logger.info(f"Updated learning models with execution data for task {context.task_id}")
    
    def get_orchestration_insights(self) -> Dict[str, Any]:
        """Get insights from orchestration history for system optimization."""
        if not self.execution_history:
            return {"message": "No execution history available"}
        
        # Analyze tool effectiveness
        tool_effectiveness = defaultdict(list)
        for execution in self.execution_history:
            for result in execution["results"]:
                effectiveness = result["confidence_score"] if result["status"] == "completed" else 0.0
                tool_effectiveness[result["tool_name"]].append(effectiveness)
        
        # Calculate average effectiveness per tool
        avg_effectiveness = {
            tool: statistics.mean(scores) 
            for tool, scores in tool_effectiveness.items()
        }
        
        # Find best performing tool combinations
        combination_performance = defaultdict(list)
        for execution in self.execution_history:
            tools = tuple(sorted(r["tool_name"] for r in execution["results"]))
            if len(tools) > 1:
                quality_score = execution["metrics"]["finding_quality_score"]
                combination_performance[tools].append(quality_score)
        
        best_combinations = []
        for combination, scores in combination_performance.items():
            if len(scores) >= 3:  # At least 3 executions
                avg_score = statistics.mean(scores)
                best_combinations.append((combination, avg_score))
        
        best_combinations.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "total_executions": len(self.execution_history),
            "tool_effectiveness": dict(sorted(avg_effectiveness.items(), key=lambda x: x[1], reverse=True)),
            "best_tool_combinations": best_combinations[:5],
            "avg_execution_time": statistics.mean([e["metrics"]["execution_time"] for e in self.execution_history]),
            "avg_success_rate": statistics.mean([e["metrics"]["tool_success_rate"] for e in self.execution_history]),
            "avg_coverage": statistics.mean([e["metrics"]["coverage_score"] for e in self.execution_history])
        } 