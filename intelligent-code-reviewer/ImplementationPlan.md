# AI-Powered Intelligent Code Reviewer: Implementation Plan

This document outlines the detailed, phased implementation plan for building the AI-Powered Intelligent Code Reviewer. We will follow this plan step-by-step to ensure a structured and robust development process.

---

## Phase 1: Backend Foundation & Core API

**Goal:** Establish the backend server, define the complete API structure, and set up project configuration. This phase provides the foundational skeleton for all subsequent development.

*   **1.1: Initialize FastAPI Project Structure**
    *   Create a standard, modular directory structure:
        ```
        backend/
        ├── app/
        │   ├── api/          # API endpoint definitions
        │   ├── core/         # Configuration, core settings
        │   ├── services/     # Business logic (RAG, Agent)
        │   ├── models/       # Pydantic/SQLAlchemy models
        │   └── db/           # Database session management
        ├── tests/            # Unit and integration tests
        └── pyproject.toml    # Dependency management
        ```

*   **1.2: Set Up Dependency Management**
    *   Initialize a `pyproject.toml` file.
    *   Add core dependencies: `fastapi`, `uvicorn`, `pydantic`.

*   **1.3: Create Initial API Endpoints**
    *   Implement placeholder functions for all endpoints defined in the architecture document:
        *   `POST /api/analyze/url`: Accepts a Git URL.
        *   `POST /api/analyze/zip`: Accepts a ZIP file upload.
        *   `GET /api/report/{task_id}`: Pollable endpoint for status and results.
    *   Define Pydantic models for request and response bodies to ensure type safety.

*   **1.4: Implement Configuration Management**
    *   Create a `core/config.py` module to manage environment variables and application settings using Pydantic's `BaseSettings`.

---

## Phase 2: Database & Job Management System

**Goal:** Build the data persistence layer to track the lifecycle, status, and logs of each analysis job using SQLite and SQLAlchemy.

*   **2.1: Define SQLAlchemy ORM Models**
    *   In `models/sql_models.py`, define the SQLAlchemy models for the three tables:
        *   `AnalysisJob`: Tracks high-level task status.
        *   `AgentLog`: Stores the detailed reasoning steps of the AI agent.
        *   `FinalReport`: Stores the final JSON analysis output.

*   **2.2: Implement Database Session Management**
    *   In `db/session.py`, create the SQLAlchemy engine and a session factory (`SessionLocal`).
    *   Implement a FastAPI dependency to manage the lifecycle of a database session per request.

*   **2.3: Implement Database Initialization**
    *   Create a script or startup event in FastAPI to create the database and all tables based on the ORM models.

*   **2.4: Integrate Database with API Endpoints**
    *   Modify the `/analyze` endpoints to create a new `AnalysisJob` record with a `PENDING` status and persist it to the database.
    -   Modify the `/report` endpoint to query the `analysis_jobs` and `final_reports` tables to return the job status and the final report if available.

---

## Phase 3: RAG Ingestion Pipeline

**Goal:** Implement the "Knowledge Creation" pipeline that ingests source code, processes it, and stores it in a searchable vector database.

*   **3.1: Implement Code Retrieval Service**
    *   Create `services/code_retriever.py`.
    *   Implement a function to clone a git repository into a temporary directory.
    *   Implement a function to extract a zip file into a temporary directory.

*   **3.2: Integrate Language-Aware Code Splitter**
    *   Choose and integrate a library for intelligent code chunking (e.g., based on `tree-sitter`).
    *   The splitter must attach metadata to each chunk (`file_path`, `language`, `start_line`, etc.) as specified in the architecture document.

*   **3.3: Set Up Vector Database Client**
    *   In `services/vector_store.py`, initialize the ChromaDB client.
    *   Create helper functions to create and delete ChromaDB collections to ensure isolation between analysis jobs.

*   **3.4: Build the `RAGIngestionPipeline`**
    *   Create `services/rag_pipeline.py`.
    *   This service will orchestrate the end-to-end ingestion process:
        1.  Call the `CodeRetriever` service.
        2.  Use the `CodeSplitter` to chunk the retrieved code.
        3.  Generate vector embeddings for each chunk.
        4.  Store the vectors and their metadata in a new, task-specific ChromaDB collection.
        5.  Update the `AnalysisJob` status from `PENDING` to `PROCESSING_RAG`.

