from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_story_flow.js"


class FrontendRuntimeStoryFlowModuleTests(unittest.TestCase):
    def test_story_call_stack_supports_nested_calls_and_safe_returns(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaRuntimeStoryFlow;
            const scenes = new Set(["main", "phone", "common"]);
            const hasScene = (sceneId) => scenes.has(sceneId);
            const first = tools.createStoryCallTransition({{
              callStack: [], sourceSceneId: "main", sourceBlockIndex: 2,
              sourceBlockId: "call_phone", targetSceneId: "phone", hasScene,
            }});
            const second = tools.createStoryCallTransition({{
              callStack: first.callStack, sourceSceneId: "phone", sourceBlockIndex: 4,
              sourceBlockId: "call_common", targetSceneId: "common", hasScene,
            }});
            const returnOne = tools.createStoryReturnTransition(second.callStack, {{ hasScene }});
            const returnTwo = tools.createStoryReturnTransition(returnOne.callStack, {{ hasScene }});
            const missingReturn = tools.createStoryReturnTransition([], {{ hasScene }});
            const missingTarget = tools.createStoryCallTransition({{
              callStack: [], sourceSceneId: "main", sourceBlockIndex: 0,
              targetSceneId: "missing", hasScene,
            }});
            const depthError = tools.createStoryCallTransition({{
              callStack: [
                {{ sceneId: "main", blockIndex: 1 }},
                {{ sceneId: "phone", blockIndex: 1 }},
              ],
              sourceSceneId: "common", sourceBlockIndex: 0,
              targetSceneId: "main", hasScene, maxDepth: 2,
            }});
            const sanitized = tools.sanitizeStoryCallStack([
              null,
              {{ sceneId: "missing", blockIndex: 1 }},
              {{ sceneId: "main", blockIndex: -1 }},
              {{ sceneId: "main", blockIndex: 3, callerBlockId: 9 }},
            ], {{ hasScene }});
            const callLocation = tools.resolveNextStoryLocation({{
              sceneId: "main", blockIndex: 2, blockId: "call_phone", blockType: "scene_call",
              block: {{ targetSceneId: "phone" }}, callStack: [],
            }}, {{
              hasScene,
              hasNextBlock: (sceneId, blockIndex) => sceneId === "phone" && blockIndex === 0,
            }});
            const nextLocation = tools.resolveNextStoryLocation({{
              sceneId: "main", blockIndex: 0, blockType: "dialogue", callStack: [],
            }}, {{ hasScene, hasNextBlock: (sceneId, blockIndex) => sceneId === "main" && blockIndex === 1 }});
            const implicitReturn = tools.resolveNextStoryLocation({{
              sceneId: "phone", blockIndex: 3, blockType: "dialogue",
              callStack: [{{ sceneId: "main", blockIndex: 3 }}],
            }}, {{ hasScene, hasNextBlock: () => false }});
            const completed = tools.resolveNextStoryLocation({{
              sceneId: "main", blockIndex: 7, blockType: "dialogue", callStack: [],
            }}, {{ hasScene, hasNextBlock: () => false }});
            const nestedTailReturn = tools.resolveNextStoryLocation({{
              sceneId: "common", blockIndex: 0, blockType: "dialogue",
              callStack: [
                {{ sceneId: "main", blockIndex: 3 }},
                {{ sceneId: "phone", blockIndex: 5 }},
              ],
            }}, {{
              hasScene,
              hasNextBlock: (sceneId, blockIndex) => sceneId === "main" && blockIndex === 3,
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(), first, second, returnOne, returnTwo,
              missingReturn, missingTarget, depthError, sanitized,
              callLocation, nextLocation, implicitReturn, completed, nestedTailReturn,
              labels: [
                tools.getStoryFlowErrorMessage("missing_call_target"),
                tools.getStoryFlowErrorMessage("empty_call_stack"),
              ],
              types: [tools.isStoryFlowBlockType("scene_call"), tools.isStoryFlowBlockType("jump")],
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("createStoryCallTransition", payload["keys"])
        self.assertEqual(payload["first"]["callStack"][0]["blockIndex"], 3)
        self.assertEqual(payload["second"]["depth"], 2)
        self.assertEqual(payload["returnOne"]["targetSceneId"], "phone")
        self.assertEqual(payload["returnOne"]["targetBlockIndex"], 5)
        self.assertEqual(payload["returnTwo"]["targetSceneId"], "main")
        self.assertEqual(payload["returnTwo"]["targetBlockIndex"], 3)
        self.assertEqual(payload["missingReturn"]["errorCode"], "empty_call_stack")
        self.assertEqual(payload["missingTarget"]["errorCode"], "missing_call_target")
        self.assertEqual(payload["depthError"]["errorCode"], "call_depth_exceeded")
        self.assertEqual(payload["sanitized"], [{
            "sceneId": "main",
            "blockIndex": 3,
            "callerBlockId": "9",
            "targetSceneId": "",
        }])
        self.assertEqual(payload["callLocation"]["reason"], "call")
        self.assertEqual(payload["callLocation"]["targetSceneId"], "phone")
        self.assertTrue(payload["callLocation"]["applyTerminalScope"])
        self.assertEqual(payload["nextLocation"]["reason"], "next")
        self.assertEqual(payload["nextLocation"]["targetBlockIndex"], 1)
        self.assertEqual(payload["implicitReturn"]["reason"], "implicit_return")
        self.assertEqual(payload["implicitReturn"]["targetSceneId"], "main")
        self.assertEqual(payload["completed"]["kind"], "complete")
        self.assertEqual(payload["nestedTailReturn"]["reason"], "implicit_return")
        self.assertEqual(payload["nestedTailReturn"]["targetSceneId"], "main")
        self.assertEqual(payload["nestedTailReturn"]["targetBlockIndex"], 3)
        self.assertEqual(payload["nestedTailReturn"]["callStack"], [])
        self.assertIn("不存在", payload["labels"][0])
        self.assertIn("没有可返回", payload["labels"][1])
        self.assertEqual(payload["types"], [True, False])


if __name__ == "__main__":
    unittest.main()
