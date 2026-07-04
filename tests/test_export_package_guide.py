from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from export_package_guide import (
    EXPORT_PLAYTEST_GUIDE_FILE_NAME,
    build_export_playtest_guide,
    write_export_playtest_guide_file,
)


class ExportPackageGuideTests(unittest.TestCase):
    def test_build_export_playtest_guide_includes_launch_checks_and_reports(self) -> None:
        markdown = build_export_playtest_guide(
            project={"title": "Guide Demo"},
            target_label="网页试玩包",
            release_version="1.2.3",
            launch_steps=["打开 `index.html`", "压缩整个文件夹后分发"],
            manifest_name="export_manifest.json",
            unlockable_manifest_name="unlockable_content_manifest.json",
            unlockable_report_name="unlockable_content_report.md",
            provenance_name="tony-na-provenance.json",
            extra_reports=["native-runtime-release-check.json"],
            runtime_notes=["未签名预览包可能触发系统提示。"],
            missing_assets=[{"id": "bg_missing", "name": "Missing Background", "type": "background"}],
        )

        self.assertIn("# 试玩与发布验收指南", markdown)
        self.assertIn("Guide Demo", markdown)
        self.assertIn("打开 `index.html`", markdown)
        self.assertIn("## 先验这几项", markdown)
        self.assertIn("unlockable_content_report.md", markdown)
        self.assertIn("Missing Background", markdown)
        self.assertIn("未签名预览包可能触发系统提示。", markdown)

    def test_write_export_playtest_guide_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = write_export_playtest_guide_file(
                Path(tmp_dir),
                project={"title": "Writable Guide"},
                target_label="桌面包",
                release_version="preview",
                launch_steps=["双击启动脚本"],
                manifest_name="export_manifest.json",
                unlockable_manifest_name="unlockable_content_manifest.json",
                unlockable_report_name="unlockable_content_report.md",
                provenance_name="tony-na-provenance.json",
            )

            self.assertEqual(path.name, EXPORT_PLAYTEST_GUIDE_FILE_NAME)
            self.assertIn("Writable Guide", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
