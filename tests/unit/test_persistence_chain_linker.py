import unittest

from pc_cleanguard.persistence.linker import link_persistence_nodes


REPORT = {
    "installed_apps": [{"target_id": "app:alpha", "display_name": "Example Alpha", "publisher": "Example", "install_location": "C:/Apps/Alpha"}],
    "startup_items": [{"target_id": "startup:alpha", "name": "Alpha Updater", "command": "C:/Apps/Alpha/updater.exe"}],
    "services": [{"target_id": "service:alpha", "display_name": "Alpha Service", "path_name": "C:/Apps/Alpha/service.exe"}],
    "scheduled_tasks": [{"target_id": "task:alpha", "task_name": "Alpha Update", "actions_summary": "C:/Apps/Alpha/update.exe"}],
}


class PersistenceLinkerTest(unittest.TestCase):
    def test_links_app_to_startup_service_and_task(self):
        linked = link_persistence_nodes(REPORT)
        edge_types = {item["edge_type"] for item in linked["edges"]}
        self.assertTrue({"persists_via", "registers_service", "schedules"} <= edge_types)

    def test_related_publisher_and_weak_name_stay_downgraded(self):
        report = {"installed_apps": [{"target_id": "a", "display_name": "Shared", "publisher": "P"}, {"target_id": "b", "display_name": "Different", "publisher": "P"}], "startup_items": [{"name": "Shared Helper"}]}
        edges = link_persistence_nodes(report)["edges"]
        self.assertTrue(any(e["edge_type"] in {"related_to_publisher", "weak_name_overlap"} and e["confidence"] == "weak" for e in edges))

    def test_registry_and_browser_are_only_caller_supplied_clues(self):
        report = {"browser_settings": [{"target_id": "browser:1", "type": "browser_homepage", "value": "https://example.invalid"}], "registry_clues": [{"target_id": "reg:1", "type": "registry_run_key", "value": "Example"}]}
        result = link_persistence_nodes(report)
        self.assertEqual(2, len(result["nodes"]))
        self.assertFalse(result["runtime_registry_read"])
        self.assertFalse(result["runtime_browser_scan"])
