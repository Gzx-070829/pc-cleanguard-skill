import ast
import inspect
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.pipeline import (
    MAX_SCAN_JSON_BYTES,
    load_scan_json_file,
    load_scan_json_text,
)


ROOT = Path(__file__).resolve().parents[2]


class ScanPipelineInputLoaderTest(unittest.TestCase):
    def test_load_scan_json_text_reads_object(self) -> None:
        self.assertEqual({"installed_apps": []}, load_scan_json_text('{"installed_apps":[]}'))

    def test_load_scan_json_text_rejects_invalid_json(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid scan JSON"):
            load_scan_json_text("{not-json}")

    def test_load_scan_json_text_rejects_non_object_root(self) -> None:
        with self.assertRaisesRegex(ValueError, "root must be an object"):
            load_scan_json_text("[]")

    def test_load_scan_json_file_reads_explicit_sample(self) -> None:
        path = ROOT / "examples" / "scan_samples" / "windows_pr6_normalized_sample.json"
        data = load_scan_json_file(path)
        self.assertEqual("Windows", data["platform"])

    def test_loader_requires_explicit_path(self) -> None:
        parameter = inspect.signature(load_scan_json_file).parameters["path"]
        self.assertIs(inspect.Parameter.empty, parameter.default)

    def test_loader_rejects_non_json_extension(self) -> None:
        with self.assertRaises(ValueError):
            load_scan_json_file("explicit.txt")

    def test_loader_rejects_unc_path(self) -> None:
        with self.assertRaises(ValueError):
            load_scan_json_file(r"\\server\share\scan.json")

    def test_loader_rejects_device_path(self) -> None:
        with self.assertRaises(ValueError):
            load_scan_json_file(r"\\?\C:\safe\scan.json")

    def test_loader_rejects_windows_system_paths(self) -> None:
        for path in (r"C:\Windows\scan.json", r"C:\Program Files\scan.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                load_scan_json_file(path)

    def test_loader_rejects_missing_file_without_creating_it(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            with self.assertRaises(FileNotFoundError):
                load_scan_json_file(path)
            self.assertFalse(path.exists())

    def test_loader_rejects_oversized_file(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "large.json"
            path.write_bytes(b'{"padding":"' + b"x" * 100 + b'"}')
            with self.assertRaisesRegex(ValueError, "exceeds"):
                load_scan_json_file(path, max_bytes=32)

    def test_default_size_limit_is_ten_megabytes(self) -> None:
        self.assertEqual(10 * 1024 * 1024, MAX_SCAN_JSON_BYTES)

    def test_loader_reads_utf8_content(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "scan.json"
            path.write_text(json.dumps({"note": "中文"}), encoding="utf-8")
            self.assertEqual("中文", load_scan_json_file(path)["note"])

    def test_loader_has_no_process_network_or_discovery_calls(self) -> None:
        path = ROOT / "pc_cleanguard" / "pipeline" / "input_loader.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        forbidden = {a + b for a, b in (("sub", "process"), ("req", "uests"), ("url", "lib"), ("sock", "et"))}
        self.assertTrue(forbidden.isdisjoint(imports))
        self.assertTrue({"glob", "rglob", "walk"}.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
