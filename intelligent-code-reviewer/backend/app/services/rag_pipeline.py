import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .code_retriever import CodeRetriever, CodeRetrievalError
from .code_splitter import CodeSplitter, CodeChunk
from .vector_store import VectorStore, VectorStoreError
from .database import DatabaseService
from ..core.config import settings


@dataclass
class RAGPipelineResult:
    """Result of the RAG ingestion pipeline."""
    task_id: str
    success: bool
    total_files_processed: int
    total_chunks_created: int
    chunks_stored: int
    processing_time_seconds: float
    project_info: Dict[str, Any]
    error_message: Optional[str] = None
    collection_stats: Optional[Dict[str, Any]] = None


class RAGPipelineError(Exception):
    """Custom exception for RAG pipeline errors."""
    pass


class RAGIngestionPipeline:
    """
    RAG (Retrieval-Augmented Generation) Ingestion Pipeline.
    
    This pipeline orchestrates the end-to-end process of:
    1. Retrieving code from Git URLs or ZIP files
    2. Splitting code into intelligent chunks
    3. Generating vector embeddings
    4. Storing in ChromaDB with rich metadata
    5. Updating job status in the database
    
    The pipeline is designed to be fault-tolerant and provides detailed
    progress reporting throughout the process.
    """
    
    def __init__(self):
        """Initialize the RAG pipeline with all required services."""
        self.code_retriever = CodeRetriever()
        self.code_splitter = CodeSplitter(
            chunk_size=settings.max_file_size_mb * 1024,  # Convert MB to characters (rough estimate)
            chunk_overlap=200
        )
        self.vector_store = VectorStore()
        self.db_service = DatabaseService()
    
    async def process_git_repository(self, task_id: str, git_url: str, db_session) -> RAGPipelineResult:
        """
        Process a Git repository through the RAG pipeline.
        
        Args:
            task_id: Unique identifier for the analysis task
            git_url: Git repository URL
            db_session: Database session for status updates
            
        Returns:
            RAGPipelineResult: Detailed results of the pipeline execution
        """
        start_time = datetime.now()
        
        try:
            # Update job status to PROCESSING_RAG
            self.db_service.update_job_status(db_session, task_id, "PROCESSING_RAG")
            
            # Step 1: Retrieve code from Git repository
            project_directory = self.code_retriever.retrieve_from_git_url(git_url, task_id)
            
            # Step 2: Process the retrieved code
            result = await self._process_project_directory(task_id, project_directory, db_session)
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            # Update job status to FAILED
            error_msg = f"RAG pipeline failed for Git repository: {str(e)}"
            self.db_service.update_job_status(db_session, task_id, "FAILED", error_msg)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return RAGPipelineResult(
                task_id=task_id,
                success=False,
                total_files_processed=0,
                total_chunks_created=0,
                chunks_stored=0,
                processing_time_seconds=processing_time,
                project_info={},
                error_message=error_msg
            )
    
    async def process_zip_file(self, task_id: str, zip_file_path: Path, db_session) -> RAGPipelineResult:
        """
        Process a ZIP file through the RAG pipeline.
        
        Args:
            task_id: Unique identifier for the analysis task
            zip_file_path: Path to the ZIP file
            db_session: Database session for status updates
            
        Returns:
            RAGPipelineResult: Detailed results of the pipeline execution
        """
        start_time = datetime.now()
        
        try:
            # Update job status to PROCESSING_RAG
            self.db_service.update_job_status(db_session, task_id, "PROCESSING_RAG")
            
            # Step 1: Extract ZIP file
            project_directory = self.code_retriever.retrieve_from_zip_file(zip_file_path, task_id)
            
            # Step 2: Process the extracted code
            result = await self._process_project_directory(task_id, project_directory, db_session)
            
            # Calculate processing time
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            # Update job status to FAILED
            error_msg = f"RAG pipeline failed for ZIP file: {str(e)}"
            self.db_service.update_job_status(db_session, task_id, "FAILED", error_msg)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return RAGPipelineResult(
                task_id=task_id,
                success=False,
                total_files_processed=0,
                total_chunks_created=0,
                chunks_stored=0,
                processing_time_seconds=processing_time,
                project_info={},
                error_message=error_msg
            )
    
    async def _process_project_directory(self, task_id: str, project_directory: Path, db_session) -> RAGPipelineResult:
        """
        Process a project directory through the RAG pipeline.
        
        Args:
            task_id: Unique identifier for the analysis task
            project_directory: Path to the project directory
            db_session: Database session for status updates
            
        Returns:
            RAGPipelineResult: Detailed results of the pipeline execution
        """
        try:
            # Step 1: Analyze project structure
            project_info = self.code_retriever.get_project_info(project_directory)
            
            # Step 2: Get source files
            source_files = self.code_retriever.get_source_files(
                project_directory, 
                max_file_size_mb=settings.max_file_size_mb
            )
            
            if not source_files:
                raise RAGPipelineError("No source files found in the project")
            
            # Step 3: Create vector database collection
            collection_name = self.vector_store.create_collection(task_id)
            
            # Step 4: Process files and create chunks
            all_chunks = []
            files_processed = 0
            
            for file_path in source_files:
                try:
                    chunks = self.code_splitter.split_file(file_path, project_directory)
                    all_chunks.extend(chunks)
                    files_processed += 1
                    
                    # Log progress for very large projects
                    if files_processed % 100 == 0:
                        print(f"Processed {files_processed} files, created {len(all_chunks)} chunks so far...")
                        
                except Exception as e:
                    # Log individual file errors but continue processing
                    print(f"Warning: Failed to process file {file_path}: {str(e)}")
                    continue
            
            if not all_chunks:
                raise RAGPipelineError("No code chunks could be created from the source files")
            
            # Step 5: Store chunks in vector database
            chunks_stored = self.vector_store.add_chunks(task_id, all_chunks)
            
            # Step 6: Get collection statistics
            collection_stats = self.vector_store.get_collection_stats(task_id)
            
            # Step 7: Update job status to ready for agent processing
            self.db_service.update_job_status(db_session, task_id, "PROCESSING_AGENT")
            
            # Create successful result
            return RAGPipelineResult(
                task_id=task_id,
                success=True,
                total_files_processed=files_processed,
                total_chunks_created=len(all_chunks),
                chunks_stored=chunks_stored,
                processing_time_seconds=0,  # Will be set by caller
                project_info=project_info,
                collection_stats=collection_stats
            )
            
        except Exception as e:
            # Clean up on failure
            try:
                self.vector_store.delete_collection(task_id)
            except Exception:
                pass  # Ignore cleanup errors
                
            raise RAGPipelineError(f"Failed to process project directory: {str(e)}")
    
    async def cleanup_task(self, task_id: str) -> bool:
        """
        Clean up all resources associated with a task.
        
        Args:
            task_id: Unique identifier for the analysis task
            
        Returns:
            bool: True if cleanup was successful
        """
        try:
            # Clean up temporary files
            self.code_retriever.cleanup_task_files(task_id)
            
            # Clean up vector database collection
            self.vector_store.delete_collection(task_id)
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to cleanup task {task_id}: {str(e)}")
            return False
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get health status of all pipeline components.
        
        Returns:
            Dict: Health status of each component
        """
        try:
            vector_store_health = self.vector_store.health_check()
            
            # Test code retriever
            retriever_healthy = True
            retriever_error = None
            try:
                temp_dir = Path(settings.temp_directory)
                temp_dir.mkdir(exist_ok=True)
                test_file = temp_dir / "health_check.txt"
                test_file.write_text("test")
                test_file.unlink()  # Clean up
            except Exception as e:
                retriever_healthy = False
                retriever_error = str(e)
            
            # Test code splitter
            splitter_healthy = True
            splitter_error = None
            try:
                test_splitter = CodeSplitter(chunk_size=100, chunk_overlap=20)
                test_chunks = test_splitter._analyze_generic_chunk("test code", "test.py")
            except Exception as e:
                splitter_healthy = False
                splitter_error = str(e)
            
            return {
                "overall_status": "healthy" if all([
                    vector_store_health["status"] == "healthy",
                    retriever_healthy,
                    splitter_healthy
                ]) else "unhealthy",
                "components": {
                    "vector_store": vector_store_health,
                    "code_retriever": {
                        "status": "healthy" if retriever_healthy else "unhealthy",
                        "error": retriever_error
                    },
                    "code_splitter": {
                        "status": "healthy" if splitter_healthy else "unhealthy", 
                        "error": splitter_error
                    }
                }
            }
            
        except Exception as e:
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "components": {}
            }
    
    async def process_task_async(self, task_id: str, input_type: str, input_path: str, db_session) -> RAGPipelineResult:
        """
        Process a task asynchronously based on input type.
        
        Args:
            task_id: Unique identifier for the analysis task
            input_type: Type of input ('git_url' or 'zip_upload')
            input_path: Path or URL to the input
            db_session: Database session for status updates
            
        Returns:
            RAGPipelineResult: Results of the pipeline execution
        """
        try:
            if input_type == "git_url":
                return await self.process_git_repository(task_id, input_path, db_session)
            elif input_type == "zip_upload":
                zip_path = Path(input_path)
                return await self.process_zip_file(task_id, zip_path, db_session)
            else:
                raise RAGPipelineError(f"Unsupported input type: {input_type}")
                
        except Exception as e:
            # Ensure cleanup happens even on unexpected errors
            await self.cleanup_task(task_id)
            raise 