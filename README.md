# EcoLLM — Sovereign On-Premise Agentic AI Workbench

> **Smart Automation | PS ID: 26117**  
> **Team: GreenForGood**

EcoLLM is a local-first, on-premise agentic AI workbench designed for confidential industrial workflows.

It combines open-weight multimodal language models, intelligent task routing, document understanding, workflow orchestration, sandboxed code execution, and human-in-the-loop review into a single local system.

The goal is simple:

**Process sensitive industrial information locally, automate repetitive decisions and documentation, and keep humans in control of important actions.**

---

## 1. Problem Statement

Industrial organizations often work with sensitive documents, inspection reports, maintenance records, and operational data.

Sending such information to external AI services can introduce concerns around:

- Data confidentiality
- Intellectual property
- Regulatory requirements
- Vendor dependency
- Network availability
- Control over AI-generated outputs

At the same time, manually processing every document is slow and difficult to scale.

EcoLLM addresses this by providing a **local agentic AI workflow** where models, document processing, orchestration, and tool execution run on the organization's own machine or infrastructure.

---

## 2. What EcoLLM Does

EcoLLM can:

- Accept industrial documents such as PDFs
- Understand scanned/image-based documents using a local vision-language model
- Route tasks to different local models based on the task type
- Extract structured inspection information
- Normalize findings, abnormalities, actions, and inspection status
- Assign workflow priority using defined business rules
- Route cases for human review
- Generate Word-based review/approval documents
- Execute Python code inside a network-isolated Docker container
- Maintain an agentic tool-calling loop
- Process multiple documents through a workflow queue
- Provide a local browser-based interface

The system is designed around **AI-assisted automation rather than autonomous safety-critical decision making**.

---

## 3. Architecture

```text
                    ┌─────────────────────────┐
                    │       Local Web UI       │
                    │    127.0.0.1:8080       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       EcoLLM Agent       │
                    │   Agentic Tool Calling    │
                    └────────────┬────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
               ▼                 ▼                 ▼
        ┌────────────┐    ┌────────────┐    ┌────────────┐
        │   Router   │    │   Tools    │    │  Workflow  │
        │            │    │            │    │   Queue    │
        └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
              │                 │                 │
      ┌───────┼───────┐         │          ┌──────┼──────┐
      │       │       │         │          │      │      │
      ▼       ▼       ▼         ▼          ▼      ▼      ▼
    Qwen    Qwen    Qwen    Document    HIGH   MEDIUM   LOW
    2.5     2.5     2.5     Processing
    7B      Coder   VL 3B
            7B
````

All model inference is performed through the local Ollama instance:

```text
http://localhost:11434
```

The browser interface runs locally at:

```text
http://127.0.0.1:8080
```

---

## 4. Models

EcoLLM uses multiple local open-weight models instead of sending every task to a single model.

### Qwen2.5 7B

Used for:

* General reasoning
* Document-related tasks
* Workflow reasoning
* Structured inspection interpretation
* Report generation

### Qwen2.5-Coder 7B

Used for:

* Programming tasks
* Code generation
* Code-oriented reasoning

### Qwen2.5-VL 3B

Used for:

* Scanned documents
* Image-based PDFs
* Visual document understanding
* Extraction of information from inspection documents

---

## 5. Intelligent Model Routing

EcoLLM selects an initial model based on the task.

```text
Task
 │
 ├── Code-related
 │       └── Qwen2.5-Coder 7B
 │
 ├── Scanned/image/PDF understanding
 │       └── Qwen2.5-VL 3B
 │
 └── General/document reasoning
         └── Qwen2.5 7B
```

For document workflows, the vision model can extract information from scanned pages before handing the structured information to the general reasoning model.

This avoids unnecessarily using the vision model for tasks that do not require visual understanding.

---

## 6. Agentic Tool Loop

The agent communicates with tools using structured JSON.

The basic flow is:

```text
User Task
   │
   ▼
Model Selection
   │
   ▼
Agent Reasoning
   │
   ▼
Tool Selection
   │
   ├── read_document
   ├── run_python
   └── write_report
   │
   ▼
Tool Result
   │
   ▼
