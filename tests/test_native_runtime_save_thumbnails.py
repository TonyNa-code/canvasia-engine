from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from native_runtime.runtime_save_thumbnails import (
    SAVE_THUMBNAIL_HEIGHT,
    SAVE_THUMBNAIL_WIDTH,
    build_save_thumbnail_metadata,
    build_save_thumbnail_status,
    calculate_cover_geometry,
    create_versioned_save_thumbnail_key,
    get_project_save_thumbnail_dir,
    get_save_thumbnail_key,
    get_save_thumbnail_path,
    is_safe_save_thumbnail_key,
    make_safe_project_storage_stem,
    prune_orphaned_save_thumbnails,
    resolve_snapshot_thumbnail_path,
    write_save_thumbnail_atomic,
)


class NativeRuntimeSaveThumbnailTests(unittest.TestCase):
    def test_project_and_thumbnail_keys_are_path_safe(self) -> None:
        self.assertEqual(make_safe_project_storage_stem("../My Game/路线"), "My_Game_路线")
        self.assertEqual(get_save_thumbnail_key("quick"), "quick")
        self.assertEqual(get_save_thumbnail_key("formal", 0), "formal-0001")
        self.assertEqual(get_save_thumbnail_key("formal", 119), "formal-0120")
        versioned_key = create_versioned_save_thumbnail_key("formal", 1)
        self.assertRegex(versioned_key, r"^formal-0002-[0-9a-f]{12}$")
        self.assertTrue(is_safe_save_thumbnail_key(versioned_key))
        self.assertTrue(is_safe_save_thumbnail_key("formal-0024"))
        self.assertFalse(is_safe_save_thumbnail_key("../formal-0024"))
        with self.assertRaises(ValueError):
            get_save_thumbnail_key("formal", -1)
        with self.assertRaises(ValueError):
            get_save_thumbnail_path("project", "../quick")

    def test_cover_geometry_crops_without_distorting(self) -> None:
        wide = calculate_cover_geometry(1920, 1080)
        self.assertEqual(wide["scaledWidth"], SAVE_THUMBNAIL_WIDTH)
        self.assertEqual(wide["scaledHeight"], SAVE_THUMBNAIL_HEIGHT)
        self.assertEqual((wide["offsetX"], wide["offsetY"]), (0, 0))

        portrait = calculate_cover_geometry(720, 1280)
        self.assertEqual(portrait["scaledWidth"], SAVE_THUMBNAIL_WIDTH)
        self.assertGreater(portrait["scaledHeight"], SAVE_THUMBNAIL_HEIGHT)
        self.assertLess(portrait["offsetY"], 0)

    def test_metadata_and_resolution_never_store_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            metadata = build_save_thumbnail_metadata("quick", captured_at="2026-07-16T12:00:00+08:00")
            self.assertEqual(metadata["thumbnailKey"], "quick")
            self.assertNotIn(str(root), str(metadata))
            self.assertIsNone(resolve_snapshot_thumbnail_path(metadata, "project", root))

            target = get_save_thumbnail_path("project", "quick", root)
            target.parent.mkdir(parents=True)
            target.write_bytes(b"png")
            self.assertEqual(resolve_snapshot_thumbnail_path(metadata, "project", root), target)
            self.assertIsNone(resolve_snapshot_thumbnail_path({"thumbnailKey": "../quick"}, "project", root))

    def test_atomic_writer_replaces_file_and_cleans_failed_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "quick.png"
            target.write_bytes(b"old")
            write_save_thumbnail_atomic(target, lambda path: path.write_bytes(b"new-image"))
            self.assertEqual(target.read_bytes(), b"new-image")

            def fail_writer(path: Path) -> None:
                path.write_bytes(b"partial")
                raise RuntimeError("simulated encoder failure")

            with self.assertRaises(RuntimeError):
                write_save_thumbnail_atomic(target, fail_writer)
            self.assertEqual(target.read_bytes(), b"new-image")
            self.assertEqual(list(target.parent.glob(".*.tmp.png")), [])

    def test_status_and_orphan_cleanup_follow_save_store_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project_id = "project"
            project_dir = get_project_save_thumbnail_dir(project_id, root)
            project_dir.mkdir(parents=True)
            (project_dir / "quick.png").write_bytes(b"quick")
            (project_dir / "formal-0001.png").write_bytes(b"slot")
            (project_dir / "formal-0099.png").write_bytes(b"orphan")
            (project_dir / "formal-0098-deadbeefcafe.png").write_bytes(b"versioned-orphan")
            (project_dir / "notes.png").write_bytes(b"leave-unknown")
            save_store = {
                "quickSave": {"thumbnailKey": "quick"},
                "formalSlots": [
                    {"thumbnailKey": "formal-0001"},
                    {"thumbnailKey": "formal-0002"},
                ],
            }

            status = build_save_thumbnail_status(save_store, project_id, root)
            self.assertEqual(status["referencedCount"], 3)
            self.assertEqual(status["availableCount"], 2)
            self.assertEqual(status["missingKeys"], ["formal-0002"])

            removed = prune_orphaned_save_thumbnails(save_store, project_id, root)
            self.assertEqual(
                sorted(path.name for path in removed),
                ["formal-0098-deadbeefcafe.png", "formal-0099.png"],
            )
            self.assertTrue((project_dir / "notes.png").is_file())


if __name__ == "__main__":
    unittest.main()
