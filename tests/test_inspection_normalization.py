import json
import os
import tempfile
import unittest
from unittest.mock import mock_open, patch

import pymupdf
from orchestrator.workflow import WorkItem, WorkflowQueue
from src.schema import normalize_inspection_result
from src.pdf_processor import pdf_to_images
from tools.tools import read_document


class InspectionNormalizationTests(unittest.TestCase):
    def run_user_workflow(self, filename, source):
        import app

        triage = {
            "priority": "MEDIUM",
            "reason": "Review the reported condition.",
            "required_action": "Review the inspection findings.",
            "alert_required": False,
        }
        patches = [
            patch("builtins.open", mock_open()),
            patch("app.agent.run", return_value={"answer": source}),
            patch("app.read_document", return_value=source),
            patch("orchestrator.workflow.triage_report", return_value=triage),
        ]
        with patches[0], patches[1] as agent_run, patches[2], patches[3]:
            result = app.run_workflow(
                [(filename, b"test report")],
                "Summarize this inspection report",
            )
        return result, agent_run

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
        self.assertEqual(result.abnormalities, [
            "Oil residue around the seal",
            "Seal leakage at the drive end",
        ])
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

    def test_normalizes_inconsistent_vlm_finding_and_action_objects(self):
        result = normalize_inspection_result({
            "findings": [
                {
                    "item": "Minor leakage observed at the flange joint.",
                    "finding": "Medium",
                },
                {
                    "item": "Tighten the flange bolts.",
                    "finding": "The equipment was operating at the time of inspection.",
                },
            ],
            "recommendations": [
                {"item": "Tighten the flange bolts.", "recommendation": ""},
                {"item": "Monitor vibration levels over the next week."},
            ],
        })

        self.assertEqual(len(result.key_findings), 1)
        self.assertEqual(
            result.key_findings[0].finding,
            "Minor leakage observed at the flange joint.",
        )
        self.assertEqual(result.key_findings[0].severity, "MEDIUM")
        self.assertEqual(result.recommended_actions, [
            "Tighten the flange bolts.",
            "Monitor vibration levels over the next week.",
        ])

    def test_workflow_level_tokens_are_not_normalized_as_inspection_status(self):
        result = normalize_inspection_result({
            "inspection_status": "MEDIUM",
            "summary": "Inspection completed with a medium source severity.",
        })

        self.assertEqual(result.inspection_status, "")
        self.assertEqual(result.overall_severity, "MEDIUM")

    def test_negative_observations_are_not_abnormalities(self):
        result = normalize_inspection_result({
            "key_findings": ["No abnormal noise detected during inspection."],
            "abnormalities": [
                "No abnormal noise detected during inspection.",
                "Minor leakage at the flange joint.",
            ],
        })

        self.assertEqual(
            result.abnormalities,
            ["Minor leakage at the flange joint."],
        )
        self.assertEqual(
            result.key_findings[0].finding,
            "No abnormal noise detected during inspection.",
        )

    def test_explicit_issues_in_findings_are_also_abnormalities(self):
        result = normalize_inspection_result({
            "key_findings": [
                "Minor leakage observed at the flange joint.",
                "Vibration levels are higher than normal.",
                "No abnormal noise detected.",
            ],
        })

        self.assertEqual(result.abnormalities, [
            "Minor leakage observed at the flange joint.",
            "Vibration levels are higher than normal.",
        ])

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
        self.assertNotIn(malformed, result.to_display_text())

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
            patch("builtins.open", mock_open()),
            patch("app.read_document", return_value=page_results),
            patch("app.agent.run") as agent_run,
            patch("orchestrator.workflow.triage_report", return_value=triage),
        ):
            result = app.run_workflow(
                [("workflow-normalization-test.pdf", b"PDF test bytes")],
                "Summarize this inspection report",
            )

        agent_run.assert_not_called()
        inspection = result["results"][0]
        self.assertEqual(len(inspection["key_findings"]), 1)
        self.assertIn("No immediate shutdown recommended.", inspection["summary"])
        self.assertIn("Monitor leakage.", result["results"][0]["recommended_actions"])

    def test_user_result_is_structured_and_uses_uploaded_filename(self):
        payload = json.dumps({
            "equipment_inspected": "Pump P-204",
            "inspection_status": "Completed",
            "overall_condition": "Leak at the drive-end seal.",
            "summary": "A leak was observed at the drive-end seal.",
            "key_findings": [
                {"item": "Drive-end seal", "finding": "Leak observed."},
                {"item": "Vibration", "finding": "Above normal."},
            ],
            "abnormalities": ["Oil residue around the seal."],
            "recommended_actions": ["Replace the seal.", "Monitor vibration."],
        })
        result, _ = self.run_user_workflow("pump-inspection.pdf", payload)
        report = result["results"][0]

        self.assertEqual(report["report_name"], "pump-inspection.pdf")
        self.assertEqual(report["equipment_inspected"], "Pump P-204")
        self.assertEqual(report["inspection_status"], "Completed")
        self.assertEqual(report["priority"], "MEDIUM")
        self.assertEqual(len(report["key_findings"]), 2)
        self.assertEqual(len(report["recommended_actions"]), 2)
        self.assertEqual(report["abnormalities"], [
            "Oil residue around the seal.",
            "Leak observed.",
            "Above normal.",
        ])
        self.assertNotIn("R001", json.dumps(report))
        self.assertNotIn("inspection_result", report)

    def test_user_result_normalizes_natural_language_and_omits_missing_fields(self):
        source = (
            "Equipment inspected: Pump P-204\n"
            "Inspection status: Completed\n"
            "Key findings: Oil residue near the seal\n"
            "Recommended action: Replace the seal"
        )
        result, agent_run = self.run_user_workflow(
            "pump-notes.txt",
            source,
        )
        report = result["results"][0]

        self.assertEqual(report["report_name"], "pump-notes.txt")
        self.assertEqual(report["equipment_inspected"], "Pump P-204")
        self.assertEqual(report["inspection_status"], "Completed")
        self.assertEqual(report["overall_condition"], "")
        self.assertEqual(report["key_findings"][0]["finding"], "Oil residue near the seal")
        self.assertEqual(report["recommended_actions"], ["Replace the seal"])
        self.assertEqual(report["priority"], "MEDIUM")
        agent_run.assert_called_once()

    def test_malformed_json_is_not_in_user_result(self):
        malformed = '{"key_findings":[}'
        result, _ = self.run_user_workflow("malformed.pdf", malformed)
        report = result["results"][0]

        self.assertEqual(report["summary"], "")
        self.assertEqual(report["key_findings"], [])
        self.assertEqual(report["abnormalities"], [])
        self.assertEqual(report["recommended_actions"], [])
        self.assertNotIn(malformed, json.dumps(report))
        self.assertNotIn("source_notes", report)
        self.assertNotIn("id", report)

    def test_pdf_native_text_skips_vision_inference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "text-report.pdf")
            pdf = pymupdf.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "Inspection status: Completed")
            pdf.save(path)
            pdf.close()

            with patch("src.extract.extract_document") as vision:
                result = json.loads(read_document(path))

        vision.assert_not_called()
        self.assertIn(
            "Inspection status: Completed",
            result[0]["source_notes"],
        )

    def test_mixed_pdf_runs_vision_only_for_scanned_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "mixed-report.pdf")
            pdf = pymupdf.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "Native text page")
            pdf.new_page()
            pdf.save(path)
            pdf.close()

            vision_result = json.dumps({"summary": "Scanned page findings."})
            with (
                patch(
                    "src.pdf_processor.pdf_to_images",
                    return_value=["uploads/pdf_pages/page_2.png"],
                ) as render,
                patch("src.extract.extract_document", return_value=vision_result) as vision,
            ):
                result = json.loads(read_document(path))

        render.assert_called_once()
        self.assertEqual(render.call_args.kwargs["page_numbers"], [1])
        vision.assert_called_once_with("uploads/pdf_pages/page_2.png")
        self.assertEqual(len(result), 2)

    def test_pdf_render_uses_native_page_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "render.pdf")
            pdf = pymupdf.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "Inspection findings and actions.")
            pdf.save(path)
            pdf.close()

            images = pdf_to_images(path, temp_dir)
            pixmap = pymupdf.Pixmap(images[0])

        self.assertLess(pixmap.width, 596)
        self.assertLess(pixmap.height, 842)

    def test_failed_document_does_not_abort_other_reports(self):
        import app

        valid_result = json.dumps({
            "summary": "Second report processed.",
            "key_findings": ["Seal leakage."],
        })
        triage = {
            "priority": "LOW",
            "reason": "No urgent action is indicated.",
            "required_action": "Monitor.",
            "alert_required": False,
        }
        with (
            patch("builtins.open", mock_open()),
            patch(
                "app.read_document",
                side_effect=["ERROR: document processing failed: timed out", valid_result],
            ),
            patch("orchestrator.workflow.triage_report", return_value=triage),
        ):
            response = app.run_workflow(
                [
                    ("slow-report.pdf", b"first"),
                    ("healthy-report.pdf", b"second"),
                ],
                "Give me a summary of these reports.",
            )

        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["status"], "ERROR")
        self.assertEqual(response["results"][0]["priority"], "NOT ASSESSED")
        self.assertEqual(response["results"][1]["status"], "TRIAGED")
        self.assertEqual(response["results"][1]["report_name"], "healthy-report.pdf")


if __name__ == "__main__":
    unittest.main()
