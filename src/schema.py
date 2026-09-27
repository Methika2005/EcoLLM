from pydantic import BaseModel
from pydantic import Field
from typing import Any, List


class Finding(BaseModel):
    item: str = ""
    finding: str = ""
    severity: str = ""
    recommendation: str = ""


class InspectionReport(BaseModel):
    document_type: str
    title: str
    summary: str
    findings: List[Finding]
    overall_severity: str
    recommendations: List[str]


class InspectionResult(BaseModel):
    """Canonical inspection details, kept separate from workflow priority."""

    equipment_inspected: str = ""
    inspection_status: str = ""
    overall_condition: str = ""
    key_findings: List[Finding] = Field(default_factory=list)
    abnormalities: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    source_notes: str = ""

    document_type: str = ""
    title: str = ""
    summary: str = ""
    overall_severity: str = ""

    def as_dict(self) -> dict:
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()

    def to_triage_text(self) -> str:
        if hasattr(self, "model_dump_json"):
            return self.model_dump_json()
        return self.json()

    def to_display_text(self) -> str:
        lines = []
        for label, value in (
            ("Equipment inspected", self.equipment_inspected),
            ("Inspection status", self.inspection_status),
            ("Overall condition", self.overall_condition),
            ("Summary", self.summary),
        ):
            if value:
                lines.append(f"{label}: {value}")

        if self.overall_severity:
            lines.append(f"Source-reported inspection severity: {self.overall_severity}")

        for label, values in (
            ("Key findings", self.key_findings),
            ("Abnormalities", self.abnormalities),
            ("Recommended actions", self.recommended_actions),
        ):
            if values:
                lines.append(f"{label}:")
                for value in values:
                    if isinstance(value, Finding):
                        detail = value.finding
                        if value.item:
                            detail = f"{value.item}: {detail}" if detail else value.item
                        if value.severity:
                            detail += f" (reported severity: {value.severity})"
                        if value.recommendation:
                            detail += f" Recommendation: {value.recommendation}"
                        lines.append(f"- {detail}")
                    else:
                        lines.append(f"- {value}")

        if self.source_notes:
            lines.append(f"Source notes: {self.source_notes}")

        return "\n".join(lines) or "No inspection details were provided."


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        import json
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _string_list(value: Any) -> List[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [text for entry in values if (text := _text(entry))]


def _finding_list(value: Any) -> List[Finding]:
    if value is None:
        return []

    values = value if isinstance(value, list) else [value]
    findings = []
    for entry in values:
        if isinstance(entry, dict):
            findings.append(Finding(
                item=_text(entry.get("item")),
                finding=_text(entry.get("finding") or entry.get("description")),
                severity=_text(entry.get("severity")),
                recommendation=_text(entry.get("recommendation")),
            ))
        else:
            text = _text(entry)
            if text:
                findings.append(Finding(finding=text))
    return findings


def _parse_labeled_text(text: str) -> dict:
    import re

    aliases = {
        "equipment inspected": "equipment_inspected",
        "equipment": "equipment_inspected",
        "subject inspected": "equipment_inspected",
        "inspection status": "inspection_status",
        "overall condition": "overall_condition",
        "key findings": "key_findings",
        "findings": "key_findings",
        "abnormalities": "abnormalities",
        "recommended actions": "recommended_actions",
        "recommended action": "recommended_actions",
        "summary": "summary",
    }
    result = {}
    for line in text.splitlines():
        match = re.match(r"^\s*([^:]+)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        field = aliases.get(match.group(1).strip().lower())
        if not field or not match.group(2):
            continue
        if field in {"key_findings", "abnormalities", "recommended_actions"}:
            result.setdefault(field, []).append(match.group(2))
        else:
            result[field] = match.group(2)
    return result


def _merge_page_payloads(pages: List[dict]) -> dict:
    merged = {}
    list_fields = {
        "key_findings", "findings", "abnormalities",
        "recommended_actions", "recommendations",
    }
    for page in pages:
        for key, value in page.items():
            if key in list_fields:
                values = value if isinstance(value, list) else [value]
                merged.setdefault(key, []).extend(values)
            elif key in {"summary", "source_notes"}:
                text = _text(value)
                if text and text not in merged.get(key, []):
                    merged.setdefault(key, []).append(text)
            elif not merged.get(key) and value not in (None, "", [], {}):
                merged[key] = value

    for key in ("summary", "source_notes"):
        if key in merged:
            merged[key] = "\n".join(merged[key])
    return merged


def normalize_inspection_result(raw: Any) -> InspectionResult:
    """Normalize structured JSON or preserve unstructured output without guessing."""
    import json
    import re

    if isinstance(raw, InspectionResult):
        return raw

    if isinstance(raw, dict):
        payload = raw
        source_text = ""
    else:
        source_text = _text(raw)
        payload = None
        candidate = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", source_text, flags=re.IGNORECASE)
        try:
            decoded = json.loads(candidate)
            if isinstance(decoded, dict):
                payload = decoded
            elif isinstance(decoded, list) and all(
                isinstance(page, dict) for page in decoded
            ):
                payload = _merge_page_payloads(decoded)
        except json.JSONDecodeError:
            pass

        if payload is None:
            payload = _parse_labeled_text(source_text)
            if not payload:
                return InspectionResult(source_notes=source_text)
            payload["source_notes"] = source_text

    known_fields = {
        "equipment_inspected", "inspection_status", "overall_condition",
        "key_findings", "findings", "abnormalities", "recommended_actions",
        "recommendations", "source_notes", "document_type", "title", "summary",
        "overall_severity",
    }
    extra_fields = {
        key: value for key, value in payload.items()
        if key not in known_fields and value not in (None, "", [], {})
    }
    source_notes = _text(payload.get("source_notes"))
    if extra_fields:
        extra_notes = json.dumps(extra_fields, ensure_ascii=False)
        source_notes = "\n".join(part for part in (source_notes, extra_notes) if part)

    return InspectionResult(
        equipment_inspected=_text(payload.get("equipment_inspected")),
        inspection_status=_text(payload.get("inspection_status")),
        overall_condition=_text(payload.get("overall_condition")),
        key_findings=_finding_list(payload.get("key_findings", payload.get("findings"))),
        abnormalities=_string_list(payload.get("abnormalities")),
        recommended_actions=_string_list(
            payload.get("recommended_actions", payload.get("recommendations"))
        ),
        source_notes=source_notes,
        document_type=_text(payload.get("document_type")),
        title=_text(payload.get("title")),
        summary=_text(payload.get("summary")),
        overall_severity=_text(payload.get("overall_severity")),
    )