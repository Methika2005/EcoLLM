"""
EcoLLM Workflow Orchestrator

Handles multiple industrial reports by:
1. Maintaining a work queue
2. Tracking report status
3. Storing AI-assigned priority
4. Deciding the next workflow action
5. Executing the required workflow
6. Tracking generated outputs and alerts
"""

from dataclasses import dataclass, field
from typing import Optional
import json

from agent.agent import chat, parse
from src.schema import InspectionResult, normalize_inspection_result
from tools.tools import write_report


@dataclass
class WorkItem:
    """Represents one industrial document in the workflow."""

    id: str
    file_path: str

    status: str = "PENDING"

    priority: Optional[str] = None
    reason: str = ""
    required_action: str = ""

    alert_required: bool = False

    outputs: list[str] = field(default_factory=list)
    inspection_result: InspectionResult = field(default_factory=InspectionResult)


@dataclass
class Alert:
    """Represents a local workflow alert."""

    item_id: str
    priority: str
    message: str
    required_action: str
    status: str = "PENDING_REVIEW"


class WorkflowQueue:
    """Stores and manages incoming industrial work items."""

    def __init__(self):
        self.items: list[WorkItem] = []
        self.alerts: list[Alert] = []

    def add(self, item: WorkItem) -> None:
        """Add a report to the queue."""
        self.items.append(item)

    def get_all(self) -> list[WorkItem]:
        """Return all reports in the queue."""
        return self.items

    def get_pending(self) -> list[WorkItem]:
        """Return reports that still need processing."""
        return [
            item
            for item in self.items
            if item.status == "PENDING"
        ]

    def get_by_priority(self, priority: str) -> list[WorkItem]:
        """Return reports matching a priority."""
        return [
            item
            for item in self.items
            if item.priority == priority
        ]

    def get_prioritized(self) -> list[WorkItem]:
        """
        Return triaged reports ordered by priority.

        HIGH reports are handled first, followed by MEDIUM,
        then LOW.
        """

        priority_order = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2,
        }

        return sorted(
            [
                item
                for item in self.items
                if item.priority in priority_order
            ],
            key=lambda item: priority_order[item.priority],
        )

    def process_prioritized(
        self,
        reports: dict[str, str],
    ) -> list[dict]:
        """
        Process triaged reports in priority order.

        reports maps item IDs to their extracted report text.
        """

        results = []

        for item in self.get_prioritized():

            extracted_report = reports.get(item.id)

            if extracted_report is None:
                results.append({
                    "id": item.id,
                    "status": "ERROR",
                    "message": "Extracted report not provided.",
                })
                continue

            action = self.decide_action(item.id)

            execution = self.execute_action(
                item.id,
                extracted_report,
            )

            results.append({
                "id": item.id,
                "priority": item.priority,
                "action": action,
                "status": item.status,
                "execution": execution,
                "inspection_result": item.inspection_result.as_dict(),
                "summary": item.inspection_result.to_display_text(),
            })

        return results

    def update_priority(
        self,
        item_id: str,
        priority: str,
        reason: str,
        required_action: str,
        alert_required: bool = False,
    ) -> bool:
        """Update the result of priority analysis."""

        for item in self.items:
            if item.id == item_id:
                item.priority = priority
                item.reason = reason
                item.required_action = required_action
                item.alert_required = alert_required
                item.status = "TRIAGED"
                return True

        return False

    def triage_item(
        self,
        item_id: str,
        extracted_report: str,
    ) -> bool:
        """Analyze a report and store its triage result."""

        item = next(
            (item for item in self.items if item.id == item_id),
            None,
        )
        if item is None:
            return False

        item.inspection_result = normalize_inspection_result(extracted_report)
        result = triage_report(item.inspection_result.to_triage_text())

        return self.update_priority(
            item_id=item_id,
            priority=result["priority"],
            reason=result["reason"],
            required_action=result["required_action"],
            alert_required=result["alert_required"],
        )

    def decide_action(self, item_id: str) -> str:
        """
        Decide the next workflow action based on priority.

        This method only decides the action.
        It does not execute the action.
        """

        for item in self.items:
            if item.id == item_id:

                if item.status != "TRIAGED":
                    return "TRIAGE_REQUIRED"

                if item.priority == "HIGH":
                    return "ALERT_AND_HUMAN_REVIEW"

                if item.priority == "MEDIUM":
                    return "GENERATE_REPORT_AND_REVIEW"

                if item.priority == "LOW":
                    return "RECORD_AND_MONITOR"

                return "HUMAN_REVIEW"

        return "ITEM_NOT_FOUND"

    def create_alert(self, item_id: str) -> str:
        """Create a local alert for a high-priority report."""

        for item in self.items:
            if item.id == item_id:

                if item.priority != "HIGH":
                    return "ALERT_NOT_REQUIRED"

                alert = Alert(
                    item_id=item.id,
                    priority=item.priority,
                    message=(
                        f"High-priority issue detected in report "
                        f"{item.id}: {item.reason}"
                    ),
                    required_action=item.required_action,
                )

                self.alerts.append(alert)

                item.status = "ALERT_REQUIRED"

                return (
                    f"ALERT CREATED: {alert.message} | "
                    f"Action: {alert.required_action}"
                )

        return "ITEM_NOT_FOUND"

    def get_alerts(self) -> list[Alert]:
        """Return all local alerts."""
        return self.alerts

    def execute_action(
        self,
        item_id: str,
        extracted_report: str,
    ) -> str:
        """
        Execute the workflow selected for an item.
        """

        for item in self.items:
            if item.id == item_id:
                break
        else:
            return "ITEM_NOT_FOUND"

        action = self.decide_action(item_id)

        if action == "TRIAGE_REQUIRED":
            return "TRIAGE_REQUIRED"

        if action == "ITEM_NOT_FOUND":
            return "ITEM_NOT_FOUND"

        if action == "GENERATE_REPORT_AND_REVIEW":

            title = (
                "Approval Note - "
                + item.id
            )

            sections = [
                {
                    "heading": "Priority",
                    "body": item.priority,
                },
                {
                    "heading": "Reason",
                    "body": item.reason,
                },
                {
                    "heading": "Required Action",
                    "body": item.required_action,
                },
                {
                    "heading": "Inspection Findings",
                    "body": item.inspection_result.to_display_text(),
                },
            ]

            result = write_report(
                title,
                json.dumps(sections),
            )

            if isinstance(result, str) and result.startswith(
                "ERROR"
            ):
                return result

            item.outputs.append(str(result))
            item.status = "REVIEW_REQUIRED"

            return str(result)

        if action == "ALERT_AND_HUMAN_REVIEW":
            return self.create_alert(item_id)

        if action == "RECORD_AND_MONITOR":
            item.status = "MONITORING"

            return (
                "LOW priority report recorded "
                "for monitoring."
            )

        item.status = "REVIEW_REQUIRED"

        return "Human review required."


