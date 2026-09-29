"""
tools.py  -- Person B owns this file. C and D fill in the bodies.

THE CONTRACT (publish this in the team chat at hour 1):

    Every tool is a plain python function.
    Input : keyword arguments only, all JSON-serialisable.
    Output: a STRING. Always. Even on failure -- return "ERROR: <what happened>".
            Never raise, never return an object, never print.
    Max ~2000 chars of output (it goes back into the model's context).

Register a tool by adding it to TOOLS with a one-line description.
The description is what the model sees, so it must be blunt and literal.
"""

import json
import os
import subprocess

# ---------------------------------------------------------------- D's tool
def run_python(code: str) -> str:
    """Person D replaces this body with the Docker sandbox call."""
    try:
        proc = subprocess.run(
            ["docker", "run", "--rm", "--network", "none",
             "--memory", "512m", "--cpus", "1",
             "-i", "python:3.11-slim", "python", "-c", code],
            capture_output=True, text=True, timeout=30,
        )
        out = (proc.stdout + proc.stderr).strip()
        return out[:2000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: execution timed out after 30s"
    except Exception as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------- C's tools
def read_document(path: str) -> str:
    """Extract structured information from a local PDF/image using C's vision pipeline."""
    try:
        import json
        import pymupdf
        from src.pdf_processor import pdf_to_images
        from src.extract import extract_document

        ext = os.path.splitext(path)[1].lower()

        if ext == ".pdf":
            native_pages = []
            scanned_pages = []
            with pymupdf.open(path) as pdf:
                for page_number, page in enumerate(pdf):
                    text = page.get_text().strip()
                    if text:
                        native_pages.append({
                            "page": page_number,
                            "result": {
                                "document_type": "PDF text",
                                "summary": text,
                                "source_notes": text,
                            },
                        })
                    else:
                        scanned_pages.append(page_number)

            if len(scanned_pages) > 8:
                return (
                    "ERROR: PDF contains more than 8 scanned pages; "
                    "split the report into smaller files."
                )

            images = pdf_to_images(
                path,
                "uploads/pdf_pages",
                page_numbers=scanned_pages,
            )
            page_results = [
                (entry["page"], entry["result"])
                for entry in native_pages
            ]
            page_results.extend(
                (page_number, json.loads(extract_document(image_path)))
                for page_number, image_path in zip(scanned_pages, images)
            )
            if not page_results:
                return "ERROR: no pages found in document"
            page_results.sort(key=lambda entry: entry[0])
            return json.dumps([result for _, result in page_results])[:2000]
        elif ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
            images = [path]
        else:
            return f"ERROR: unsupported document type: {ext}"

        if not images:
            return "ERROR: no pages found in document"

        results = [json.loads(extract_document(image_path)) for image_path in images]

        return json.dumps(results)[:2000]

    except Exception as e:
        return f"ERROR: document processing failed: {e}"


def search_documents(query: str) -> str:
    """Person C: vector search over the ingested corpus. Return top chunks."""
    return "ERROR: search_documents not implemented yet"


# ---------------------------------------------------------------- B's tool
def write_report(title: str, sections_json: str) -> str:
    """
    Render a structured report to .docx via python-docx.
    sections_json: '[{"heading": "...", "body": "..."}, ...]'
    """
    try:
        from docx import Document
        sections = json.loads(sections_json)
        doc = Document()
        doc.add_heading(title, 0)
        for s in sections:
            doc.add_heading(str(s.get("heading", "")), level=1)
            doc.add_paragraph(str(s.get("body", "")))
        os.makedirs("output", exist_ok=True)
        out = f"output/{title.replace(' ', '_')[:40]}.docx"
        doc.save(out)
        return f"Report written to {out}"
    except Exception as e:
        return f"ERROR: {e}"


TOOLS = {
    "run_python": (run_python,
        "Execute Python code in an offline sandbox. Args: code (string). Returns stdout."),
    "read_document": (read_document,
        "Read and OCR a local file. Args: path (string). Returns extracted text."),
    "search_documents": (search_documents,
        "Search the local document index. Args: query (string). Returns matching passages."),
    "write_report": (write_report,
        'Save a Word report. Args: title (string), sections_json (JSON array of {"heading","body"}).'),
}


def tool_manifest() -> str:
    """Human-readable tool list injected into the system prompt."""
    return "\n".join(f"- {name}: {desc}" for name, (_, desc) in TOOLS.items())


def call_tool(name: str, args: dict) -> str:
    if name not in TOOLS:
        return f"ERROR: unknown tool '{name}'. Available: {list(TOOLS)}"
    fn, _ = TOOLS[name]
    try:
        return str(fn(**args))[:2000]
    except TypeError as e:
        return f"ERROR: bad arguments for {name}: {e}"
    except Exception as e:
        return f"ERROR: {name} failed: {e}"
