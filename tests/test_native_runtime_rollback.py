import unittest

from native_runtime.runtime_rollback import (
    append_rollback_checkpoint,
    build_rollback_checkpoint_key,
    build_rollback_status,
    can_rollback_story,
    clone_rollback_checkpoint,
    normalize_rollback_limit,
    take_rollback_step,
)


def make_snapshot(index: int, *, saved_at: str = "2026-07-16T00:00:00Z") -> dict:
    return {
        "kind": "auto-resume",
        "savedAt": saved_at,
        "sceneId": "scene_start",
        "sceneName": "Opening",
        "blockIndex": index,
        "variableState": {"affection": index},
        "visibleCharacters": {"heroine": {"position": "center", "expressionId": f"expr_{index}"}},
        "textHistory": [{"key": f"line_{index}", "text": f"Line {index}"}],
        "summaryText": f"Line {index}",
    }


class NativeRuntimeRollbackTests(unittest.TestCase):
    def test_limit_normalization_is_bounded(self) -> None:
        self.assertEqual(normalize_rollback_limit(None), 120)
        self.assertEqual(normalize_rollback_limit(1), 2)
        self.assertEqual(normalize_rollback_limit(9999), 500)

    def test_checkpoint_clone_isolated_from_source_mutation(self) -> None:
        source = make_snapshot(1)
        checkpoint = clone_rollback_checkpoint(source)

        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint["kind"], "rollback")
        source["variableState"]["affection"] = 999
        self.assertEqual(checkpoint["variableState"]["affection"], 1)

    def test_identity_ignores_timestamp_and_text_history_but_not_story_state(self) -> None:
        first = make_snapshot(1, saved_at="2026-07-16T00:00:00Z")
        duplicate = make_snapshot(1, saved_at="2026-07-16T00:01:00Z")
        duplicate["textHistory"].append({"key": "extra", "text": "Extra"})
        changed = make_snapshot(2)

        self.assertEqual(build_rollback_checkpoint_key(first), build_rollback_checkpoint_key(duplicate))
        self.assertNotEqual(build_rollback_checkpoint_key(first), build_rollback_checkpoint_key(changed))

    def test_append_deduplicates_latest_checkpoint_and_keeps_fresh_history(self) -> None:
        timeline = append_rollback_checkpoint([], make_snapshot(1))
        refreshed = make_snapshot(1, saved_at="2026-07-16T00:02:00Z")
        refreshed["textHistory"].append({"key": "extra", "text": "Extra"})
        timeline = append_rollback_checkpoint(timeline, refreshed)

        self.assertEqual(len(timeline), 1)
        self.assertEqual(len(timeline[0]["textHistory"]), 2)
        self.assertEqual(timeline[0]["savedAt"], "2026-07-16T00:02:00Z")

    def test_append_enforces_capacity_and_take_restores_previous_state(self) -> None:
        timeline = []
        for index in range(5):
            timeline = append_rollback_checkpoint(timeline, make_snapshot(index), limit=3)

        self.assertEqual([item["blockIndex"] for item in timeline], [2, 3, 4])
        self.assertTrue(can_rollback_story(timeline))
        remaining, previous = take_rollback_step(timeline)
        self.assertEqual([item["blockIndex"] for item in remaining], [2, 3])
        self.assertEqual(previous["blockIndex"], 3)
        previous["variableState"]["affection"] = 999
        self.assertEqual(remaining[-1]["variableState"]["affection"], 3)

    def test_status_and_empty_step_are_safe(self) -> None:
        timeline = append_rollback_checkpoint([], make_snapshot(0))
        status = build_rollback_status(timeline)
        remaining, previous = take_rollback_step(timeline)

        self.assertEqual(status, {"checkpointCount": 1, "availableSteps": 0, "canRollback": False})
        self.assertFalse(can_rollback_story(timeline))
        self.assertEqual(len(remaining), 1)
        self.assertIsNone(previous)


if __name__ == "__main__":
    unittest.main()