TRIAGE_SYSTEM = """
You are an industrial report triage assistant.

Analyze the supplied inspection report and classify its priority.

Return ONE JSON object and nothing else:

{
  "priority": "HIGH | MEDIUM | LOW",
  "reason": "short explanation",
  "required_action": "recommended next action",
  "alert_required": true or false
}

Rules:
- HIGH means the report contains a potentially critical issue requiring prompt human attention.
- MEDIUM means the report contains an issue that requires attention but is not immediately critical.
- LOW means no urgent action is indicated.
- Do not invent findings.
- Base the decision only on the supplied report.
- Classify workflow priority separately from inspection status and source-reported severity.
- Never copy HIGH, MEDIUM, or LOW into inspection_status.
- alert_required must normally be true only for HIGH priority.
"""


def triage_report(extracted_report: str) -> dict:
    """
    Analyze an extracted industrial report and assign a priority.
    """

    messages = [
        {
            "role": "system",
            "content": TRIAGE_SYSTEM,
        },
        {
            "role": "user",
            "content": (
                "Analyze this industrial report:\n\n"
                + extracted_report
            ),
        },
    ]

    raw = chat(
        "qwen2.5:7b",
        messages,
    )

    result = parse(raw)

    if "answer" in result and isinstance(
        result["answer"],
        str,
    ):
        try:
            result = json.loads(
                result["answer"]
            )
        except json.JSONDecodeError:
            return {
                "priority": "UNKNOWN",
                "reason": "Could not parse AI triage result.",
                "required_action": "Human review required.",
                "alert_required": False,
            }

    priority = str(
        result.get("priority", "UNKNOWN")
    ).upper()

    if priority not in {
        "HIGH",
        "MEDIUM",
        "LOW",
    }:
        priority = "UNKNOWN"

    return {
        "priority": priority,
        "reason": str(
            result.get("reason", "")
        ),
        "required_action": str(
            result.get("required_action", "")
        ),
        "alert_required": bool(
            result.get(
                "alert_required",
                False,
            )
        ),
    }