from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from export_release_evidence_pack import EXPORT_RELEASE_EVIDENCE_PACK_NAME, build_export_release_evidence_pack, write_export_release_evidence_pack_file


class ExportReleaseEvidencePackTests(unittest.TestCase):
    def test_build_release_evidence_pack_describes_priority_reports(self) -> None:
        markdown = build_export_release_evidence_pack(
            project={"title": "Evidence Demo"},
            target_label="网页试玩包",
            release_version="1.0.0-preview",
            manifest_name="export_manifest.json",
            playtest_guide_name="README_试玩验收先看这里.md",
            provenance_name="canvasia-provenance.json",
            story_route_map_report_name="story_route_map.md",
            localization_audit_report_name="localization_audit.md",
            release_readiness_report_name="release_readiness_summary.md",
            unlockable_report_name="unlockable_content_report.md",
            unlockable_manifest_name="unlockable_content_manifest.json",
            launch_steps=["打开 index.html"],
            runtime_notes=["网页包适合快速试玩。"],
            extra_reports=["performance-budget.md", "release-fix-order.md", "unknown-report.json"],
            missing_assets=[{"name": "Missing BG", "type": "background"}],
        )

        self.assertIn("# 发布证据包", markdown)
        self.assertIn("Evidence Demo", markdown)
        self.assertIn("performance-budget.md", markdown)
        self.assertIn("复查包体、已引用素材、首屏预加载", markdown)
        self.assertIn("release-fix-order.md", markdown)
        self.assertIn("按优先级排好", markdown)
        self.assertIn("机器可读补充检查报告", markdown)
        self.assertIn("Missing BG", markdown)

    def test_write_release_evidence_pack_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = write_export_release_evidence_pack_file(
                Path(tmp_dir),
                project={"title": "Writable Evidence"},
                target_label="桌面包",
                release_version="preview",
                manifest_name="export_manifest.json",
                playtest_guide_name="README_试玩验收先看这里.md",
                provenance_name="canvasia-provenance.json",
                story_route_map_report_name="story_route_map.md",
                localization_audit_report_name="localization_audit.md",
                release_readiness_report_name="release_readiness_summary.md",
                unlockable_report_name="unlockable_content_report.md",
                unlockable_manifest_name="unlockable_content_manifest.json",
                extra_reports=["performance-budget.md"],
            )

            self.assertEqual(path.name, EXPORT_RELEASE_EVIDENCE_PACK_NAME)
            self.assertIn("Writable Evidence", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