Agent Continues Reasoning
   │
   ▼
Final Response
```

The loop includes safeguards such as:

* Maximum number of agent steps
* Bounded context
* Tool failure recovery
* Structured output parsing
* Model handoff after document extraction

---

## 7. Industrial Inspection Workflow

One of the main EcoLLM workflows is inspection-report processing.

### Input

A user provides an inspection report, such as a scanned PDF.

### Processing

```text
Inspection PDF
      │
      ▼
PDF Analysis
      │
      ├── Native text available
      │       └── Extract text directly
      │
      └── Scanned page
              └── Qwen2.5-VL 3B
                       │
                       ▼
              Structured Extraction
                       │
                       ▼
                 Normalization
                       │
                       ▼
                 Workflow Triage
```

### Extracted Information

EcoLLM separates information into meaningful fields:

* Equipment
* Inspection status
* Overall condition
* Summary
* Key findings
* Abnormalities
* Recommended actions
* Workflow priority
* Workflow assessment
* Workflow action

This prevents workflow severity from being incorrectly presented as the physical inspection status.

---

## 8. Workflow Orchestration

EcoLLM includes a workflow queue so that documents can be processed as workflow items instead of treating every upload as an isolated chatbot request.

Each work item can contain:

* File path
* Status
* Priority
* Reason
* Required action
* Alert requirement
* Extracted inspection information
* Generated outputs

The workflow can process multiple reports and triage them according to defined rules.

---

## 9. Priority and Human Review

The workflow uses three priority levels:

| Priority | Workflow Behaviour       |
| -------- | ------------------------ |
| HIGH     | Alert and human review   |
| MEDIUM   | Review/approval workflow |
| LOW      | Record and monitor       |

The priority is a workflow-level classification and is kept separate from the inspection's physical condition/status.

### HIGH

High-priority cases generate a human-review alert.

```text
HIGH
  ↓
ALERT_AND_HUMAN_REVIEW
  ↓
ALERT_REQUIRED
```

### MEDIUM

Medium-priority cases can enter a review/report workflow.

```text
MEDIUM
  ↓
GENERATE_REPORT_AND_REVIEW
  ↓
REVIEW_REQUIRED
  ↓
Word Review / Approval Note
```

### LOW

Low-priority cases can be recorded for monitoring.

```text
LOW
  ↓
RECORD_AND_MONITOR
  ↓
MONITORING
```

The system is intended to support human decision-making rather than independently making safety-critical decisions.

---

## 10. Word Report Generation

EcoLLM can generate a Word document from structured inspection information.

For example:

```text
Inspection Report
       │
       ▼
AI Extraction
       │
       ▼
Workflow Triage
       │
       ▼
Review Required
       │
       ▼
Word Approval / Review Note
```

Generated reports can contain sections such as:

* Priority
* Reason
* Required Action
* Inspection Findings

The generated document is stored locally under the project's `output/` directory.

---

## 11. Sandboxed Python Execution

EcoLLM supports Python execution through Docker.

The execution environment is configured with:

```text
--network none
--memory 512m
--cpus 1
```

This provides a restricted environment for agent-generated Python execution.

The sandbox is intended as a practical local isolation mechanism for the demo; it should not be treated as a complete production security boundary without further hardening.

---

## 12. Document Processing

EcoLLM supports PDF processing with different paths depending on the document.

### Text-based PDF

If native text is available:

```text
PDF
 ↓
Native text extraction
 ↓
Structured processing
```

Vision inference is skipped when it is unnecessary.

### Scanned PDF

For scanned pages:

```text
PDF
 ↓
Page rendering
 ↓
Image preprocessing
 ↓
Qwen2.5-VL 3B
 ↓
Structured information
```

For mixed PDFs, vision processing is performed only for scanned pages.

The system also rejects excessively large scanned-PDF workloads rather than silently dropping pages.

---

## 13. Inspection Normalization

Model output can vary in structure and wording.

EcoLLM therefore normalizes inspection information before presenting it to the user.

For example, it separates:

```text
Inspection Status
        ≠
Workflow Priority
```

and distinguishes:

```text
Normal Observation
        ≠
