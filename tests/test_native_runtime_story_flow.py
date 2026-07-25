from __future__ import annotations

import unittest

from native_runtime.runtime_story_flow import (
    create_story_call_transition,
    create_story_return_transition,
    get_story_flow_error_message,
    is_story_scene_ending_candidate,
    sanitize_story_call_stack,
)
from native_runtime.runtime_player import (
    build_ending_scene_ids,
    collect_scene_outgoing_targets,
)


class NativeRuntimeStoryFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenes = {"main", "phone", "common"}
        self.has_scene = self.scenes.__contains__

    def test_nested_calls_return_to_exact_next_blocks(self) -> None:
        first = create_story_call_transition(
            call_stack=[],
            source_scene_id="main",
            source_block_index=2,
            source_block_id="call_phone",
            target_scene_id="phone",
            has_scene=self.has_scene,
        )
        second = create_story_call_transition(
            call_stack=first["callStack"],
            source_scene_id="phone",
            source_block_index=4,
            source_block_id="call_common",
            target_scene_id="common",
            has_scene=self.has_scene,
        )
        return_one = create_story_return_transition(second["callStack"], has_scene=self.has_scene)
        return_two = create_story_return_transition(return_one["callStack"], has_scene=self.has_scene)

        self.assertEqual(first["callStack"][0]["blockIndex"], 3)
        self.assertEqual(second["depth"], 2)
        self.assertEqual((return_one["targetSceneId"], return_one["targetBlockIndex"]), ("phone", 5))
        self.assertEqual((return_two["targetSceneId"], return_two["targetBlockIndex"]), ("main", 3))

    def test_invalid_targets_depth_and_malformed_frames_fail_safely(self) -> None:
        missing = create_story_call_transition(
            call_stack=[],
            source_scene_id="main",
            source_block_index=0,
            source_block_id="call_missing",
            target_scene_id="missing",
            has_scene=self.has_scene,
        )
        depth = create_story_call_transition(
            call_stack=[
                {"sceneId": "main", "blockIndex": 1},
                {"sceneId": "phone", "blockIndex": 1},
            ],
            source_scene_id="common",
            source_block_index=0,
            source_block_id="call_main",
            target_scene_id="main",
            has_scene=self.has_scene,
            max_depth=2,
        )
        sanitized = sanitize_story_call_stack(
            [None, {"sceneId": "missing", "blockIndex": 1}, {"sceneId": "main", "blockIndex": 3}],
            has_scene=self.has_scene,
        )
        empty = create_story_return_transition([], has_scene=self.has_scene)

        self.assertEqual(missing["errorCode"], "missing_call_target")
        self.assertEqual(depth["errorCode"], "call_depth_exceeded")
        self.assertEqual(sanitized[0]["sceneId"], "main")
        self.assertEqual(empty["errorCode"], "empty_call_stack")
        self.assertIn("没有可返回", get_story_flow_error_message(empty["errorCode"]))

    def test_subscene_links_count_for_reachability_but_not_false_endings(self) -> None:
        caller = {"id": "main", "blocks": [{"type": "scene_call", "targetSceneId": "common"}]}
        common = {"id": "common", "blocks": [{"type": "scene_return"}]}
        chapters = [{"scenes": [caller, common]}]

        self.assertEqual(collect_scene_outgoing_targets(caller), ["common"])
        self.assertTrue(is_story_scene_ending_candidate(caller))
        self.assertFalse(is_story_scene_ending_candidate(common))
        self.assertEqual(build_ending_scene_ids(chapters), ["main"])


if __name__ == "__main__":
    unittest.main()
