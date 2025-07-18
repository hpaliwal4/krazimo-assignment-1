# AI Agent Playbooks

This document contains the detailed, step-by-step playbooks for the AI Agent. Each playbook is a sequence of tool calls and reasoning steps designed to solve a specific analysis goal defined in our project scope.

---

## Playbook 1: God Class Detection and Refactoring

**Goal:** To identify classes that violate the Single Responsibility Principle and suggest a concrete refactoring plan.

-   **Step 1: Initial Sweep for Candidates**
    -   **Agent Thought:** "I need to find all classes in the project that are unusually large, which might indicate they are God Classes."
    -   **Tool Call:** `list_project_files()` to get a list of all source files.
    -   **Tool Call (Loop):** For each file, call `get_code_metrics(file_path=...)` to get metrics for every class within that file.
    -   **Agent Logic:** Filter this list for classes that exceed a baseline threshold (e.g., more than 15 methods OR more than 200 lines of code). This creates a list of "candidate classes."

-   **Step 2: Semantic Confirmation**
    -   **Agent Thought:** "I have a list of large classes. Now I must determine if they handle multiple, unrelated responsibilities."
    -   **Tool Call (Loop):** For each candidate class:
        -   **LLM Prompt:** `Analyze the following code for the class '{class_name}'. Based on the method names and their contents, does this class appear to handle multiple distinct business domains (e.g., user management, billing, and logging all in one place)? Please list the distinct responsibilities you can identify.`
    -   **Agent Logic:** If the LLM identifies more than one distinct responsibility, the class is confirmed as a God Class.

-   **Step 3: Formulate a Refactoring Plan**
    -   **Agent Thought:** "I have confirmed `{class_name}` is a God Class handling {responsibility_A} and {responsibility_B}. I will now find which methods belong to each responsibility to suggest a clear split."
    -   **Tool Call (Loop):** For each identified responsibility:
        -   `query_codebase(semantic_query="Methods in class {class_name} that are semantically related to '{responsibility_name}'")`
    -   **Agent Logic:** The agent now has clusters of methods associated with each responsibility.

-   **Step 4: Synthesize Final Report**
    -   **LLM Prompt:** `The class '{class_name}' has been identified as a God Class. It handles the following distinct responsibilities: {list_of_responsibilities}. **Recommendation:** Refactor this class by creating new, smaller classes. For example, create a '{NewClassA_name}' and move the following methods into it: {list_of_methods_A}. Create a '{NewClassB_name}' and move the following methods into it: {list_of_methods_B}.`

---

## Playbook 2: Circular Dependency Detection

**Goal:** To find and explain circular import references between modules.

-   **Step 1: Build and Analyze the Dependency Graph**
    -   **Agent Thought:** "I need to understand the import structure of the entire project to find cycles."
    -   **Tool Call:** `build_dependency_graph()`
    -   **Observation:** The tool returns a list of detected cycles (e.g., `[['file_a.py', 'file_b.py'], ['file_c.py', 'file_d.py']]`).

-   **Step 2: Explain the Findings**
    -   **Agent Thought:** "I have found one or more circular dependencies. I need to explain the problem clearly for each one."
    -   **Tool Call (Loop):** For each detected cycle:
        -   **LLM Prompt:** `A circular dependency was detected between the following files: {file_list}. In simple terms, explain why this is a problem for software maintainability and initialization. Then, suggest two common strategies to resolve it: 1) Using Dependency Injection, and 2) Extracting shared logic into a third, independent module.`

---

## Playbook 3: High Cyclomatic Complexity

**Goal:** To find functions that are too complex and recommend simplification.

-   **Step 1: Identify Complex Functions**
    -   **Agent Thought:** "I will scan all functions in the project to find any that are too complex."
    -   **Tool Call:** `list_project_files()`
    -   **Tool Call (Loop):** For each file, call `get_code_metrics(file_path=...)` to get the cyclomatic complexity for every function.
    -   **Agent Logic:** Filter this list for functions that exceed a complexity threshold (e.g., > 10).

