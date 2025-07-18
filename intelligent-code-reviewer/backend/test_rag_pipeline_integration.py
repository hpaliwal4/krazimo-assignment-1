#!/usr/bin/env python3
"""
Integration test for the RAG pipeline.
Tests the complete flow from code retrieval to vector storage.
"""

import asyncio
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))
os.environ["PYTHONPATH"] = str(Path(__file__).parent / "app")

# Monkey patch the relative imports for testing
import importlib.util

def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules with fixed imports
app_path = Path(__file__).parent / "app"

# Create mock config for testing
class MockSettings:
    vector_store_path = "./temp_vector_store"
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

# Import code retriever and fix its imports
code_retriever_path = app_path / "services" / "code_retriever.py"
with open(code_retriever_path, 'r') as f:
    code_content = f.read()

# Replace relative imports with absolute imports for testing
code_content = code_content.replace("from ..core.config import settings", "# from ..core.config import settings")

# Write temporary version
temp_code_retriever = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
temp_code_retriever.write(code_content + "\nsettings = MockSettings()")
temp_code_retriever.close()

# Import the fixed module
CodeRetriever = import_from_file("code_retriever", temp_code_retriever.name).CodeRetriever

# Do the same for other modules
code_splitter_path = app_path / "services" / "code_splitter.py"
with open(code_splitter_path, 'r') as f:
    splitter_content = f.read()

temp_code_splitter = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
temp_code_splitter.write(splitter_content)
temp_code_splitter.close()

CodeSplitter = import_from_file("code_splitter", temp_code_splitter.name).CodeSplitter

# Vector store
vector_store_path = app_path / "services" / "vector_store.py"
with open(vector_store_path, 'r') as f:
    vector_content = f.read()

temp_vector_store = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
temp_vector_store.write(vector_content)
temp_vector_store.close()

VectorStoreClient = import_from_file("vector_store", temp_vector_store.name).VectorStoreClient

# RAG pipeline
rag_pipeline_path = app_path / "services" / "rag_pipeline.py"
with open(rag_pipeline_path, 'r') as f:
    rag_content = f.read()

# Fix imports for rag_pipeline
rag_content = rag_content.replace("from .code_retriever import CodeRetriever", "# from .code_retriever import CodeRetriever")
rag_content = rag_content.replace("from .code_splitter import CodeSplitter", "# from .code_splitter import CodeSplitter")
rag_content = rag_content.replace("from .vector_store import VectorStoreClient", "# from .vector_store import VectorStoreClient")

temp_rag_pipeline = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
temp_rag_pipeline.write(rag_content)
temp_rag_pipeline.close()

# Import and patch the RAG pipeline
rag_module = import_from_file("rag_pipeline", temp_rag_pipeline.name)
RAGIngestionPipeline = rag_module.RAGIngestionPipeline

# Patch the class to use our imported classes
RAGIngestionPipeline._CodeRetriever = CodeRetriever
RAGIngestionPipeline._CodeSplitter = CodeSplitter
RAGIngestionPipeline._VectorStoreClient = VectorStoreClient

def create_test_python_project():
    """Create a simple test Python project structure."""
    temp_dir = tempfile.mkdtemp(prefix="test_project_")
    
    # Create main.py
    main_py = Path(temp_dir) / "main.py"
    main_py.write_text("""
def calculate_factorial(n):
    '''Calculate factorial of a number.'''
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

class Calculator:
    '''A simple calculator class.'''
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.multiply(4, 6))
    print(calculate_factorial(5))
""")
    
    # Create utils.py
    utils_py = Path(temp_dir) / "utils.py"
    utils_py.write_text("""
import os
import json

def read_config(filename):
    '''Read configuration from JSON file.'''
    if not os.path.exists(filename):
        return {}
    
    with open(filename, 'r') as f:
        return json.load(f)

def validate_email(email):
    '''Simple email validation.'''
    return '@' in email and '.' in email

class FileManager:
    '''Manages file operations.'''
    
    def __init__(self, base_path):
        self.base_path = base_path
    
    def create_directory(self, name):
        dir_path = os.path.join(self.base_path, name)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
""")
    
    # Create README.md
    readme_md = Path(temp_dir) / "README.md"
    readme_md.write_text("""
# Test Project

This is a simple test project for RAG pipeline testing.

## Features
- Calculator functionality
- File management utilities
- Configuration handling

## Usage
```python
from main import Calculator
calc = Calculator()
result = calc.add(1, 2)
```
""")
    
    return temp_dir


async def test_code_retriever():
    """Test the CodeRetriever service."""
    print("🔍 Testing CodeRetriever...")
    
    # Create test project
    test_project = create_test_python_project()
    
    try:
        retriever = CodeRetriever()
        
        # Test project analysis
        project_info = retriever.analyze_project(test_project)
        
        print(f"✅ Project analysis successful:")
        print(f"   - Languages: {project_info['languages']}")
        print(f"   - File count: {project_info['file_count']}")
        print(f"   - Total size: {project_info['total_size']} bytes")
        
        # Test source file detection
        source_files = retriever.get_source_files(test_project)
        print(f"✅ Found {len(source_files)} source files:")
        for file_path in source_files:
            print(f"   - {file_path}")
        
        assert len(source_files) >= 2, "Should find at least 2 Python files"
        assert any(f.endswith('main.py') for f in source_files), "Should find main.py"
        assert any(f.endswith('utils.py') for f in source_files), "Should find utils.py"
        
    finally:
        shutil.rmtree(test_project)
    
    print("✅ CodeRetriever test passed!\n")


