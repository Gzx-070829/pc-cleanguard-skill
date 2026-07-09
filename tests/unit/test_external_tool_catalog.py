import unittest

from pc_cleanguard.core.models import RiskLevel
from pc_cleanguard.external_tools.catalog import (
    ExternalToolCatalog,
    ExternalToolRecord,
    ExternalToolType,
)


def make_record(
    tool_type: ExternalToolType = ExternalToolType.OFFICIAL_UNINSTALLER,
    *,
    tool_id: str = "example-official-tool",
) -> ExternalToolRecord:
    return ExternalToolRecord(
        tool_id=tool_id,
        name="Example Tool Metadata",
        tool_type=tool_type,
        official_website="https://tools.example.invalid/example-tool",
        license="Example License",
        supported_actions=("standard_uninstall",),
        risk_level=RiskLevel.HIGH,
        required_user_confirmation=True,
    )


class ExternalToolCatalogTest(unittest.TestCase):
    def test_record_serializes_required_metadata(self) -> None:
        record = make_record()
        data = record.to_dict()
        self.assertEqual("example-official-tool", data["tool_id"])
        self.assertEqual("official_uninstaller", data["tool_type"])
        self.assertTrue(data["required_user_confirmation"])

    def test_catalog_supports_all_pr12_tool_types(self) -> None:
        records = tuple(
            make_record(tool_type, tool_id=f"example-{tool_type.value}")
            for tool_type in ExternalToolType
        )
        catalog = ExternalToolCatalog(records)
        self.assertEqual(4, len(catalog.records))
        self.assertEqual(
            {tool_type.value for tool_type in ExternalToolType},
            {record.tool_type.value for record in catalog.records},
        )

    def test_catalog_lookup_is_explicit(self) -> None:
        record = make_record()
        catalog = ExternalToolCatalog((record,))
        self.assertIs(record, catalog.get(record.tool_id))
        self.assertIsNone(catalog.get("not-cataloged"))
        with self.assertRaises(ValueError):
            catalog.require("not-cataloged")

    def test_catalog_rejects_duplicate_ids(self) -> None:
        with self.assertRaises(ValueError):
            ExternalToolCatalog((make_record(), make_record()))

    def test_record_rejects_non_https_website(self) -> None:
        with self.assertRaises(ValueError):
            ExternalToolRecord(
                tool_id="invalid-website",
                name="Invalid Website",
                tool_type=ExternalToolType.WINGET,
                official_website="http://tools.example.invalid",
                license="Example",
                supported_actions=("standard_uninstall",),
                risk_level=RiskLevel.HIGH,
                required_user_confirmation=True,
            )

    def test_record_rejects_empty_supported_actions(self) -> None:
        with self.assertRaises(ValueError):
            ExternalToolRecord(
                tool_id="no-actions",
                name="No Actions",
                tool_type=ExternalToolType.WINGET,
                official_website="https://tools.example.invalid/no-actions",
                license="Example",
                supported_actions=(),
                risk_level=RiskLevel.HIGH,
                required_user_confirmation=True,
            )


if __name__ == "__main__":
    unittest.main()
