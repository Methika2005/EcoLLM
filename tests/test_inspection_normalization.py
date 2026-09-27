import json
import unittest
from unittest.mock import patch

from orchestrator.workflow import WorkItem, WorkflowQueue
from src.schema import normalize_inspection_result


class InspectionNormalizationTests(unittest.TestCase):
    def test_normalizes_valid_structured_json(self):
        result = normalize_inspection_result(json.dumps({
            "equipment_inspected": "Pump P-204",
            "inspection_status": "Inspection completed",
            "overall_condition": "Leak observed at seal",
            "key_findings": ["Seal leakage at the drive end"],
            "abnormalities": ["Oil residue around the seal"],
            "recommended_actions": ["Replace the seal"],
            "overall_severity": "HIGH",
        }))

        self.assertEqual(result.equipment_inspected, "Pump P-204")
        self.assertEqual(result.inspection_status, "Inspection completed")
        self.assertEqual(result.overall_condition, "Leak observed at seal")
        self.assertEqual(result.key_findings[0].finding, "Seal leakage at the drive end")
        self.assertEqual(result.abnormalities, ["Oil residue around the seal"])
        self.assertEqual(result.recommended_actions, ["Replace the seal"])
        self.assertEqual(result.overall_severity, "HIGH")
        self.assertNotEqual(result.inspection_status, result.overall_severity)

    def test_preserves_natural_language_as_source_notes(self):
        text = (
            "The technician inspected Pump P-204. Oil was found near the seal. "
            "The report recommends replacing the seal."
        )

        result = normalize_inspection_result(text)

        self.assertEqual(result.source_notes, text)
        self.assertEqual(result.equipment_inspected, "")
        self.assertEqual(result.inspection_status, "")
        self.assertEqual(result.key_findings, [])
        self.assertIn(text, result.to_display_text())

    def test_normalizes_explicit_labels_in_natural_language(self):
        result = normalize_inspection_result(
            "Equipment inspected: Pump P-204\n"
            "Inspection status: Completed\n"
            "Key findings: Oil residue around the seal\n"
            "Recommended action: Replace the seal"
        )

        self.assertEqual(result.equipment_inspected, "Pump P-204")
        self.assertEqual(result.inspection_status, "Completed")
        self.assertEqual(result.key_findings[0].finding, "Oil residue around the seal")
        self.assertEqual(result.recommended_actions, ["Replace the seal"])

    def test_normalizes_existing_ocr_schema_without_repurposing_severity(self):
        result = normalize_inspection_result(json.dumps({
            "document_type": "Inspection report",
            "title": "Pump inspection",
            "summary": "Leak observed.",
            "findings": [{
                "item": "Pump P-204",
                "finding": "Seal leak observed.",
                "severity": "HIGH",
                "recommendation": "Replace seal.",
            }],
            "overall_severity": "HIGH",
            "recommendations": ["Replace seal."],
        }))

        self.assertEqual(result.inspection_status, "")
        self.assertEqual(result.overall_severity, "HIGH")
        self.assertEqual(result.key_findings[0].severity, "HIGH")
        self.assertEqual(result.recommended_actions, ["Replace seal."])

    def test_merges_multiple_pdf_page_payloads(self):
        result = normalize_inspection_result(json.dumps([
            {
                "title": "Pump Room - Unit 2",
                "summary": "Minor leakage at flange joint.",
                "findings": [{"finding": "Minor leakage observed."}],
            },
            {
                "title": "RECOMMENDATIONS",
                "summary": "No immediate shutdown was recommended.",
                "findings": [{"finding": "Monitor vibration levels."}],
                "recommendations": ["Monitor vibration levels next week."],
            },
        ]))

        self.assertEqual(result.title, "Pump Room - Unit 2")
        self.assertIn("Minor leakage at flange joint.", result.summary)
        self.assertIn("No immediate shutdown was recommended.", result.summary)
        self.assertEqual(len(result.key_findings), 2)
        self.assertEqual(
            result.recommended_actions,
            ["Monitor vibration levels next week."],
        )

    def test_leaves_missing_fields_empty(self):
        result = normalize_inspection_result({
            "inspection_status": "Completed",
            "priority": "HIGH",
        })

        self.assertEqual(result.inspection_status, "Completed")
        self.assertEqual(result.equipment_inspected, "")
        self.assertEqual(result.overall_condition, "")
        self.assertEqual(result.key_findings, [])
        self.assertEqual(result.abnormalities, [])
        self.assertEqual(result.recommended_actions, [])
        self.assertEqual(result.source_notes, '{"priority": "HIGH"}')

    def test_malformed_model_output_is_preserved_without_guessing(self):
        malformed = '{"inspection_status": "HIGH", "key_findings": [}'

        result = normalize_inspection_result(malformed)

        self.assertEqual(result.source_notes, malformed)
        self.assertEqual(result.inspection_status, "")
        self.assertEqual(result.key_findings, [])

    def test_workflow_normalizes_before_triage(self):
        queue = WorkflowQueue()
        queue.add(WorkItem(id="R001", file_path="report.pdf"))
        triage_input = {}

        def capture_triage(report):
            triage_input["report"] = json.loads(report)
            return {
                "priority": "MEDIUM",
                "reason": "A seal leak is reported.",
                "required_action": "Review the seal condition.",
                "alert_required": False,
            }

        with patch("orchestrator.workflow.triage_report", side_effect=capture_triage):
            self.assertTrue(queue.triage_item(
                "R001",
                '{"key_findings":["Seal leakage"],"inspection_status":"Completed"}',
            ))

        item = queue.get_all()[0]
        self.assertEqual(item.inspection_result.inspection_status, "Completed")
        self.assertEqual(
            triage_input["report"]["key_findings"][0]["finding"],
            "Seal leakage",
        )
        self.assertEqual(item.priority, "MEDIUM")

    def test_pdf_workflow_skips_redundant_agent_loop(self):
        import app

        page_results = json.dumps([
            {
                "summary": "Inspection completed.",
                "findings": [{"finding": "Minor leakage observed."}],
            },
            {
                "summary": "No immediate shutdown recommended.",
                "recommendations": ["Monitor leakage."],
            },
        ])
        triage = {
            "priority": "MEDIUM",
            "reason": "Leakage requires review.",
            "required_action": "Monitor leakage.",
            "alert_required": False,
        }
        with (
            patch("app.read_document", return_value=page_results),
            patch("app.agent.run") as agent_run,
            patch("orchestrator.workflow.triage_report", return_value=triage),
        ):
            result = app.run_workflow(
                [("workflow-normalization-test.pdf", b"PDF test bytes")],
                "Summarize this inspection report",
            )

        agent_run.assert_not_called()
        inspection = result["results"][0]["inspection_result"]
        self.assertEqual(len(inspection["key_findings"]), 1)
        self.assertIn("No immediate shutdown recommended.", inspection["summary"])
        self.assertIn("Monitor leakage.", result["results"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
