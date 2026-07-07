from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from export_icon import (
    build_export_icon_ico,
    build_export_icon_palette,
    build_export_icon_png,
    write_export_icon_files,
)


class ExportIconTests(unittest.TestCase):
    def test_export_icon_png_and_ico_have_valid_headers(self) -> None:
        project = {"projectId": "demo", "title": "Canvasia Demo"}
        png_bytes = build_export_icon_png(project, size=64)
        ico_bytes = build_export_icon_ico(png_bytes, size=64)

        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", png_bytes[16:24])
        self.assertEqual((width, height), (64, 64))
        self.assertEqual(struct.unpack("<HHH", ico_bytes[:6]), (0, 1, 1))
        self.assertEqual(ico_bytes[6], 64)
        self.assertEqual(ico_bytes[7], 64)
        self.assertEqual(struct.unpack("<I", ico_bytes[14:18])[0], len(png_bytes))

    def test_export_icon_palette_is_stable_for_same_project(self) -> None:
        project = {"projectId": "same", "title": "Same Project"}
        self.assertEqual(build_export_icon_palette(project), build_export_icon_palette(dict(project)))
        self.assertIn("backgroundTop", build_export_icon_palette(project))

    def test_write_export_icon_files_outputs_png_and_ico(self) -> None:
        png_bytes = build_export_icon_png({"projectId": "write", "title": "Write Test"}, size=32)
        ico_bytes = build_export_icon_ico(png_bytes, size=32)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_icon_files(Path(tmp_dir), png_bytes, ico_bytes, file_stem="demo_icon")

            self.assertTrue(result["pngPath"].is_file())
            self.assertTrue(result["icoPath"].is_file())
            self.assertEqual(result["pngFileName"], "demo_icon.png")
            self.assertEqual(result["icoFileName"], "demo_icon.ico")
            self.assertEqual(result["pngPath"].read_bytes(), png_bytes)
            self.assertEqual(result["icoPath"].read_bytes(), ico_bytes)


if __name__ == "__main__":
    unittest.main()
