import ast
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import Language


@dataclass
class CodeChunk:
    """
    Represents a chunk of source code with metadata.
    
    This structure matches the metadata schema specified in the architecture document.
    """
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str  # e.g., 'class', 'function', 'module', 'block'
    parent_context: str  # e.g., 'Class: MyController'
    chunk_code: str
    tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for ChromaDB storage."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type,
            "parent_context": self.parent_context,
            "chunk_code": self.chunk_code,
            "tokens": self.tokens
        }


class CodeSplitter:
    """
    Language-aware code splitter that intelligently chunks source code.
    
    Features:
    - Language-specific splitting strategies
    - Structure-aware chunking (functions, classes, etc.)
    - Rich metadata extraction
    - Configurable chunk sizes
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the code splitter.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Map file extensions to languages
        self.extension_to_language = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.vue': 'html',
            '.svelte': 'html',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
            '.rst': 'markdown',
            '.txt': 'text',
            '.sh': 'bash',
            '.bat': 'batch',
            '.ps1': 'powershell'
        }
        
        # Create language-specific splitters
        self.splitters = {}
        self._initialize_splitters()
    
    def _initialize_splitters(self):
        """Initialize language-specific text splitters."""
        supported_languages = [
            Language.PYTHON,
            Language.JAVASCRIPT,
            Language.TYPESCRIPT,
            Language.JAVA,
            Language.CPP,
            Language.CSHARP,
            Language.PHP,
            Language.RUBY,
            Language.GO,
            Language.RUST,
            Language.SWIFT,
            Language.KOTLIN,
            Language.SCALA,
            Language.R,
            Language.HTML,
            Language.CSS,
            Language.MARKDOWN,
        ]
        
        for lang in supported_languages:
            try:
                self.splitters[lang.value] = RecursiveCharacterTextSplitter.from_language(
                    language=lang,
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
            except Exception:
                # Fallback for unsupported languages
                pass
        
        # Default text splitter for unsupported languages
        self.default_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def detect_language(self, file_path: Path) -> str:
        """
        Detect the programming language of a file.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            str: Detected language name
        """
        extension = file_path.suffix.lower()
        
        # Check extension mapping
        if extension in self.extension_to_language:
            return self.extension_to_language[extension]
        
        # Special cases for files without extensions
        filename = file_path.name.lower()
        if filename in ['makefile']:
            return 'makefile'
        elif filename in ['dockerfile']:
            return 'dockerfile'
        elif filename.startswith('.'):
            return 'config'
        
        return 'text'  # Default fallback
    
    def split_file(self, file_path: Path, project_root: Path) -> List[CodeChunk]:
        """
        Split a source code file into intelligent chunks.
        
        Args:
            file_path: Path to the source file
            project_root: Root directory of the project
            
        Returns:
            List[CodeChunk]: List of code chunks with metadata
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return []  # Skip empty files
            
            # Detect language
            language = self.detect_language(file_path)
            
            # Get relative path from project root
            try:
                relative_path = file_path.relative_to(project_root)
            except ValueError:
                relative_path = file_path
            
            # Choose appropriate splitter
            splitter = self.splitters.get(language, self.default_splitter)
            
            # Split content
            chunks = splitter.split_text(content)
            
            # Convert to CodeChunk objects with metadata
            code_chunks = []
            content_lines = content.split('\n')
            current_line = 1
            
            for i, chunk_text in enumerate(chunks):
                chunk_lines = chunk_text.split('\n')
                start_line = current_line
                end_line = current_line + len(chunk_lines) - 1
                
                # Determine chunk type and parent context
                chunk_type, parent_context = self._analyze_chunk_structure(
                    chunk_text, language, file_path
                )
                
                # Create chunk
                chunk = CodeChunk(
                    file_path=str(relative_path),
                    language=language,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type=chunk_type,
                    parent_context=parent_context,
                    chunk_code=chunk_text,
                    tokens=len(chunk_text.split())  # Simple token count
                )
                
                code_chunks.append(chunk)
                
                # Update line tracking (accounting for overlap)
                if i < len(chunks) - 1:  # Not the last chunk
                    # Move forward by chunk size minus overlap
                    advance_lines = len(chunk_lines) - self._estimate_overlap_lines(chunk_text)
                    current_line += max(1, advance_lines)
                else:
                    current_line = end_line + 1
            
            return code_chunks
            
        except Exception as e:
            # Return a single chunk with the error for debugging
            return [CodeChunk(
                file_path=str(file_path),
                language="error",
                start_line=1,
                end_line=1,
                chunk_type="error",
                parent_context=f"Error processing file: {str(e)}",
                chunk_code=f"Error reading file: {str(e)}",
                tokens=0
            )]
    
    def _analyze_chunk_structure(self, chunk_text: str, language: str, file_path: Path) -> tuple[str, str]:
        """
        Analyze the structure of a code chunk to determine its type and context.
        
        Args:
            chunk_text: The chunk content
            language: Programming language
            file_path: File path for context
            
        Returns:
            tuple: (chunk_type, parent_context)
        """
        chunk_type = "code_block"
        parent_context = f"File: {file_path.name}"
        
        # Python-specific analysis
        if language == 'python':
            return self._analyze_python_chunk(chunk_text, file_path.name)
        
        # JavaScript/TypeScript analysis
        elif language in ['javascript', 'typescript']:
            return self._analyze_js_chunk(chunk_text, file_path.name)
        
        # Java analysis
        elif language == 'java':
            return self._analyze_java_chunk(chunk_text, file_path.name)
        
        # Generic analysis for other languages
        return self._analyze_generic_chunk(chunk_text, file_path.name)
    
    def _analyze_python_chunk(self, chunk_text: str, filename: str) -> tuple[str, str]:
        """Analyze Python code structure."""
        try:
            # Try to parse as Python AST
            tree = ast.parse(chunk_text)
            
            # Look for classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    return "class", f"Class: {node.name}"
                elif isinstance(node, ast.FunctionDef):
                    return "function", f"Function: {node.name}"
                elif isinstance(node, ast.AsyncFunctionDef):
                    return "async_function", f"Async Function: {node.name}"
            
            # Check for imports
            if any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in tree.body):
                return "imports", f"File: {filename}"
            
            return "module", f"File: {filename}"
            
        except SyntaxError:
            # Fallback for partial code
            lines = chunk_text.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('class '):
                    class_name = stripped.split()[1].split('(')[0].rstrip(':')
                    return "class", f"Class: {class_name}"
                elif stripped.startswith('def '):
                    func_name = stripped.split()[1].split('(')[0]
                    return "function", f"Function: {func_name}"
                elif stripped.startswith('async def '):
                    func_name = stripped.split()[2].split('(')[0]
                    return "async_function", f"Async Function: {func_name}"
            
            return "code_block", f"File: {filename}"
    
    def _analyze_js_chunk(self, chunk_text: str, filename: str) -> tuple[str, str]:
        """Analyze JavaScript/TypeScript code structure."""
        lines = chunk_text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            # Check for class definitions
            if 'class ' in stripped and not stripped.startswith('//'):
                class_name = stripped.split('class')[1].split()[0].split('{')[0]
                return "class", f"Class: {class_name}"
            
            # Check for function definitions
            elif 'function ' in stripped and not stripped.startswith('//'):
                func_name = stripped.split('function')[1].split('(')[0].strip()
                return "function", f"Function: {func_name}"
            
            # Check for arrow functions
            elif '=>' in stripped and ('const ' in stripped or 'let ' in stripped or 'var ' in stripped):
                func_name = stripped.split('=')[0].split()[-1]
                return "function", f"Function: {func_name}"
            
            # Check for exports
            elif stripped.startswith('export'):
                return "export", f"File: {filename}"
            
            # Check for imports
            elif stripped.startswith('import'):
                return "import", f"File: {filename}"
        
        return "code_block", f"File: {filename}"
    
    def _analyze_java_chunk(self, chunk_text: str, filename: str) -> tuple[str, str]:
        """Analyze Java code structure."""
        lines = chunk_text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('public class ') or stripped.startswith('class '):
                class_name = stripped.split('class')[1].split()[0].split('{')[0]
                return "class", f"Class: {class_name}"
            
            elif 'public ' in stripped and '(' in stripped and '{' in stripped:
                # Likely a method
                method_name = stripped.split('(')[0].split()[-1]
                return "method", f"Method: {method_name}"
            
            elif stripped.startswith('package '):
                return "package", f"File: {filename}"
            
            elif stripped.startswith('import '):
                return "import", f"File: {filename}"
        
        return "code_block", f"File: {filename}"
    
    def _analyze_generic_chunk(self, chunk_text: str, filename: str) -> tuple[str, str]:
        """Generic analysis for unsupported languages."""
        lines = chunk_text.split('\n')
        
        # Simple heuristics
        for line in lines:
            stripped = line.strip()
            
            if any(keyword in stripped.lower() for keyword in ['function', 'def', 'func']):
                return "function", f"File: {filename}"
            elif any(keyword in stripped.lower() for keyword in ['class', 'struct', 'interface']):
                return "class", f"File: {filename}"
            elif any(keyword in stripped.lower() for keyword in ['import', 'include', 'require']):
                return "import", f"File: {filename}"
        
        return "code_block", f"File: {filename}"
    
    def _estimate_overlap_lines(self, chunk_text: str) -> int:
        """Estimate number of overlapping lines based on chunk overlap setting."""
        total_lines = len(chunk_text.split('\n'))
        overlap_ratio = self.chunk_overlap / self.chunk_size
        return int(total_lines * overlap_ratio)
    
    def split_project(self, project_directory: Path) -> List[CodeChunk]:
        """
        Split all source files in a project directory.
        
        Args:
            project_directory: Root directory of the project
            
        Returns:
            List[CodeChunk]: All code chunks from the project
        """
        from .code_retriever import CodeRetriever
        
        retriever = CodeRetriever()
        source_files = retriever.get_source_files(project_directory)
        
        all_chunks = []
        for file_path in source_files:
            chunks = self.split_file(file_path, project_directory)
            all_chunks.extend(chunks)
        
        return all_chunks 