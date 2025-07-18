# Implementation Verification and Testing Plan

This document provides a clear, phase-by-phase checklist to verify the correct implementation of the Intelligent Code Reviewer. Its purpose is to ensure that all requirements from a given phase are met before development proceeds to the next, preventing cascading issues and ensuring a stable build process.

The verification steps are designed to be simple, often involving file existence checks or manual API calls, rather than formal automated tests.

---

## Phase 1 Verification: Backend Foundation & Core API

**Goal:** To confirm that the core backend project structure and API shell have been created correctly.

### Checklist:

-   **[ ] 1.1: Project Structure Verified**
    -   Does the directory `backend/app/api/` exist?
    -   Does the directory `backend/app/core/` exist?
    -   Does the directory `backend/app/services/` exist?
    -   Does the directory `backend/app/models/` exist?
    -   Does the directory `backend/app/db/` exist?

-   **[ ] 1.2: Dependency Management Verified**
    -   Does the file `backend/pyproject.toml` (or `requirements.txt`) exist?
    -   Does the dependency file contain `fastapi` and `uvicorn`?

-   **[ ] 1.3: API Endpoints Verified**
    -   Is there a file for API endpoints (e.g., `backend/app/api/main.py`)?
    -   Does this file contain placeholder functions for `POST /api/analyze/url`, `POST /api/analyze/zip`, and `GET /api/report/{task_id}`?
    -   Are there Pydantic models defined for the request/response bodies of these endpoints?

-   **[ ] 1.4: Configuration Management Verified**
    -   Does the file `backend/app/core/config.py` exist?
    -   Does it contain a class inheriting from Pydantic's `BaseSettings` for managing environment variables?

---

## Phase 2 Verification: Database & Job Management

**Goal:** To confirm that the database is correctly set up and integrated with the API for job tracking.

### Prerequisite:
-   **[ ] All Phase 1 checklist items must be complete.**

### Checklist:

-   **[ ] 2.1: ORM Models Verified**
    -   Does the file `backend/app/models/sql_models.py` exist?
    -   Does it define the classes: `AnalysisJob`, `AgentLog`, and `FinalReport`?

-   **[ ] 2.2: Database Session Verified**
    -   Does the file `backend/app/db/session.py` exist?
    -   Does it initialize a SQLAlchemy `engine` and `sessionmaker`?

-   **[ ] 2.3: Database Initialization Verified**
    -   Can you manually run a script or confirm a FastAPI startup event exists to create the database tables?
    -   After running the app for the first time, does a SQLite database file (e.g., `database.db`) appear?

-   **[ ] 2.4: API Integration Verified**
    -   Run the backend server.
    -   Send a `POST` request to `/api/analyze/url`. Do you receive a `task_id` in the response?
    -   Inspect the database. Was a new row added to the `analysis_jobs` table with a `PENDING` status?

---

## Phase 3 Verification: RAG Ingestion Pipeline

**Goal:** To confirm that the system can retrieve, process, and vectorize source code.

### Prerequisite:
-   **[ ] All Phase 2 checklist items must be complete.**

### Checklist:

-   **[ ] 3.1: Code Retrieval Verified**
    -   Does the file `backend/app/services/code_retriever.py` exist?
    -   Can you manually execute its functions with a test Git URL and ZIP file and see the code appear in a temporary local directory?

-   **[ ] 3.2: Code Splitter Verified**
    -   Is there a service responsible for code splitting?
    -   Can you verify that it chunks a sample source file and attaches the required metadata?

-   **[ ] 3.3: Vector Database Verified**
    -   Does `backend/app/services/vector_store.py` exist and correctly initialize a ChromaDB client?

-   **[ ] 3.4: Full Pipeline Verified**
    -   Trigger the end-to-end RAG pipeline (e.g., via a test script or an API call).
    -   Does the corresponding `AnalysisJob` in the database update its status to `PROCESSING_RAG`?
    -   Does a new ChromaDB collection, named with the `task_id`, get created and populated with data?

---

## Phase 4 Verification: AI Agent & Toolbox

**Goal:** To confirm the AI Agent can be initialized and all its tools are implemented.

### Prerequisite:
-   **[ ] All Phase 3 checklist items must be complete.**

### Checklist:

-   **[ ] 4.1: Agent Framework Verified**
    -   Is there a service for the AI Agent (e.g., `backend/app/services/agent.py`)?
    -   Can the agent be initialized without errors?

-   **[ ] 4.2: Toolbox Verified**
    -   For each of the 7 tools, does a corresponding implementation exist in the services layer? (e.g., `list_project_files`, `query_codebase`, etc.)
    -   Can each tool be called individually and return an expected output?

-   **[ ] 4.3: Logging Verified**
    -   Trigger a test run of the agent.
    -   Are new rows being added to the `agent_logs` table for each step the agent takes?

---

## Phase 5 Verification: Frontend User Interface

**Goal:** To confirm the Next.js frontend is set up and can communicate with the backend.

### Prerequisite:
-   **[ ] All Phase 1-4 backend checklist items must be complete.** The backend must be running.

### Checklist:

-   **[ ] 5.1: Project Structure Verified**
    -   Does a `frontend/` directory exist with a standard Next.js project structure?

-   **[ ] 5.2: Submission UI Verified**
    -   Run the frontend application.
    -   Does the UI display a form for submitting a URL or uploading a file?
    -   When you submit, does it successfully make a `POST` call to the backend API?

-   **[ ] 5.3: Report Page Verified**
    -   After submitting, are you redirected to a report page (e.g., `/report/some-task-id`)?
    -   Does the page correctly poll the backend's `GET /api/report/{task_id}` endpoint and display the changing job status?

---

## Phase 6 Verification: Final Integration

**Goal:** To confirm all components work together seamlessly in an end-to-end flow.

### Prerequisite:
-   **[ ] All Phase 1-5 checklist items must be complete.**

### Checklist:

-   **[ ] 6.1: `AnalysisManager` Verified**
    -   Is there a high-level `AnalysisManager` service in the backend?
    -   When a new job is submitted, is this manager correctly invoked as a background task?

-   **[ ] 6.2: End-to-End Flow Verified**
    -   Submit a new analysis job from the frontend.
    -   Monitor the job status in the database and on the frontend page. Does it progress through `PENDING` -> `PROCESSING_RAG` -> `PROCESSING_AGENT` -> `COMPLETE`?
    -   Is the final report stored in the `final_reports` table?
    -   Is the final report correctly displayed on the frontend?

-   **[ ] 6.3: Cleanup Verified**
    -   After a job is `COMPLETE`, check the temporary file system. Is the source code directory deleted?
    -   Check the vector database. Is the job-specific ChromaDB collection deleted? 