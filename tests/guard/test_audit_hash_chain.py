import json
import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.guard import GuardInputError, append_event, verify_audit_chain


class AuditHashChainTests(unittest.TestCase):
    def test_valid_chain_verifies_and_tampering_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guard.jsonl"
            append_event(
                path,
                event_type="REQUEST_RECEIVED",
                request_id="request-1",
                decision_id=None,
                payload={"action_type": "read_metadata"},
                timestamp="2026-01-01T00:00:00Z",
            )
            append_event(
                path,
                event_type="DECISION_ISSUED",
                request_id="request-1",
                decision_id="decision-1",
                payload={"disposition": "ALLOW"},
                timestamp="2026-01-01T00:00:01Z",
            )
            self.assertTrue(verify_audit_chain(path))
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            records[0]["payload"]["action_type"] = "delete_file"
            path.write_text(
                "\n".join(json.dumps(item) for item in records) + "\n",
                encoding="utf-8",
            )
            verification = verify_audit_chain(path)
            self.assertFalse(verification)
            self.assertTrue(verification.errors)

    def test_audit_output_rejects_system_unc_and_non_jsonl_paths(self):
        for path in (
            r"C:\Windows\System32\guard.jsonl",
            r"C:\Program Files\Guard\guard.jsonl",
            r"\\server\share\guard.jsonl",
            r"C:\Temp\guard.log",
        ):
            with self.subTest(path=path), self.assertRaises(GuardInputError):
                append_event(
                    path,
                    event_type="REQUEST_RECEIVED",
                    request_id="request-1",
                    decision_id=None,
                    payload={"action_type": "read_metadata"},
                    timestamp="2026-01-01T00:00:00Z",
                )


if __name__ == "__main__":
    unittest.main()
