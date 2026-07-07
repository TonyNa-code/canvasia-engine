from __future__ import annotations

import unittest

from native_runtime_export_digest import build_native_3d_asset_export_digest, format_export_digest_number


class NativeRuntimeExportDigestTests(unittest.TestCase):
    def test_format_export_digest_number_handles_invalid_values(self) -> None:
        self.assertEqual(format_export_digest_number(1234567), "1,234,567")
        self.assertEqual(format_export_digest_number("bad"), "0")

    def test_native_3d_asset_export_digest_handles_unavailable_report(self) -> None:
        digest = build_native_3d_asset_export_digest(None)

        self.assertEqual(digest["status"], "unavailable")
        self.assertEqual(digest["issueAssets"], [])
        self.assertTrue(digest["recommendations"])

    def test_native_3d_asset_export_digest_summarizes_risky_assets(self) -> None:
        digest = build_native_3d_asset_export_digest(
            {
                "status": "needs_attention",
                "summary": {
                    "assetCount": 2,
                    "issueCount": 3,
                    "performanceBudgetIssueCount": 1,
                    "estimatedTriangleCount": 120000,
                    "drawCallCount": 42,
                },
                "recommendations": ["压缩贴图。"],
                "entries": [
                    {
                        "assetId": "model_hero",
                        "name": "Hero Model",
                        "type": "model3d",
                        "status": "needs_attention",
                        "statusLabel": "需要处理",
                        "performanceBudgetProbe": {"issueCount": 1},
                        "previewProbe": {"textureSlotIssueCount": 2},
                        "usages": [{"kind": "character_model", "characterName": "Hero"}],
                    }
                ],
            }
        )

        self.assertEqual(digest["status"], "needs_attention")
        self.assertEqual(digest["issueAssetIds"], ["model_hero"])
        self.assertEqual(digest["issueAssets"][0]["summary"], "性能预算 1 项 / 贴图槽 2 项")
        self.assertEqual(digest["metrics"][3]["value"], "120,000")
        self.assertEqual(digest["recommendations"], ["压缩贴图。"])


if __name__ == "__main__":
    unittest.main()