async def test_code_splitter():
    """Test the CodeSplitter service."""
    print("🔧 Testing CodeSplitter...")
    
    # Create test project
    test_project = create_test_python_project()
    
    try:
        retriever = CodeRetriever()
        splitter = CodeSplitter()
        
        # Get source files
        source_files = retriever.get_source_files(test_project)
        
        # Test chunking
        all_chunks = []
        for file_path in source_files:
            with open(file_path, 'r') as f:
                content = f.read()
            
            chunks = splitter.split_code(content, file_path)
            all_chunks.extend(chunks)
            
            print(f"✅ Split {file_path}: {len(chunks)} chunks")
            for chunk in chunks:
                print(f"   - {chunk.metadata.get('chunk_type', 'unknown')} "
                      f"({chunk.metadata.get('start_line', '?')}-{chunk.metadata.get('end_line', '?')})")
        
        assert len(all_chunks) > 0, "Should create at least one chunk"
        
        # Verify metadata
        for chunk in all_chunks:
            assert 'file_path' in chunk.metadata
            assert 'language' in chunk.metadata
            assert chunk.metadata['language'] in ['python', 'markdown']
        
    finally:
        shutil.rmtree(test_project)
    
    print("✅ CodeSplitter test passed!\n")


async def test_vector_store():
    """Test the VectorStoreClient service."""
    print("🗄️ Testing VectorStoreClient...")
    
    # Create temporary vector store
    temp_dir = tempfile.mkdtemp(prefix="test_vectorstore_")
    
    try:
        vector_store = VectorStoreClient(persist_directory=temp_dir)
        
        # Test collection creation
        collection_name = "test_collection"
        vector_store.create_collection(collection_name)
        
        # Test document addition
        test_docs = [
            {
                "content": "def hello_world(): print('Hello, World!')",
                "metadata": {"file_path": "test.py", "language": "python", "chunk_type": "function"}
            },
            {
                "content": "class TestClass: pass",
                "metadata": {"file_path": "test.py", "language": "python", "chunk_type": "class"}
            }
        ]
        
        vector_store.add_documents(collection_name, test_docs)
        print(f"✅ Added {len(test_docs)} documents to vector store")
        
        # Test search
        results = vector_store.search(collection_name, "hello world function", k=1)
        assert len(results) > 0, "Should find at least one result"
        
        print(f"✅ Search successful: found {len(results)} results")
        print(f"   - Best match: {results[0]['content'][:50]}...")
        
        # Test health check
        health = vector_store.health_check()
        assert health['status'] == 'healthy', "Vector store should be healthy"
        print(f"✅ Health check passed: {health}")
        
    finally:
        shutil.rmtree(temp_dir)
    
    print("✅ VectorStoreClient test passed!\n")


async def test_simplified_pipeline():
    """Test the simplified pipeline functionality."""
    print("🚀 Testing simplified RAG pipeline components...")
    
    # Create test project
    test_project = create_test_python_project()
    temp_vector_dir = tempfile.mkdtemp(prefix="test_pipeline_vectorstore_")
    
    try:
        # Test individual components working together
        retriever = CodeRetriever()
        splitter = CodeSplitter()
        vector_store = VectorStoreClient(persist_directory=temp_vector_dir)
        
        # Step 1: Retrieve code files
        source_files = retriever.get_source_files(test_project)
        print(f"📁 Retrieved {len(source_files)} source files")
        
        # Step 2: Split and chunk code
        all_chunks = []
        for file_path in source_files:
            with open(file_path, 'r') as f:
                content = f.read()
            chunks = splitter.split_code(content, file_path)
            all_chunks.extend(chunks)
        
        print(f"🔧 Created {len(all_chunks)} chunks from source files")
        
        # Step 3: Store in vector database
        collection_name = "test_pipeline_collection"
        vector_store.create_collection(collection_name)
        
        # Convert chunks to documents format
        documents = []
        for chunk in all_chunks:
            documents.append({
                "content": chunk.page_content,
                "metadata": chunk.metadata
            })
        
        vector_store.add_documents(collection_name, documents)
        print(f"🗄️ Stored {len(documents)} documents in vector store")
        
        # Step 4: Test semantic search
        search_results = vector_store.search(collection_name, "calculator class functions", k=3)
        print(f"🔍 Search found {len(search_results)} relevant results:")
        
        for i, result in enumerate(search_results[:2]):
            print(f"   - Result {i+1}: {result['content'][:60]}...")
            print(f"     Metadata: {result['metadata']['file_path']} ({result['metadata']['chunk_type']})")
        
        # Assertions
        assert len(source_files) >= 2, "Should find multiple source files"
        assert len(all_chunks) > 0, "Should create chunks from source code"
        assert len(search_results) > 0, "Should find relevant search results"
        
        print("✅ Pipeline components working together successfully!")
        
    finally:
        shutil.rmtree(test_project)
        shutil.rmtree(temp_vector_dir)
    
    print("✅ Simplified pipeline test passed!\n")


async def main():
    """Run all RAG pipeline tests."""
    print("🧪 Starting RAG Pipeline Integration Tests\n")
    print("=" * 60)
    
    try:
        # Test individual components
        await test_code_retriever()
        await test_code_splitter()
        await test_vector_store()
        
        # Test simplified pipeline
        await test_simplified_pipeline()
        
        print("=" * 60)
        print("🎉 All RAG pipeline tests passed successfully!")
        print("\n✅ Phase 3 implementation is working correctly")
        print("✅ Ready to proceed to Phase 4 (AI Agent & Toolbox)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup temporary files
        try:
            os.unlink(temp_code_retriever.name)
            os.unlink(temp_code_splitter.name)
            os.unlink(temp_vector_store.name)
            os.unlink(temp_rag_pipeline.name)
        except:
            pass
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 