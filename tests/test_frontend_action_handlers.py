from __future__ import annotations

import json
import re
import subprocess
import textwrap
import unittest
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
INDEX_PATH = EDITOR_DIR / "index.html"
APP_PATH = EDITOR_DIR / "app.js"
MODULE_PATHS = tuple(sorted((EDITOR_DIR / "modules").glob("*.js")))
ACTION_ATTRIBUTE_PATHS = (INDEX_PATH, APP_PATH)
ACTION_CONFIG_PATHS = (APP_PATH, *MODULE_PATHS)

ACTION_ATTRIBUTE_PATTERN = re.compile(
    r"(?<!\[)\bdata-action\s*=\s*([\"'])([^\"'${}]+)\1"
)
ACTION_HANDLER_PATTERN = re.compile(r"\baction\s*===\s*([\"'])([^\"']+)\1")
ACTION_CASE_HANDLER_PATTERN = re.compile(r"\bcase\s+([\"'])([^\"']+)\1\s*:")
ACTION_CONFIG_VALUE_PATTERN = re.compile(r"\baction\s*:\s*([\"'])([^\"']+)\1")

DYNAMIC_DATA_ACTION_MARKERS = Counter(
    {
        'data-action="${project.isSample ? "duplicate-project" : "rename-project"}"': 1,
        'data-action="${actionName}"': 2,
        'data-action="${mode === "save" ? "quick-save-preview" : "quick-load-preview"}"': 1,
        'data-action="${action.action}"': 1,
        'data-action="${escapeHtml(action.action ?? "")}"': 1,
        'data-action="${button.action}"': 1,
        'data-action="${action.action}"${': 1,
        'data-action="${escapeHtml(button.action)}"': 1,
    }
)

NON_CLICK_ACTION_VALUES = {
    "apply",
    "fade_out",
    "start",
    "stop",
    "zoom_in",
}


def _line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _get_handled_actions() -> set[str]:
    app_source = APP_PATH.read_text(encoding="utf-8")
    click_handler = _extract_function_source(app_source, "handleClick")
    handled_actions = {
        match.group(2)
        for match in ACTION_HANDLER_PATTERN.finditer(click_handler)
    }
    handled_actions.update(
        match.group(2)
        for match in ACTION_CASE_HANDLER_PATTERN.finditer(click_handler)
    )
    return handled_actions


def _extract_function_source(source: str, function_name: str) -> str:
    marker_match = re.search(
        rf"(?:async\s+)?function\s+{re.escape(function_name)}\s*\(",
        source,
    )
    if not marker_match:
        raise AssertionError(f"Missing function {function_name}")
    signature_depth = 0
    body_start = -1
    for index in range(marker_match.end() - 1, len(source)):
        char = source[index]
        if char == "(":
            signature_depth += 1
        elif char == ")":
            signature_depth -= 1
            if signature_depth == 0:
                body_start = source.find("{", index)
                break
    if body_start < 0:
        raise AssertionError(f"Missing function body for {function_name}")

    depth = 0
    for index in range(body_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start : index + 1]
    raise AssertionError(f"Unclosed function body for {function_name}")


