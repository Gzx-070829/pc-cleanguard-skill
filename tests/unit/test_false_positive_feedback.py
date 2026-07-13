import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.reputation import build_false_positive_feedback_template, validate_false_positive_feedback, render_false_positive_feedback_markdown


class FalsePositiveFeedbackTest(unittest.TestCase):
    def setUp(self):
        self.match = {"matched_record_id": "ev:test", "matched_name": "Example App"}
        self.metadata = {"publisher": "Example Publisher", "version": "1.0", "path_redacted": "C:/Users/<USER>/Example"}

    def test_template_is_private_offline_review_only(self):
        result = build_false_positive_feedback_template(self.match, self.metadata)
        self.assertFalse(result["uploaded"]); self.assertFalse(result["runtime_network_access"])
        self.assertEqual("review_queue_only", result["review_status"])
        self.assertFalse(result["evidence_pack_modified"])

    def test_validation_requires_redaction_confirmation(self):
        result = build_false_positive_feedback_template(self.match, self.metadata)
        self.assertIn("privacy_redaction_confirmed", " ".join(validate_false_positive_feedback(result)))
        result["privacy_redaction_confirmed"] = True
        self.assertNotIn("privacy_redaction_confirmed", " ".join(validate_false_positive_feedback(result)))

    def test_rejects_unredacted_user_path(self):
        result = build_false_positive_feedback_template(self.match, {**self.metadata, "path_redacted": "C:/Users/Alice/Example"})
        result["privacy_redaction_confirmed"] = True
        self.assertTrue(validate_false_positive_feedback(result))

    def test_markdown_mentions_no_automatic_database_change(self):
        text = render_false_positive_feedback_markdown(build_false_positive_feedback_template(self.match, self.metadata))
        self.assertIn("不会自动修改", text)

    def test_cli_feedback_template_writes_json(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "matches.json"; output = root / "feedback.json"
            source.write_text(json.dumps([self.match], ensure_ascii=False), encoding="utf-8")
            self.assertEqual(0, main(["feedback", "false-positive-template", "--match", str(source), "--output", str(output)]))
            self.assertEqual("review_queue_only", json.loads(output.read_text(encoding="utf-8"))["review_status"])


if __name__ == "__main__": unittest.main()
