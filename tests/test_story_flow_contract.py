from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def read_source(relative_path: str) -> str:
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


class StoryFlowContractTests(unittest.TestCase):
    def test_reusable_subscenes_are_wired_across_authoring_and_runtimes(self) -> None:
        sources = {
            "catalog": read_source("prototype_editor/modules/story_block_catalog.js"),
            "actions": read_source("prototype_editor/modules/story_block_actions.js"),
            "editors": read_source("prototype_editor/modules/story_block_editors.js"),
            "importer": read_source("prototype_editor/modules/script_importer.js"),
            "mapping": read_source("prototype_editor/modules/script_import_mapping.js"),
            "editor": read_source("prototype_editor/app.js"),
            "web": read_source("export_player_template/player.js"),
            "native": read_source("native_runtime/runtime_player.py"),
        }

        self.assertIn('type: "scene_call"', sources["catalog"])
        self.assertIn('type: "scene_return"', sources["catalog"])
        self.assertIn('"add-scene-call": Object.freeze({', sources["actions"])
        self.assertIn('"add-scene-return": Object.freeze({', sources["actions"])
        self.assertIn("function renderSceneCallEditor", sources["editors"])
        self.assertIn("parseSceneFlowLine", sources["importer"])
        self.assertIn('draftBlock.type === "scene_call"', sources["mapping"])
        self.assertIn("resolveNextStoryLocation", sources["editor"])
        self.assertIn("resolveNextStoryLocation", sources["web"])
        self.assertIn("create_story_call_transition", sources["native"])

    def test_story_call_stack_and_exports_share_the_same_contract(self) -> None:
        editor_index = read_source("prototype_editor/index.html")
        web_index = read_source("export_player_template/index.html")
        preview_save = read_source("prototype_editor/modules/preview_save.js")
        editor = read_source("prototype_editor/app.js")
        web = read_source("export_player_template/player.js")
        native = read_source("native_runtime/runtime_player.py")
        renpy_js = read_source("prototype_editor/modules/renpy_exporter.js")
        renpy_py = read_source("renpy_export.py")
        run_editor = read_source("run_editor.py")
        route_analyzer = read_source("prototype_editor/modules/route_analyzer.js")
        route_report = read_source("prototype_editor/modules/route_testing_report.js")

        self.assertIn("runtime_story_flow.js", editor_index)
        self.assertIn("runtime_story_flow.js", web_index)
        self.assertIn("callStack: sanitizeCallStack", preview_save)
        self.assertIn("callStack: safeCallStack", editor)
        self.assertIn("callStack: safeCallStack", web)
        self.assertIn('"storyCallStack": sanitize_story_call_stack', native)
        self.assertIn('type === "scene_call"', renpy_js)
        self.assertIn('block_type == "scene_call"', renpy_py)
        self.assertIn('"runtime_story_flow.js"', run_editor)
        self.assertIn('NATIVE_RUNTIME_STORY_FLOW_NAME = "runtime_story_flow.py"', run_editor)
        self.assertIn("subsceneCases", route_analyzer)
        self.assertIn("serialized.subsceneCases", route_report)


if __name__ == "__main__":
    unittest.main()
