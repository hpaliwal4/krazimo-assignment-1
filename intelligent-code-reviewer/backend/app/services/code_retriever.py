import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import git
from git import Repo

from ..core.config import settings


class CodeRetrievalError(Exception):
    """Custom exception for code retrieval errors."""
    pass


class CodeRetriever:
    """
    Service for retrieving source code from various sources.
    
    Supports:
    - Git repository cloning (HTTP/HTTPS)
    - ZIP file extraction
    - Local directory handling
    """
    
    def __init__(self):
        self.temp_base_dir = Path(settings.temp_directory)
        self.temp_base_dir.mkdir(exist_ok=True)
    
    def retrieve_from_git_url(self, git_url: str, task_id: str) -> Path:
        """
        Clone a Git repository to a temporary directory.
        
        Args:
            git_url: The Git repository URL (HTTP/HTTPS)
            task_id: Unique identifier for the task
            
        Returns:
            Path: Path to the cloned repository directory
            
        Raises:
            CodeRetrievalError: If cloning fails
        """
        try:
            # Validate URL
            parsed_url = urlparse(git_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise CodeRetrievalError(f"Invalid Git URL: {git_url}")
            
            # Create task-specific temporary directory
            task_temp_dir = self.temp_base_dir / f"git_{task_id}"
            if task_temp_dir.exists():
                shutil.rmtree(task_temp_dir)
            
            task_temp_dir.mkdir(parents=True)
            
            # Clone repository
            repo_dir = task_temp_dir / "repository"
            
            try:
                repo = Repo.clone_from(
                    git_url, 
                    repo_dir,
                    depth=1,  # Shallow clone for efficiency
                    single_branch=True  # Only clone default branch
                )
                
                # Remove .git directory to save space
                git_dir = repo_dir / ".git"
                if git_dir.exists():
                    shutil.rmtree(git_dir)
                
                return repo_dir
                
            except git.GitCommandError as e:
                raise CodeRetrievalError(f"Failed to clone repository: {str(e)}")
            except Exception as e:
                raise CodeRetrievalError(f"Unexpected error during git clone: {str(e)}")
                
        except CodeRetrievalError:
            raise
        except Exception as e:
            raise CodeRetrievalError(f"Failed to retrieve code from Git URL: {str(e)}")
    
    def retrieve_from_zip_file(self, zip_file_path: Union[str, Path], task_id: str) -> Path:
        """
        Extract a ZIP file to a temporary directory.
        
        Args:
            zip_file_path: Path to the ZIP file
            task_id: Unique identifier for the task
            
        Returns:
            Path: Path to the extracted directory
            
        Raises:
            CodeRetrievalError: If extraction fails
        """
        try:
            zip_path = Path(zip_file_path)
            
            if not zip_path.exists():
                raise CodeRetrievalError(f"ZIP file not found: {zip_file_path}")
            
            if not zip_path.is_file():
                raise CodeRetrievalError(f"Path is not a file: {zip_file_path}")
            
            # Create task-specific temporary directory
            task_temp_dir = self.temp_base_dir / f"zip_{task_id}"
            if task_temp_dir.exists():
                shutil.rmtree(task_temp_dir)
            
            task_temp_dir.mkdir(parents=True)
            
            # Extract ZIP file
            extracted_dir = task_temp_dir / "extracted"
            extracted_dir.mkdir()
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Security check: prevent zip bombs and path traversal
                    for member in zip_ref.namelist():
                        if member.startswith('/') or '..' in member:
                            raise CodeRetrievalError(f"Unsafe path in ZIP file: {member}")
                    
                    zip_ref.extractall(extracted_dir)
                
                # If there's only one top-level directory, use that as the root
                contents = list(extracted_dir.iterdir())
                if len(contents) == 1 and contents[0].is_dir():
                    return contents[0]
                else:
                    return extracted_dir
                    
            except zipfile.BadZipFile:
                raise CodeRetrievalError("Invalid or corrupted ZIP file")
            except Exception as e:
                raise CodeRetrievalError(f"Failed to extract ZIP file: {str(e)}")
                
        except CodeRetrievalError:
            raise
        except Exception as e:
            raise CodeRetrievalError(f"Failed to retrieve code from ZIP file: {str(e)}")
    
    def save_uploaded_file(self, file_content: bytes, filename: str, task_id: str) -> Path:
        """
        Save uploaded file content to a temporary file.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            task_id: Unique identifier for the task
            
        Returns:
            Path: Path to the saved file
            
        Raises:
            CodeRetrievalError: If saving fails
        """
        try:
            # Create task-specific temporary directory
            task_temp_dir = self.temp_base_dir / f"upload_{task_id}"
            task_temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = task_temp_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return file_path
            
        except Exception as e:
            raise CodeRetrievalError(f"Failed to save uploaded file: {str(e)}")
    
    def cleanup_task_files(self, task_id: str) -> None:
        """
        Clean up all temporary files for a specific task.
        
        Args:
            task_id: Unique identifier for the task
        """
        try:
            patterns = [f"git_{task_id}", f"zip_{task_id}", f"upload_{task_id}"]
            
            for pattern in patterns:
                task_dir = self.temp_base_dir / pattern
                if task_dir.exists():
                    shutil.rmtree(task_dir)
                    
        except Exception as e:
            # Log error but don't raise - cleanup should not fail the main operation
            print(f"Warning: Failed to cleanup files for task {task_id}: {str(e)}")
    
    def get_source_files(self, directory: Path, max_file_size_mb: int = 10) -> list[Path]:
        """
        Get a list of source code files from a directory.
        
        Args:
            directory: Directory to scan
            max_file_size_mb: Maximum file size in MB to include
            
        Returns:
            list[Path]: List of source code file paths
        """
        # Common source code file extensions
        source_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
            '.sql', '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            '.yaml', '.yml', '.json', '.xml', '.md', '.rst', '.txt', '.sh', '.bat',
            '.ps1', '.dockerfile', '.makefile', '.gitignore', '.gitattributes'
        }
        
        # Directories to skip
        skip_dirs = {
            '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.vscode',
            '.idea', 'build', 'dist', '.next', '.nuxt', 'target', 'bin', 'obj',
            'vendor', 'venv', 'env', '.env', 'coverage'
        }
        
        source_files = []
        max_size_bytes = max_file_size_mb * 1024 * 1024
        
        try:
            for file_path in directory.rglob('*'):
                # Skip if not a file
                if not file_path.is_file():
                    continue
                
                # Skip if in excluded directory
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                
                # Check file extension
                if file_path.suffix.lower() in source_extensions or file_path.name.lower() in {'makefile', 'dockerfile'}:
                    # Check file size
                    try:
                        if file_path.stat().st_size <= max_size_bytes:
                            source_files.append(file_path)
                    except OSError:
                        # Skip files that can't be accessed
                        continue
            
            return source_files
            
        except Exception as e:
            raise CodeRetrievalError(f"Failed to scan directory for source files: {str(e)}")
    
    def get_project_info(self, directory: Path) -> dict:
        """
        Extract basic information about the project.
        
        Args:
            directory: Project directory
            
        Returns:
            dict: Project information
        """
        info = {
            "name": directory.name,
            "total_files": 0,
            "source_files": 0,
            "languages": set(),
            "size_mb": 0,
            "has_readme": False,
            "has_requirements": False,
            "has_package_json": False,
            "has_dockerfile": False
        }
        
        try:
            source_files = self.get_source_files(directory)
            info["source_files"] = len(source_files)
            
            # Count total files and detect languages
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    info["total_files"] += 1
                    try:
                        total_size += file_path.stat().st_size
                        
                        # Detect language by extension
                        ext = file_path.suffix.lower()
                        if ext == '.py':
                            info["languages"].add('Python')
                        elif ext in ['.js', '.jsx']:
                            info["languages"].add('JavaScript')
                        elif ext in ['.ts', '.tsx']:
                            info["languages"].add('TypeScript')
                        elif ext == '.java':
                            info["languages"].add('Java')
                        elif ext in ['.cpp', '.c', '.h', '.hpp']:
                            info["languages"].add('C/C++')
                        elif ext == '.cs':
                            info["languages"].add('C#')
                        elif ext == '.go':
                            info["languages"].add('Go')
                        elif ext == '.rs':
                            info["languages"].add('Rust')
                        elif ext == '.php':
                            info["languages"].add('PHP')
                        elif ext == '.rb':
                            info["languages"].add('Ruby')
                        
                        # Check for special files
                        name = file_path.name.lower()
                        if 'readme' in name:
                            info["has_readme"] = True
                        elif name in ['requirements.txt', 'requirements.in', 'pyproject.toml', 'setup.py']:
                            info["has_requirements"] = True
                        elif name == 'package.json':
                            info["has_package_json"] = True
                        elif name == 'dockerfile':
                            info["has_dockerfile"] = True
                            
                    except OSError:
                        continue
            
            info["size_mb"] = round(total_size / (1024 * 1024), 2)
            info["languages"] = list(info["languages"])
            
            return info
            
        except Exception as e:
            # Return basic info even if detailed analysis fails
            info["error"] = str(e)
            return info 