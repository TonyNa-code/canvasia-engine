from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from editor_local_security import extract_host_from_header, is_local_editor_host, is_local_editor_origin
from editor_snapshot_cache import SnapshotCache, build_file_cache_signature


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


if __name__ == "__main__":
    unittest.main()