-   **Step 2: Generate Recommendation**
    -   **Agent Thought:** "I have found complex functions. I need to explain the risk and suggest refactoring."
    -   **Tool Call (Loop):** For each complex function:
        -   **LLM Prompt:** `The function '{function_name}' in '{file_path}' has a cyclomatic complexity of {complexity_score}, which is high. Explain that this makes the function difficult to test and maintain. Recommend refactoring it by extracting parts of its logic into smaller, well-named helper functions.`

---

## Playbook 4: Full Dependency Health Analysis

**Goal:** To report on both CVEs and the general maintenance health of all dependencies.

-   **Step 1: Run the Health Check**
    -   **Agent Thought:** "I will now perform a comprehensive health check on all third-party dependencies."
    -   **Tool Call:** `run_dependency_health_check()`
    -   **Observation:** The tool returns a list of structured objects, one for each dependency, containing CVE info, version status, and maintenance data.

-   **Step 2: Process and Categorize Findings**
    -   **Agent Thought:** "I will now process these results and create two distinct categories: immediate threats and long-term risks."
    -   **Agent Logic (Loop):** For each dependency:
        -   If it has a CVE, add it to the "Immediate Security Threats" list.
        -   If it is marked as unmaintained or the last commit was over 2 years ago, add it to the "Maintenance & Future Risks" list.

-   **Step 3: Generate Actionable Report Items**
    -   **Agent Thought:** "For each identified issue, I will generate a clear report."
    -   **Agent Logic (Loop):**
        -   **For CVEs:** Generate a `diff` to update the package file to the recommended secure version. Use an LLM prompt to summarize the CVE risk.
        -   **For Abandoned Libraries:** Use an LLM prompt to explain the risk of using unmaintained code and, if possible, `query_codebase(semantic_query="What is the primary purpose of the library '{library_name}' in this project?")` to help suggest a modern alternative.

---

## Playbook 5: Hardcoded Secret Detection

**Goal:** To find potentially hardcoded credentials in the source code.

-   **Step 1: Scan for Secrets**
    -   **Agent Thought:** "I will scan the codebase for patterns that look like hardcoded secrets."
    -   **Tool Call:** `scan_for_secrets()`. This new tool will use a combination of regular expressions for common API key formats and entropy analysis.
    -   **Observation:** The tool returns a list of potential secrets and their locations.

-   **Step 2: Report the Findings**
    -   **Agent Thought:** "I have found potential secrets. I need to report them with a strong recommendation."
    -   **Tool Call (Loop):** For each finding:
        -   **LLM Prompt:** `A potential hardcoded secret was found in '{file_path}' on line {line_number}. Explain that storing secrets in source code is a major security risk and strongly recommend moving it to an environment variable or a dedicated secrets management service.`

---

## Playbook 6: Potential IDOR Detection

**Goal:** To find API endpoints that may be vulnerable to Insecure Direct Object Reference attacks.

-   **Step 1: Find Candidate Endpoints**
    -   **Agent Thought:** "I need to find all API endpoints where the code retrieves an item from a database using an ID that comes directly from the user's request."
    -   **Tool Call:** `query_codebase(semantic_query="API endpoint that fetches a database record using an ID from a URL path or request parameter")`
    -   **Observation:** RAG returns a list of code chunks that match this pattern.

-   **Step 2: Analyze for Missing Authorization**
    -   **Agent Thought:** "I have a list of candidate functions. I must now analyze each one to see if it performs an ownership check."
    -   **Tool Call (Loop):** For each code chunk:
        -   **LLM Prompt:** `Analyze the following code for a potential Insecure Direct Object Reference (IDOR) vulnerability. The key question is: **Before querying the database for the object with '{id_variable_name}', does the code verify that the currently authenticated user has permission to access it?** Please answer with a simple 'Yes' or 'No', followed by a brief explanation of your reasoning.`
    -   **Agent Logic:** If the LLM answers "No", the agent flags it as a potential vulnerability.

-   **Step 3: Generate the Report**
    -   **LLM Prompt:** `The endpoint defined in '{file_path}' appears to fetch a resource by its ID without verifying the user's ownership of that resource. This could allow users to access data belonging to others. **Recommendation:** Before executing the database query, add an authorization check to ensure the resource's owner ID matches the current user's ID.` 