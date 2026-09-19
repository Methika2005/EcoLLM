from pydantic import BaseModel
from typing import List


class Finding(BaseModel):
    item: str
    finding: str
    severity: str
    recommendation: str


class InspectionReport(BaseModel):
    document_type: str
    title: str
    summary: str
    findings: List[Finding]
    overall_severity: str
    recommendations: List[str]