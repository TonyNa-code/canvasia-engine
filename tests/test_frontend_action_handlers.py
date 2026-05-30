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
PLAYER_PATH = ROOT_DIR / "export_player_template" / "player.js"
NATIVE_RUNTIME_PATH = ROOT_DIR / "native_runtime" / "runtime_player.py"
MODULE_PATHS = tuple(sorted((EDITOR_DIR / "modules").glob("*.js")))
ACTION_ATTRIBUTE_PATHS = (INDEX_PATH, APP_PATH, *MODULE_PATHS)
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
    def test_post_json_reports_readable_response_errors(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        fetch_editor_resource = _extract_function_source(source, "fetchEditorResource")
        read_json_response = _extract_function_source(source, "readJsonResponse")
        post_json = _extract_function_source(source, "postJson")
        script = textwrap.dedent(
            f"""
            async function fetchEditorResource(url, options = {{}}, contextLabel = "请求") {fetch_editor_resource}
            async function readJsonResponse(response, options = {{}}) {read_json_response}
            async function postJson(url, payload) {post_json}

            const calls = [];
            globalThis.fetch = async (url, options) => {{
              calls.push({{ url, options }});
              return {{
                ok: false,
                status: 502,
                async text() {{ return "<html>Bad gateway</html>"; }},
              }};
            }};
            let htmlMessage = "";
            try {{
              await postJson("/api/test", {{ hello: "world" }});
            }} catch (error) {{
              htmlMessage = error.message;
            }}

            globalThis.fetch = async () => ({{
              ok: false,
              status: 500,
              async text() {{ return ""; }},
            }});
            let emptyMessage = "";
            try {{
              await postJson("/api/test", {{}});
            }} catch (error) {{
              emptyMessage = error.message;
            }}

            globalThis.fetch = async () => ({{
              ok: false,
              status: 418,
              async text() {{
                return JSON.stringify({{
                  ok: false,
                  error: "茶壶坏了",
                  recovery: {{ mode: "snapshot" }},
                  history: ["safe-point"],
                }});
              }},
            }});
            let jsonError = null;
            try {{
              await postJson("/api/test", {{}});
            }} catch (error) {{
              jsonError = {{ message: error.message, recovery: error.recovery, history: error.history }};
            }}

            globalThis.fetch = async () => ({{
              ok: true,
              status: 200,
              async text() {{ return JSON.stringify({{ ok: true, value: 7 }}); }},
            }});
            const okResult = await postJson("/api/test", {{ ok: true }});

            globalThis.fetch = async () => {{
              throw new TypeError("Failed to fetch");
            }};
            let networkMessage = "";
            try {{
              await postJson("/api/test", {{}});
            }} catch (error) {{
              networkMessage = error.message;
            }}

            console.log(JSON.stringify({{
              htmlMessage,
              emptyMessage,
              jsonError,
              okResult,
              networkMessage,
              firstCall: calls[0],
            }}));
            """
        )
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertIn("无法识别的内容", payload["htmlMessage"])
        self.assertIn("HTTP 502", payload["htmlMessage"])
        self.assertEqual(payload["emptyMessage"], "请求失败，状态码 500")
        self.assertEqual(payload["jsonError"]["message"], "茶壶坏了")
        self.assertEqual(payload["jsonError"]["recovery"], {"mode": "snapshot"})
        self.assertEqual(payload["jsonError"]["history"], ["safe-point"])
        self.assertEqual(payload["okResult"]["value"], 7)
        self.assertIn("无法连接到编辑器后端", payload["networkMessage"])
        self.assertNotIn("Failed to fetch", payload["networkMessage"])
        self.assertEqual(payload["firstCall"]["url"], "/api/test")
        self.assertEqual(payload["firstCall"]["options"]["method"], "POST")

    def test_project_bootstrap_fetches_use_readable_response_errors(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        fetch_editor_resource = _extract_function_source(source, "fetchEditorResource")
        load_project_center = _extract_function_source(source, "loadProjectCenter")
        load_project_data = _extract_function_source(source, "loadProjectData")

        self.assertIn("无法连接到编辑器后端", fetch_editor_resource)
        self.assertIn('fetchEditorResource(API_PROJECT_CENTER, {}, "读取项目列表")', load_project_center)
        self.assertIn('fetchEditorResource(API_PROJECT_DATA, {}, "读取项目数据")', load_project_data)
        self.assertIn('readJsonResponse(response, { contextLabel: "读取项目列表" })', load_project_center)
        self.assertIn('readJsonResponse(response, { contextLabel: "读取项目数据" })', load_project_data)
        self.assertIn("resultObject.error", load_project_center)
        self.assertIn("loadError.recovery = bundle.recovery ?? null", load_project_data)
        self.assertNotIn("response.json()", load_project_center)
        self.assertNotIn("response.json()", load_project_data)

    def test_startup_and_fatal_errors_use_readable_messages(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        index_source = INDEX_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        init_source = _extract_function_source(source, "init")
        startup_message = _extract_function_source(source, "getEditorStartupErrorMessage")
        fatal_project_load = _extract_function_source(source, "showFatalProjectLoadError")
        project_load_message = _extract_function_source(source, "getProjectLoadErrorMessage")
        copy_load_error_message = _extract_function_source(source, "copyCurrentLoadErrorMessage")
        runtime_error_handler = _extract_function_source(source, "handleEditorRuntimeError")

        self.assertIn('data-action="copy-error-message"', index_source)
        self.assertIn('action === "copy-error-message"', click_handler)
        self.assertIn("void copyCurrentLoadErrorMessage();", click_handler)
        self.assertIn("getEditorStartupErrorMessage(error)", init_source)
        self.assertNotIn("refs.errorMessage.textContent = error.message", init_source)
        self.assertIn("编辑器没有载入成功", startup_message)
        self.assertIn("重新运行启动脚本后刷新页面", startup_message)
        self.assertIn("getErrorDetailMessage(", startup_message)

        self.assertIn("getProjectLoadErrorMessage(error)", fatal_project_load)
        self.assertIn("项目没有载入成功", project_load_message)
        self.assertIn("自动快照", project_load_message)
        self.assertNotIn("error?.message", fatal_project_load)

        self.assertIn("refs.errorMessage?.textContent", copy_load_error_message)
        self.assertIn("copyTextToClipboard(message)", copy_load_error_message)
        self.assertIn("错误信息已复制，可直接粘贴到反馈里", copy_load_error_message)
        self.assertIn("当前没有可复制的错误信息", copy_load_error_message)
        self.assertIn("复制失败，可以手动选中错误信息", copy_load_error_message)

        self.assertIn('getErrorDetailMessage(error, "未知错误")', runtime_error_handler)
        self.assertIn("详细错误已记录在控制台", runtime_error_handler)
        self.assertNotIn("error.message", runtime_error_handler)

    def test_project_center_failures_use_copyable_detail_dialogs(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        handle_project_load_failure = _extract_function_source(source, "handleProjectLoadFailure")
        show_copyable_operation_failure = _extract_function_source(source, "showCopyableOperationFailure")
        show_project_center_failure = _extract_function_source(source, "showProjectCenterFailure")

        self.assertIn("getErrorDetailMessage(error)", show_copyable_operation_failure)
        self.assertIn("getErrorSummaryLine(error, title)", show_copyable_operation_failure)
        self.assertIn("copyable: true", show_copyable_operation_failure)
        self.assertIn("`${title}，已列出原因`", show_copyable_operation_failure)
        self.assertIn("await showCopyableOperationFailure(error, title, detailPrefix)", show_project_center_failure)
        self.assertIn("error?.recovery", handle_project_load_failure)
        self.assertNotIn("fallbackMessage", handle_project_load_failure)
        self.assertNotIn("setSaveStatus(fallbackMessage", handle_project_load_failure)

        expected_calls = [
            'await showProjectCenterFailure(error, "刷新项目列表失败", "项目列表没有刷新成功")',
            'await showProjectCenterFailure(error, "新建空白项目失败", "空白项目没有创建成功")',
            'await showProjectCenterFailure(error, "打开项目失败", "项目没有打开成功")',
            'await showProjectCenterFailure(error, "修改项目名失败", "项目名没有修改成功")',
            'await showProjectCenterFailure(error, "复制项目失败", "项目没有复制成功")',
            'await showProjectCenterFailure(error, "删除项目失败", `项目「${project.title}」没有删除成功`)',
        ]
        for expected_call in expected_calls:
            self.assertIn(expected_call, handle_click)

        old_alerts = [
            "刷新项目列表失败：${error.message}",
            "新建空白项目失败：${error.message}",
            "打开项目失败：${error.message}",
            "修改项目名失败：${error.message}",
            "复制项目失败：${error.message}",
            "删除项目失败：${error.message}",
        ]
        for old_alert in old_alerts:
            self.assertNotIn(old_alert, handle_click)

    def test_story_structure_failures_use_copyable_detail_dialogs(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        show_editor_operation_failure = _extract_function_source(source, "showEditorOperationFailure")
        operation_sources = "\n".join(
            _extract_function_source(source, function_name)
            for function_name in (
                "createScene",
                "duplicateScene",
                "createChapter",
                "createStarterKit",
                "createHistoryCheckpoint",
                "renameProjectHistorySnapshot",
                "acknowledgeProjectRecoveryNotice",
                "applyProjectHistoryAction",
                "duplicateChapter",
                "moveScene",
                "renameScene",
                "renameChapter",
                "moveChapter",
                "deleteScene",
                "deleteChapter",
            )
        )

        self.assertIn("await showCopyableOperationFailure(error, title, detailPrefix)", show_editor_operation_failure)
        expected_calls = [
            'await showEditorOperationFailure(error, "新建场景失败", "场景没有创建成功")',
            'await showEditorOperationFailure(error, "复制场景失败", "场景没有复制成功")',
            'await showEditorOperationFailure(error, "新建章节失败", "章节没有创建成功")',
            'await showEditorOperationFailure(error, "生成起步骨架失败", "起步骨架没有生成成功")',
            'await showEditorOperationFailure(error, "保存检查点失败", "检查点没有保存成功")',
            'await showEditorOperationFailure(error, "更新检查点备注失败", "检查点备注没有更新成功")',
            'await showEditorOperationFailure(error, "收起异常提醒失败", "异常退出提醒没有收起成功")',
            "await showEditorOperationFailure(error, `${actionLabel}失败`, `${actionLabel}没有成功`)",
            'await showEditorOperationFailure(error, "复制章节失败", "章节没有复制成功")',
            'await showEditorOperationFailure(error, "调整场景顺序失败", "场景顺序没有调整成功")',
            'await showEditorOperationFailure(error, "修改场景名失败", "场景名没有修改成功")',
            'await showEditorOperationFailure(error, "修改章节名失败", "章节名没有修改成功")',
            'await showEditorOperationFailure(error, "调整章节顺序失败", "章节顺序没有调整成功")',
            'await showEditorOperationFailure(error, "删除场景失败", `场景「${scene.name}」没有删除成功`)',
            'await showEditorOperationFailure(error, "删除章节失败", `章节「${chapter.name}」没有删除成功`)',
        ]
        for expected_call in expected_calls:
            self.assertIn(expected_call, operation_sources)

        old_alerts = [
            "新建场景没有成功：${error.message}",
            "复制场景没有成功：${error.message}",
            "新建章节没有成功：${error.message}",
            "生成起步骨架没有成功：${error.message}",
            "保存检查点没有成功：${error.message}",
            "更新检查点备注没有成功：${error.message}",
            "收起提醒没有成功：${error.message}",
            "${actionLabel}没有成功：${error.message}",
            "复制章节没有成功：${error.message}",
            "调整场景顺序没有成功：${error.message}",
            "修改场景名没有成功：${error.message}",
            "修改章节名没有成功：${error.message}",
            "调整章节顺序没有成功：${error.message}",
            "删除场景没有成功：${error.message}",
            "删除章节没有成功：${error.message}",
        ]
        for old_alert in old_alerts:
            self.assertNotIn(old_alert, operation_sources)

    def test_foundation_operation_failures_use_copyable_detail_dialogs(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        operation_sources = "\n".join(
            _extract_function_source(source, function_name)
            for function_name in (
                "createVoicePlaceholderForLine",
                "createVoicePlaceholdersForEntries",
                "matchVoiceFilesToPlaceholders",
                "bindVoiceMatchReviewFile",
                "saveSelectedAssetMetadata",
                "toggleAssetFavorite",
                "saveCharacterPresentation",
                "applyBulkAssetTags",
                "applyPresetTag",
                "repairProjectDoctor",
                "generateCreativeAssistant",
                "saveProjectResolution",
                "saveProjectEditorMode",
                "saveProjectReleaseVersion",
                "saveProjectFormalSaveSlotCount",
                "saveProjectLocalizationSettings",
                "addProjectVariable",
                "saveProjectVariable",
                "duplicateProjectVariable",
                "deleteProjectVariable",
                "deleteUnusedProjectVariables",
                "repairProjectVariableRanges",
                "saveProjectDialogBoxConfig",
                "saveProjectGameUiConfig",
                "generateOpenAiAsset",
                "persistScene",
                "saveParticleCustomPreset",
                "deleteParticleCustomPreset",
                "ensureStarterVariables",
            )
        )

        expected_calls = [
            'await showEditorOperationFailure(error, "生成语音条目失败", "语音条目没有生成成功")',
            'await showEditorOperationFailure(error, "批量生成语音条目失败", "语音条目没有批量生成成功")',
            'await showEditorOperationFailure(error, "批量匹配语音文件失败", "语音文件没有批量匹配成功")',
            'await showEditorOperationFailure(error, "手动绑定语音文件失败", "语音文件没有手动绑定成功")',
            'await showEditorOperationFailure(error, "保存素材信息失败", "素材信息没有保存成功")',
            'await showEditorOperationFailure(error, "切换收藏失败", "素材收藏状态没有切换成功")',
            'await showEditorOperationFailure(error, "保存角色表现失败", "角色表现没有保存成功")',
            'await showEditorOperationFailure(error, "批量改标签失败", "素材标签没有批量更新成功")',
            'await showEditorOperationFailure(error, "添加预设标签失败", "预设标签没有添加成功")',
            "await showEditorOperationFailure(error, `${actionLabel}失败`, `${actionLabel}没有执行成功`)",
            'await showEditorOperationFailure(error, "智能助手生成失败", "智能助手没有生成成功")',
            'await showEditorOperationFailure(error, "切换分辨率失败", "项目分辨率没有切换成功")',
            'await showEditorOperationFailure(error, "切换编辑模式失败", "编辑模式没有切换成功")',
            'await showEditorOperationFailure(error, "保存发布版本失败", "发布版本没有保存成功")',
            'await showEditorOperationFailure(error, "保存正式存档位失败", "正式存档位没有保存成功")',
            'await showEditorOperationFailure(error, "保存多语言设置失败", "多语言设置没有保存成功")',
            'await showEditorOperationFailure(error, "新增变量失败", "变量没有新增成功")',
            'await showEditorOperationFailure(error, "保存变量失败", "变量没有保存成功")',
            'await showEditorOperationFailure(error, "复制变量失败", "变量没有复制成功")',
            'await showEditorOperationFailure(error, "删除变量失败", `变量「${variable.name}」没有删除成功`)',
            'await showEditorOperationFailure(error, "清理未引用变量失败", "未引用变量没有清理成功")',
            'await showEditorOperationFailure(error, "整理变量范围失败", "变量范围没有整理成功")',
            'await showEditorOperationFailure(error, "保存文本框样式失败", "项目文本框样式没有保存成功")',
            'await showEditorOperationFailure(error, "保存成品 UI 皮肤失败", "成品 UI 皮肤没有保存成功")',
            'await showEditorOperationFailure(error, "AI 生成素材失败", "素材没有生成成功")',
            'await showEditorOperationFailure(error, "保存失败", "当前内容没有保存成功")',
            'await showEditorOperationFailure(error, "保存粒子预设失败", "粒子预设没有保存成功")',
            'await showEditorOperationFailure(error, "删除粒子预设失败", `粒子预设「${preset.name}」没有删除成功`)',
            'await showEditorOperationFailure(error, "创建基础变量库失败", "基础变量库没有创建成功")',
        ]
        for expected_call in expected_calls:
            self.assertIn(expected_call, operation_sources)

        self.assertIn("state.creativeAssistantError = getErrorDetailMessage(", operation_sources)
        self.assertIn("请检查 API Key、模型、服务地址或网络连接", operation_sources)
        self.assertIn("state.openAiAssetError = getErrorDetailMessage(", operation_sources)
        self.assertIn("请检查 API Key、模型、额度、服务地址或网络连接", operation_sources)
        self.assertNotIn("state.creativeAssistantError = error.message", operation_sources)
        self.assertNotIn("state.openAiAssetError = error.message", operation_sources)
        self.assertNotRegex(source, r"showEngineAlert\(`[^`]*\$\{error\.message\}")

    def test_batch_file_read_reports_all_failed_local_files(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        read_file = _extract_function_source(source, "readFileAsBase64Payload")
        read_files = _extract_function_source(source, "readFilesAsBase64Payloads")
        read_text = _extract_function_source(source, "readFileAsText")
        parse_json_import = _extract_function_source(source, "parseJsonImportText")
        script = textwrap.dedent(
            f"""
            class MockFileReader {{
              readAsDataURL(file) {{
                if (file.fail) {{
                  this.onerror?.(new Error("simulated read error"));
                  return;
                }}
                if (file.abort) {{
                  this.onabort?.();
                  return;
                }}
                this.result = `data:${{file.type || ""}};base64,${{file.payload || ""}}`;
                this.onload?.();
              }}
              readAsText(file) {{
                if (file.fail) {{
                  this.onerror?.(new Error("simulated read error"));
                  return;
                }}
                if (file.abort) {{
                  this.onabort?.();
                  return;
                }}
                this.result = file.text ?? "";
                this.onload?.();
              }}
            }}
            globalThis.FileReader = MockFileReader;

            async function readFileAsBase64Payload(file) {read_file}
            async function readFilesAsBase64Payloads(files, options = {{}}) {read_files}
            async function readFileAsText(file) {read_text}
            function parseJsonImportText(rawText, contextLabel = "导入文件") {parse_json_import}

            const successPayload = await readFilesAsBase64Payloads([
              {{ name: "ok.png", type: "image/png", payload: "ZmFrZQ==" }},
            ], {{ actionLabel: "导入" }});
            const textPayload = await readFileAsText({{ name: "ideas.json", text: "{{\\"records\\":[]}}" }});
            const parsedPayload = parseJsonImportText(textPayload, "助手灵感包");

            let batchMessage = "";
            try {{
              await readFilesAsBase64Payloads([
                {{ name: "ok.png", type: "image/png", payload: "ZmFrZQ==" }},
                {{ name: "lost.mp3", fail: true }},
                {{ name: "busy.wav", abort: true }},
              ], {{ actionLabel: "导入" }});
            }} catch (error) {{
              batchMessage = error.message;
            }}

            let missingFileMessage = "";
            try {{
              await readFileAsBase64Payload(null);
            }} catch (error) {{
              missingFileMessage = error.message;
            }}

            let textReadMessage = "";
            try {{
              await readFileAsText({{ name: "presets.json", abort: true }});
            }} catch (error) {{
              textReadMessage = error.message;
            }}

            let jsonMessage = "";
            try {{
              parseJsonImportText("not json", "粒子预设包");
            }} catch (error) {{
              jsonMessage = error.message;
            }}

            console.log(JSON.stringify({{
              successPayload,
              parsedPayload,
              batchMessage,
              missingFileMessage,
              textReadMessage,
              jsonMessage,
            }}));
            """
        )
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["successPayload"], [{"name": "ok.png", "dataBase64": "ZmFrZQ=="}])
        self.assertEqual(payload["parsedPayload"], {"records": []})
        self.assertIn("导入失败", payload["batchMessage"])
        self.assertIn("lost.mp3", payload["batchMessage"])
        self.assertIn("busy.wav", payload["batchMessage"])
        self.assertIn("重新选择", payload["batchMessage"])
        self.assertEqual(payload["missingFileMessage"], "没有收到要读取的文件。")
        self.assertIn("presets.json", payload["textReadMessage"])
        self.assertIn("没有读到这个文件", payload["textReadMessage"])
        self.assertIn("粒子预设包不是可识别的 JSON 文件", payload["jsonMessage"])
        self.assertIn("Canvasia 导出的 .json 文件", payload["jsonMessage"])

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
        dynamic_action_paths = (
            APP_PATH,
            EDITOR_DIR / "modules" / "editor_common.js",
            EDITOR_DIR / "modules" / "project_center.js",
        )
        source = "\n".join(path.read_text(encoding="utf-8") for path in dynamic_action_paths)
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
        self.assertIn("function handleEditorRuntimeError", source)
        self.assertIn("handleMissingProjectAction(actionTarget);", click_handler)
        self.assertIn("handleUnhandledEditorAction(action, actionTarget);", click_handler)
        self.assertLess(
            click_handler.rfind('action === "reset-preview-debug-defaults"'),
            click_handler.rfind("handleUnhandledEditorAction(action, actionTarget);"),
        )
        self.assertIn("[Canvasia Engine] Unhandled editor action", source)
        self.assertIn("handleClick(event).catch", source)
        self.assertIn('handleEditorRuntimeError(error, "点击操作")', source)
        self.assertIn("installEditorRuntimeErrorBoundary();", source)
        self.assertIn('window.addEventListener("unhandledrejection"', source)
        self.assertIn("lastEditorRuntimeErrorKey", source)
        self.assertIn("[Canvasia Engine] Editor runtime error", source)

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

    def test_runtime_error_handler_dedupes_user_notifications(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        get_error_detail_message = _extract_function_source(source, "getErrorDetailMessage")
        runtime_error_handler = _extract_function_source(source, "handleEditorRuntimeError")
        script = textwrap.dedent(
            f"""
            let lastEditorRuntimeErrorKey = "";
            let lastEditorRuntimeErrorAt = 0;
            let now = 1000;
            Date.now = () => now;
            const calls = [];
            function setSaveStatus(message, isError = false) {{
              calls.push({{ type: "status", message, isError }});
            }}
            function showToast(message, tone = "soft") {{
              calls.push({{ type: "toast", message, tone }});
            }}
            console.error = (...args) => {{
              calls.push({{
                type: "console",
                label: String(args[0]),
                message: String(args[1]?.message ?? args[1] ?? ""),
              }});
            }};
            function getErrorDetailMessage(error, fallbackMessage = "请求没有成功，请稍后再试一次。") {get_error_detail_message}
            function handleEditorRuntimeError(error, context = "操作") {runtime_error_handler}
            handleEditorRuntimeError(new Error("按钮爆了"), "点击操作");
            handleEditorRuntimeError(new Error("按钮爆了"), "点击操作");
            now = 3001;
            handleEditorRuntimeError(new Error("按钮爆了"), "点击操作");
            process.stdout.write(JSON.stringify({{ calls }}));
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
        calls = json.loads(completed.stdout)["calls"]
        status_calls = [call for call in calls if call["type"] == "status"]
        toast_calls = [call for call in calls if call["type"] == "toast"]
        console_calls = [call for call in calls if call["type"] == "console"]

        self.assertEqual(len(status_calls), 2)
        self.assertEqual(len(toast_calls), 2)
        self.assertEqual(len(console_calls), 3)
        self.assertEqual(status_calls[0]["message"], "点击操作没有成功，详细错误已记录在控制台")
        self.assertTrue(status_calls[0]["isError"])
        self.assertEqual(toast_calls[0], {"type": "toast", "message": "点击操作没有成功", "tone": "error"})

    def test_quick_switch_screen_actions_keep_dataset_screen(self) -> None:
        editor_common_source = (EDITOR_DIR / "modules" / "editor_common.js").read_text(encoding="utf-8")
        quick_action_button = _extract_function_source(editor_common_source, "renderQuickActionButton")

        self.assertIn('action.action === "switch-screen"', quick_action_button)
        self.assertIn('action.dataset?.screen', quick_action_button)
        self.assertIn('data-screen="${escapeHtml(screen)}"', quick_action_button)

    def test_preview_thumbnail_block_label_helper_is_defined(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        preview_thumbnail = _extract_function_source(source, "buildPreviewThumbnailDataUrl")
        get_block_label = _extract_function_source(source, "getBlockLabel")

        self.assertIn("BLOCK_LABELS[type]", get_block_label)
        self.assertIn("getBlockLabel(snapshot.blockType)", preview_thumbnail)

    def test_quick_action_button_renders_disabled_state(self) -> None:
        editor_common_path = EDITOR_DIR / "modules" / "editor_common.js"
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const moduleContext = {{ window: {{}} }};
            moduleContext.globalThis = moduleContext;
            vm.createContext(moduleContext);
            vm.runInContext(fs.readFileSync({json.dumps(str(editor_common_path))}, "utf8"), moduleContext);
            const tools = moduleContext.window.CanvasiaEditorCommon;
            const html = tools.renderQuickActionButton({{
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

    def test_exported_runtimes_honor_bgm_fade_controls(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        story_editor_source = (EDITOR_DIR / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        music_editor = _extract_function_source(app_source, "renderMusicPlayEditor")
        music_editor_template = _extract_function_source(story_editor_source, "renderMusicPlayEditor")
        music_options = _extract_function_source(app_source, "renderMusicRangeEndBlockOptions")
        music_effective_end = _extract_function_source(app_source, "getMusicRangeEffectiveEndBlockId")
        music_label = _extract_function_source(app_source, "getMusicRangeBlockLabel")
        music_summary = _extract_function_source(app_source, "getMusicRangeSummaryFromValues")
        music_timeline = _extract_function_source(app_source, "getMusicRangeTimelineFromValues")
        music_preview = _extract_function_source(app_source, "updateMusicRangePreviewFromControls")
        handle_change = _extract_function_source(app_source, "handleChange")
        collect_edited_block = _extract_function_source(app_source, "collectEditedBlock")
        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        sync_audio = _extract_function_source(player_source, "syncAudio")
        apply_block = _extract_function_source(player_source, "applyBlockToPreviewState")
        fade_audio = _extract_function_source(player_source, "fadeAudioVolume")
        stop_music = _extract_function_source(player_source, "stopMusic")

        self.assertIn("storyBlockEditorTools.renderMusicPlayEditor", music_editor)
        self.assertIn("editorMusicEndMode", music_editor_template)
        self.assertIn("editorMusicEndBlockId", music_editor_template)
        self.assertIn("editorMusicVolume", music_editor_template)
        self.assertIn("editorMusicRangeFadeOutMs", music_editor_template)
        self.assertIn("music-range-preview", music_editor_template)
        self.assertIn("music-range-timeline", music_editor_template)
        self.assertIn("data-music-range-start", music_editor_template)
        self.assertIn("data-music-range-count", music_editor_template)
        self.assertIn("data-has-range-candidates", music_editor_template)
        self.assertIn("getMusicRangeSummary(block)", music_editor_template)
        self.assertIn("getMusicRangeTimeline(block)", music_editor_template)
        self.assertIn("getMusicRangeSummary", music_editor)
        self.assertIn("getMusicRangeTimeline", music_editor)
        self.assertIn("candidates[0]?.id", music_effective_end)
        self.assertIn("getMusicRangeEffectiveEndBlockId(block)", music_options)
        self.assertIn("sceneIndex >= 0 ? sceneIndex + 1 : index + 1", music_label)
        self.assertIn("第 ${displayIndex} 张", music_label)
        self.assertIn('safeEndMode === "scene_end"', music_summary)
        self.assertIn('safeEndMode === "after_block"', music_summary)
        self.assertIn("options.hasRangeCandidates === false", music_summary)
        self.assertIn("getSelectedScene()", music_summary)
        self.assertIn("options.currentBlockId", music_summary)
        self.assertIn("spanCount", music_summary)
        self.assertIn("共覆盖 ${spanCount} 张卡片", music_summary)
        self.assertIn("getMusicRangeTimelineFromValues", app_source)
        self.assertIn("modeLabel: \"指定结束卡\"", music_timeline)
        self.assertIn("countLabel: `覆盖 ${spanCount} 张`", music_timeline)
        self.assertIn("selectedEndBlockId", music_preview)
        self.assertIn("timelineStart", music_preview)
        self.assertIn('endBlockSelect.querySelector("option[value]")', music_preview)
        self.assertIn("endBlockSelect.disabled = endMode !== \"after_block\" || !hasRangeCandidates", music_preview)
        self.assertIn("getMusicRangeSummaryFromValues(endMode, selectedEndBlockId, {", music_preview)
        self.assertIn("getMusicRangeTimelineFromValues(endMode, selectedEndBlockId, {", music_preview)
        self.assertIn("currentBlockId: state.selectedBlockId", music_preview)
        self.assertIn('target.id === "editorMusicEndMode" || target.id === "editorMusicEndBlockId"', handle_change)
        self.assertIn("updateMusicRangePreviewFromControls()", handle_change)
        self.assertIn("endMode", collect_edited_block)
        self.assertIn("endBlockId", collect_edited_block)
        self.assertIn("editorMusicVolume", collect_edited_block)
        self.assertIn("getSafeVolumePercent", collect_edited_block)
        self.assertIn("snapshot.block?.fadeInMs", sync_audio)
        self.assertIn("getRuntimeMusicTargetVolume(snapshot)", sync_audio)
        self.assertIn("snapshot.visualState?.musicFadeOutMs", sync_audio)
        self.assertIn("snapshot.visualState?.musicPreviousFadeOutMs", sync_audio)
        self.assertIn("musicVolume = getSafeVolumePercent(block.volume, 100)", apply_block)
        self.assertIn("getMusicScopeFromBlock(block, sceneId)", apply_block)
        self.assertIn("applyMusicScopeBeforeBlock", player_source)
        self.assertIn("window.requestAnimationFrame", fade_audio)
        self.assertIn("fadeOutPreviousMusic(fadeOutMs)", stop_music)

        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")
        self.assertIn("def get_safe_audio_fade_ms", native_source)
        self.assertIn("def get_safe_volume_percent", native_source)
        self.assertIn("def get_music_scope_from_block", native_source)
        self.assertIn("self.current_bgm_scope = get_music_scope_from_block(block, self.current_scene_id)", native_source)
        self.assertIn("def apply_bgm_scope_before_block", native_source)
        self.assertIn('fade_in_ms=get_safe_audio_fade_ms(block.get("fadeInMs"), 600)', native_source)
        self.assertIn('volume_percent=block.get("volume")', native_source)
        self.assertIn("def get_effective_bgm_volume", native_source)
        self.assertIn('self.stop_bgm(fade_out_ms=get_safe_audio_fade_ms(block.get("fadeOutMs"), 600))', native_source)
        self.assertIn("self.pygame.mixer.music.fadeout(safe_fade_out_ms)", native_source)

    def test_sfx_card_volume_reaches_preview_export_and_native_runtime(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        story_editor_source = (EDITOR_DIR / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")

        sfx_editor_template = _extract_function_source(story_editor_source, "renderSfxPlayEditor")
        collect_edited_block = _extract_function_source(app_source, "collectEditedBlock")
        play_preview_sfx = _extract_function_source(app_source, "playPreviewOneShotAudio")
        sync_preview_sfx = _extract_function_source(app_source, "syncPreviewOneShotAudio")
        sync_runtime_sfx = _extract_function_source(player_source, "syncOneShotAudio")
        update_runtime_audio = _extract_function_source(player_source, "updateRuntimeAudioVolumes")

        self.assertIn("editorSfxVolume", sfx_editor_template)
        self.assertIn("getSafeVolumePercent(document.getElementById(\"editorSfxVolume\")?.value, 100)", collect_edited_block)
        self.assertIn("_canvasiaSfxVolumePercent", play_preview_sfx)
        self.assertIn("playPreviewOneShotAudio(previewUrl, snapshot.block?.volume)", sync_preview_sfx)
        self.assertIn("getRuntimeSfxTargetVolume", sync_runtime_sfx)
        self.assertIn("_canvasiaSfxVolumePercent", sync_runtime_sfx)
        self.assertIn("getRuntimeSfxTargetVolume(audio._canvasiaSfxVolumePercent)", update_runtime_audio)
        self.assertIn('self.play_sfx(block.get("assetId"), volume_percent=block.get("volume"))', native_source)
        self.assertIn("def play_sfx(self, asset_id: str | None, volume_percent: object | None = None)", native_source)

    def test_screen_filter_color_grade_controls_reach_exported_runtimes(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        story_editor_source = (EDITOR_DIR / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        filter_editor = _extract_function_source(app_source, "renderScreenFilterEditor")
        filter_editor_template = _extract_function_source(story_editor_source, "renderScreenFilterEditor")
        collect_edited_block = _extract_function_source(app_source, "collectEditedBlock")
        filter_layer = _extract_function_source(app_source, "renderStageFilterLayer")

        self.assertIn("storyBlockEditorTools.renderScreenFilterEditor", filter_editor)
        self.assertIn("editorColorGradeBrightness", filter_editor_template)
        self.assertIn("editorColorGradeContrast", filter_editor_template)
        self.assertIn("editorColorGradeSaturation", filter_editor_template)
        self.assertIn("editorColorGradeHue", filter_editor_template)
        self.assertIn("editorColorGradeTemperature", filter_editor_template)
        self.assertIn("editorColorGradeVignette", filter_editor_template)
        self.assertIn("grade: readScreenColorGradeControls()", collect_edited_block)
        self.assertIn("--filter-vignette-opacity", filter_layer)
        self.assertIn("getScreenColorGradeSummary(block.grade)", app_source)

        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        screen_css = _extract_function_source(player_source, "getScreenFilterCss")
        apply_block = _extract_function_source(player_source, "applyBlockToPreviewState")
        presentation = _extract_function_source(player_source, "applyStageWorldPresentation")

        self.assertIn("getScreenColorGradeCss(screenFilter.grade)", screen_css)
        self.assertIn("grade: getSafeScreenColorGrade(block.grade)", apply_block)
        self.assertIn("getScreenFilterVignette(visualState.screenFilter)", presentation)
        self.assertIn("--filter-vignette-opacity", (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8"))

        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")
        self.assertIn("SCREEN_COLOR_GRADE_DEFAULTS", native_source)
        self.assertIn("def get_safe_screen_color_grade", native_source)
        self.assertIn('"grade": get_safe_screen_color_grade(block.get("grade"))', native_source)
        self.assertIn("temperature = int(grade.get(\"temperature\") or 0)", native_source)
        self.assertIn("vignette = int(grade.get(\"vignette\") or 0)", native_source)

    def test_project_doctor_report_labels_distinguish_preview_from_repair(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        report_labels = _extract_function_source(source, "getProjectDoctorRepairReceiptReportLabels")
        get_code_label = _extract_function_source(source, "getProjectDoctorRepairCodeLabel")
        get_requested_codes = _extract_function_source(source, "getProjectDoctorRepairReceiptRequestedCodes")
        format_scope = _extract_function_source(source, "formatProjectDoctorRepairReceiptScope")
        build_receipt_file_name = _extract_function_source(source, "buildProjectDoctorRepairReceiptFileName")
        get_write_status = _extract_function_source(source, "getProjectDoctorRepairReceiptWriteStatus")
        format_receipt_id_stamp = _extract_function_source(source, "formatProjectDoctorRepairReceiptIdStamp")
        get_receipt_id = _extract_function_source(source, "getProjectDoctorRepairReceiptId")
        normalize_receipt_id = _extract_function_source(source, "normalizeProjectDoctorRepairReceiptId")
        get_display_id = _extract_function_source(source, "getProjectDoctorRepairReceiptDisplayId")
        with_receipt_id = _extract_function_source(source, "withProjectDoctorRepairReceiptId")
        compact_receipt_text = _extract_function_source(source, "compactProjectDoctorRepairReceiptReportText")
        format_receipt_item = _extract_function_source(source, "formatProjectDoctorRepairReceiptReportItem")
        build_receipt_items = _extract_function_source(source, "buildProjectDoctorRepairReceiptReportItems")
        build_receipt_summary = _extract_function_source(source, "buildProjectDoctorRepairReceiptReportSummary")
        build_receipt_markdown = _extract_function_source(source, "buildProjectDoctorRepairReceiptMarkdownContent")
        build_receipt_clipboard = _extract_function_source(source, "buildProjectDoctorRepairReceiptClipboardSummary")
        script = textwrap.dedent(
            f"""
            const state = {{
              data: {{ project: {{ title: "Project: Demo" }} }},
              projectDoctorRepairReceipt: null,
            }};
            function sanitizeFileName(value) {{
              return String(value ?? "")
                .trim()
                .replace(/[\\\\/:*?"<>|]/g, "_")
                .replace(/\\s+/g, "_")
                .replace(/_+/g, "_")
                .replace(/^_+|_+$/g, "");
            }}
            function formatDate(value) {{ return `日期:${{String(value)}}`; }}
            function escapeMarkdownTableCell(value) {{
              return String(value ?? "")
                .replace(/\\|/g, "\\\\|")
                .replace(/\\r?\\n/g, "<br />")
                .trim();
            }}
            function buildMarkdownTable(headers, rows) {{
              if (!rows.length) {{ return ""; }}
              return [
                `| ${{headers.map(escapeMarkdownTableCell).join(" | ")}} |`,
                `| ${{headers.map(() => "---").join(" | ")}} |`,
                ...rows.map((row) => `| ${{row.map(escapeMarkdownTableCell).join(" | ")}} |`),
              ].join("\\n");
            }}
            function buildProjectDoctorRepairNextActions() {{
              return [
                {{ label: "重新巡检确认", action: "run-project-inspection" }},
                {{ label: "导出巡检报告", action: "export-inspection-report" }},
              ];
            }}
            function getProjectDoctorRepairCodeLabel(code) {get_code_label}
            function getProjectDoctorRepairReceiptRequestedCodes(receipt = {{}}) {get_requested_codes}
            function formatProjectDoctorRepairReceiptScope(receipt = {{}}) {format_scope}
            function buildProjectDoctorRepairReceiptFileName(receipt = state.projectDoctorRepairReceipt) {build_receipt_file_name}
            function getProjectDoctorRepairReceiptWriteStatus(receipt = {{}}) {get_write_status}
            function formatProjectDoctorRepairReceiptIdStamp(value) {format_receipt_id_stamp}
            function getProjectDoctorRepairReceiptId(receipt = {{}}) {get_receipt_id}
            function normalizeProjectDoctorRepairReceiptId(value) {normalize_receipt_id}
            function getProjectDoctorRepairReceiptDisplayId(receipt = {{}}) {get_display_id}
            function withProjectDoctorRepairReceiptId(receipt = null) {with_receipt_id}
            function getProjectDoctorRepairReceiptReportLabels(receipt = {{}}) {report_labels}
            function compactProjectDoctorRepairReceiptReportText(value, fallback = "", maxLength = 140) {compact_receipt_text}
            function formatProjectDoctorRepairReceiptReportItem(item = {{}}, verb = "已处理") {format_receipt_item}
            function buildProjectDoctorRepairReceiptReportItems(receipt = {{}}, labels = getProjectDoctorRepairReceiptReportLabels(receipt)) {build_receipt_items}
            function buildProjectDoctorRepairReceiptReportSummary(receipt = null) {build_receipt_summary}
            function buildProjectDoctorRepairReceiptMarkdownContent(receipt = state.projectDoctorRepairReceipt) {build_receipt_markdown}
            function buildProjectDoctorRepairReceiptClipboardSummary(receipt = state.projectDoctorRepairReceipt) {build_receipt_clipboard}
            const preview = getProjectDoctorRepairReceiptReportLabels({{ status: "preview", dryRun: true }});
            const repaired = getProjectDoctorRepairReceiptReportLabels({{ status: "repaired" }});
            const unknown = getProjectDoctorRepairReceiptReportLabels({{ status: "unknown" }});
            const compacted = compactProjectDoctorRepairReceiptReportText("  第一行\\n\\n第二行   第三行  ", "fallback", 20);
            const truncated = compactProjectDoctorRepairReceiptReportText("1234567890", "fallback", 6);
            const fallback = compactProjectDoctorRepairReceiptReportText("   ", "项目医生记录", 20);
            const previewItems = buildProjectDoctorRepairReceiptReportItems({{
              status: "preview",
              dryRun: true,
              repairs: [
                {{ title: "将入口改成第一幕", detail: "入口场景会从 ghost 改为 scene_01。" }},
                {{ title: "将场景补回排序", detail: "第一章会补回 2 个场景。" }},
              ],
              skipped: [
                {{ title: "章节顺序无需处理", detail: "章节排序已完整。" }},
              ],
            }}, preview);
            const manyItems = buildProjectDoctorRepairReceiptReportItems({{
              status: "repaired",
              repairs: Array.from({{ length: 6 }}, (_, index) => ({{ title: `修复 ${{index + 1}}` }})),
              skipped: Array.from({{ length: 6 }}, (_, index) => ({{ title: `跳过 ${{index + 1}}` }})),
            }}, repaired);
            const multilineItem = formatProjectDoctorRepairReceiptReportItem({{
              title: "  多行\\n标题  ",
              detail: "  多行\\n细节   会压成一行  ",
            }}, "将修复");
            const summary = buildProjectDoctorRepairReceiptReportSummary({{
              status: "preview",
              dryRun: true,
              generatedAt: "2026-05-09T18:54:14+08:00",
              title: "  项目医生\\n预览到 2 项可安全修复  ",
              repairCount: 2,
              skippedCount: 1,
              requestedCodes: ["entry_scene", "scene_order"],
              repairs: [{{ title: "将入口改成第一幕", detail: "入口场景会从 ghost 改为 scene_01。" }}],
              skipped: [{{ title: "章节顺序无需处理" }}],
            }});
            const receiptForExport = {{
              status: "preview",
              dryRun: true,
              generatedAt: "2026-05-09T18:54:14+08:00",
              title: "项目医生预览到 2 项可安全修复",
              repairCount: 2,
              skippedCount: 1,
              requestedCodes: ["entry_scene", "scene_order"],
              repairs: [{{ title: "将入口改成第一幕", detail: "入口场景会从 ghost 改为 scene_01。" }}],
              skipped: [{{ title: "章节顺序无需处理" }}],
              nextActions: [{{ label: "确认执行安全修复", action: "repair-project-doctor" }}],
            }};
            state.projectDoctorRepairReceipt = receiptForExport;
            const receiptFileName = buildProjectDoctorRepairReceiptFileName(receiptForExport);
            const receiptMarkdown = buildProjectDoctorRepairReceiptMarkdownContent(receiptForExport);
            const clipboardSummary = buildProjectDoctorRepairReceiptClipboardSummary(receiptForExport);
            const receiptStamp = formatProjectDoctorRepairReceiptIdStamp(receiptForExport.generatedAt);
            const normalizedReceipt = withProjectDoctorRepairReceiptId(receiptForExport);
            const exportSummary = buildProjectDoctorRepairReceiptReportSummary(receiptForExport);
            const emptySummary = buildProjectDoctorRepairReceiptReportSummary(null);
            const unknownScope = formatProjectDoctorRepairReceiptScope({{ status: "unknown", requestedCodes: [] }});
            const defaultScope = formatProjectDoctorRepairReceiptScope({{ status: "clean", requestedCodes: [] }});
            const unknownWriteStatus = getProjectDoctorRepairReceiptWriteStatus({{ status: "unknown" }});
            const repairedWriteStatus = getProjectDoctorRepairReceiptWriteStatus({{ status: "repaired" }});
            const similarReceiptA = {{
              status: "preview",
              dryRun: true,
              generatedAt: "2026-05-09T18:54:14+08:00",
              title: "项目医生预览到 1 项可安全修复",
              repairCount: 1,
              skippedCount: 0,
              requestedCodes: ["entry_scene"],
              repairs: [{{ code: "entry_scene", title: "将入口改成第一幕", detail: "入口会改为 scene_01。" }}],
              skipped: [],
            }};
            const similarReceiptB = {{
              ...similarReceiptA,
              repairs: [{{ code: "entry_scene", title: "将入口改成第一幕", detail: "入口会改为 scene_02。" }}],
            }};
            const similarReceiptIds = [
              getProjectDoctorRepairReceiptId(similarReceiptA),
              getProjectDoctorRepairReceiptId(similarReceiptB),
            ];
            const existingReceipt = {{
              ...similarReceiptA,
              receiptId: " doctor existing/202605091054 custom1 ",
            }};
            const existingSummary = buildProjectDoctorRepairReceiptReportSummary(existingReceipt);
            const existingFileName = buildProjectDoctorRepairReceiptFileName(existingReceipt);
            const existingMarkdown = buildProjectDoctorRepairReceiptMarkdownContent(existingReceipt);
            const existingClipboardSummary = buildProjectDoctorRepairReceiptClipboardSummary(existingReceipt);
            const normalizedExistingReceipt = withProjectDoctorRepairReceiptId(existingReceipt);
            process.stdout.write(JSON.stringify({{ preview, repaired, unknown, compacted, truncated, fallback, previewItems, manyItems, multilineItem, summary, receiptFileName, receiptMarkdown, clipboardSummary, receiptStamp, normalizedReceipt, exportSummary, emptySummary, unknownScope, defaultScope, unknownWriteStatus, repairedWriteStatus, similarReceiptIds, existingSummary, existingFileName, existingMarkdown, existingClipboardSummary, normalizedExistingReceipt }}));
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
        self.assertEqual(payload["compacted"], "第一行 第二行 第三行")
        self.assertEqual(payload["truncated"], "12345…")
        self.assertEqual(payload["fallback"], "项目医生记录")
        self.assertEqual(payload["previewItems"][0], "将修复：将入口改成第一幕；入口场景会从 ghost 改为 scene_01。")
        self.assertEqual(payload["previewItems"][1], "将修复：将场景补回排序；第一章会补回 2 个场景。")
        self.assertEqual(payload["previewItems"][2], "将跳过：章节顺序无需处理；章节排序已完整。")
        self.assertEqual(payload["multilineItem"], "将修复：多行 标题；多行 细节 会压成一行")
        self.assertIn("另有 1 项没有展开", payload["manyItems"][-2])
        self.assertIn("另有 1 项没有展开", payload["manyItems"][-1])
        self.assertEqual(payload["summary"]["heading"], "最近一次安全修复预览")
        self.assertEqual(payload["summary"]["title"], "项目医生 预览到 2 项可安全修复")
        self.assertEqual(payload["summary"]["repairCount"], 2)
        self.assertEqual(payload["summary"]["skippedCount"], 1)
        self.assertEqual(payload["summary"]["requestedRepairCodes"], ["entry_scene", "scene_order"])
        self.assertEqual(payload["summary"]["requestedRepairLabels"], ["入口场景", "场景排序"])
        self.assertEqual(payload["summary"]["scopeLabel"], "入口场景 / 场景排序")
        self.assertRegex(payload["summary"]["receiptId"], r"^doctor-preview-[0-9]{12}-[a-z0-9]{6}$")
        self.assertEqual(payload["receiptStamp"], "202605091054")
        self.assertEqual(payload["normalizedReceipt"]["receiptId"], payload["exportSummary"]["receiptId"])
        self.assertEqual(payload["summary"]["writeStatus"]["status"], "preview")
        self.assertEqual(payload["summary"]["writeStatus"]["label"], "未写入项目文件")
        self.assertIn("不会改动项目", payload["summary"]["writeStatus"]["detail"])
        self.assertEqual(payload["summary"]["items"][0], "将修复：将入口改成第一幕；入口场景会从 ghost 改为 scene_01。")
        self.assertNotEqual(payload["similarReceiptIds"][0], payload["similarReceiptIds"][1])
        self.assertEqual(payload["existingSummary"]["receiptId"], "doctor-existing-202605091054-custom1")
        self.assertEqual(payload["normalizedExistingReceipt"]["receiptId"], "doctor-existing-202605091054-custom1")
        self.assertIn("doctor-existing-202605091054-custom1", payload["existingFileName"])
        self.assertIn("回执编号：doctor-existing-202605091054-custom1", payload["existingMarkdown"])
        self.assertIn("回执编号：doctor-existing-202605091054-custom1", payload["existingClipboardSummary"])
        self.assertRegex(
            payload["receiptFileName"],
            r"^Project_Demo_project_doctor_preview_doctor-preview-[0-9]{12}-[a-z0-9]{6}\.md$",
        )
        self.assertIn("# 最近一次安全修复预览", payload["receiptMarkdown"])
        self.assertIn("- 回执编号：doctor-preview-", payload["receiptMarkdown"])
        self.assertIn("| 回执编号 | doctor-preview-", payload["receiptMarkdown"])
        self.assertIn("| 写入状态 | 未写入项目文件：这只是安全修复预览，确认执行前不会改动项目。 |", payload["receiptMarkdown"])
        self.assertIn("| 修复范围 | 入口场景 / 场景排序 |", payload["receiptMarkdown"])
        self.assertIn("| 将修复 | 将入口改成第一幕 | 入口场景会从 ghost 改为 scene_01。 |", payload["receiptMarkdown"])
        self.assertIn("1. 确认执行安全修复", payload["receiptMarkdown"])
        self.assertIn("最近一次安全修复预览：项目医生预览到 2 项可安全修复", payload["clipboardSummary"])
        self.assertIn("回执编号：doctor-preview-", payload["clipboardSummary"])
        self.assertIn("项目：Project: Demo", payload["clipboardSummary"])
        self.assertIn("预览时间：日期:2026-05-09T18:54:14+08:00", payload["clipboardSummary"])
        self.assertIn("写入状态：未写入项目文件（这只是安全修复预览，确认执行前不会改动项目。）", payload["clipboardSummary"])
        self.assertIn("修复范围：入口场景 / 场景排序", payload["clipboardSummary"])
        self.assertIn("将修复 / 将跳过：2 / 1", payload["clipboardSummary"])
        self.assertIn("- 将修复：将入口改成第一幕；入口场景会从 ghost 改为 scene_01。", payload["clipboardSummary"])
        self.assertIn("下一步：确认执行安全修复", payload["clipboardSummary"])
        self.assertNotIn("| 项目 | 内容 |", payload["clipboardSummary"])
        self.assertIsNone(payload["emptySummary"])
        self.assertEqual(payload["unknownScope"], "无可执行范围")
        self.assertEqual(payload["defaultScope"], "全部安全项")
        self.assertEqual(payload["unknownWriteStatus"]["label"], "未执行")
        self.assertIn("重新巡检刷新", payload["unknownWriteStatus"]["detail"])
        self.assertEqual(payload["repairedWriteStatus"]["label"], "已写入项目文件")
        self.assertIn("projectDoctorReceiptLabels", source)
        self.assertIn("projectDoctorReceiptReportItems", source)
        self.assertIn("buildProjectDoctorRepairReceiptReportItems", source)
        self.assertIn("buildProjectDoctorRepairReceiptMarkdownContent", source)
        self.assertIn("buildProjectDoctorRepairReceiptClipboardSummary", source)
        self.assertIn("getProjectDoctorRepairReceiptId", source)
        self.assertIn("normalizeProjectDoctorRepairReceiptId", source)
        self.assertIn("withProjectDoctorRepairReceiptId", source)
        self.assertIn("getProjectDoctorRepairReceiptDisplayId", source)
        self.assertIn("`- 回执编号：${getProjectDoctorRepairReceiptDisplayId(state.projectDoctorRepairReceipt)}`", source)
        self.assertIn("copyProjectDoctorRepairReceiptSummary", source)
        self.assertIn("getProjectDoctorRepairReceiptWriteStatus", source)
        self.assertIn('data-action="copy-project-doctor-receipt-summary"', source)
        self.assertIn('data-action="export-project-doctor-receipt"', source)
        self.assertIn("formatProjectDoctorRepairReceiptScope", source)
        self.assertIn("修复范围", source)
        self.assertIn("receiptWriteStatus", source)
        self.assertIn("projectDoctorReceiptWriteStatus", source)
        self.assertIn("`- 写入状态：${receiptWriteStatus.label}（${receiptWriteStatus.detail}）`", source)
        self.assertIn("`- 写入状态：${projectDoctorReceiptWriteStatus.label}（${projectDoctorReceiptWriteStatus.detail}）`", source)
        self.assertIn("lastRepairReceiptReport", source)
        self.assertIn("receiptLabels.countLabel", source)

    def test_export_project_doctor_receipt_reports_result(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        export_receipt = _extract_function_source(source, "exportProjectDoctorRepairReceipt")
        script = textwrap.dedent(
            f"""
            const calls = [];
            const statuses = [];
            const toasts = [];
            const state = {{ projectDoctorRepairReceipt: null }};
            function showToast(message, tone = "soft") {{ toasts.push({{ message, tone }}); }}
            function setSaveStatus(message, isError = false) {{ statuses.push({{ message, isError }}); }}
            function buildProjectDoctorRepairReceiptFileName(receipt) {{
              calls.push({{ type: "fileName", title: receipt.title }});
              return "doctor-preview.md";
            }}
            function buildProjectDoctorRepairReceiptMarkdownContent(receipt) {{
              calls.push({{ type: "markdown", title: receipt.title }});
              return `# ${{receipt.title}}`;
            }}
            function downloadTextFile(fileName, content, mimeType) {{
              calls.push({{ type: "download", fileName, content, mimeType }});
            }}
            function exportProjectDoctorRepairReceipt() {export_receipt}

            const noReceiptResult = exportProjectDoctorRepairReceipt();
            const noReceipt = {{
              result: noReceiptResult,
              calls: calls.length,
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            state.projectDoctorRepairReceipt = {{ title: "预览回执" }};
            const exportedResult = exportProjectDoctorRepairReceipt();
            const exported = {{
              result: exportedResult,
              calls: calls.slice(),
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            process.stdout.write(JSON.stringify({{ noReceipt, exported }}));
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
        self.assertFalse(payload["noReceipt"]["result"])
        self.assertEqual(payload["noReceipt"]["calls"], 0)
        self.assertEqual(payload["noReceipt"]["status"]["message"], "暂无项目医生回执可导出")
        self.assertTrue(payload["noReceipt"]["status"]["isError"])
        self.assertEqual(payload["noReceipt"]["toast"]["tone"], "error")
        self.assertTrue(payload["exported"]["result"])
        self.assertEqual(payload["exported"]["calls"][0], {"type": "fileName", "title": "预览回执"})
        self.assertEqual(payload["exported"]["calls"][1], {"type": "markdown", "title": "预览回执"})
        self.assertEqual(
            payload["exported"]["calls"][2],
            {
                "type": "download",
                "fileName": "doctor-preview.md",
                "content": "# 预览回执",
                "mimeType": "text/markdown;charset=utf-8",
            },
        )
        self.assertEqual(payload["exported"]["status"]["message"], "已导出项目医生回执：doctor-preview.md")
        self.assertFalse(payload["exported"]["status"]["isError"])
        self.assertEqual(payload["exported"]["toast"]["message"], "项目医生回执已导出")

    def test_copy_project_doctor_receipt_summary_reports_result(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        copy_receipt_summary = _extract_function_source(source, "copyProjectDoctorRepairReceiptSummary")
        script = textwrap.dedent(
            f"""
            const calls = [];
            const statuses = [];
            const toasts = [];
            const state = {{ projectDoctorRepairReceipt: null }};
            let copyResult = false;
            function showToast(message, tone = "soft") {{ toasts.push({{ message, tone }}); }}
            function setSaveStatus(message, isError = false) {{ statuses.push({{ message, isError }}); }}
            function getProjectDoctorRepairReceiptDisplayId(receipt) {{
              return receipt.receiptId ?? "doctor-preview-copy-id";
            }}
            function buildProjectDoctorRepairReceiptClipboardSummary(receipt) {{
              calls.push({{ type: "summary", title: receipt.title }});
              return `SUMMARY:${{receipt.title}}`;
            }}
            async function copyTextToClipboard(text) {{
              calls.push({{ type: "copy", text }});
              return copyResult;
            }}
            async function copyProjectDoctorRepairReceiptSummary() {copy_receipt_summary}

            const noReceiptResult = await copyProjectDoctorRepairReceiptSummary();
            const noReceipt = {{
              result: noReceiptResult,
              calls: calls.length,
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            state.projectDoctorRepairReceipt = {{ title: "预览回执", receiptId: "doctor-preview-copy-id" }};
            copyResult = false;
            const failedResult = await copyProjectDoctorRepairReceiptSummary();
            const failed = {{
              result: failedResult,
              calls: calls.slice(),
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            calls.length = 0;
            copyResult = true;
            const succeededResult = await copyProjectDoctorRepairReceiptSummary();
            const succeeded = {{
              result: succeededResult,
              calls: calls.slice(),
              status: statuses.at(-1),
              toast: toasts.at(-1),
            }};

            process.stdout.write(JSON.stringify({{ noReceipt, failed, succeeded }}));
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
        self.assertFalse(payload["noReceipt"]["result"])
        self.assertEqual(payload["noReceipt"]["calls"], 0)
        self.assertEqual(payload["noReceipt"]["status"]["message"], "暂无项目医生回执可复制")
        self.assertTrue(payload["noReceipt"]["status"]["isError"])
        self.assertEqual(payload["noReceipt"]["toast"]["tone"], "error")
        self.assertFalse(payload["failed"]["result"])
        self.assertEqual(payload["failed"]["calls"][0], {"type": "summary", "title": "预览回执"})
        self.assertEqual(payload["failed"]["calls"][1], {"type": "copy", "text": "SUMMARY:预览回执"})
        self.assertEqual(payload["failed"]["status"]["message"], "项目医生回执复制失败")
        self.assertTrue(payload["failed"]["status"]["isError"])
        self.assertTrue(payload["succeeded"]["result"])
        self.assertEqual(payload["succeeded"]["calls"][0], {"type": "summary", "title": "预览回执"})
        self.assertEqual(payload["succeeded"]["calls"][1], {"type": "copy", "text": "SUMMARY:预览回执"})
        self.assertEqual(payload["succeeded"]["status"]["message"], "已复制项目医生回执摘要：doctor-preview-copy-id")
        self.assertFalse(payload["succeeded"]["status"]["isError"])
        self.assertEqual(payload["succeeded"]["toast"]["message"], "项目医生回执摘要已复制")

    def test_project_doctor_receipt_panel_uses_unknown_recovery_copy(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        get_code_label = _extract_function_source(source, "getProjectDoctorRepairCodeLabel")
        get_requested_codes = _extract_function_source(source, "getProjectDoctorRepairReceiptRequestedCodes")
        format_scope = _extract_function_source(source, "formatProjectDoctorRepairReceiptScope")
        report_labels = _extract_function_source(source, "getProjectDoctorRepairReceiptReportLabels")
        format_receipt_id_stamp = _extract_function_source(source, "formatProjectDoctorRepairReceiptIdStamp")
        get_receipt_id = _extract_function_source(source, "getProjectDoctorRepairReceiptId")
        normalize_receipt_id = _extract_function_source(source, "normalizeProjectDoctorRepairReceiptId")
        get_display_id = _extract_function_source(source, "getProjectDoctorRepairReceiptDisplayId")
        get_write_status = _extract_function_source(source, "getProjectDoctorRepairReceiptWriteStatus")
        build_next_actions = _extract_function_source(source, "buildProjectDoctorRepairNextActions")
        render_receipt_list = _extract_function_source(source, "renderProjectDoctorReceiptList")
        render_receipt_panel = _extract_function_source(source, "renderProjectDoctorRepairReceiptPanel")
        script = textwrap.dedent(
            f"""
            const projectDoctorTools = null;
            const state = {{ projectDoctorRepairReceipt: null }};
            function escapeHtml(value) {{
              return String(value ?? "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
            }}
            function formatDate(value) {{ return `日期:${{value}}`; }}
            function renderRouteMetricCard(label, value, hint) {{
              return `<metric data-label="${{escapeHtml(label)}}" data-value="${{escapeHtml(value)}}" data-hint="${{escapeHtml(hint)}}"></metric>`;
            }}
            function renderQuickActionButton(action) {{
              const datasetMarkup = Object.entries(action.dataset ?? {{}})
                .map(([key, value]) => ` data-${{key}}="${{escapeHtml(String(value ?? ""))}}"`)
                .join("");
              return `<button data-action="${{escapeHtml(action.action ?? "")}}"${{datasetMarkup}}>${{escapeHtml(action.label ?? "")}}</button>`;
            }}
            function sanitizeFileName(value) {{
              return String(value ?? "")
                .trim()
                .replace(/[\\\\/:*?"<>|]/g, "_")
                .replace(/\\s+/g, "_")
                .replace(/_+/g, "_")
                .replace(/^_+|_+$/g, "");
            }}
            function getProjectDoctorRepairCodeLabel(code) {get_code_label}
            function getProjectDoctorRepairReceiptRequestedCodes(receipt = {{}}) {get_requested_codes}
            function formatProjectDoctorRepairReceiptScope(receipt = {{}}) {format_scope}
            function getProjectDoctorRepairReceiptReportLabels(receipt = {{}}) {report_labels}
            function formatProjectDoctorRepairReceiptIdStamp(value) {format_receipt_id_stamp}
            function getProjectDoctorRepairReceiptId(receipt = {{}}) {get_receipt_id}
            function normalizeProjectDoctorRepairReceiptId(value) {normalize_receipt_id}
            function getProjectDoctorRepairReceiptDisplayId(receipt = {{}}) {get_display_id}
            function getProjectDoctorRepairReceiptWriteStatus(receipt = {{}}) {get_write_status}
            function buildProjectDoctorRepairNextActions(status = "clean", repairCodes = []) {build_next_actions}
            function renderProjectDoctorReceiptList(items = [], emptyText = "没有记录") {render_receipt_list}
            function renderProjectDoctorRepairReceiptPanel(receipt = state.projectDoctorRepairReceipt) {render_receipt_panel}
            const html = renderProjectDoctorRepairReceiptPanel({{
              status: "unknown",
              badge: "未识别",
              title: "项目医生未识别 1 个修复码",
              description: "这些修复码不属于当前安全修复范围：unknown_code。",
              generatedAt: "2026-05-09T19:46:15+08:00",
              repairCount: 0,
              skippedCount: 1,
              requestedCodes: [],
              repairs: [],
              skipped: [{{ title: "未识别修复码：unknown_code", detail: "请重新巡检后再点项目医生按钮。" }}],
            }});
            const previewFallbackHtml = renderProjectDoctorRepairReceiptPanel({{
              status: "preview",
              badge: "预览未写入",
              title: "项目医生预览到 2 项可安全修复",
              description: "这只是预览，不会写入项目文件；确认列表无误后再执行安全修复。",
              generatedAt: "2026-05-09T20:06:15+08:00",
              repairCount: 2,
              skippedCount: 0,
              requestedCodes: ["entry_scene", "scene_order"],
              repairs: [{{ title: "将修复入口场景" }}],
              skipped: [],
            }});
            process.stdout.write(JSON.stringify({{ html, previewFallbackHtml }}));
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
        html = payload["html"]
        preview_fallback_html = payload["previewFallbackHtml"]
        self.assertIn("data-label=\"可修复\"", html)
        self.assertIn("data-label=\"已跳过\"", html)
        self.assertIn("data-label=\"请求时间\"", html)
        self.assertIn("data-label=\"写入状态\"", html)
        self.assertIn("data-value=\"未执行\"", html)
        self.assertIn("修复码未识别，请重新巡检刷新后再预览。", html)
        self.assertIn("data-label=\"回执编号\"", html)
        self.assertIn("doctor-unknown-", html)
        self.assertIn("data-value=\"无可执行范围\"", html)
        self.assertIn("请重新巡检刷新修复码", html)
        self.assertIn("可自动处理", html)
        self.assertIn("未识别 / 已跳过", html)
        self.assertIn('data-action="run-project-inspection"', html)
        self.assertIn("重新巡检刷新修复码", html)
        self.assertIn('data-action="preview-project-doctor-repair"', html)
        self.assertIn("重新预览安全修复", html)
        self.assertNotIn("修复时间", html)
        self.assertNotIn("已自动处理", html)
        self.assertNotIn("本次自动修复范围", html)
        self.assertIn('data-action="repair-project-doctor"', preview_fallback_html)
        self.assertIn('data-repair-codes="entry_scene,scene_order"', preview_fallback_html)
        self.assertIn("未写入项目文件", preview_fallback_html)
        self.assertIn("确认按钮只执行这个范围", preview_fallback_html)

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
        beginner_tutorial_source = (EDITOR_DIR / "modules" / "beginner_tutorial.js").read_text(encoding="utf-8")
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
        self.assertIn("beginnerTutorialTools.renderBeginnerDashboardWorkflow", renderer)
        self.assertIn("function getBeginnerWorkflowStepStatusLabel", beginner_tutorial_source)
        self.assertIn("function getBeginnerWorkflowStepToneClass", beginner_tutorial_source)
        self.assertIn("getBeginnerWorkflowStepStatusLabel(step)", beginner_tutorial_source)
        self.assertIn("getBeginnerWorkflowStepToneClass(step)", beginner_tutorial_source)

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
        self.assertIn("导出${targetLabel}失败，已列出原因", export_build)
        self.assertIn("${targetLabel}没有导出成功", export_build)
        self.assertIn("copyable: true", export_build)

    def test_asset_delete_confirmations_preview_exact_targets(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        render_assets = _extract_function_source(source, "renderAssetsScreen")
        render_asset_details = _extract_function_source(source, "renderAssetDetails")
        import_accept = _extract_function_source(source, "getAssetImportAccept")
        import_assets = _extract_function_source(source, "importAssets")
        read_files = _extract_function_source(source, "readFilesAsBase64Payloads")
        replace_accept = _extract_function_source(source, "getAssetReplaceAccept")
        replace_format_label = _extract_function_source(source, "getAssetReplaceFormatLabel")
        replace_button_label = _extract_function_source(source, "getAssetReplaceButtonLabel")
        replace_button_title = _extract_function_source(source, "getAssetReplaceButtonTitle")
        replace_asset = _extract_function_source(source, "replaceSelectedAssetFile")
        accepted_file = _extract_function_source(source, "isFileAcceptedByAccept")
        mismatch_message = _extract_function_source(source, "getFileAcceptMismatchMessage")
        should_advance_replace = _extract_function_source(source, "shouldAdvanceAssetSelectionAfterReplace")
        delete_single = _extract_function_source(source, "deleteSelectedAsset")
        next_after_delete = _extract_function_source(source, "getNextAssetSelectionAfterDelete")
        delete_bulk = _extract_function_source(source, "deleteSelectedUnusedAssets")
        deletion_preview = _extract_function_source(source, "formatAssetDeletionPreview")
        usage_entry = _extract_function_source(source, "formatAssetUsageEntry")
        usage_preview = _extract_function_source(source, "formatAssetUsagePreview")

        self.assertIn("currentDeletableCheckedCount", render_assets)
        self.assertIn("currentProtectedCheckedCount", render_assets)
        self.assertIn("currentCheckedIds.length === 0 || currentDeletableCheckedCount === 0", render_assets)
        self.assertIn("无可删未使用 (${currentCheckedIds.length})", render_assets)
        self.assertIn("删未使用 ${currentDeletableCheckedCount}/${currentCheckedIds.length}", render_assets)
        self.assertIn("跳过 ${currentProtectedCheckedCount} 个正在使用的素材", render_assets)
        self.assertIn("getAssetReplaceButtonLabel(selectedAsset)", render_assets)
        self.assertIn("getAssetReplaceButtonTitle(selectedAsset)", render_assets)
        self.assertIn('classList.toggle("toolbar-button-primary", Boolean(selectedAsset && !selectedAsset.fileExists))', render_assets)
        self.assertIn("refs.assetImportInput.accept = getAssetImportAccept(state.selectedAssetType)", render_assets)
        self.assertIn("refs.assetSmartImportInput.accept = ASSET_SMART_IMPORT_ACCEPT", render_assets)
        self.assertIn("refs.assetReplaceInput.accept = getAssetReplaceAccept(selectedAsset)", render_assets)
        self.assertIn("formatAssetUsagePreview(usages, { limit: 4, separator: \" / \" })", render_asset_details)
        self.assertIn("ASSET_REPLACE_ACCEPTS[assetType]", import_accept)
        self.assertIn("const rejectedFiles = getRejectedAssetFilesByAccept(files, accept)", import_assets)
        self.assertIn("导入素材失败：文件格式不匹配", import_assets)
        self.assertIn("如果这一批文件本来就混着多种素材，请改用“智能导入”。", import_assets)
        self.assertIn("导入素材失败，已列出问题文件", import_assets)
        self.assertIn("这批素材没有导入成功", import_assets)
        self.assertIn("copyable: true", import_assets)
        self.assertIn("readFilesAsBase64Payloads(files", import_assets)
        self.assertIn("Promise.allSettled", read_files)
        self.assertIn("还有 ${failedMessages.length - 6} 个文件未展开", read_files)
        self.assertIn("ASSET_REPLACE_ACCEPTS[asset.type]", replace_accept)
        self.assertIn("ASSET_REPLACE_FORMAT_LABELS[asset.type]", replace_format_label)
        self.assertIn('["可补/替换格式", getAssetReplaceFormatLabel(asset)]', render_asset_details)
        self.assertIn('return asset.fileExists ? "替换当前文件" : "补这个文件"', replace_button_label)
        self.assertIn("补完后会自动跳到下一个缺文件素材", replace_button_title)
        self.assertIn("素材引用关系会保留", replace_button_title)
        self.assertIn("const ASSET_SMART_IMPORT_ACCEPT = Array.from", source)
        self.assertIn('live2d: "application/json,.model3.json', source)
        self.assertIn('video: "video/*,.mp4,.webm,.mov,.m4v"', source)
        self.assertIn("const shouldAdvanceAfterReplace = shouldAdvanceAssetSelectionAfterReplace(asset)", replace_asset)
        self.assertIn("if (!isFileAcceptedByAccept(file, accept))", replace_asset)
        self.assertIn("替换素材失败：文件格式不匹配", replace_asset)
        self.assertIn("如果这个文件其实属于别的素材分类", replace_asset)
        self.assertIn("替换素材失败，已列出原因", replace_asset)
        self.assertIn("这个素材文件没有替换成功", replace_asset)
        self.assertIn("copyable: true", replace_asset)
        self.assertIn("await showEngineAlert", replace_asset)
        self.assertIn("? getNextAssetSelectionAfterDelete(asset.id)", replace_asset)
        self.assertIn("selectedAssetId: selectedAssetIdAfterReplace", replace_asset)
        self.assertIn("当前筛选下的缺文件素材已经补完", replace_asset)
        self.assertNotIn('assetFilterMode: "all"', replace_asset)
        self.assertIn('state.assetFilterMode === "missing_file"', should_advance_replace)
        self.assertIn('state.assetFilterMode === "urgent_missing"', should_advance_replace)
        self.assertIn("formatAssetDeletionPreview([asset], { includeFileSize: true })", delete_single)
        self.assertIn("const usagePreview = formatAssetUsagePreview(usages, { limit: 6, separator: \"\\n\" })", delete_single)
        self.assertIn("先解除这些引用后再删：\\n${usagePreview}", delete_single)
        self.assertNotIn(".slice(0, 6)\n        .join(\"\\n\")", delete_single)
        self.assertIn("将删除：\\n${deletePreview}", delete_single)
        self.assertIn("如仅需更换或补上传文件，优先使用“补/替换文件”", delete_single)
        self.assertIn("删除素材失败，已列出原因", delete_single)
        self.assertIn("素材「${asset.name}」没有删除成功", delete_single)
        self.assertIn("copyable: true", delete_single)
        self.assertIn("const nextSelectedAssetId = getNextAssetSelectionAfterDelete(asset.id)", delete_single)
        self.assertIn("selectedAssetId: nextSelectedAssetId", delete_single)
        self.assertNotIn('assetFilterMode: "all"', delete_single)
        self.assertIn("deletedAssetIds", next_after_delete)
        self.assertIn("deletedIdSet", next_after_delete)
        self.assertIn("selectedIndex", next_after_delete)
        self.assertIn("firstDeletedIndex", next_after_delete)
        self.assertIn("getCurrentFilteredAssetsOfSelectedType()", next_after_delete)
        self.assertIn("remainingAssets[Math.min(anchorIndex, remainingAssets.length - 1)]", next_after_delete)
        self.assertIn("const deletePreview = formatAssetDeletionPreview(unusedAssets)", delete_bulk)
        self.assertIn("const skipPreview = formatAssetDeletionPreview(usedAssets", delete_bulk)
        self.assertIn("formatAssetUsagePreview(state.data.assetUsage.get(asset.id) ?? []", delete_bulk)
        self.assertIn("批量删除素材失败，已列出原因", delete_bulk)
        self.assertIn("这批素材没有批量删除成功", delete_bulk)
        self.assertIn("copyable: true", delete_bulk)
        self.assertIn("会自动跳过：${usedAssets.length} 个仍在使用的素材\\n${skipPreview}", delete_bulk)
        self.assertIn("const nextSelectedAssetId = deletedIds.has(state.selectedAssetId)", delete_bulk)
        self.assertIn("? getNextAssetSelectionAfterDelete(deletedIds)", delete_bulk)
        self.assertIn("selectedAssetId: nextSelectedAssetId", delete_bulk)
        self.assertIn("truncateText(asset.name || asset.id, 40)", deletion_preview)
        self.assertIn("formatFileSize(asset.fileSizeBytes)", deletion_preview)
        self.assertIn("已使用 ${getAssetUsageCount(asset.id)} 处", deletion_preview)
        self.assertIn('token.endsWith("/*")', accepted_file)
        self.assertIn("fileName.endsWith(token)", accepted_file)
        self.assertIn("fileType === token", accepted_file)
        self.assertIn("需要的格式：${options.expectedLabel", mismatch_message)
        self.assertIn("usage.meta ? `${label}（${usage.meta}）` : label", usage_entry)
        self.assertIn("list.slice(0, limit).map((usage) => formatAssetUsageEntry(usage))", usage_preview)
        self.assertIn("还有 ${list.length - limit} 处未展开", usage_preview)

    def test_character_stage_flip_is_wired_through_editor_export_and_native_runtime(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        read_stage = _extract_function_source(app_source, "readCharacterStageControls")
        render_stage = _extract_function_source(app_source, "renderCharacterStageControls")
        live_preview = _extract_function_source(app_source, "renderCharacterStageLivePreview")
        update_preview = _extract_function_source(app_source, "updateCharacterStagePreview")
        update_preset_state = _extract_function_source(app_source, "updateCharacterStagePresetState")
        self.assertIn("editorCharacterFlipX", read_stage)
        self.assertIn("editorCharacterFlipX", render_stage)
        self.assertIn("水平镜像", render_stage)
        self.assertIn("getCharacterStagePresetEntries", render_stage)
        self.assertIn("getMatchingCharacterStagePresetId(stage, position)", render_stage)
        self.assertIn("getCharacterStageAdjustmentEntries", render_stage)
        self.assertIn("apply-character-stage-preset", render_stage)
        self.assertIn("adjust-character-stage", render_stage)
        self.assertIn("aria-pressed", render_stage)
        self.assertIn("stage-preset-current", render_stage)
        self.assertIn("stage-shortcut-strip", render_stage)
        self.assertIn("方向键", render_stage)
        self.assertIn("+ / -", render_stage)
        self.assertIn("renderCharacterStageLivePreview(stage, position)", render_stage)
        self.assertIn("getPositionLabel(preset.position)", render_stage)
        self.assertIn("data-character-stage-preview-sprite", live_preview)
        self.assertIn("data-character-stage-preview-summary", live_preview)
        self.assertIn('tabindex="0"', live_preview)
        self.assertIn("方向键微调位置", live_preview)
        self.assertIn('data-position="${escapeHtml(position)}"', live_preview)
        self.assertIn("getCharacterStageStyle(stage)", update_preview)
        self.assertIn("previewSprite.dataset.position = position", update_preview)
        self.assertIn("getCharacterStagePreviewSummary(stage, position)", update_preview)
        self.assertIn("updateCharacterStagePresetState(stage, position)", update_preview)
        self.assertIn("getMatchingCharacterStagePresetId(stageSource, positionSource)", update_preset_state)
        self.assertIn('button.classList.toggle("is-active", isActive)', update_preset_state)
        self.assertIn("aria-pressed", update_preset_state)

        apply_preset = _extract_function_source(app_source, "applyCharacterStagePresetToEditor")
        position_getter = _extract_function_source(app_source, "getCharacterStageEditorPosition")
        position_setter = _extract_function_source(app_source, "setCharacterStageEditorPosition")
        set_values = _extract_function_source(app_source, "setCharacterStageEditorValues")
        adjust_stage = _extract_function_source(app_source, "adjustCharacterStageInEditor")
        keyboard_delta = _extract_function_source(app_source, "getCharacterStageKeyboardDelta")
        keyboard_nudge = _extract_function_source(app_source, "handleCharacterStageKeyboardNudge")
        self.assertIn("getCharacterStagePreset(presetId)", apply_preset)
        self.assertIn("setCharacterStageEditorPosition(preset.position)", apply_preset)
        self.assertIn("updateCharacterStagePreview(preset.stage, position)", apply_preset)
        self.assertIn("scheduleAutoSave(300)", apply_preset)
        self.assertIn("editorCharacterPosition", position_getter)
        self.assertIn("editorCharacterPosition", position_setter)
        self.assertIn("editorCharacterScale", set_values)
        self.assertIn("editorCharacterFlipX", set_values)
        self.assertIn("applyCharacterStageAdjustment(readCharacterStageControls(), adjustmentId)", adjust_stage)
        self.assertIn("setCharacterStageEditorValues(nextStage)", adjust_stage)
        self.assertIn("updateCharacterStagePreview(nextStage)", adjust_stage)
        self.assertIn("scheduleAutoSave(240)", adjust_stage)
        self.assertIn("event.shiftKey ? 10 : 2", keyboard_delta)
        self.assertIn('event.code === "ArrowLeft"', keyboard_delta)
        self.assertIn('event.code === "BracketRight"', keyboard_delta)
        self.assertIn("applyCharacterStageDelta(readCharacterStageControls(), delta)", keyboard_nudge)
        self.assertIn("event.target.closest(\"input, textarea, select\")", keyboard_nudge)
        self.assertIn("scheduleAutoSave(180)", keyboard_nudge)
        self.assertIn("handleCharacterStageKeyboardNudge(event)", app_source)
        self.assertIn('"apply-character-stage-preset"', app_source)
        self.assertIn('"adjust-character-stage"', app_source)
        self.assertIn('target.id === "editorCharacterPosition"', app_source)

        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        player_stage = _extract_function_source(player_source, "getSafeCharacterStage")
        player_style = _extract_function_source(player_source, "getCharacterStageStyle")
        self.assertIn("flipX: getSafeBoolean(raw.flipX, false)", player_stage)
        self.assertIn("--sprite-flip-x", player_style)
        player_css = (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8")
        self.assertIn(".sprite-visual-frame", player_css)
        self.assertIn("scaleX(var(--sprite-flip-x, 1))", player_css)

        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")
        self.assertIn('"flipX": read_bool("flipX")', native_source)
        self.assertIn("self.pygame.transform.flip(scaled, True, False)", native_source)

    def test_transition_duration_reaches_editor_preview_and_export_runtime(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        story_editor_source = (EDITOR_DIR / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        editor_css = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")
        player_css = (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8")

        collect_edited_block = _extract_function_source(app_source, "collectEditedBlock")
        apply_preview_block = _extract_function_source(app_source, "applyBlockToPreviewState")
        render_stage = _extract_function_source(app_source, "renderStage")
        render_sprite = _extract_function_source(app_source, "renderStageSpriteCard")
        block_summary = _extract_function_source(app_source, "getBlockSummary")
        runtime_apply_block = _extract_function_source(player_source, "applyBlockToPreviewState")
        runtime_stage_visual = _extract_function_source(player_source, "renderStageVisual")
        runtime_sprite = _extract_function_source(player_source, "renderSpriteCard")
        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")

        self.assertIn("editorTransitionDurationMs", story_editor_source)
        self.assertIn("getSafeTransitionDurationMs", story_editor_source)
        self.assertIn("transitionDurationMs: getSafeTransitionDurationMs", collect_edited_block)
        self.assertIn("backgroundTransitionEvent", apply_preview_block)
        self.assertIn("durationMs: getSafeTransitionDurationMs(block.transitionDurationMs)", apply_preview_block)
        self.assertIn("--background-transition-ms", render_stage)
        self.assertIn("--sprite-transition-ms", render_sprite)
        self.assertIn("getTransitionDurationSummary(block)", block_summary)
        self.assertIn("getSafeTransitionDurationMs(block.transitionDurationMs)", app_source)
        self.assertIn("backgroundTransitionEvent", runtime_apply_block)
        self.assertIn("getSafeTransitionDurationMs(block.transitionDurationMs)", runtime_apply_block)
        self.assertIn("--background-transition-ms", runtime_stage_visual)
        self.assertIn("--sprite-transition-ms", runtime_sprite)
        self.assertIn("stage-backdrop-fade-in var(--background-transition-ms", editor_css)
        self.assertIn("player-background-fade-in var(--background-transition-ms", player_css)
        self.assertIn("var(--sprite-transition-ms", editor_css)
        self.assertIn("var(--sprite-transition-ms", player_css)
        self.assertIn("def get_safe_transition_duration_ms", native_source)
        self.assertIn("self.start_background_transition(previous_background_asset_id, block)", native_source)
        self.assertIn('"transition": self.get_character_transition_state(block, "in")', native_source)
        self.assertIn('transition = self.get_character_transition_state(block, "out")', native_source)
        self.assertIn("self.background_transition", native_source)
        self.assertIn("self.leaving_characters", native_source)

    def test_line_text_speed_override_reaches_preview_export_and_native_runtime(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        collect_edited_block = _extract_function_source(app_source, "collectEditedBlock")
        preview_speed = _extract_function_source(app_source, "getPreviewSnapshotTextSpeed")
        preview_typewriter = _extract_function_source(app_source, "shouldUsePreviewTypewriter")
        preview_delay = _extract_function_source(app_source, "getPreviewAutoAdvanceDelay")
        preview_schedule_typewriter = _extract_function_source(app_source, "schedulePreviewTypewriterTick")
        self.assertIn("editorTextSpeed", collect_edited_block)
        self.assertIn("nextBlock.textSpeed = getSafeTextSpeed(rawTextSpeed);", collect_edited_block)
        self.assertIn("delete nextBlock.textSpeed;", collect_edited_block)
        self.assertIn("snapshot?.block?.textSpeed ?? state.previewPlayback.textSpeed", preview_speed)
        self.assertIn('getPreviewSnapshotTextSpeed(snapshot) === "instant"', preview_typewriter)
        self.assertIn("getPreviewSnapshotTextSpeed(snapshot)", preview_delay)
        self.assertIn("function getTypewriterPunctuationPause", app_source)
        self.assertIn("getTypewriterPunctuationPause(visibleText, fullText)", app_source)
        self.assertIn("state.previewTyping.visibleText", preview_schedule_typewriter)

        story_editor_source = (EDITOR_DIR / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        self.assertIn("renderTextSpeedOverrideRow", story_editor_source)
        self.assertIn("跟随全局文字速度", story_editor_source)
        self.assertIn("editorTextSpeed", story_editor_source)

        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        runtime_speed = _extract_function_source(player_source, "getSnapshotTextSpeed")
        runtime_typewriter = _extract_function_source(player_source, "shouldUseRuntimeTypewriter")
        runtime_delay = _extract_function_source(player_source, "getAutoAdvanceDelay")
        runtime_schedule_typewriter = _extract_function_source(player_source, "scheduleRuntimeTypewriterTick")
        self.assertIn("snapshot?.block?.textSpeed ?? state.playback.textSpeed", runtime_speed)
        self.assertIn('getSnapshotTextSpeed(snapshot) === "instant"', runtime_typewriter)
        self.assertIn("getSnapshotTextSpeed(snapshot)", runtime_delay)
        self.assertIn("function getTypewriterPunctuationPause", player_source)
        self.assertIn("getTypewriterPunctuationPause(visibleText, fullText)", player_source)
        self.assertIn("state.typingVisibleText", runtime_schedule_typewriter)

        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")
        self.assertIn("def get_safe_text_speed", native_source)
        self.assertIn("def get_next_typewriter_index", native_source)
        self.assertIn("def get_typewriter_punctuation_pause_ms", native_source)
        self.assertIn("def get_current_line_text_speed", native_source)
        self.assertIn('"textSpeed": block.get("textSpeed")', native_source)
        self.assertIn("self.get_current_line_text_speed() == \"instant\"", native_source)
        self.assertIn("self.current_line_next_reveal_at_ms", native_source)

    def test_typewriter_index_helpers_keep_unicode_characters_intact(self) -> None:
        for path in (APP_PATH, PLAYER_PATH):
            source = path.read_text(encoding="utf-8")
            script = "\n".join(
                [
                    "const typewriterGraphemeSegmenter = null;",
                    f"function getNextUnicodeScalarIndex(text, index) {_extract_function_source(source, 'getNextUnicodeScalarIndex')}",
                    f"function getTypewriterCodePointAtIndex(text, index) {_extract_function_source(source, 'getTypewriterCodePointAtIndex')}",
                    f"function isRegionalIndicatorSymbol(text, index) {_extract_function_source(source, 'isRegionalIndicatorSymbol')}",
                    f"function isTypewriterGraphemeExtension(text, index) {_extract_function_source(source, 'isTypewriterGraphemeExtension')}",
                    f"function getNextTypewriterClusterIndex(text, index) {_extract_function_source(source, 'getNextTypewriterClusterIndex')}",
                    f"function getNextCodePointIndex(text, index) {_extract_function_source(source, 'getNextCodePointIndex')}",
                    f"function getCodePointAtIndex(text, index) {_extract_function_source(source, 'getCodePointAtIndex')}",
                    "const TYPEWRITER_LEADING_OPENERS = '“‘\"\\'（([{【〔〈《「『';",
                    f"function includeTypewriterTrailingClosers(text, index) {_extract_function_source(source, 'includeTypewriterTrailingClosers')}",
                    f"function includeTypewriterLeadingFollower(text, currentIndex, index) {_extract_function_source(source, 'includeTypewriterLeadingFollower')}",
                    f"function getNextTypewriterIndex(text, currentIndex) {_extract_function_source(source, 'getNextTypewriterIndex')}",
                    "const TEXT_SPEED_LABELS = { slow: '慢速', normal: '标准', fast: '快速', instant: '立刻显示' };",
                    "const TYPEWRITER_TRAILING_CLOSERS = '”’\"\\')）]}】〕〉》」』';",
                    "const TYPEWRITER_PERIOD_ABBREVIATIONS = new Set(['mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'st', 'vs', 'etc', 'e.g', 'i.e', 'u.s', 'u.k', 'no', 'fig', 'vol', 'ch', 'dept', 'inc', 'ltd', 'co']);",
                    "function getSafeTextSpeed(speed) { return Object.hasOwn(TEXT_SPEED_LABELS, speed) ? speed : 'normal'; }",
                    f"function getTypewriterPauseAnchorText(text) {_extract_function_source(source, 'getTypewriterPauseAnchorText')}",
                    f"function getTypewriterPauseAnchorChar(text) {_extract_function_source(source, 'getTypewriterPauseAnchorChar')}",
                    f"function isTypewriterInlinePeriod(anchorText, fullText = '') {_extract_function_source(source, 'isTypewriterInlinePeriod')}",
                    f"function isTypewriterAbbreviationPeriod(anchorText, fullText = '') {_extract_function_source(source, 'isTypewriterAbbreviationPeriod')}",
                    f"function getTypewriterPunctuationPause(text, fullText = '') {_extract_function_source(source, 'getTypewriterPunctuationPause')}",
                    f"function getTypewriterStepDelay(speed, visibleText = '', fullText = '') {_extract_function_source(source, 'getTypewriterStepDelay')}",
                    """
                    const emojiText = "A💙B";
                    if (getNextTypewriterIndex(emojiText, 1) !== 3) {
                      throw new Error("emoji step split a surrogate pair");
                    }
                    if (getNextTypewriterIndex(emojiText, 2) !== 3) {
                      throw new Error("emoji recovery from a partial surrogate pair regressed");
                    }
                    if (emojiText.slice(0, getNextTypewriterIndex(emojiText, 1)) !== "A💙") {
                      throw new Error("emoji reveal text is not intact");
                    }
                    const familyText = "A👨‍👩‍👧‍👦B";
                    if (getNextTypewriterIndex(familyText, 1) !== familyText.indexOf("B")) {
                      throw new Error("grapheme cluster emoji was split during reveal");
                    }
                    const flagText = "A🇯🇵B";
                    if (getNextTypewriterIndex(flagText, 1) !== flagText.indexOf("B")) {
                      throw new Error("flag emoji was split during reveal");
                    }
                    const skinToneText = "A👍🏽B";
                    if (getNextTypewriterIndex(skinToneText, 1) !== skinToneText.indexOf("B")) {
                      throw new Error("emoji modifier was split during fallback reveal");
                    }
                    const accentedText = "e\\u0301!";
                    if (getNextTypewriterIndex(accentedText, 0) !== accentedText.indexOf("!")) {
                      throw new Error("combining accent was split during fallback reveal");
                    }
                    if (getNextTypewriterIndex("abc def", 0) !== 4) {
                      throw new Error("latin grouping or whitespace folding regressed");
                    }
                    const openingSentence = "“再见。”";
                    if (getNextTypewriterIndex(openingSentence, 0) !== openingSentence.indexOf("见")) {
                      throw new Error("opening quote should reveal with the first content character");
                    }
                    const openingWord = '"Hi" there';
                    if (getNextTypewriterIndex(openingWord, 0) !== openingWord.indexOf("i")) {
                      throw new Error("opening quote should not appear as a lonely first frame");
                    }
                    const quotedSentence = "“再见。”下一句";
                    if (getNextTypewriterIndex(quotedSentence, quotedSentence.indexOf("。")) !== quotedSentence.indexOf("下")) {
                      throw new Error("closing quote should reveal with the punctuation before the pause");
                    }
                    const quotedWord = '"Hi" there';
                    if (getNextTypewriterIndex(quotedWord, quotedWord.indexOf("i")) !== quotedWord.indexOf(" ") + 1) {
                      throw new Error("closing quote should reveal with the previous word");
                    }
                    if (getTypewriterStepDelay("instant", "世界！") !== 0) {
                      throw new Error("instant typewriter speed should not inherit punctuation pauses");
                    }
                    if (getTypewriterStepDelay("normal", "世界！") <= getTypewriterStepDelay("normal", "世界")) {
                      throw new Error("punctuation pause no longer extends natural reading delay");
                    }
                    if (getTypewriterPunctuationPause("“再见。”") !== 260) {
                      throw new Error("closing quote swallowed the sentence punctuation pause");
                    }
                    if (getTypewriterPunctuationPause("嗯，") !== 140) {
                      throw new Error("clause punctuation pause regressed");
                    }
                    if (getTypewriterPunctuationPause("Hello.") !== 260) {
                      throw new Error("english sentence punctuation pause regressed");
                    }
                    if (getTypewriterPunctuationPause("Wait...") !== 220) {
                      throw new Error("ascii ellipsis pause regressed");
                    }
                    if (getTypewriterPunctuationPause('"Wait..."') !== 220) {
                      throw new Error("quoted ascii ellipsis pause regressed");
                    }
                    if (getTypewriterPunctuationPause("3.", "3.14") !== 0) {
                      throw new Error("decimal period should not pause like a sentence");
                    }
                    if (getTypewriterPunctuationPause("v1.", "v1.2") !== 0) {
                      throw new Error("version period should not pause like a sentence");
                    }
                    if (getTypewriterPunctuationPause("example.", "example.com") !== 0) {
                      throw new Error("domain period should not pause like a sentence");
                    }
                    if (getTypewriterPunctuationPause("Chapter 1.") !== 260) {
                      throw new Error("terminal numeric sentence period should still pause");
                    }
                    if (getTypewriterPunctuationPause("Mr.", "Mr. Smith") !== 0) {
                      throw new Error("english honorific abbreviation should not pause like a sentence");
                    }
                    if (getTypewriterPunctuationPause("e.g.", "e.g. this") !== 0) {
                      throw new Error("latin abbreviation should not pause like a sentence");
                    }
                    if (getTypewriterPunctuationPause("Dr.") !== 260) {
                      throw new Error("terminal abbreviation should still pause when no following text exists");
                    }
                    """,
                ]
            )
            completed = subprocess.run(
                ["node", "-e", script],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"{path.name} typewriter helper regression:\n{completed.stderr}",
            )

    def test_voice_line_volume_reaches_preview_export_and_native_runtime(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        story_editor_source = (EDITOR_DIR / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        player_source = PLAYER_PATH.read_text(encoding="utf-8")
        native_source = NATIVE_RUNTIME_PATH.read_text(encoding="utf-8")

        dialogue_editor_template = _extract_function_source(story_editor_source, "renderDialogueEditor")
        narration_editor_template = _extract_function_source(story_editor_source, "renderNarrationEditor")
        render_narration_editor = _extract_function_source(app_source, "renderNarrationEditor")
        collect_edited_block = _extract_function_source(app_source, "collectEditedBlock")
        preview_voice_asset = _extract_function_source(app_source, "getPreviewVoiceAssetId")
        preview_voice = _extract_function_source(app_source, "syncPreviewVoice")
        preview_voice_volume = _extract_function_source(app_source, "getPreviewVoiceTargetVolume")
        runtime_voice = _extract_function_source(player_source, "syncVoice")
        runtime_voice_asset = _extract_function_source(player_source, "getVoiceAssetId")
        runtime_voice_volume = _extract_function_source(player_source, "getRuntimeVoiceTargetVolume")
        runtime_audio_update = _extract_function_source(player_source, "updateRuntimeAudioVolumes")

        self.assertIn("editorVoiceVolume", dialogue_editor_template)
        self.assertIn("editorNarrationVoiceAssetId", narration_editor_template)
        self.assertIn("editorNarrationVoiceVolume", narration_editor_template)
        self.assertIn('asset.type === "voice"', render_narration_editor)
        self.assertIn("nextBlock.voiceVolume = getSafeVolumePercent", collect_edited_block)
        self.assertIn("editorNarrationVoiceAssetId", collect_edited_block)
        self.assertIn("editorNarrationVoiceVolume", collect_edited_block)
        self.assertIn("delete nextBlock.voiceVolume", collect_edited_block)
        self.assertIn('snapshot.blockType !== "dialogue" && snapshot.blockType !== "narration"', preview_voice_asset)
        self.assertIn("getPreviewVoiceTargetVolume(snapshot)", preview_voice)
        self.assertIn("snapshot?.block?.voiceVolume", preview_voice_volume)
        self.assertIn('snapshot.blockType !== "dialogue" && snapshot.blockType !== "narration"', runtime_voice_asset)
        self.assertIn("getRuntimeVoiceTargetVolume(snapshot)", runtime_voice)
        self.assertIn("snapshot?.block?.voiceVolume", runtime_voice_volume)
        self.assertIn("state.voiceAudio.volume = getRuntimeVoiceTargetVolume(getCurrentSnapshot())", runtime_audio_update)
        self.assertIn("def get_effective_voice_volume", native_source)
        self.assertIn('voiceVolume": block.get("voiceVolume")', native_source)
        self.assertIn('if block.get("voiceAssetId"):', native_source)
        self.assertIn('self.play_voice(block.get("voiceAssetId"), volume_percent=block.get("voiceVolume"))', native_source)
        self.assertIn("def play_voice(self, asset_id: str | None, volume_percent: object | None = None)", native_source)


if __name__ == "__main__":
    unittest.main()
