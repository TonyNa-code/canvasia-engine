from __future__ import annotations

import unittest

from native_runtime.runtime_preload import (
    build_runtime_preload_status,
    format_runtime_preload_status_line,
    get_runtime_preload_adaptive_frame_budget,
    mark_runtime_preload_entry,
)


def make_entry(asset_id: str, *, size_bytes: int = 1024) -> dict:
    return {
        "assetId": asset_id,
        "name": asset_id,
        "type": "ui",
        "phase": "deferred",
        "sizeBytes": size_bytes,
    }


class NativeRuntimePreloadTests(unittest.TestCase):
    def test_fast_samples_restore_high_quality_frame_budget(self) -> None:
        entries = [make_entry("a"), make_entry("b"), make_entry("c")]
        status = build_runtime_preload_status(entries, "high_quality_pc")

        for entry, elapsed_ms in zip(entries, (1.0, 2.0, 3.0), strict=True):
            status = mark_runtime_preload_entry(status, entry, "loaded_image", elapsed_ms=elapsed_ms)

        self.assertEqual(status["timedEntries"], 3)
        self.assertEqual(status["averageEntryMs"], 2.0)
        self.assertEqual(status["maxEntryMs"], 3.0)
        self.assertEqual(status["adaptiveFrameBudget"], 3)
        self.assertEqual(get_runtime_preload_adaptive_frame_budget(status), 3)
        self.assertEqual(status["slowEntryCount"], 0)
        self.assertIn("每帧预算 3/3", format_runtime_preload_status_line(status))

    def test_slow_sample_reduces_budget_and_records_bounded_diagnostics(self) -> None:
        entries = [make_entry(f"asset-{index}") for index in range(7)]
        status = build_runtime_preload_status(entries, "high_quality_pc")

        for index, entry in enumerate(entries):
            status = mark_runtime_preload_entry(
                status,
                entry,
                "failed" if index == 0 else "loaded_image",
                elapsed_ms=10 + index,
            )

        self.assertEqual(status["adaptiveFrameBudget"], 1)
        self.assertEqual(status["slowEntryCount"], 7)
        self.assertEqual(len(status["slowestEntries"]), 5)
        self.assertEqual(status["slowestEntries"][0]["assetId"], "asset-6")
        self.assertEqual(status["slowestEntries"][0]["elapsedMs"], 16.0)
        self.assertIn("慢项 7", status["summaryText"])
        self.assertIn("每帧预算 1/3", status["summaryText"])

    def test_missing_timing_samples_keep_conservative_ramp_up(self) -> None:
        status = build_runtime_preload_status([make_entry("a")], "high_quality_pc")

        self.assertEqual(status["adaptiveFrameBudget"], 1)
        self.assertEqual(get_runtime_preload_adaptive_frame_budget(status), 1)


if __name__ == "__main__":
    unittest.main()
