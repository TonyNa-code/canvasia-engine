from __future__ import annotations

import tempfile
import unittest
from email.utils import formatdate
from pathlib import Path

from editor_local_security import extract_host_from_header, is_local_editor_host, is_local_editor_origin
from editor_snapshot_cache import SnapshotCache, build_file_cache_signature
from editor_static_cache import (
    build_editor_static_cache_headers,
    is_editor_static_cache_candidate,
    normalize_request_path,
    request_etag_matches,
    request_modified_since_matches,
)


class EditorInfrastructureTests(unittest.TestCase):
    def test_local_editor_security_accepts_only_loopback_hosts(self) -> None:
        self.assertEqual(extract_host_from_header("[::1]:8765"), "::1")
        self.assertTrue(is_local_editor_host("127.0.0.1:8765"))
        self.assertTrue(is_local_editor_host("localhost."))
        self.assertTrue(is_local_editor_origin("http://[::1]:8765/prototype_editor/index.html"))
        self.assertFalse(is_local_editor_host("127.0.0.1.example.com"))
        self.assertFalse(is_local_editor_origin("null"))
        self.assertFalse(is_local_editor_origin("https://example.com/probe"))

    def test_snapshot_cache_reuses_deep_copies_until_signature_changes(self) -> None:
        signature = {"value": 1}
        build_count = {"value": 0}
        cache = SnapshotCache()

        def build_signature() -> int:
            return signature["value"]

        def build_payload() -> dict:
            build_count["value"] += 1
            return {"items": ["clean"], "build": build_count["value"]}

        first_payload = cache.get_or_build(build_signature, build_payload)
        first_payload["items"].append("caller mutation")

        second_payload = cache.get_or_build(build_signature, build_payload)
        self.assertEqual(second_payload, {"items": ["clean"], "build": 1})
        self.assertEqual(build_count["value"], 1)

        signature["value"] = 2
        refreshed_payload = cache.get_or_build(build_signature, build_payload)
        self.assertEqual(refreshed_payload["build"], 2)

    def test_file_cache_signature_tracks_size_and_mtime_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "watched.json"
            missing_signature = build_file_cache_signature(path)
            self.assertEqual(missing_signature, (path.as_posix(), "missing"))

            path.write_text("one", encoding="utf-8")
            first_signature = build_file_cache_signature(path)
            path.write_text("one plus more", encoding="utf-8")
            second_signature = build_file_cache_signature(path)

        self.assertNotEqual(first_signature, second_signature)

    def test_editor_static_cache_only_targets_safe_static_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_path = root / "app.js"
            script_path.write_text("console.log('ready');", encoding="utf-8")
            image_path = root / "room.png"
            image_path.write_bytes(b"fake-png")
            data_path = root / "assets.json"
            data_path.write_text("{}", encoding="utf-8")
            python_path = root / "app.py"
            python_path.write_text("print('not static')", encoding="utf-8")

            self.assertEqual(normalize_request_path("prototype_editor/app.js?v=1"), "/prototype_editor/app.js")
            self.assertTrue(is_editor_static_cache_candidate("/prototype_editor/app.js", script_path))
            self.assertTrue(is_editor_static_cache_candidate("/template_project/assets/backgrounds/room.png", image_path))
            self.assertFalse(is_editor_static_cache_candidate("/api/project-data", script_path))
            self.assertFalse(is_editor_static_cache_candidate("/template_project/data/assets.json", data_path))
            self.assertFalse(is_editor_static_cache_candidate("/prototype_editor/app.py", python_path))

    def test_editor_static_cache_headers_support_etag_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "module.js"
            path.write_text("export const ok = true;", encoding="utf-8")

            headers = build_editor_static_cache_headers(path)
            self.assertEqual(headers["Cache-Control"], "private, max-age=0, must-revalidate")
            self.assertTrue(headers["ETag"].startswith('W/"canvasia-'))
            self.assertTrue(request_etag_matches(headers["ETag"], headers["ETag"]))
            self.assertTrue(request_etag_matches(headers["ETag"].removeprefix("W/"), headers["ETag"]))
            self.assertTrue(request_etag_matches("*, \"other\"", headers["ETag"]))
            self.assertFalse(request_etag_matches('"other"', headers["ETag"]))
            self.assertTrue(request_modified_since_matches(headers["Last-Modified"], path))
            self.assertFalse(request_modified_since_matches(formatdate(0, usegmt=True), path))
            self.assertFalse(request_modified_since_matches("not-a-http-date", path))


if __name__ == "__main__":
    unittest.main()
