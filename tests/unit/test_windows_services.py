import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.core.models import ClassificationLabel, GovernanceTarget, ObjectType
from pc_cleanguard.core.policy_engine import evaluate_target
from pc_cleanguard.windows import (
    WindowsService,
    normalize_service,
    normalize_services,
    service_to_governance_target,
    service_to_scan_target_record,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-06T00:00:00Z"


class WindowsServicesTest(unittest.TestCase):
    def test_normalize_win32_service_record(self) -> None:
        service = normalize_service(
            {"Name": "ExampleSvc", "DisplayName": "Example Service", "State": "Running"}
        )
        self.assertEqual("ExampleSvc", service.service_name)
        self.assertEqual("Example Service", service.display_name)

    def test_service_fields_are_preserved(self) -> None:
        service = self._service()
        self.assertEqual("OK", service.status)
        self.assertEqual("Auto", service.start_type)
        self.assertEqual("Running", service.state)
        self.assertEqual(1234, service.process_id)

    def test_service_without_identity_is_skipped(self) -> None:
        self.assertIsNone(normalize_service({"State": "Stopped"}))
        self.assertEqual([], normalize_services([{"State": "Stopped"}]))

    def test_path_name_is_metadata_only(self) -> None:
        path_name = r"C:\Program Files\Example\service.exe --service"
        service = self._service(path_name=path_name)
        self.assertEqual(path_name, service.path_name)
        self.assertNotIn(path_name, repr(service))

    def test_service_id_is_stable_and_excludes_path(self) -> None:
        first = self._service(path_name="first-path")
        second = self._service(path_name="second-path")
        self.assertEqual(first.service_id, second.service_id)
        self.assertNotIn("first-path", first.service_id)

    def test_invalid_process_id_becomes_none(self) -> None:
        self.assertIsNone(self._service(process_id="unknown").process_id)

    def test_governance_target_has_service_type_without_classification(self) -> None:
        target = service_to_governance_target(self._service())
        self.assertIsInstance(target, GovernanceTarget)
        self.assertEqual(ObjectType.SERVICE, target.object_type)
        self.assertIsNone(target.requested_classification)

    def test_microsoft_service_never_becomes_safe_remove(self) -> None:
        service = self._service(
            service_name="MicrosoftExampleService",
            display_name="Microsoft Windows Example Service",
            path_name=r"%SystemRoot%\System32\svchost.exe -k Example",
        )
        decision = evaluate_target(service_to_governance_target(service))
        self.assertEqual(ClassificationLabel.ASK_USER, decision.classification)
        self.assertNotEqual(ClassificationLabel.SAFE_REMOVE, decision.classification)

    def test_scan_target_record_matches_sqlite_fields(self) -> None:
        record = service_to_scan_target_record(self._service(), "scan-1")
        self.assertEqual("SERVICE", record["object_type"])
        self.assertNotIn("path_name", record)
        self.assertEqual(self._service().path_name, record["path"])

    def test_service_sample_is_safe_and_parseable(self) -> None:
        data = json.loads(
            (ROOT / "examples" / "scan_samples" / "windows_services_sample.json").read_text(encoding="utf-8")
        )
        self.assertEqual(3, len(normalize_services(data)))
        self.assertNotIn("C:\\Users\\", json.dumps(data))

    def test_module_imports_no_process_or_network_packages(self) -> None:
        path = ROOT / "pc_cleanguard" / "windows" / "services.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        forbidden = {a + b for a, b in (("sub", "process"), ("req", "uests"), ("url", "lib"), ("sock", "et"))}
        self.assertTrue(forbidden.isdisjoint(imports))

    @staticmethod
    def _service(**overrides) -> WindowsService:
        raw = {
            "service_name": "ExampleService",
            "display_name": "Example Service",
            "status": "OK",
            "start_type": "Auto",
            "state": "Running",
            "path_name": r"C:\Program Files\Example\service.exe",
            "process_id": 1234,
            "service_type": "Own Process",
            "start_name": "LocalSystem",
            "description": "Synthetic service.",
            "source": "windows_cim_service",
            "collected_at": NOW,
        }
        raw.update(overrides)
        return normalize_service(raw)


if __name__ == "__main__":
    unittest.main()