Abnormality
```

Explicit issues such as leakage or above-normal readings can be preserved as abnormalities, while negative observations are not incorrectly classified as problems.

The user-facing result does not expose raw model JSON or internal workflow IDs.

---

## 14. Error Handling

The workflow is designed so that a failure in one document does not automatically abort processing of other documents.

For example:

```text
Document 1 → SUCCESS
Document 2 → PROCESSING ERROR
Document 3 → SUCCESS
Document 4 → SUCCESS
```

The failed document can retain its error information while the remaining workflow items continue.

The agent loop also handles:

* Unknown tools
* Invalid tool arguments
* Malformed model responses
* Excessive agent-loop steps
* Bounded context requirements

---

## 15. Security and Sovereignty

EcoLLM is designed around a local-first architecture.

### Current Design

* Local Ollama inference
* No cloud model API required
* Local browser interface
* Local document processing
* Local generated documents
* Docker-based restricted Python execution
* Network-disabled Python sandbox
* No external CDN dependency for the local UI

### Important Limitation

Running a system locally does not automatically guarantee complete host-level isolation or enterprise-grade security.

For production deployment, additional controls would be required, such as:

* OS-level isolation
* Access control
* Authentication
* Audit logging
* Container hardening
* File-system permissions
* Network policy enforcement
* Resource monitoring
* Security testing

---

## 16. Project Structure

```text
EcoLLM/
│
├── agent/
│   ├── __init__.py
│   └── agent.py
│
├── router/
│   ├── __init__.py
│   └── router.py
│
├── tools/
│   ├── __init__.py
│   └── tools.py
│
├── orchestrator/
│   ├── __init__.py
│   └── workflow.py
│
├── src/
│   ├── extract.py
│   ├── generate_doc.py
│   ├── pdf_processor.py
│   └── schema.py
│
├── tests/
│   ├── __init__.py
│   └── test_loop.py
│
├── uploads/
├── output/
├── app.py
├── CONTRACT.md
├── README.md
└── .gitignore
```

---

## 17. Main Components

### `app.py`

Local browser-based interface and workflow entry point.

### `agent/agent.py`

Implements:

* Local Ollama communication
* Model routing
* Agentic tool loop
* JSON parsing
* Tool invocation
* Context management

### `router/router.py`

Selects an appropriate local model based on the task.

### `tools/tools.py`

Provides tools for:

* Document reading
* Python execution
* Word report generation

### `orchestrator/workflow.py`

Implements:

* Workflow queue
* Priority handling
* Triage
* Alerts
* Human-review routing
* Report-generation actions

### `src/extract.py`

Handles document/image extraction and multimodal model interaction.

### `src/pdf_processor.py`

Handles PDF inspection and page preprocessing.

### `src/schema.py`

Normalizes extracted inspection information into a consistent structure.

### `src/generate_doc.py`

Generates Word documents.

---

## 18. Setup

### Requirements

Recommended environment:

* Windows/Linux/macOS
* Python 3.10+
* Ollama
* Docker Desktop
* Approximately 16 GB RAM for the demonstrated local model setup

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Pull the required Ollama models:

```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5vl:3b
```

Make sure Ollama is running.

---

## 19. Running EcoLLM

From the project root:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:8080
```

---

## 20. Example Tasks

### General document summary

```text
Give me a summary of the inspection report.
```

### Word report

```text
Generate a Word document report for this inspection report.
```

### Multiple reports

```text
Generate a Word document report for all these inspection reports.
```

### Code task

```text
Write Python code to calculate the average inspection reading.
```

The router can direct code-related tasks to the coder model while document and visual tasks are handled by the appropriate models.

---

## 21. Testing

Compile the main Python modules:

```bash
python -m py_compile app.py src\schema.py src\extract.py src\pdf_processor.py tools\tools.py orchestrator\workflow.py
```

Run inspection normalization tests:

```bash
python -m unittest tests.test_inspection_normalization -v
```

Run agent-loop tests:

```bash
python -m tests.test_loop
```

Check Git whitespace:

```bash
git diff --check
```

---

## 22. Current Validation

The current implementation has been validated for:

