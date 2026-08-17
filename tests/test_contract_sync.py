import json
from pathlib import Path
import unittest

from scripts.sync_contract import extract_contract, render_catalog


ROOT = Path(__file__).resolve().parents[1]


class ContractSyncTests(unittest.TestCase):
    def test_checked_in_contract_has_34_unique_tools(self) -> None:
        contract = json.loads(
            (ROOT / "references" / "tubealfred-tools.json").read_text(encoding="utf-8")
        )
        names = [item["mcp_tool"] for item in contract["tools"]]
        operations = [(item["method"], item["path"]) for item in contract["tools"]]
        self.assertEqual(34, contract["tool_count"])
        self.assertEqual(34, len(names))
        self.assertEqual(34, len(set(names)))
        self.assertEqual(34, len(set(operations)))

    def test_extracts_path_query_and_json_body_parameters(self) -> None:
        manifest = {
            "manifest_version": "1.0.0",
            "api": {"title": "Fixture", "version": "1"},
            "operations": [{
                "id": "things_page",
                "method": "POST",
                "path": "/v1/youtube/things/{thing_id}",
                "summary": "Fixture page",
                "credit_cost": "1 credit per call",
                "mcp": {"name": "youtube_things_page", "public": True},
                "parameters": [
                    {
                        "name": "thing_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "enum": ["new", "top"]},
                    },
                    {
                        "name": "continuation_token",
                        "in": "body",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                ],
            }],
        }
        contract = extract_contract(manifest, "2026-07-15")
        self.assertEqual(1, contract["tool_count"])
        parameters = contract["tools"][0]["parameters"]
        self.assertIn(
            {"name": "thing_id", "in": "path", "required": True, "type": "string"},
            parameters,
        )
        self.assertIn(
            {
                "name": "sort",
                "in": "query",
                "required": False,
                "type": "string",
                "enum": ["new", "top"],
            },
            parameters,
        )
        self.assertIn(
            {
                "name": "continuation_token",
                "in": "body",
                "required": True,
                "type": "string",
            },
            parameters,
        )

    def test_skips_rest_operations_without_an_mcp_mapping(self) -> None:
        manifest = {
            "manifest_version": "1.0.0",
            "api": {"title": "Fixture", "version": "1"},
            "operations": [{
                "id": "legacy",
                "method": "GET",
                "path": "/v1/youtube/legacy",
                "summary": "REST-only legacy alias",
                "mcp": {"name": "youtube_legacy", "public": False},
                "parameters": [],
            }],
        }

        contract = extract_contract(manifest, "2026-08-17")

        self.assertEqual(0, contract["tool_count"])
        self.assertEqual([], contract["tools"])

    def test_catalog_is_generated_and_warns_about_spend(self) -> None:
        contract = json.loads(
            (ROOT / "references" / "tubealfred-tools.json").read_text(encoding="utf-8")
        )
        catalog = render_catalog(contract)
        self.assertIn("**34 read-only tools**", catalog)
        self.assertIn("explicit user approval", catalog)
        self.assertIn("Treat video metadata", catalog)
        self.assertEqual(
            catalog,
            (ROOT / "skills" / "youtube-full" / "references" / "tool-catalog.md").read_text(
                encoding="utf-8"
            ),
        )


if __name__ == "__main__":
    unittest.main()
