#!/usr/bin/env python3
"""
Manual Analysis Testing Script

This script allows you to test the complete analysis pipeline with detailed logging.
It will show you exactly what's happening at each step.

Usage:
    python manual_scripts/test_analysis.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import uuid

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.services.progress_tracker import ProgressTracker, AnalysisStatus
from app.db.session import create_tables, get_session
from app.models.sql_models import AnalysisJob


# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'analysis_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


class AnalysisTestRunner:
    """Manual analysis test runner with detailed logging."""
    
    def __init__(self, github_url: str):
        self.github_url = github_url
        self.task_id = str(uuid.uuid4())
        self.tracker = ProgressTracker(self.task_id)
        
        # Initialize database
        create_tables()
        
        logger.info("="*80)
        logger.info(f"🚀 STARTING MANUAL ANALYSIS TEST")
        logger.info(f"📅 Time: {datetime.now().isoformat()}")
        logger.info(f"🔗 Repository: {github_url}")
        logger.info(f"🆔 Task ID: {self.task_id}")
        logger.info("="*80)
    
    def check_configuration(self) -> bool:
        """Check if all required configuration is present."""
        logger.info("\n🔧 CHECKING CONFIGURATION")
        logger.info("-" * 40)
        
        issues = []
        
        # Check OpenAI API key
        if not settings.openai_api_key:
            issues.append("❌ OpenAI API key not configured")
            logger.error("OpenAI API key is missing!")
            logger.info("💡 To fix: Create a .env file in the backend folder with:")
            logger.info("   OPENAI_API_KEY=your_actual_api_key_here")
        else:
            key_preview = settings.openai_api_key[:10] + "..." if len(settings.openai_api_key) > 10 else "***"
            logger.info(f"✅ OpenAI API key configured: {key_preview}")
        
        # Check other settings
        logger.info(f"✅ Database URL: {settings.database_url}")
        logger.info(f"✅ Temp directory: {settings.temp_directory}")
        logger.info(f"✅ Vector store path: {settings.vector_store_path}")
        logger.info(f"✅ Embedding model: {settings.embedding_model}")
        
        # Check directories exist
        os.makedirs(settings.temp_directory, exist_ok=True)
        os.makedirs(settings.vector_store_path, exist_ok=True)
        
        if issues:
            logger.error("\n❌ Configuration issues found:")
            for issue in issues:
                logger.error(f"   {issue}")
            return False
        
        logger.info("✅ All configuration looks good!")
        return True
    
    def create_analysis_job(self):
        """Create the analysis job in the database."""
        logger.info("\n📝 CREATING ANALYSIS JOB")
        logger.info("-" * 40)
        
        try:
            with get_session() as db:
                # Use the existing model structure that matches the database
                from app.models.sql_models import AnalysisJob as DatabaseAnalysisJob
                job = DatabaseAnalysisJob(
                    task_id=self.task_id,
                    input_source_type='git_url',
                    input_source_path=self.github_url,
                    status='PENDING',
                )
                db.add(job)
                db.commit()
                
                logger.info(f"✅ Created analysis job: {self.task_id}")
                logger.info(f"📊 Status: {job.status}")
                logger.info(f"🔗 Source: {job.input_source_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create analysis job: {e}")
            raise
    
    async def simulate_rag_pipeline(self):
        """Simulate the RAG pipeline processing."""
        logger.info("\n🧠 SIMULATING RAG PIPELINE")
        logger.info("-" * 40)
        
        # Step 1: Clone repository
        self.tracker.update_status(
            AnalysisStatus.CLONING_REPO,
            progress=5.0,
            step="Cloning repository"
        )
        self.tracker.log_step_start("Clone Repository", "rag")
        
        logger.info("📥 Cloning repository...")
        await asyncio.sleep(1)  # Simulate work
        
        self.tracker.log_step_complete("Clone Repository", success=True)
        logger.info("✅ Repository cloned successfully")
        
        # Step 2: Process files
        self.tracker.update_status(
            AnalysisStatus.PROCESSING_FILES,
            progress=15.0,
            step="Processing files"
        )
        self.tracker.log_step_start("Process Files", "rag")
        
        logger.info("📁 Processing files...")
        # Simulate file processing
        total_files = 25
        for i in range(1, total_files + 1):
            self.tracker.update_file_progress(i, total_files)
            if i % 5 == 0:
                logger.info(f"   📄 Processed {i}/{total_files} files")
            await asyncio.sleep(0.1)
        
        self.tracker.log_step_complete("Process Files", success=True, output={"files_processed": total_files})
        logger.info(f"✅ Processed {total_files} files")
        
        # Step 3: Build RAG index
        self.tracker.update_status(
            AnalysisStatus.BUILDING_RAG,
            progress=30.0,
            step="Building knowledge base"
        )
        self.tracker.log_step_start("Build RAG Index", "rag")
        
        logger.info("🔍 Building vector embeddings...")
        await asyncio.sleep(2)  # Simulate embedding creation
        
        self.tracker.log_step_complete("Build RAG Index", success=True)
        logger.info("✅ Knowledge base built successfully")
    
    async def simulate_ai_analysis(self):
        """Simulate the AI analysis with all tools."""
        logger.info("\n🤖 SIMULATING AI ANALYSIS")
        logger.info("-" * 40)
        
        self.tracker.update_status(
            AnalysisStatus.RUNNING_TOOLS,
            progress=35.0,
            step="Running AI analysis tools"
        )
        
        # List of our 13 analysis tools (7 tools + 6 playbooks)
        tools = [
            # 7 Analysis Tools
            "Static Code Analysis",
            "Dependency Analysis", 
            "Security Vulnerability Scanner",
            "Code Complexity Analysis",
            "Code Quality Assessment",
            "Performance Analysis",
            "Architecture Analysis",
            
            # 6 Analysis Playbooks
            "God Classes Detection",
            "Circular Dependencies Detection",
            "High Complexity Functions",
            "Dependency Health Check",
            "Hardcoded Secrets Scanner",
            "IDOR Vulnerability Detection"
        ]
        
        for i, tool in enumerate(tools, 1):
            self.tracker.log_step_start(tool, "tool")
            logger.info(f"🔧 Running: {tool}")
            
            # Simulate tool execution
            await asyncio.sleep(0.5)
            
            # Simulate occasional warnings or issues
            if i % 4 == 0:
                self.tracker.add_warning(f"Minor issue detected in {tool}")
                logger.warning(f"⚠️  Warning in {tool}: Minor code quality issue")
            
            # Calculate progress (tools are 35% to 85% of total)
            tool_progress = 35 + (i / len(tools)) * 50
            
            self.tracker.update_tool_progress(i)
            self.tracker.update_status(
                AnalysisStatus.RUNNING_TOOLS,
                progress=tool_progress,
                step=f"Running {tool}"
            )
            
            # Simulate tool results
            tool_results = {
                "findings_count": i * 2 + 1,
                "severity_breakdown": {
                    "critical": 0 if i % 5 != 0 else 1,
                    "high": i % 3,
                    "medium": i % 4 + 1,
                    "low": i % 2 + 2
                }
            }
            
            self.tracker.log_step_complete(tool, success=True, output=tool_results)
            logger.info(f"✅ Completed: {tool} - Found {tool_results['findings_count']} issues")
        
        logger.info(f"🎯 All {len(tools)} analysis tools completed successfully!")
    
    async def simulate_report_generation(self):
        """Simulate the final report generation."""
        logger.info("\n📊 SIMULATING REPORT GENERATION")
        logger.info("-" * 40)
        
        self.tracker.update_status(
            AnalysisStatus.GENERATING_REPORT,
            progress=90.0,
            step="Generating analysis report"
        )
        self.tracker.log_step_start("Generate Report", "report")
        
        logger.info("📈 Aggregating findings...")
        await asyncio.sleep(1)
        
        logger.info("📝 Creating recommendations...")
        await asyncio.sleep(1)
        
        logger.info("📋 Finalizing report...")
        await asyncio.sleep(0.5)
        
        # Create mock report
        report_data = {
            "summary": {
                "total_issues": 47,
                "critical_issues": 2,
                "high_priority_issues": 8,
                "files_analyzed": 25,
                "analysis_duration": "3m 45s",
                "overall_score": 78
            },
            "findings_count": 47,
            "recommendations_count": 12
        }
        
        self.tracker.log_step_complete("Generate Report", success=True, output=report_data)
        
        # Mark as complete
        self.tracker.update_status(
            AnalysisStatus.COMPLETE,
            progress=100.0,
            step="Analysis complete"
        )
        
        logger.info("✅ Report generated successfully!")
        logger.info(f"📊 Total issues found: {report_data['summary']['total_issues']}")
        logger.info(f"🎯 Overall code quality score: {report_data['summary']['overall_score']}/100")
    
    def show_final_summary(self):
        """Show the final analysis summary."""
        logger.info("\n" + "="*80)
        logger.info("🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        
        # Get final status
        status = self.tracker.get_current_status()
        steps = self.tracker.get_step_history()
        
        logger.info(f"📊 Final Status: {status.get('status', 'Unknown')}")
        logger.info(f"⏱️  Total Duration: {status.get('duration', 0):.1f} seconds")
        logger.info(f"📈 Progress: {status.get('progress_percentage', 0):.1f}%")
        logger.info(f"🔧 Steps Completed: {len([s for s in steps if s['success']])}/{len(steps)}")
        
        # Show step summary
        logger.info("\n📋 STEP SUMMARY:")
        logger.info("-" * 40)
        for step in steps:
            status_icon = "✅" if step['success'] else "❌"
            duration = f"{step['duration']:.1f}s" if step['duration'] else "N/A"
            logger.info(f"{status_icon} {step['step_name']} ({duration})")
        
        logger.info("\n💡 NEXT STEPS:")
        logger.info("-" * 40)
        logger.info("1. Check the detailed logs above for any issues")
        logger.info("2. If everything looks good, test the full API integration")
        logger.info("3. Test the frontend connection to see live progress")
        logger.info(f"4. View detailed results at: /admin/jobs/{self.task_id}/details")
        
        logger.info("\n🔧 MONITORING ENDPOINTS:")
        logger.info("-" * 40)
        logger.info(f"📊 Job Status: GET /admin/jobs/{self.task_id}/details")
        logger.info(f"📝 Job Logs: GET /admin/jobs/{self.task_id}/logs")
        logger.info("📈 All Jobs: GET /admin/jobs/all")
        logger.info("📊 System Stats: GET /admin/stats")
    
    async def run_complete_test(self):
        """Run the complete analysis test."""
        try:
            # Step 1: Check configuration
            if not self.check_configuration():
                logger.error("❌ Configuration check failed. Please fix the issues above.")
                return False
            
            # Step 2: Create analysis job
            self.create_analysis_job()
            
            # Step 3: Simulate RAG pipeline
            await self.simulate_rag_pipeline()
            
            # Step 4: Simulate AI analysis
            await self.simulate_ai_analysis()
            
            # Step 5: Generate report
            await self.simulate_report_generation()
            
            # Step 6: Show summary
            self.show_final_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            self.tracker.log_error(str(e), {"exception_type": type(e).__name__})
            return False


async def main():
    """Main function to run the analysis test."""
    
    # GitHub repository to test with
    test_repositories = [
        "https://github.com/octocat/Hello-World",
        "https://github.com/microsoft/vscode",
        "https://github.com/facebook/react"
    ]
    
    print("🧪 AI Code Reviewer - Manual Analysis Test")
    print("=" * 50)
    print("\nAvailable test repositories:")
    for i, repo in enumerate(test_repositories, 1):
        print(f"{i}. {repo}")
    
    print("\nOr enter your own GitHub URL:")
    
    try:
        choice = input("\nEnter choice (1-3) or GitHub URL: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_repositories):
            github_url = test_repositories[int(choice) - 1]
        elif choice.startswith("https://github.com/"):
            github_url = choice
        else:
            print("❌ Invalid choice. Using default repository.")
            github_url = test_repositories[0]
        
        print(f"\n🎯 Testing with: {github_url}")
        
        # Run the test
        runner = AnalysisTestRunner(github_url)
        success = await runner.run_complete_test()
        
        if success:
            print("\n🎉 Test completed successfully!")
            print(f"📁 Check the log file: analysis_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        else:
            print("\n❌ Test failed. Check the logs for details.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 