* Python syntax
* Inspection normalization
* PDF extraction behaviour
* Mixed native/scanned PDFs
* Workflow normalization
* User-facing result formatting
* Malformed model output handling
* Tool failure recovery
* Agent-loop limits
* Context bounds
* Docker network isolation behaviour
* Multi-document error isolation

The exact runtime of multimodal PDF processing can vary significantly depending on the local machine and model state.

---

## 23. Current Capabilities

### Implemented

* Local Ollama inference
* Multi-model routing
* Qwen2.5 7B
* Qwen2.5-Coder 7B
* Qwen2.5-VL 3B
* Agentic tool calling
* PDF processing
* Scanned-document understanding
* Inspection normalization
* Workflow queue
* HIGH/MEDIUM/LOW workflow prioritization
* Human-review routing
* Alert generation
* Word document generation
* Docker sandboxed Python execution
* Local browser UI
* Multi-document error isolation

### Not currently implemented

The following should not be considered completed capabilities:

* Full retrieval-augmented generation (RAG)
* Production-grade authentication
* Enterprise access control
* Full host-level air-gap enforcement
* Production-grade security isolation
* Hardware-level energy telemetry
* Automatic model escalation based on validation confidence

---

## 24. Future Extensions

Potential future improvements include:

* Local document search and retrieval
* Vector-based knowledge base
* Retrieval-augmented generation
* Long-term local memory
* More industrial document formats
* Authentication and role-based access control
* Detailed audit trails
* Stronger sandbox isolation
* Resource and energy monitoring
* Additional open-weight models
* Confidence-based validation and escalation
* Enterprise deployment controls

---

## 25. Design Principles

EcoLLM follows a few core principles:

### Sovereignty

Sensitive industrial information should remain under the organization's control.

### Local-first AI

Use local open-weight models wherever practical.

### Right model for the task

Different tasks should use appropriate models instead of unnecessarily sending everything to the largest model.

### Human-in-the-loop

AI should assist with prioritization and documentation while humans retain control over important decisions.

### Structured automation

Convert unstructured documents into structured workflow information that can drive downstream actions.

### Graceful failure

One failed document or tool call should not unnecessarily break the entire workflow.

### Practical security

Use local execution and sandboxing while recognizing that production deployments require additional security controls.

---

## 26. Hackathon Context

**Hackathon:** Smart Automation
**Problem Statement ID:** 26117
**Project:** EcoLLM
**Team:** GreenForGood

EcoLLM demonstrates how open-weight multimodal models can be combined with agentic workflows to create a practical local AI assistant for confidential industrial environments.

The project focuses on the complete workflow:

```text
Industrial Document
        ↓
Local AI Understanding
        ↓
Structured Information
        ↓
Workflow Triage
        ↓
Priority / Alert
        ↓
Human Review
        ↓
Documented Action
```

---

## 27. Demo Flow

A typical demonstration can follow this sequence:

```text
1. Upload an industrial inspection PDF
              ↓
2. EcoLLM identifies the document workflow
              ↓
3. Qwen2.5-VL processes scanned pages
              ↓
4. Inspection information is normalized
              ↓
5. Workflow queue triages the report
              ↓
6. Priority and required action are determined
              ↓
7. HIGH cases generate human-review alerts
              ↓
8. MEDIUM cases can generate a Word review note
              ↓
9. LOW cases are recorded for monitoring
```

This demonstrates the transition from:

```text
AI model → agent → workflow → action
```

rather than using an LLM only as a conversational chatbot.

---

## Credits & Acknowledgements

EcoLLM was developed with the support of AI-assisted development tools for brainstorming, debugging, documentation, and development assistance.

### AI & Models

- **Ollama** — Used for local inference and serving the open-weight models.
- **Qwen2.5 7B** — Used for general reasoning and document/workflow tasks.
- **Qwen2.5-Coder 7B** — Used for code-related tasks.
- **Qwen2.5-VL 3B** — Used for scanned-document and visual understanding.
- **AI-assisted development tools** — Used as development support for ideation, debugging, code assistance, and documentation.

The architecture, implementation, integration, testing, and final project decisions were carried out and validated by the **GreenForGood** team.