---

## Phase 4: AI Agent & Toolbox Implementation

**Goal:** Build the "brain" of the system by creating the AI agent and implementing its full suite of analysis tools.

*   **4.1: Set Up AI Agent Framework**
    *   Integrate an agent framework like LangChain.
    *   Define the agent's core prompt, which instructs it on how to use its tools and follow playbooks.

*   **4.2: Implement the Agent's Toolbox (One Tool at a Time)**
    *   For each tool, create a dedicated function with clear inputs and outputs.
    *   **Tool 1: `list_project_files`**: Walk the project directory and return a file tree.
    *   **Tool 2: `read_file_contents`**: Read and return the content of a specific file.
    *   **Tool 3: `query_codebase`**: Interface with the `VectorStore` service to perform semantic search.
    *   **Tool 4: `get_code_metrics`**: Integrate a static analysis library (e.g., `radon`) to calculate cyclomatic complexity, etc.
    *   **Tool 5: `scan_for_secrets`**: Implement regex and entropy-based scanning.
    *   **Tool 6: `build_dependency_graph`**: Parse import statements to build a graph and detect cycles.
    *   **Tool 7: `run_dependency_health_check`**: Use a library like `safety` for CVEs and call external APIs (GitHub, PyPI) for maintenance data.

*   **4.3: Implement Agent's Reasoning Loop & Logging**
    *   Invoke the agent and manage its execution.
    *   For every `(thought, action, observation)` step in the agent's process, insert a new record into the `agent_logs` table in the database.

---

## Phase 5: Frontend User Interface

**Goal:** Build the client-facing Next.js application for users to submit code and view analysis reports.

*   **5.1: Initialize Next.js Project**
    *   Set up a new Next.js application with TypeScript.
    *   Structure the project with standard directories (`components`, `pages`, `hooks`, `lib`).

*   **5.2: Create Code Submission UI**
    *   Build a form with two tabs: one for submitting a Git URL and another for uploading a ZIP file.
    *   Implement the API call to the backend's `/analyze` endpoints.

*   **5.3: Develop the Report Viewing Page**
    *   Create a dynamic page (e.g., `/report/[taskId]`).
    *   This page will use a hook (like `useSWR`) to poll the backend's `/api/report/{task_id}` endpoint.
    *   Display the current job status (`Processing...`, `Analyzing...`, `Complete`).

*   **5.4: Design and Implement Report Renderer**
    *   Create components to render the final JSON report in a structured and user-friendly format. This should include clear sections for each finding, code snippets, and recommendations.

---

## Phase 6: Final Integration & Playbook Execution

**Goal:** Tie all components together into a cohesive, fully functional application and implement the high-level analysis strategies.

*   **6.1: Create the Main `AnalysisManager`**
    *   This high-level service in the backend will manage the entire lifecycle of a job.
    *   It will be invoked as a background task (e.g., using FastAPI's `BackgroundTasks`).
    *   It will first trigger the `RAGIngestionPipeline`.
    *   Once the RAG pipeline is complete, it will update the job status to `PROCESSING_AGENT` and invoke the AI Agent.

*   **6.2: Implement Agent Playbooks**
    *   Translate the strategies from `agent_playbooks.md` into concrete logic within the `AnalysisManager`.
    *   The manager will pass a specific high-level goal or initial prompt to the agent to kick off the correct playbook (e.g., "Analyze this codebase for God Classes").

*   **6.3: Implement Finalization and Cleanup**
    *   After the agent completes its work and generates a report:
        1.  The `AnalysisManager` saves the report to the `final_reports` table.
        2.  It updates the `analysis_jobs` status to `COMPLETE`.
        3.  It deletes the temporary source code directory and the job-specific ChromaDB collection.

*   **6.4: End-to-End Testing and Refinement**
    *   Thoroughly test the entire application with various real-world codebases.
    *   Refine prompts, tool implementations, and the frontend based on test results to ensure accuracy and usability. 