class FrontendActionHandlerTests(unittest.TestCase):
    def test_literal_data_actions_have_click_handlers(self) -> None:
        action_locations: dict[str, list[str]] = {}
        for path in ACTION_ATTRIBUTE_PATHS:
            source = path.read_text(encoding="utf-8")
            for match in ACTION_ATTRIBUTE_PATTERN.finditer(source):
                action = match.group(2).strip()
                if not action:
                    continue
                relative_path = path.relative_to(ROOT_DIR).as_posix()
                action_locations.setdefault(action, []).append(
                    f"{relative_path}:{_line_number(source, match.start())}"
                )

        handled_actions = _get_handled_actions()

        missing_actions = {
            action: locations
            for action, locations in sorted(action_locations.items())
            if action not in handled_actions
        }

        self.assertGreaterEqual(len(action_locations), 200)
        self.assertFalse(
            missing_actions,
            "Literal data-action values without handleClick coverage:\n"
            + "\n".join(
                f"- {action}: {', '.join(locations[:4])}"
                for action, locations in missing_actions.items()
            ),
        )

    def test_dynamic_data_action_sites_are_audited(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        dynamic_markers = Counter()
        for line in source.splitlines():
            if 'data-action="${' not in line:
                continue
            marker = line.strip()
            marker = marker[marker.index("data-action=") :]
            if 'data-action="${action.action}"${' in marker:
                marker = 'data-action="${action.action}"${'
            if 'data-action="${escapeHtml(button.action)}"' in marker:
                marker = 'data-action="${escapeHtml(button.action)}"'
            dynamic_markers[marker] += 1

        self.assertEqual(dynamic_markers, DYNAMIC_DATA_ACTION_MARKERS)

    def test_action_config_values_have_click_handlers(self) -> None:
        handled_actions = _get_handled_actions()
        action_locations: dict[str, list[str]] = {}
        for path in ACTION_CONFIG_PATHS:
            source = path.read_text(encoding="utf-8")
            relative_path = path.relative_to(ROOT_DIR).as_posix()
            for match in ACTION_CONFIG_VALUE_PATTERN.finditer(source):
                action = match.group(2)
                if action in NON_CLICK_ACTION_VALUES:
                    continue
                action_locations.setdefault(action, []).append(
                    f"{relative_path}:{_line_number(source, match.start())}"
                )

        missing_actions = {
            action: locations
            for action, locations in sorted(action_locations.items())
            if action not in handled_actions
        }

        self.assertGreaterEqual(len(action_locations), 45)
        self.assertFalse(
            missing_actions,
            "Action config values without handleClick coverage:\n"
            + "\n".join(
                f"- {action}: {', '.join(locations[:4])}"
                for action, locations in missing_actions.items()
            ),
        )

    def test_handle_click_has_runtime_fallback_for_unwired_buttons(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")

        self.assertIn('actionTarget.matches(":disabled")', click_handler)
        self.assertIn('actionTarget.getAttribute("aria-disabled") === "true"', click_handler)
        self.assertLess(
            click_handler.index('actionTarget.matches(":disabled")'),
            click_handler.index("const { action } = actionTarget.dataset;"),
        )
        self.assertIn("function handleMissingProjectAction", source)
        self.assertIn("function handleUnhandledEditorAction", source)
        self.assertIn("handleMissingProjectAction(actionTarget);", click_handler)
        self.assertIn("handleUnhandledEditorAction(action, actionTarget);", click_handler)
        self.assertLess(
            click_handler.rfind('action === "reset-preview-debug-defaults"'),
            click_handler.rfind("handleUnhandledEditorAction(action, actionTarget);"),
        )
        self.assertIn("[Tony Na Engine] Unhandled editor action", source)

    def test_handle_click_ignores_disabled_actions_before_dispatch(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        script = textwrap.dedent(
            f"""
            const calls = [];
            const state = {{ beginnerTutorialOpen: false }};
            const event = {{
              prevented: false,
              preventDefault() {{ this.prevented = true; }},
              target: {{
                closest(selector) {{
                  calls.push({{ type: "closest", selector }});
                  return {{
                    dataset: {{ action: "export-build" }},
                    matches(selector) {{
                      calls.push({{ type: "matches", selector }});
                      return selector === ":disabled";
                    }},
                    getAttribute(name) {{
                      calls.push({{ type: "getAttribute", name }});
                      return null;
                    }},
                  }};
                }},
              }},
            }};
            async function exportBuild() {{ throw new Error("disabled action should not dispatch"); }}
            async function handleClick(event) {click_handler}
            await handleClick(event);
            process.stdout.write(JSON.stringify({{ prevented: event.prevented, calls }}));
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
        self.assertTrue(payload["prevented"])
        self.assertEqual(payload["calls"][0], {"type": "closest", "selector": "[data-action]"})
        self.assertEqual(payload["calls"][1], {"type": "matches", "selector": ":disabled"})

    def test_quick_switch_screen_actions_keep_dataset_screen(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        quick_action_button = _extract_function_source(source, "renderQuickActionButton")

        self.assertIn('action.action === "switch-screen"', quick_action_button)
        self.assertIn('action.dataset?.screen', quick_action_button)
        self.assertIn('data-screen="${escapeHtml(screen)}"', quick_action_button)

    def test_quick_action_button_renders_disabled_state(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        quick_action_button = _extract_function_source(source, "renderQuickActionButton")
        escape_html = _extract_function_source(source, "escapeHtml")
        script = textwrap.dedent(
            f"""
            const editorCommonTools = null;
            function escapeHtml(value) {escape_html}
            function renderQuickActionButton(action, emphasized = false) {quick_action_button}
            const html = renderQuickActionButton({{
              label: "确认 <执行>",
              action: "repair-project-doctor",
              disabled: true,
              title: "先点“预览”再执行",
              dataset: {{ "repair-codes": "entry_scene,scene_order" }},
            }});
            process.stdout.write(JSON.stringify({{ html }}));
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
        html = json.loads(completed.stdout)["html"]
        self.assertIn('data-action="repair-project-doctor"', html)
        self.assertIn('data-repair-codes="entry_scene,scene_order"', html)
        self.assertIn('disabled aria-disabled="true"', html)
        self.assertIn('title="先点“预览”再执行"', html)
        self.assertIn("确认 &lt;执行&gt;", html)

    def test_project_doctor_report_labels_distinguish_preview_from_repair(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        report_labels = _extract_function_source(source, "getProjectDoctorRepairReceiptReportLabels")
        script = textwrap.dedent(
            f"""
            function getProjectDoctorRepairReceiptReportLabels(receipt = {{}}) {report_labels}
            const preview = getProjectDoctorRepairReceiptReportLabels({{ status: "preview", dryRun: true }});
            const repaired = getProjectDoctorRepairReceiptReportLabels({{ status: "repaired" }});
            const unknown = getProjectDoctorRepairReceiptReportLabels({{ status: "unknown" }});
            process.stdout.write(JSON.stringify({{ preview, repaired, unknown }}));
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
        self.assertEqual(payload["preview"]["heading"], "最近一次安全修复预览")
        self.assertEqual(payload["preview"]["timeLabel"], "预览时间")
        self.assertEqual(payload["preview"]["repairVerb"], "将修复")
        self.assertEqual(payload["preview"]["skipVerb"], "将跳过")
        self.assertEqual(payload["repaired"]["heading"], "最近一次安全修复")
        self.assertEqual(payload["repaired"]["timeLabel"], "修复时间")
        self.assertEqual(payload["repaired"]["repairVerb"], "已修复")
        self.assertEqual(payload["unknown"]["heading"], "最近一次未识别修复请求")
        self.assertIn("projectDoctorReceiptLabels", source)
        self.assertIn("receiptLabels.countLabel", source)

    def test_project_doctor_repair_requires_matching_preview(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        parse_codes = _extract_function_source(source, "parseProjectDoctorRepairCodes")
        get_preview_codes = _extract_function_source(source, "getCurrentProjectDoctorPreviewRepairCodes")
        repair_project_doctor = _extract_function_source(source, "repairProjectDoctor")
        script = textwrap.dedent(
            f"""
            const API_REPAIR_PROJECT_DOCTOR = "/api/repair-project-doctor";
            const calls = [];
            const statuses = [];
            const toasts = [];
            const reloads = [];
            const renders = [];
            const state = {{
              data: {{ project: {{ title: "测试项目" }} }},
              projectDoctorRepairReceipt: null,
              lastExportResult: {{ ok: true }},
              currentScreen: "dashboard",
            }};
            function parseProjectDoctorRepairCodes(value) {parse_codes}
            function getCurrentProjectDoctorPreviewRepairCodes() {get_preview_codes}
            function buildProjectDoctorRepairReceipt(result) {{
              return {{
                ...result,
                status: result.dryRun ? "preview" : "repaired",
                requestedCodes: result.requestedCodes ?? result.repairs?.map((item) => item.code) ?? [],
                wouldChange: Boolean(result.wouldChange) || Boolean(result.repairs?.length),
              }};
            }}
            async function postJson(endpoint, payload) {{
              calls.push({{ endpoint, payload }});
              return {{
                changed: !payload.dryRun,
                dryRun: Boolean(payload.dryRun),
                wouldChange: true,
                requestedCodes: payload.repairCodes ?? [],
                repairs: (payload.repairCodes ?? ["entry_scene"]).map((code) => ({{ code }})),
                skipped: [],
              }};
            }}
            function setSaveStatus(message, isError = false) {{ statuses.push({{ message, isError }}); }}
            function showToast(message, tone = "soft") {{ toasts.push({{ message, tone }}); }}
            function showEngineAlert(message) {{ throw new Error(message); }}
            function getCurrentUiState() {{ return {{ selectedSceneId: "scene_01" }}; }}
            async function reloadProjectData(preserved) {{ reloads.push(preserved); }}
            function renderInspectionScreen() {{ throw new Error("inspection render should not run in this test"); }}
            function renderPreviewScreen() {{ renders.push("preview"); }}
            function renderDashboard() {{ renders.push("dashboard"); }}
            async function repairProjectDoctor(repairCodesValue = "", options = {{}}) {repair_project_doctor}

            await repairProjectDoctor("entry_scene");
            const blockedWithoutPreview = {{
              calls: calls.length,
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            state.projectDoctorRepairReceipt = {{
              status: "preview",
              wouldChange: true,
              requestedCodes: ["scene_order"],
            }};
            await repairProjectDoctor("entry_scene");
            const blockedMismatch = {{
              calls: calls.length,
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            state.projectDoctorRepairReceipt = {{
              status: "preview",
              wouldChange: true,
              requestedCodes: ["entry_scene", "scene_order"],
            }};
            await repairProjectDoctor("entry_scene");
            const matchedSingle = calls.at(-1);

            state.projectDoctorRepairReceipt = {{
              status: "preview",
              wouldChange: true,
              requestedCodes: ["entry_scene", "scene_order"],
            }};
            await repairProjectDoctor("");
            const matchedPreviewAll = calls.at(-1);

            state.projectDoctorRepairReceipt = null;
            await repairProjectDoctor("", {{ dryRun: true }});
            const dryRunPreview = calls.at(-1);

            process.stdout.write(JSON.stringify({{
              blockedWithoutPreview,
              blockedMismatch,
              matchedSingle,
              matchedPreviewAll,
              dryRunPreview,
              reloads,
              renders,
              lastReceipt: state.projectDoctorRepairReceipt,
              lastExportResult: state.lastExportResult,
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
        self.assertEqual(payload["blockedWithoutPreview"]["calls"], 0)
        self.assertEqual(payload["blockedWithoutPreview"]["status"]["message"], "请先点“先预览安全修复”，确认后再执行")
        self.assertTrue(payload["blockedWithoutPreview"]["status"]["isError"])
        self.assertEqual(payload["blockedWithoutPreview"]["toast"]["tone"], "error")
        self.assertEqual(payload["blockedMismatch"]["calls"], 0)
        self.assertEqual(payload["blockedMismatch"]["status"]["message"], "项目医生预览已变化，请先重新预览安全修复")
        self.assertEqual(payload["matchedSingle"]["payload"]["repairCodes"], ["entry_scene"])
        self.assertEqual(payload["matchedPreviewAll"]["payload"]["repairCodes"], ["entry_scene", "scene_order"])
        self.assertTrue(payload["dryRunPreview"]["payload"]["dryRun"])
        self.assertNotIn("repairCodes", payload["dryRunPreview"]["payload"])
        self.assertTrue(all(item["preserveProjectDoctorRepairReceipt"] for item in payload["reloads"]))
        self.assertEqual(payload["renders"], ["dashboard", "dashboard", "dashboard"])
        self.assertEqual(payload["lastReceipt"]["status"], "preview")
        self.assertIsNone(payload["lastExportResult"])

    def test_preview_regression_action_refreshes_current_progress_surface(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        regression_block_start = click_handler.index('action === "run-preview-regression"')
        regression_block_end = click_handler.index('action === "export-inspection-report"', regression_block_start)
        regression_block = click_handler[regression_block_start:regression_block_end]

        self.assertIn("state.inspectionRegressionResult = runPreviewRegressionSmokeTest", regression_block)
        self.assertIn('state.currentScreen === "preview"', regression_block)
        self.assertIn("renderPreviewScreen();", regression_block)
        self.assertIn('state.currentScreen === "dashboard"', regression_block)
        self.assertIn("renderDashboard();", regression_block)

    def test_beginner_dashboard_export_step_requires_real_export_record(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        workflow = _extract_function_source(source, "buildBeginnerDashboardWorkflow")
        renderer = _extract_function_source(source, "renderBeginnerDashboardWorkflow")

        self.assertIn("const canPreviewAndExport =", workflow)
        self.assertIn("const hasExportRecord = Boolean(state.lastExportResult);", workflow)
        self.assertIn("const exportMissingAssetCount = Number(state.lastExportResult?.missingAssets ?? 0) || 0;", workflow)
        self.assertIn("const hasCleanExportRecord = hasExportRecord && exportMissingAssetCount <= 0;", workflow)
        self.assertIn("done: hasCleanExportRecord", workflow)
        self.assertIn("已导出，缺 ${exportMissingAssetCount} 个素材", workflow)
        self.assertIn("导出成功后这一步才算完成", workflow)
        self.assertIn("补齐后再导出才更接近可交付", workflow)
        self.assertIn('action: "export-build"', workflow)
        self.assertIn('dataset: { "export-target": "web" }', workflow)
        self.assertIn('action: "focus-asset-gap"', workflow)
        self.assertIn('dataset: { "asset-filter-mode": "urgent_missing" }', workflow)
        self.assertIn('dataset: { screen: "inspection" }', workflow)
        self.assertIn("function getBeginnerWorkflowStepStatusLabel", source)
        self.assertIn("function getBeginnerWorkflowStepToneClass", source)
        self.assertIn("getBeginnerWorkflowStepStatusLabel(step)", renderer)
        self.assertIn("getBeginnerWorkflowStepToneClass(step)", renderer)

    def test_export_build_refreshes_current_progress_surface(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        export_build = _extract_function_source(source, "exportBuild")

        self.assertIn("state.lastExportResult = result;", export_build)
        self.assertIn("renderPreviewScreen();", export_build)
        self.assertIn('state.currentScreen === "dashboard"', export_build)
        self.assertIn("renderDashboard();", export_build)
        self.assertIn('state.currentScreen === "inspection"', export_build)
        self.assertIn("renderInspectionScreen();", export_build)
        self.assertLess(export_build.index("state.lastExportResult = result;"), export_build.index("renderDashboard();"))
        self.assertLess(export_build.index("state.lastExportResult = result;"), export_build.index("renderInspectionScreen();"))


if __name__ == "__main__":
    unittest.main()
