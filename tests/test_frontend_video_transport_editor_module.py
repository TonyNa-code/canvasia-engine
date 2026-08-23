from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "video_transport_editor.js"
RUNTIME_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_video_transport.js"
LIFECYCLE_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_playback_lifecycle.js"


class FrontendVideoTransportEditorModuleTests(unittest.TestCase):
    def test_beginner_presets_render_and_update_real_transport_fields(self) -> None:
        script = textwrap.dedent(
            f"""
            import fs from "fs";
            import vm from "vm";
            import * as runtimeTools from {json.dumps(RUNTIME_MODULE_PATH.as_uri())};
            import * as delayTools from {json.dumps(LIFECYCLE_MODULE_PATH.as_uri())};

            const controls = new Map([
              ["editorVideoAutoplay", {{ value: "true" }}],
              ["editorVideoLoop", {{ value: "false" }}],
              ["editorVideoResumeMode", {{ value: "restart" }}],
              ["editorVideoStartTime", {{ value: "0" }}],
              ["editorVideoEndTime", {{ value: "0" }}],
              ["editorVideoFit", {{ value: "contain" }}],
              ["editorVideoVolume", {{ value: "100" }}],
              ["editorVideoSkippable", {{ value: "true", disabled: false }}],
            ]);
            const summary = {{ textContent: "" }};
            const status = {{ textContent: "", className: "" }};
            const document = {{
              getElementById(id) {{ return controls.get(id) ?? null; }},
              querySelector(selector) {{
                if (selector === "[data-video-transport-summary]") return summary;
                if (selector === "[data-video-transport-status]") return status;
                return null;
              }},
            }};
            const context = {{ window: {{ CanvasiaRuntimeVideoTransport: runtimeTools }}, document }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(EDITOR_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorVideoTransport;
            const html = tools.renderVideoTransportEditor({{ startTimeSeconds: 3, endTimeSeconds: 12 }}, {{ runtimeTools }});
            const applied = tools.applyVideoTransportPreset("atmosphere_loop", document, {{ runtimeTools }});
            const value = tools.readVideoTransportEditor({{}}, document, {{ runtimeTools }});
            const missingPreset = tools.applyVideoTransportPreset("missing", document, {{ runtimeTools }});
            process.stdout.write(JSON.stringify({{
              html,
              applied,
              missingPreset,
              value,
              summary: summary.textContent,
              status: status.textContent,
              statusClass: status.className,
              skippableDisabled: controls.get("editorVideoSkippable").disabled,
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("视频播放导演", payload["html"])
        self.assertIn('data-video-transport-preset="op_ed"', payload["html"])
        self.assertIn('data-video-transport-preset="atmosphere_loop"', payload["html"])
        self.assertTrue(payload["applied"]["ok"])
        self.assertFalse(payload["missingPreset"]["ok"])
        self.assertEqual(payload["value"]["loop"], True)
        self.assertEqual(payload["value"]["resumeMode"], "resume")
        self.assertEqual(payload["value"]["fit"], "cover")
        self.assertEqual(payload["value"]["volume"], 0)
        self.assertTrue(payload["value"]["skippable"])
        self.assertTrue(payload["skippableDisabled"])
        self.assertIn("循环播放", payload["summary"])
        self.assertIn("有效", payload["status"])
        self.assertEqual(payload["statusClass"], "video-transport-status is-good")

    def test_preview_controller_plays_segment_captures_position_and_finishes(self) -> None:
        script = textwrap.dedent(
            f"""
            import fs from "fs";
            import vm from "vm";
            import * as runtimeTools from {json.dumps(RUNTIME_MODULE_PATH.as_uri())};
            import * as delayTools from {json.dumps(LIFECYCLE_MODULE_PATH.as_uri())};

            class FakeElement {{
              constructor(tagName, ownerDocument) {{
                this.tagName = tagName;
                this.ownerDocument = ownerDocument;
                this.children = [];
                this.listeners = new Map();
                this.dataset = {{}};
                this.currentTime = 0;
                this.duration = 30;
                this.readyState = 1;
                this.parentNode = null;
                this.playCount = 0;
                this.pauseCount = 0;
                this.paused = true;
                this.ended = false;
                this.removed = false;
              }}
              append(...items) {{
                items.forEach((item) => {{ item.parentNode = this; this.children.push(item); }});
              }}
              addEventListener(name, callback) {{ this.listeners.set(name, callback); }}
              removeEventListener(name) {{ this.listeners.delete(name); }}
              setAttribute() {{}}
              removeAttribute() {{}}
              load() {{}}
              pause() {{ this.pauseCount += 1; this.paused = true; }}
              play() {{ this.playCount += 1; this.paused = false; return Promise.resolve(); }}
              emit(name, event = {{ stopPropagation() {{}} }}) {{ this.listeners.get(name)?.(event); }}
              contains(target) {{ return this === target || this.children.some((child) => child.contains?.(target)); }}
              remove() {{
                this.removed = true;
                if (this.parentNode) {{
                  this.parentNode.children = this.parentNode.children.filter((item) => item !== this);
                }}
              }}
            }}
            const document = {{ createElement(tagName) {{ return new FakeElement(tagName, document); }} }};
            const root = new FakeElement("root", document);
            const context = {{
              window: {{ CanvasiaRuntimeVideoTransport: runtimeTools }},
              document,
              clearTimeout,
              setTimeout,
            }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(EDITOR_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorVideoTransport;
            const controller = tools.createPreviewVideoController({{ runtimeTools, delayTools }});
            const snapshot = {{
              blockType: "video_play",
              videoPlaybackPositionSeconds: 2,
              block: {{ resumeMode: "resume", startTimeSeconds: 1, endTimeSeconds: 4, skippable: true }},
            }};
            let finishReason = "";
            const synced = controller.sync(snapshot, {{
              root,
              stepKey: "scene:0",
              videoUrl: "opening movie.mp4",
              title: "Opening",
              onFinished(_snapshot, detail) {{ finishReason = detail.reason; }},
            }});
            const overlay = root.children[0];
            const video = overlay.children[0];
            const initialTime = video.currentTime;
            const suspended = controller.suspend();
            const resumed = controller.resume();
            video.currentTime = 3.25;
            const captured = controller.capture(snapshot);
            video.currentTime = 4;
            video.emit("timeupdate");
            process.stdout.write(JSON.stringify({{
              synced,
              initialTime,
              captured,
              snapshotPosition: snapshot.videoPlaybackPositionSeconds,
              playCount: video.playCount,
              pauseCount: video.pauseCount,
              suspended,
              resumed,
              finishReason,
              overlayRemoved: overlay.removed,
              remainingChildren: root.children.length,
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["synced"])
        self.assertEqual(payload["initialTime"], 2)
        self.assertEqual(payload["captured"], 3.25)
        self.assertEqual(payload["snapshotPosition"], 3.25)
        self.assertEqual(payload["playCount"], 2)
        self.assertGreaterEqual(payload["pauseCount"], 1)
        self.assertTrue(payload["suspended"]["suspended"])
        self.assertFalse(payload["resumed"]["suspended"])
        self.assertEqual(payload["finishReason"], "segment-end")
        self.assertTrue(payload["overlayRemoved"])
        self.assertEqual(payload["remainingChildren"], 0)


if __name__ == "__main__":
    unittest.main()
