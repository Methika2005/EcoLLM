"""
router.py  -- Person B
Decides which locally-hosted open-weight model should handle a request.

Rules only, no ML. It must be explainable on stage: that is the point.
"""

from dataclasses import dataclass

# Model names exactly as pulled via `ollama pull`
GENERAL = "qwen2.5:7b"
CODER = "qwen2.5-coder:7b"
VISION = "qwen2.5vl:3b"  # only if C confirms it is pulled

CODE_WORDS = {
    "code", "script", "python", "function", "bug", "debug", "error",
    "traceback", "compile", "regex", "sql", "calculate", "compute",
    "plot", "csv", "dataframe", "algorithm", "refactor", "unit test",
    "simulate", "parse", "api", "json schema",
}

DOC_WORDS = {
    "report", "summarise", "summarize", "inspection", "findings",
    "severity", "recommendation", "clause", "invoice", "form",
    "p&id", "drawing", "scan", "handwritten", "extract", "audit",
}


@dataclass
class Route:
    model: str
    reason: str          # shown in the demo UI -- judges love visible reasoning
    needs_vision: bool = False


def route(task_text: str, has_file: bool = False, file_kind: str = "") -> Route:
    """
    task_text : the user's request
    has_file  : True if a document/image was attached
    file_kind : "image" | "pdf" | "text" | "" (Person C sets this)
    """
    t = (task_text or "").lower()

    # 1. Anything with an image/scan must start on the vision model.
    if has_file and file_kind in ("image", "pdf_scanned"):
        return Route(VISION, "Scanned input detected -> vision model for OCR pass", True)

    # 2. Explicit code/computation intent.
    hits = [w for w in CODE_WORDS if w in t]
    if hits:
        return Route(CODER, f"Code intent keywords: {', '.join(sorted(hits)[:3])}")

    # 3. Document understanding / structured reporting.
    dhits = [w for w in DOC_WORDS if w in t]
    if has_file or dhits:
        return Route(GENERAL, "Document/reporting task -> general reasoning model")

    # 4. Default.
    return Route(GENERAL, "General query -> default reasoning model")


if __name__ == "__main__":
    tests = [
        ("Write a python script to compute pipe wall thickness", False, ""),
        ("Summarise the inspection findings and give severity", True, "pdf"),
        ("Read this scanned form", True, "image"),
        ("What is ISO 9001", False, ""),
    ]
    for txt, hf, fk in tests:
        r = route(txt, hf, fk)
        print(f"{txt[:45]:48s} -> {r.model:20s} ({r.reason})")
