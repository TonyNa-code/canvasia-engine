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
STYLES_PATH = EDITOR_DIR / "styles.css"
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

    def test_command_palette_wiring_stays_integrated_with_editor_actions(self) -> None:
        html = INDEX_PATH.read_text(encoding="utf-8")
        app_source = APP_PATH.read_text(encoding="utf-8")
        command_palette_source = (EDITOR_DIR / "modules" / "command_palette.js").read_text(encoding="utf-8")
        story_templates_source = (EDITOR_DIR / "modules" / "story_templates.js").read_text(encoding="utf-8")
        script_importer_source = (EDITOR_DIR / "modules" / "script_importer.js").read_text(encoding="utf-8")
        route_analyzer_source = (EDITOR_DIR / "modules" / "route_analyzer.js").read_text(encoding="utf-8")
        styles = STYLES_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(app_source, "handleClick")
        handle_global_keydown = _extract_function_source(app_source, "handleGlobalKeydown")
        get_context = _extract_function_source(app_source, "getCommandPaletteContext")
        run_command = _extract_function_source(app_source, "runCommandPaletteCommand")
        render_story_editor_mode_banner = _extract_function_source(app_source, "renderStoryEditorModeBanner")
        render_story_template_grid = _extract_function_source(app_source, "renderStoryTemplateGrid")
        render_story_template_button = _extract_function_source(app_source, "renderStoryTemplateButton")
        render_script_importer_panel = _extract_function_source(app_source, "renderScriptImporterPanel")
        parse_current_script_import_draft = _extract_function_source(app_source, "parseCurrentScriptImportDraft")
        insert_script_import_blocks = _extract_function_source(app_source, "insertScriptImportBlocks")
        build_scene_route_overview = _extract_function_source(app_source, "buildSceneRouteOverview")
        collect_scene_routes = _extract_function_source(app_source, "collectSceneRoutes")
        render_story_screen = _extract_function_source(app_source, "renderStoryScreen")
        hydrate_project_runtime = _extract_function_source(app_source, "hydrateProjectRuntime")
        clear_loaded_project_state = _extract_function_source(app_source, "clearLoadedProjectState")
        add_block = _extract_function_source(app_source, "addBlock")
        build_story_template_blocks = _extract_function_source(app_source, "buildStoryTemplateBlocks")
        apply_story_template = _extract_function_source(app_source, "applyStoryTemplate")

        self.assertIn("./modules/command_palette.js", html)
        self.assertIn('id="storyTemplatePanel"', html)
        self.assertIn('id="storyTemplateGrid"', html)
        self.assertIn('id="scriptImporterPanel"', html)
        self.assertNotIn('data-template-id="opening_intro"', html)
        self.assertIn('id="commandPaletteDialog"', html)
        self.assertIn('aria-keyshortcuts="Meta+K Control+K"', html)
        self.assertIn('action === "open-command-palette"', handle_click)
        self.assertIn('action === "close-command-palette"', handle_click)
        self.assertIn('action === "run-command-palette-command"', handle_click)
        self.assertIn('event.code === "KeyK"', handle_global_keydown)
        self.assertIn("handleCommandPaletteKeydown(event)", handle_global_keydown)
        self.assertIn('getStoryTemplateSummary("playable_scene", { getBlockLabel })', render_story_editor_mode_banner)
        self.assertIn("playableTemplateSummary", render_story_editor_mode_banner)
        self.assertIn("getStoryTemplatePanelItems()", render_story_template_grid)
        self.assertIn('data-template-id="${escapeHtml(templateId)}"', render_story_template_button)
        self.assertIn("story-template-button-meta", render_story_template_button)
        self.assertIn("renderStoryTemplateGrid()", render_story_screen)
        self.assertIn("refs.storyTemplatePanel", render_story_screen)
        self.assertIn("renderScriptImporterPanel(scene, selectedBlock)", render_story_screen)
        self.assertIn("refs.scriptImporterPanel", render_story_screen)
        self.assertIn("buildScriptDraftPreviewLines", render_script_importer_panel)
        self.assertIn("parseScriptDraftToBlocks", parse_current_script_import_draft)
        self.assertIn('data-action="preview-script-import"', render_script_importer_panel)
        self.assertIn('data-action="insert-script-import-blocks"', render_script_importer_panel)
        self.assertIn("buildAssistantBlocksForInsertion(scene, draftBlocks)", insert_script_import_blocks)
        self.assertIn('state.scriptImporterError = "识别成功，但没有生成可保存的剧情卡片。"', insert_script_import_blocks)
        self.assertIn("routeAnalyzerTools.buildSceneRouteOverview", build_scene_route_overview)
        self.assertIn("routeAnalyzerTools.collectSceneRoutes", collect_scene_routes)
        self.assertIn("state.data ? state.validation ?? runValidation(state.data) : { errors: [], warnings: [] }", get_context)
        self.assertIn("const selectedScene = state.data ? getSelectedScene() : null", get_context)
        self.assertIn("const selectedBlock = state.data ? getSelectedBlock() : null", get_context)
        self.assertIn("hasSelectedScene: Boolean(selectedScene)", get_context)
        self.assertIn("selectedSceneTitle: selectedScene?.name ?? \"\"", get_context)
        self.assertIn("selectedSceneBlockCount: selectedScene?.blocks?.length ?? 0", get_context)
        self.assertIn("selectedBlockType: selectedBlock?.type ?? \"\"", get_context)
        self.assertIn("recentCommandIds: state.commandPaletteRecentIds", get_context)
        self.assertIn("recentLimit: COMMAND_PALETTE_RECENT_LIMIT", get_context)
        self.assertNotIn("validateProject()", get_context)
        self.assertIn("buildVirtualActionTarget(command)", run_command)
        self.assertIn("await handleClick({", run_command)
        self.assertIn("recordCommandPaletteCommand(command.id)", run_command)
        self.assertIn("state.commandPaletteRecentIds = loadStoredCommandPaletteRecentIds(data.project)", hydrate_project_runtime)
        self.assertIn("state.commandPaletteRecentIds = loadStoredCommandPaletteRecentIds(null)", clear_loaded_project_state)
        self.assertIn('success && state.currentScreen !== "story"', add_block)
        self.assertIn('switchScreen("story")', add_block)
        self.assertIn('state.currentScreen !== "story"', apply_story_template)
        self.assertIn('switchScreen("story")', apply_story_template)
        self.assertIn("getStoryTemplateBlockRecipes(templateId)", build_story_template_blocks)
        self.assertIn("createTemplateBlock(sceneDraft, recipe, context)", build_story_template_blocks)
        self.assertNotIn('templateId === "opening_intro"', build_story_template_blocks)
        self.assertIn("const STORY_BLOCK_COMMANDS", command_palette_source)
        self.assertIn("const STORY_TEMPLATE_COMMANDS", command_palette_source)
        self.assertIn('id: "template-playable-scene"', command_palette_source)
        self.assertIn('templateId: "playable_scene"', command_palette_source)
        self.assertIn('action: "add-dialogue"', command_palette_source)
        self.assertIn('dataset: { "template-id": command.templateId }', command_palette_source)
        self.assertIn("getRecommendedCommandIds", command_palette_source)
        self.assertIn("prioritizeRecommendedCommands", command_palette_source)
        self.assertIn("mergeCommandPaletteRecentId", command_palette_source)
        self.assertIn("loadStoredCommandPaletteRecentIds", command_palette_source)
        self.assertIn("parseScriptDraftToBlocks", script_importer_source)
        self.assertIn("summarizeScriptDraftBlocks", script_importer_source)
        self.assertIn("buildSceneRouteOverview", route_analyzer_source)
        self.assertIn("collectSceneRoutes", route_analyzer_source)
        self.assertIn("buildRouteSceneProduction", route_analyzer_source)
        self.assertIn("STORY_TEMPLATE_BLOCK_RECIPES", story_templates_source)
        self.assertIn("STORY_TEMPLATE_PANEL_ITEMS", story_templates_source)
        self.assertIn("getStoryTemplateSummary", story_templates_source)
        self.assertIn("getStoryTemplatePanelItems", story_templates_source)
        self.assertIn("playable_scene", story_templates_source)
        self.assertIn("认真回应她", story_templates_source)
        self.assertIn(".command-palette-item.is-selected", styles)
        self.assertIn(".workflow-template-summary", styles)
        self.assertIn(".story-template-button.is-hero", styles)
        self.assertIn(".story-template-button-meta", styles)
        self.assertIn(".script-importer-shell", styles)
        self.assertIn(".script-importer-textarea", styles)
        self.assertIn(".command-palette-item.is-recommended", styles)
        self.assertIn(".command-palette-item.is-recent", styles)
        self.assertIn('html[data-ui-theme="light"] .command-palette-item.is-selected', styles)
        self.assertIn('html[data-ui-theme="light"] .command-palette-item.is-recommended', styles)
        self.assertIn('html[data-ui-theme="light"] .command-palette-item.is-recent', styles)

    def test_editor_mode_switch_explains_project_center_default_scope(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        apply_editor_mode_ui = _extract_function_source(source, "applyEditorModeUi")
        sync_editor_mode_button = _extract_function_source(source, "syncEditorModeButton")
        handle_click = _extract_function_source(source, "handleClick")

        self.assertIn("syncEditorModeButton(refs.editorModeBeginnerButton", apply_editor_mode_ui)
        self.assertIn("syncEditorModeButton(refs.editorModeAdvancedButton", apply_editor_mode_ui)
        self.assertIn("aria-pressed", sync_editor_mode_button)
        self.assertIn("默认：${modeLabel}", sync_editor_mode_button)
        self.assertIn("设为${modeLabel}", sync_editor_mode_button)
        self.assertIn("当前项目正在使用${modeLabel}", sync_editor_mode_button)
        self.assertIn("新建项目将默认使用${modeLabel}", sync_editor_mode_button)
        self.assertIn("const currentMode = getSafeEditorMode(state.projectCenterEditorMode)", handle_click)
        self.assertIn("新建项目已经默认使用${modeLabel}", handle_click)
        self.assertIn("已经默认使用${modeLabel}", handle_click)
        self.assertIn("showToast(`新建项目默认：${modeLabel}`)", handle_click)

        script = textwrap.dedent(
            f"""
            function getSafeEditorMode(mode) {{
              return String(mode).trim() === "advanced" ? "advanced" : "beginner";
            }}
            function getEditorModeLabel(mode) {{
              return getSafeEditorMode(mode) === "advanced" ? "高级模式" : "新手模式";
            }}
            function createButton() {{
              const classes = new Set();
              return {{
                disabled: true,
                textContent: "",
                title: "",
                attrs: {{}},
                classList: {{
                  toggle(name, enabled) {{
                    enabled ? classes.add(name) : classes.delete(name);
                  }},
                  remove(name) {{
                    classes.delete(name);
                  }},
                }},
                setAttribute(name, value) {{
                  this.attrs[name] = value;
                }},
                get classes() {{
                  return Array.from(classes).sort();
                }},
              }};
            }}
            function syncEditorModeButton(button, targetMode, activeMode, hasProject) {sync_editor_mode_button}
            const projectCenterActive = createButton();
            const projectCenterInactive = createButton();
            const projectActive = createButton();
            const projectInactive = createButton();
            syncEditorModeButton(projectCenterActive, "beginner", "beginner", false);
            syncEditorModeButton(projectCenterInactive, "advanced", "beginner", false);
            syncEditorModeButton(projectActive, "advanced", "advanced", true);
            syncEditorModeButton(projectInactive, "beginner", "advanced", true);
            process.stdout.write(JSON.stringify({{
              projectCenterActive,
              projectCenterInactive,
              projectActive,
              projectInactive,
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
        self.assertEqual(payload["projectCenterActive"]["textContent"], "默认：新手模式")
        self.assertEqual(payload["projectCenterActive"]["attrs"]["aria-pressed"], "true")
        self.assertIn("新建项目将默认使用新手模式", payload["projectCenterActive"]["attrs"]["aria-label"])
        self.assertEqual(payload["projectCenterInactive"]["textContent"], "设为高级模式")
        self.assertEqual(payload["projectCenterInactive"]["attrs"]["aria-pressed"], "false")
        self.assertIn("设为新建项目默认高级模式", payload["projectCenterInactive"]["title"])
        self.assertEqual(payload["projectActive"]["textContent"], "高级模式")
        self.assertEqual(payload["projectActive"]["attrs"]["aria-pressed"], "true")
        self.assertIn("当前项目正在使用高级模式", payload["projectActive"]["title"])
        self.assertEqual(payload["projectInactive"]["textContent"], "新手模式")
        self.assertEqual(payload["projectInactive"]["attrs"]["aria-pressed"], "false")
        self.assertIn("切换当前项目到新手模式", payload["projectInactive"]["attrs"]["aria-label"])

    def test_startup_and_fatal_errors_use_readable_messages(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        index_source = INDEX_PATH.read_text(encoding="utf-8")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        init_source = _extract_function_source(source, "init")
        startup_message = _extract_function_source(source, "getEditorStartupErrorMessage")
        fatal_project_load = _extract_function_source(source, "showFatalProjectLoadError")
        project_load_message = _extract_function_source(source, "getProjectLoadErrorMessage")
        load_error_stage_label = _extract_function_source(source, "getLoadErrorStageLabel")
        load_error_project_title = _extract_function_source(source, "getLoadErrorProjectTitle")
        load_error_recovery_summary = _extract_function_source(source, "getLoadErrorRecoverySummary")
        feedback_text = _extract_function_source(source, "buildLoadErrorFeedbackText")
        focus_error_state = _extract_function_source(source, "focusErrorStatePrimaryAction")
        is_error_state_visible = _extract_function_source(source, "isErrorStateVisible")
        copy_load_error_message = _extract_function_source(source, "copyCurrentLoadErrorMessage")
        reload_editor_page = _extract_function_source(source, "reloadEditorPage")
        project_center_from_error = _extract_function_source(source, "openProjectCenterFromErrorState")
        runtime_error_handler = _extract_function_source(source, "handleEditorRuntimeError")
        open_project_center = _extract_function_source(source, "openProjectCenter")
        show_editor_shell = _extract_function_source(source, "showEditorShell")

        self.assertIn('data-action="reload-editor-page"', index_source)
        self.assertIn('aria-label="重新载入编辑器页面"', index_source)
        self.assertIn('data-action="open-project-center"', index_source)
        self.assertIn('aria-label="返回项目中心重新选择项目"', index_source)
        self.assertIn('data-action="copy-error-message"', index_source)
        self.assertIn('role="alert"', index_source)
        self.assertIn('aria-live="assertive"', index_source)
        self.assertIn('aria-atomic="true"', index_source)
        self.assertIn('class="error-message-copy"', index_source)
        self.assertIn('aria-label="复制当前载入失败的反馈信息"', index_source)
        self.assertIn(".state-card .error-message-copy", style_source)
        self.assertIn("line-height: 1.65", style_source)
        self.assertIn("overflow-wrap: anywhere", style_source)
        self.assertIn("white-space: pre-line", style_source)
        self.assertIn('action === "reload-editor-page"', click_handler)
        self.assertIn("reloadEditorPage();", click_handler)
        self.assertIn('action === "copy-error-message"', click_handler)
        self.assertIn("void copyCurrentLoadErrorMessage();", click_handler)
        self.assertIn("isErrorStateVisible()", click_handler)
        self.assertIn("await openProjectCenterFromErrorState();", click_handler)
        self.assertIn('state.loadErrorStage = ""', open_project_center)
        self.assertIn('state.loadErrorStage = ""', show_editor_shell)
        self.assertLess(
            click_handler.index('action === "open-project-center"'),
            click_handler.index("if (!state.data) {"),
        )
        self.assertLess(
            click_handler.index('action === "reload-editor-page"'),
            click_handler.index("if (!state.data) {"),
        )
        self.assertIn('loadErrorStage: ""', source)
        self.assertIn("getEditorStartupErrorMessage(error)", init_source)
        self.assertIn('state.loadErrorStage = "editor_startup"', init_source)
        self.assertIn("focusErrorStatePrimaryAction();", init_source)
        self.assertNotIn("refs.errorMessage.textContent = error.message", init_source)
        self.assertIn("编辑器没有载入成功", startup_message)
        self.assertIn("重新运行启动脚本后刷新页面", startup_message)
        self.assertIn("getErrorDetailMessage(", startup_message)

        self.assertIn("getProjectLoadErrorMessage(error)", fatal_project_load)
        self.assertIn('state.loadErrorStage = "project_load"', fatal_project_load)
        self.assertIn("focusErrorStatePrimaryAction();", fatal_project_load)
        self.assertIn("项目没有载入成功", project_load_message)
        self.assertIn("自动快照", project_load_message)
        self.assertNotIn("error?.message", fatal_project_load)

        self.assertIn("options.stageLabel", load_error_stage_label)
        self.assertIn("editor_startup", load_error_stage_label)
        self.assertIn("编辑器启动", load_error_stage_label)
        self.assertIn("project_load", load_error_stage_label)
        self.assertIn("项目载入", load_error_stage_label)
        self.assertIn("state.projectCenter?.activeProjectId", load_error_project_title)
        self.assertIn("project?.projectId === activeProjectId", load_error_project_title)
        self.assertIn("未打开项目", load_error_project_title)
        self.assertIn("getSafeProjectHistory", load_error_recovery_summary)
        self.assertIn("history.totalSnapshots", load_error_recovery_summary)
        self.assertIn("history.canUndo", load_error_recovery_summary)
        self.assertIn("previousSnapshot?.label", load_error_recovery_summary)
        self.assertIn("# Canvasia Engine 错误反馈", feedback_text)
        self.assertIn("页面：${pageUrl}", feedback_text)
        self.assertIn("阶段：${stageLabel}", feedback_text)
        self.assertIn("项目：${projectTitle}", feedback_text)
        self.assertIn("项目版本：${releaseVersion}", feedback_text)
        self.assertIn("自动快照：${recoverySummary}", feedback_text)
        self.assertIn("错误信息：", feedback_text)
        self.assertIn('[data-action="reload-editor-page"]', focus_error_state)
        self.assertIn("preventScroll: true", focus_error_state)
        self.assertIn("return false", focus_error_state)
        self.assertIn('classList.contains("is-hidden")', is_error_state_visible)
        self.assertIn("refs.errorMessage?.textContent", copy_load_error_message)
        self.assertIn("copyTextToClipboard(buildLoadErrorFeedbackText(message))", copy_load_error_message)
        self.assertIn("错误信息已复制，可直接粘贴到反馈里", copy_load_error_message)
        self.assertIn("当前没有可复制的错误信息", copy_load_error_message)
        self.assertIn("复制失败，可以手动选中错误信息", copy_load_error_message)
        self.assertIn("globalThis.location?.reload", reload_editor_page)
        self.assertIn("浏览器没有允许自动刷新，请手动刷新页面", reload_editor_page)
        self.assertIn("refreshProjectCenterState()", project_center_from_error)
        self.assertIn("openProjectCenter({ keepStatus: true })", project_center_from_error)
        self.assertIn("项目列表暂时无法刷新，已显示上次读取结果", project_center_from_error)
        self.assertIn("getEditorStartupErrorMessage(error)", project_center_from_error)
        self.assertIn("项目列表仍然无法读取", project_center_from_error)
        self.assertIn("focusErrorStatePrimaryAction()", project_center_from_error)

        self.assertIn('getErrorDetailMessage(error, "未知错误")', runtime_error_handler)
        self.assertIn("详细错误已记录在控制台", runtime_error_handler)
        self.assertNotIn("error.message", runtime_error_handler)

        script = textwrap.dedent(
            f"""
            let state = {{
              data: null,
              loadErrorStage: "project_load",
              projectCenter: {{
                activeProjectId: "broken-project",
                projects: [{{ projectId: "broken-project", title: "破损测试工程" }}],
              }},
              projectHistory: {{
                totalSnapshots: 3,
                canUndo: true,
                previousSnapshot: {{ label: "自动保存 2" }},
              }},
            }};
            function getLoadErrorStageLabel(options = {{}}) {load_error_stage_label}
            function getLoadErrorProjectTitle(options = {{}}) {load_error_project_title}
            function getSafeProjectHistory(history = state.projectHistory) {{
              return history ?? {{ totalSnapshots: 0, canUndo: false, previousSnapshot: null }};
            }}
            function getLoadErrorRecoverySummary(options = {{}}) {load_error_recovery_summary}
            function buildLoadErrorFeedbackText(message, options = {{}}) {feedback_text}
            const payload = buildLoadErrorFeedbackText("启动服务断开", {{
              capturedAt: "2026-05-31T12:00:00.000Z",
              pageUrl: "http://127.0.0.1:8765/prototype_editor/index.html",
              stageLabel: "编辑器启动",
              projectTitle: "心跳时差",
              releaseVersion: "1.2.3-preview",
              recoverySummary: "无可用快照",
            }});
            const fallbackPayload = buildLoadErrorFeedbackText("项目数据损坏", {{
              capturedAt: "2026-05-31T12:05:00.000Z",
              pageUrl: "http://127.0.0.1:8765/prototype_editor/index.html",
            }});
            const lockedPayload = buildLoadErrorFeedbackText("已经无法继续回退", {{
              capturedAt: "2026-05-31T12:10:00.000Z",
              pageUrl: "http://127.0.0.1:8765/prototype_editor/index.html",
              history: {{
                totalSnapshots: 2,
                canUndo: false,
                previousSnapshot: null,
              }},
              stage: "editor_startup",
            }});
            process.stdout.write(JSON.stringify({{ payload, fallbackPayload, lockedPayload }}));
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
        payload = json.loads(completed.stdout)["payload"]
        self.assertIn("# Canvasia Engine 错误反馈", payload)
        self.assertIn("时间：2026-05-31T12:00:00.000Z", payload)
        self.assertIn("页面：http://127.0.0.1:8765/prototype_editor/index.html", payload)
        self.assertIn("阶段：编辑器启动", payload)
        self.assertIn("项目：心跳时差", payload)
        self.assertIn("项目版本：1.2.3-preview", payload)
        self.assertIn("自动快照：无可用快照", payload)
        self.assertIn("启动服务断开", payload)
        fallback_payload = json.loads(completed.stdout)["fallbackPayload"]
        self.assertIn("阶段：项目载入", fallback_payload)
        self.assertIn("项目：破损测试工程", fallback_payload)
        self.assertIn("自动快照：3 份，可恢复到「自动保存 2」", fallback_payload)
        self.assertIn("项目数据损坏", fallback_payload)
        locked_payload = json.loads(completed.stdout)["lockedPayload"]
        self.assertIn("阶段：编辑器启动", locked_payload)
        self.assertIn("自动快照：2 份，当前已是最早版本", locked_payload)

        reload_script = textwrap.dedent(
            f"""
            const calls = [];
            function setSaveStatus(message, isError = false) {{
              calls.push({{ type: "status", message, isError }});
            }}
            function showToast(message, tone = "soft") {{
              calls.push({{ type: "toast", message, tone }});
            }}
            console.warn = (...args) => calls.push({{ type: "warn", message: String(args[0]) }});
            globalThis.location = {{
              reload() {{
                calls.push({{ type: "reload" }});
              }},
            }};
            function reloadEditorPage() {reload_editor_page}
            const succeeded = reloadEditorPage();
            delete globalThis.location;
            const failed = reloadEditorPage();
            process.stdout.write(JSON.stringify({{ succeeded, failed, calls }}));
            """
        )
        reload_completed = subprocess.run(
            ["node", "-e", reload_script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(reload_completed.returncode, 0, reload_completed.stderr)
        reload_payload = json.loads(reload_completed.stdout)
        self.assertTrue(reload_payload["succeeded"])
        self.assertFalse(reload_payload["failed"])
        self.assertIn({"type": "reload"}, reload_payload["calls"])
        self.assertIn(
            {"type": "status", "message": "浏览器没有允许自动刷新，请手动刷新页面", "isError": True},
            reload_payload["calls"],
        )

        project_center_script = textwrap.dedent(
            f"""
            const calls = [];
            const state = {{ projectCenter: {{ projects: [] }} }};
            const refs = {{ errorMessage: {{ textContent: "" }} }};
            let refreshMode = "success";
            function setSaveStatus(message, isError = false) {{
              calls.push({{ type: "status", message, isError }});
            }}
            async function refreshProjectCenterState() {{
              calls.push({{ type: "refresh" }});
              if (refreshMode !== "success") {{
                throw new Error("后端暂时不可用");
              }}
              state.projectCenter = {{ projects: [{{ projectId: "demo" }}] }};
            }}
            function openProjectCenter(options = {{}}) {{
              calls.push({{ type: "open", options }});
            }}
            function showToast(message, tone = "soft") {{
              calls.push({{ type: "toast", message, tone }});
            }}
            function getEditorStartupErrorMessage(error) {{
              return `startup:${{error.message}}`;
            }}
            function focusErrorStatePrimaryAction() {{
              calls.push({{ type: "focus" }});
              return true;
            }}
            console.warn = (...args) => calls.push({{ type: "warn", message: String(args[0]) }});
            async function run() {{
              async function openProjectCenterFromErrorState() {project_center_from_error}
              const success = await openProjectCenterFromErrorState();
              refreshMode = "fail-with-cache";
              const cached = await openProjectCenterFromErrorState();
              state.projectCenter = {{ projects: [] }};
              refs.errorMessage.textContent = "";
              refreshMode = "fail-empty";
              const empty = await openProjectCenterFromErrorState();
              process.stdout.write(JSON.stringify({{ success, cached, empty, errorMessage: refs.errorMessage.textContent, calls }}));
            }}
            run().catch((error) => {{
              console.error(error);
              process.exit(1);
            }});
            """
        )
        project_center_completed = subprocess.run(
            ["node", "-e", project_center_script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(project_center_completed.returncode, 0, project_center_completed.stderr)
        project_center_payload = json.loads(project_center_completed.stdout)
        self.assertTrue(project_center_payload["success"])
        self.assertTrue(project_center_payload["cached"])
        self.assertFalse(project_center_payload["empty"])
        self.assertEqual(project_center_payload["errorMessage"], "startup:后端暂时不可用")
        self.assertIn(
            {"type": "status", "message": "项目列表暂时无法刷新，已显示上次读取结果", "isError": True},
            project_center_payload["calls"],
        )
        self.assertIn(
            {"type": "status", "message": "项目列表仍然无法读取", "isError": True},
            project_center_payload["calls"],
        )
        self.assertIn({"type": "focus"}, project_center_payload["calls"])

    def test_project_center_failures_use_copyable_detail_dialogs(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        handle_project_load_failure = _extract_function_source(source, "handleProjectLoadFailure")
        show_copyable_operation_failure = _extract_function_source(source, "showCopyableOperationFailure")
        show_project_center_failure = _extract_function_source(source, "showProjectCenterFailure")
        create_playable_demo_project = _extract_function_source(source, "createPlayableDemoProject")
        project_center_operation_sources = "\n".join([handle_click, create_playable_demo_project])

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
            'await showProjectCenterFailure(error, "新建可试玩 Demo 失败", "可试玩 Demo 没有创建成功")',
            'await showProjectCenterFailure(error, "打开项目失败", "项目没有打开成功")',
            'await showProjectCenterFailure(error, "修改项目名失败", "项目名没有修改成功")',
            'await showProjectCenterFailure(error, "复制项目失败", "项目没有复制成功")',
            'await showProjectCenterFailure(error, "删除项目失败", `项目「${project.title}」没有删除成功`)',
        ]
        for expected_call in expected_calls:
            self.assertIn(expected_call, project_center_operation_sources)

        old_alerts = [
            "刷新项目列表失败：${error.message}",
            "新建空白项目失败：${error.message}",
            "新建可试玩 Demo 失败：${error.message}",
            "打开项目失败：${error.message}",
            "修改项目名失败：${error.message}",
            "复制项目失败：${error.message}",
            "删除项目失败：${error.message}",
        ]
        for old_alert in old_alerts:
            self.assertNotIn(old_alert, project_center_operation_sources)

    def test_create_project_prompt_confirms_default_editor_mode(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        prompt_for_text = _extract_function_source(source, "promptForText")

        self.assertIn('action === "create-project"', handle_click)
        self.assertIn("state.projectCreateInFlight", source)
        self.assertIn("正在准备新项目，请稍等", source)
        self.assertIn("blockProjectCenterOperationIfInFlight()", handle_click)
        self.assertIn("setProjectCreateInFlight(true)", handle_click)
        self.assertIn("setProjectCreateInFlight(false)", handle_click)
        self.assertIn("finally", handle_click)
        self.assertIn("const projectMode = getSafeEditorMode(state.projectCenterEditorMode)", handle_click)
        self.assertIn("const projectModeLabel = getEditorModeLabel(projectMode)", handle_click)
        self.assertIn("将以${projectModeLabel}创建一个真正的空白项目", handle_click)
        self.assertIn('title: "新建空白项目"', handle_click)
        self.assertIn("confirmLabel: `创建${projectModeLabel}项目`", handle_click)
        self.assertIn('placeholder: "例如：雨夜校园序章"', handle_click)
        self.assertIn("setSaveStatus(`正在创建${projectModeLabel}空白项目...`)", handle_click)
        self.assertIn("editorMode: projectMode", handle_click)
        self.assertIn("`已打开${projectModeLabel}空白项目：${name}`", handle_click)
        self.assertIn("`空白项目已创建：${name}（${projectModeLabel}）`", handle_click)
        self.assertNotIn("editorMode: state.projectCenterEditorMode", handle_click)
        self.assertIn("options.title", prompt_for_text)
        self.assertIn("options.placeholder", prompt_for_text)
        self.assertIn("options.confirmLabel", prompt_for_text)
        self.assertIn("options.requiredMessage", prompt_for_text)
        self.assertIn("options.maxLength", prompt_for_text)
        self.assertIn("options.copyText ?? false", prompt_for_text)
        self.assertIn('action === "create-playable-demo-project"', handle_click)
        self.assertIn("await createPlayableDemoProject()", handle_click)
        self.assertIn("async function createPlayableDemoProject", source)
        self.assertIn("新建可试玩 Demo", source)
        self.assertIn("生成 Demo 项目", source)
        self.assertIn("await postJson(API_CREATE_PROJECT", source)
        self.assertIn("await postJson(API_CREATE_CHAPTER", source)
        self.assertIn("rethrowErrors: true", source)
        self.assertIn('switchScreen("preview")', source)

        script = textwrap.dedent(
            f"""
            const calls = [];
            async function showEnginePrompt(options) {{
              calls.push(options);
              return "  心跳练习曲  ";
            }}
            async function promptForText(message, defaultValue, options = {{}}) {prompt_for_text}
            async function run() {{
              const value = await promptForText(["起名", "模式说明"], "未命名新作", {{
                title: "新建空白项目",
                confirmLabel: "创建新手模式项目",
                placeholder: "例如：雨夜校园序章",
                requiredMessage: "先填项目名。",
                maxLength: 40,
              }});
              const empty = await (async () => {{
                showEnginePrompt = async (options) => {{
                  calls.push(options);
                  return "   ";
                }};
                return promptForText("空白测试", "默认名");
              }})();
              process.stdout.write(JSON.stringify({{ value, empty, calls }}));
            }}
            run().catch((error) => {{
              console.error(error);
              process.exit(1);
            }});
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
        self.assertEqual(payload["value"], "心跳练习曲")
        self.assertIsNone(payload["empty"])
        self.assertEqual(payload["calls"][0]["title"], "新建空白项目")
        self.assertEqual(payload["calls"][0]["message"], ["起名", "模式说明"])
        self.assertEqual(payload["calls"][0]["confirmLabel"], "创建新手模式项目")
        self.assertEqual(payload["calls"][0]["placeholder"], "例如：雨夜校园序章")
        self.assertEqual(payload["calls"][0]["requiredMessage"], "先填项目名。")
        self.assertEqual(payload["calls"][0]["maxLength"], 40)
        self.assertIs(payload["calls"][0]["copyText"], False)
        self.assertEqual(payload["calls"][1]["title"], "填写名称")
        self.assertEqual(payload["calls"][1]["confirmLabel"], "确认")
        self.assertEqual(payload["calls"][1]["placeholder"], "默认名")
        self.assertIs(payload["calls"][1]["copyText"], False)

    def test_project_center_operations_share_busy_gate(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        get_in_flight_message = _extract_function_source(source, "getProjectCenterOperationInFlightMessage")
        block_operation = _extract_function_source(source, "blockProjectCenterOperationIfInFlight")

        self.assertGreaterEqual(handle_click.count("blockProjectCenterOperationIfInFlight()"), 7)
        self.assertIn('action === "set-editor-mode"', handle_click)
        self.assertIn("setSaveStatus(message)", block_operation)
        self.assertIn("showToast(message)", block_operation)
        expected_pairs = [
            ("state.projectCreateInFlight", "正在准备新项目，请稍等..."),
            ("state.projectCenterRefreshInFlight", "正在刷新项目列表，请稍等..."),
            ("state.projectOpenInFlightId", "正在打开项目，请稍等..."),
            ("state.projectRenameInFlightId", "正在修改项目名，请稍等..."),
            ("state.projectDuplicateInFlightId", "正在复制项目，请稍等..."),
            ("state.projectDeleteInFlightId", "正在删除项目，请稍等..."),
        ]
        for state_key, message in expected_pairs:
            self.assertIn(state_key, get_in_flight_message)
            self.assertIn(message, get_in_flight_message)

        script = textwrap.dedent(
            f"""
            const state = {{
              projectCreateInFlight: false,
              projectCenterRefreshInFlight: false,
              projectOpenInFlightId: "",
              projectRenameInFlightId: "",
              projectDuplicateInFlightId: "",
              projectDeleteInFlightId: "",
            }};
            const statusMessages = [];
            const toastMessages = [];
            function setSaveStatus(message) {{
              statusMessages.push(message);
            }}
            function showToast(message) {{
              toastMessages.push(message);
            }}
            function getProjectCenterOperationInFlightMessage() {get_in_flight_message}
            function blockProjectCenterOperationIfInFlight() {block_operation}
            function reset(overrides = {{}}) {{
              Object.assign(state, {{
                projectCreateInFlight: false,
                projectCenterRefreshInFlight: false,
                projectOpenInFlightId: "",
                projectRenameInFlightId: "",
                projectDuplicateInFlightId: "",
                projectDeleteInFlightId: "",
              }}, overrides);
              statusMessages.length = 0;
              toastMessages.length = 0;
              const message = getProjectCenterOperationInFlightMessage();
              const blocked = blockProjectCenterOperationIfInFlight();
              return {{
                message,
                blocked,
                statusMessages: [...statusMessages],
                toastMessages: [...toastMessages],
              }};
            }}
            process.stdout.write(JSON.stringify({{
              idle: reset(),
              create: reset({{ projectCreateInFlight: true }}),
              refresh: reset({{ projectCenterRefreshInFlight: true }}),
              open: reset({{ projectOpenInFlightId: "project-a" }}),
              rename: reset({{ projectRenameInFlightId: "project-a" }}),
              duplicate: reset({{ projectDuplicateInFlightId: "project-a" }}),
              delete: reset({{ projectDeleteInFlightId: "project-a" }}),
              priority: reset({{
                projectCreateInFlight: true,
                projectDeleteInFlightId: "project-a",
              }}),
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
        self.assertFalse(payload["idle"]["blocked"])
        self.assertEqual(payload["idle"]["message"], "")
        self.assertEqual(payload["idle"]["statusMessages"], [])
        self.assertTrue(payload["create"]["blocked"])
        self.assertEqual(payload["create"]["message"], "正在准备新项目，请稍等...")
        self.assertEqual(payload["create"]["statusMessages"], ["正在准备新项目，请稍等..."])
        self.assertEqual(payload["refresh"]["message"], "正在刷新项目列表，请稍等...")
        self.assertEqual(payload["open"]["message"], "正在打开项目，请稍等...")
        self.assertEqual(payload["rename"]["message"], "正在修改项目名，请稍等...")
        self.assertEqual(payload["duplicate"]["message"], "正在复制项目，请稍等...")
        self.assertEqual(payload["delete"]["message"], "正在删除项目，请稍等...")
        self.assertEqual(payload["priority"]["message"], "正在准备新项目，请稍等...")
        self.assertEqual(payload["priority"]["toastMessages"], ["正在准备新项目，请稍等..."])

    def test_playable_demo_starter_kit_failure_surfaces_and_restores_busy_state(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        create_playable_demo_project = _extract_function_source(source, "createPlayableDemoProject")
        create_starter_kit = _extract_function_source(source, "createStarterKit")

        script = textwrap.dedent(
            f"""
            const calls = [];
            const statuses = [];
            const toasts = [];
            const failures = [];
            const switches = [];
            const reloads = [];
            const API_CREATE_PROJECT = "/api/create-project";
            const API_CREATE_CHAPTER = "/api/create-chapter";
            const API_CREATE_STARTER_KIT = "/api/create-starter-kit";
            const state = {{
              projectCenterEditorMode: "beginner",
              projectCreateInFlight: false,
              selectedSceneId: "old-scene",
              selectedBlockId: "old-block",
              previewSceneId: "old-preview",
              previewStartSceneId: "old-preview",
              selectedCharacterId: "old-character",
            }};
            function blockProjectCenterOperationIfInFlight() {{
              return false;
            }}
            function getSafeEditorMode(mode) {{
              return mode === "advanced" ? "advanced" : "beginner";
            }}
            function getEditorModeLabel(mode) {{
              return getSafeEditorMode(mode) === "advanced" ? "高级模式" : "新手模式";
            }}
            function getBlankProjectStarterDefaults() {{
              return {{ chapterName: "第一章 开场", firstSceneName: "第一场 相遇" }};
            }}
            function setProjectCreateInFlight(value) {{
              state.projectCreateInFlight = Boolean(value);
              calls.push(["busy", state.projectCreateInFlight]);
            }}
            async function promptForText() {{
              return "失败回归 Demo";
            }}
            async function postJson(url, payload) {{
              calls.push(["post", url, payload]);
              if (url === API_CREATE_PROJECT) {{
                return {{ projectCenter: {{ projects: [] }} }};
              }}
              if (url === API_CREATE_CHAPTER) {{
                return {{ sceneId: "scene_intro", scene: {{ blocks: [{{ id: "block_start" }}] }} }};
              }}
              if (url === API_CREATE_STARTER_KIT) {{
                throw new Error("starter kit boom");
              }}
              throw new Error(`unexpected url ${{url}}`);
            }}
            async function loadProjectCenter() {{
              return {{ projects: [] }};
            }}
            async function enterActiveProjectEditor(message) {{
              calls.push(["enter", message]);
              state.data = {{ project: {{ title: "失败回归 Demo" }}, chapters: [], scenes: [] }};
            }}
            function getCurrentUiState() {{
              return {{}};
            }}
            async function reloadProjectData(payload) {{
              reloads.push(payload);
              state.selectedSceneId = payload.selectedSceneId;
              state.selectedBlockId = payload.selectedBlockId;
              state.previewSceneId = payload.previewSceneId;
              state.previewStartSceneId = payload.previewStartSceneId;
            }}
            function getStarterKitOverview() {{
              return {{
                needsStarterKit: true,
                missingLabels: ["角色", "背景", "BGM"],
                missingCharacter: true,
                missingBackground: true,
                missingBgm: true,
              }};
            }}
            function getStarterKitDefaults() {{
              return {{ characterName: "女主角", backgroundName: "第一场背景", bgmName: "开场 BGM" }};
            }}
            async function showEditorOperationFailure(error) {{
              calls.push(["editorFailure", error.message]);
            }}
            function handleProjectLoadFailure() {{
              return false;
            }}
            async function showProjectCenterFailure(error, title, detail) {{
              failures.push({{ message: error.message, title, detail }});
            }}
            function setSaveStatus(message, isError = false) {{
              statuses.push({{ message, isError }});
            }}
            function showToast(message, type = null) {{
              toasts.push({{ message, type }});
            }}
            function switchScreen(screen) {{
              switches.push(screen);
            }}
            async function createStarterKit(options = {{}}) {create_starter_kit}
            async function createPlayableDemoProject() {create_playable_demo_project}
            createPlayableDemoProject().then(() => {{
              process.stdout.write(JSON.stringify({{
                calls,
                statuses,
                toasts,
                failures,
                switches,
                reloads,
                busy: state.projectCreateInFlight,
              }}));
            }}).catch((error) => {{
              console.error(error);
              process.exit(1);
            }});
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
        post_urls = [call[1] for call in payload["calls"] if call[0] == "post"]

        self.assertEqual(post_urls, ["/api/create-project", "/api/create-chapter", "/api/create-starter-kit"])
        self.assertEqual(payload["calls"][0], ["busy", True])
        self.assertEqual(payload["calls"][-1], ["busy", False])
        self.assertFalse(payload["busy"])
        self.assertEqual(payload["failures"][0]["message"], "starter kit boom")
        self.assertEqual(payload["failures"][0]["title"], "新建可试玩 Demo 失败")
        self.assertEqual(payload["failures"][0]["detail"], "可试玩 Demo 没有创建成功")
        self.assertEqual(payload["reloads"][0]["selectedSceneId"], "scene_intro")
        self.assertEqual(payload["reloads"][0]["selectedBlockId"], "block_start")
        self.assertNotIn("preview", payload["switches"])
        self.assertFalse(any("可试玩 Demo 已生成" in status["message"] for status in payload["statuses"]))
        self.assertEqual(payload["toasts"], [])

    def test_project_create_busy_state_disables_project_center_entry(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_project_create_in_flight = _extract_function_source(source, "setProjectCreateInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("button.textContent = busyLabel", set_action_button_busy_state)
        self.assertIn("button.dataset[idleLabelKey]", set_action_button_busy_state)
        self.assertIn('button.setAttribute("aria-busy", "true")', set_action_button_busy_state)
        self.assertIn("state.projectCreateInFlight = Boolean(isInFlight)", set_project_create_in_flight)
        self.assertIn('[data-action="create-project"], [data-action="create-playable-demo-project"]', set_project_create_in_flight)
        self.assertIn('busyLabel: "准备中..."', set_project_create_in_flight)
        self.assertIn("projectCreateIdleLabel", set_project_create_in_flight)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(label) {{
                this.dataset = {{}};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ projectCreateInFlight: false }};
            const createButton = new HTMLButtonElement("新建空白项目");
            const demoButton = new HTMLButtonElement("新建可试玩 Demo");
            const document = {{
              querySelectorAll(selector) {{
                return selector === '[data-action="create-project"], [data-action="create-playable-demo-project"]'
                  ? [createButton, demoButton]
                  : [];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setProjectCreateInFlight(isInFlight) {set_project_create_in_flight}
            setProjectCreateInFlight(true);
            const busy = {{
              inFlight: state.projectCreateInFlight,
              disabled: createButton.disabled,
              text: createButton.textContent,
              busy: createButton.attrs["aria-busy"],
              ariaDisabled: createButton.attrs["aria-disabled"],
              demoText: demoButton.textContent,
              demoBusy: demoButton.attrs["aria-busy"],
              classes: Array.from(createButton.classes),
            }};
            setProjectCreateInFlight(false);
            const idle = {{
              inFlight: state.projectCreateInFlight,
              disabled: createButton.disabled,
              text: createButton.textContent,
              busy: createButton.attrs["aria-busy"] ?? null,
              ariaDisabled: createButton.attrs["aria-disabled"] ?? null,
              demoText: demoButton.textContent,
              demoBusy: demoButton.attrs["aria-busy"] ?? null,
              classes: Array.from(createButton.classes),
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertTrue(payload["busy"]["inFlight"])
        self.assertTrue(payload["busy"]["disabled"])
        self.assertEqual(payload["busy"]["text"], "准备中...")
        self.assertEqual(payload["busy"]["demoText"], "准备中...")
        self.assertEqual(payload["busy"]["busy"], "true")
        self.assertEqual(payload["busy"]["demoBusy"], "true")
        self.assertEqual(payload["busy"]["ariaDisabled"], "true")
        self.assertIn("is-busy", payload["busy"]["classes"])
        self.assertFalse(payload["idle"]["inFlight"])
        self.assertFalse(payload["idle"]["disabled"])
        self.assertEqual(payload["idle"]["text"], "新建空白项目")
        self.assertEqual(payload["idle"]["demoText"], "新建可试玩 Demo")
        self.assertIsNone(payload["idle"]["busy"])
        self.assertIsNone(payload["idle"]["demoBusy"])
        self.assertIsNone(payload["idle"]["ariaDisabled"])
        self.assertNotIn("is-busy", payload["idle"]["classes"])

    def test_project_center_refresh_busy_state_disables_refresh_entry(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_refresh_in_flight = _extract_function_source(source, "setProjectCenterRefreshInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("button.textContent = busyLabel", set_action_button_busy_state)
        self.assertIn("state.projectCenterRefreshInFlight", source)
        self.assertIn("正在刷新项目列表，请稍等", source)
        self.assertIn("blockProjectCenterOperationIfInFlight()", handle_click)
        self.assertIn("setProjectCenterRefreshInFlight(true)", handle_click)
        self.assertIn("setProjectCenterRefreshInFlight(false)", handle_click)
        self.assertIn("finally", handle_click)
        self.assertIn("state.projectCenterRefreshInFlight = Boolean(isInFlight)", set_refresh_in_flight)
        self.assertIn('data-action="refresh-project-center"', set_refresh_in_flight)
        self.assertIn('busyLabel: "刷新中..."', set_refresh_in_flight)
        self.assertIn("projectCenterRefreshIdleLabel", set_refresh_in_flight)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(label) {{
                this.dataset = {{}};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ projectCenterRefreshInFlight: false }};
            const refreshButton = new HTMLButtonElement("刷新项目列表");
            const document = {{
              querySelectorAll(selector) {{
                return selector === '[data-action="refresh-project-center"]' ? [refreshButton] : [];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setProjectCenterRefreshInFlight(isInFlight) {set_refresh_in_flight}
            setProjectCenterRefreshInFlight(true);
            const busy = {{
              inFlight: state.projectCenterRefreshInFlight,
              disabled: refreshButton.disabled,
              text: refreshButton.textContent,
              busy: refreshButton.attrs["aria-busy"],
              ariaDisabled: refreshButton.attrs["aria-disabled"],
              classes: Array.from(refreshButton.classes),
            }};
            setProjectCenterRefreshInFlight(false);
            const idle = {{
              inFlight: state.projectCenterRefreshInFlight,
              disabled: refreshButton.disabled,
              text: refreshButton.textContent,
              busy: refreshButton.attrs["aria-busy"] ?? null,
              ariaDisabled: refreshButton.attrs["aria-disabled"] ?? null,
              classes: Array.from(refreshButton.classes),
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertTrue(payload["busy"]["inFlight"])
        self.assertTrue(payload["busy"]["disabled"])
        self.assertEqual(payload["busy"]["text"], "刷新中...")
        self.assertEqual(payload["busy"]["busy"], "true")
        self.assertEqual(payload["busy"]["ariaDisabled"], "true")
        self.assertIn("is-busy", payload["busy"]["classes"])
        self.assertFalse(payload["idle"]["inFlight"])
        self.assertFalse(payload["idle"]["disabled"])
        self.assertEqual(payload["idle"]["text"], "刷新项目列表")
        self.assertIsNone(payload["idle"]["busy"])
        self.assertIsNone(payload["idle"]["ariaDisabled"])
        self.assertNotIn("is-busy", payload["idle"]["classes"])

    def test_project_open_busy_state_disables_only_target_project(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_project_open_in_flight = _extract_function_source(source, "setProjectOpenInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("const isTarget = typeof options.isTarget", set_action_button_busy_state)
        self.assertIn("state.projectOpenInFlightId", source)
        self.assertIn("正在打开项目，请稍等", source)
        self.assertIn("blockProjectCenterOperationIfInFlight()", handle_click)
        self.assertIn("setProjectOpenInFlight(projectId)", handle_click)
        self.assertIn('setProjectOpenInFlight("")', handle_click)
        self.assertIn("finally", handle_click)
        self.assertIn("state.projectOpenInFlightId = String(projectId ?? \"\").trim()", set_project_open_in_flight)
        self.assertIn('data-action="open-project"', set_project_open_in_flight)
        self.assertIn('busyLabel: "打开中..."', set_project_open_in_flight)
        self.assertIn("projectOpenIdleLabel", set_project_open_in_flight)
        self.assertIn("isTarget: (button) => button.dataset.projectId === state.projectOpenInFlightId", set_project_open_in_flight)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(projectId, label) {{
                this.dataset = {{ projectId }};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ projectOpenInFlightId: "" }};
            const target = new HTMLButtonElement("project-a", "打开这个项目");
            const other = new HTMLButtonElement("project-b", "继续编辑这个项目");
            const document = {{
              querySelectorAll(selector) {{
                return selector === '[data-action="open-project"]' ? [target, other] : [];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setProjectOpenInFlight(projectId) {set_project_open_in_flight}
            setProjectOpenInFlight("project-a");
            const busy = {{
              inFlight: state.projectOpenInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"],
              targetAriaDisabled: target.attrs["aria-disabled"],
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            setProjectOpenInFlight("");
            const idle = {{
              inFlight: state.projectOpenInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"] ?? null,
              targetAriaDisabled: target.attrs["aria-disabled"] ?? null,
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertEqual(payload["busy"]["inFlight"], "project-a")
        self.assertTrue(payload["busy"]["targetDisabled"])
        self.assertEqual(payload["busy"]["targetText"], "打开中...")
        self.assertEqual(payload["busy"]["targetBusy"], "true")
        self.assertEqual(payload["busy"]["targetAriaDisabled"], "true")
        self.assertIn("is-busy", payload["busy"]["targetClasses"])
        self.assertFalse(payload["busy"]["otherDisabled"])
        self.assertEqual(payload["busy"]["otherText"], "继续编辑这个项目")
        self.assertIsNone(payload["busy"]["otherBusy"])
        self.assertEqual(payload["idle"]["inFlight"], "")
        self.assertFalse(payload["idle"]["targetDisabled"])
        self.assertEqual(payload["idle"]["targetText"], "打开这个项目")
        self.assertIsNone(payload["idle"]["targetBusy"])
        self.assertIsNone(payload["idle"]["targetAriaDisabled"])
        self.assertNotIn("is-busy", payload["idle"]["targetClasses"])
        self.assertFalse(payload["idle"]["otherDisabled"])
        self.assertEqual(payload["idle"]["otherText"], "继续编辑这个项目")
        self.assertIsNone(payload["idle"]["otherBusy"])

    def test_project_rename_busy_state_disables_only_target_project(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_project_rename_in_flight = _extract_function_source(source, "setProjectRenameInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("state.projectRenameInFlightId", source)
        self.assertIn("正在修改项目名，请稍等", source)
        self.assertIn("blockProjectCenterOperationIfInFlight()", handle_click)
        self.assertIn("setProjectRenameInFlight(projectId)", handle_click)
        self.assertIn('setProjectRenameInFlight("")', handle_click)
        self.assertIn("finally", handle_click)
        self.assertIn(
            "state.projectRenameInFlightId = String(projectId ?? \"\").trim()",
            set_project_rename_in_flight,
        )
        self.assertIn('data-action="rename-project"', set_project_rename_in_flight)
        self.assertIn('busyLabel: "改名中..."', set_project_rename_in_flight)
        self.assertIn("projectRenameIdleLabel", set_project_rename_in_flight)
        self.assertIn(
            "isTarget: (button) => button.dataset.projectId === state.projectRenameInFlightId",
            set_project_rename_in_flight,
        )
        self.assertIn("button.textContent = busyLabel", set_action_button_busy_state)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(projectId, label) {{
                this.dataset = {{ projectId }};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ projectRenameInFlightId: "" }};
            const target = new HTMLButtonElement("project-a", "改项目名");
            const other = new HTMLButtonElement("project-b", "改项目名");
            const document = {{
              querySelectorAll(selector) {{
                return selector === '[data-action="rename-project"]' ? [target, other] : [];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setProjectRenameInFlight(projectId) {set_project_rename_in_flight}
            setProjectRenameInFlight("project-a");
            const busy = {{
              inFlight: state.projectRenameInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"],
              targetAriaDisabled: target.attrs["aria-disabled"],
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            setProjectRenameInFlight("");
            const idle = {{
              inFlight: state.projectRenameInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"] ?? null,
              targetAriaDisabled: target.attrs["aria-disabled"] ?? null,
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertEqual(payload["busy"]["inFlight"], "project-a")
        self.assertTrue(payload["busy"]["targetDisabled"])
        self.assertEqual(payload["busy"]["targetText"], "改名中...")
        self.assertEqual(payload["busy"]["targetBusy"], "true")
        self.assertEqual(payload["busy"]["targetAriaDisabled"], "true")
        self.assertIn("is-busy", payload["busy"]["targetClasses"])
        self.assertFalse(payload["busy"]["otherDisabled"])
        self.assertEqual(payload["busy"]["otherText"], "改项目名")
        self.assertIsNone(payload["busy"]["otherBusy"])
        self.assertEqual(payload["idle"]["inFlight"], "")
        self.assertFalse(payload["idle"]["targetDisabled"])
        self.assertEqual(payload["idle"]["targetText"], "改项目名")
        self.assertIsNone(payload["idle"]["targetBusy"])
        self.assertIsNone(payload["idle"]["targetAriaDisabled"])
        self.assertNotIn("is-busy", payload["idle"]["targetClasses"])
        self.assertFalse(payload["idle"]["otherDisabled"])
        self.assertEqual(payload["idle"]["otherText"], "改项目名")
        self.assertIsNone(payload["idle"]["otherBusy"])

    def test_project_duplicate_busy_state_disables_only_target_project(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_project_duplicate_in_flight = _extract_function_source(source, "setProjectDuplicateInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("state.projectDuplicateInFlightId", source)
        self.assertIn("正在复制项目，请稍等", source)
        self.assertIn("blockProjectCenterOperationIfInFlight()", handle_click)
        self.assertIn("setProjectDuplicateInFlight(projectId)", handle_click)
        self.assertIn('setProjectDuplicateInFlight("")', handle_click)
        self.assertIn("finally", handle_click)
        self.assertIn(
            "state.projectDuplicateInFlightId = String(projectId ?? \"\").trim()",
            set_project_duplicate_in_flight,
        )
        self.assertIn('data-action="duplicate-project"', set_project_duplicate_in_flight)
        self.assertIn('busyLabel: "复制中..."', set_project_duplicate_in_flight)
        self.assertIn("projectDuplicateIdleLabel", set_project_duplicate_in_flight)
        self.assertIn(
            "isTarget: (button) => button.dataset.projectId === state.projectDuplicateInFlightId",
            set_project_duplicate_in_flight,
        )
        self.assertIn("button.textContent = busyLabel", set_action_button_busy_state)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(projectId, label) {{
                this.dataset = {{ projectId }};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ projectDuplicateInFlightId: "" }};
            const target = new HTMLButtonElement("project-a", "复制项目");
            const other = new HTMLButtonElement("project-b", "复制成正式项目");
            const document = {{
              querySelectorAll(selector) {{
                return selector === '[data-action="duplicate-project"]' ? [target, other] : [];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setProjectDuplicateInFlight(projectId) {set_project_duplicate_in_flight}
            setProjectDuplicateInFlight("project-a");
            const busy = {{
              inFlight: state.projectDuplicateInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"],
              targetAriaDisabled: target.attrs["aria-disabled"],
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            setProjectDuplicateInFlight("");
            const idle = {{
              inFlight: state.projectDuplicateInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"] ?? null,
              targetAriaDisabled: target.attrs["aria-disabled"] ?? null,
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertEqual(payload["busy"]["inFlight"], "project-a")
        self.assertTrue(payload["busy"]["targetDisabled"])
        self.assertEqual(payload["busy"]["targetText"], "复制中...")
        self.assertEqual(payload["busy"]["targetBusy"], "true")
        self.assertEqual(payload["busy"]["targetAriaDisabled"], "true")
        self.assertIn("is-busy", payload["busy"]["targetClasses"])
        self.assertFalse(payload["busy"]["otherDisabled"])
        self.assertEqual(payload["busy"]["otherText"], "复制成正式项目")
        self.assertIsNone(payload["busy"]["otherBusy"])
        self.assertEqual(payload["idle"]["inFlight"], "")
        self.assertFalse(payload["idle"]["targetDisabled"])
        self.assertEqual(payload["idle"]["targetText"], "复制项目")
        self.assertIsNone(payload["idle"]["targetBusy"])
        self.assertIsNone(payload["idle"]["targetAriaDisabled"])
        self.assertNotIn("is-busy", payload["idle"]["targetClasses"])
        self.assertFalse(payload["idle"]["otherDisabled"])
        self.assertEqual(payload["idle"]["otherText"], "复制成正式项目")
        self.assertIsNone(payload["idle"]["otherBusy"])

    def test_project_delete_busy_state_disables_only_target_project(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_project_delete_in_flight = _extract_function_source(source, "setProjectDeleteInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("state.projectDeleteInFlightId", source)
        self.assertIn("正在删除项目，请稍等", source)
        self.assertIn("blockProjectCenterOperationIfInFlight()", handle_click)
        self.assertIn("setProjectDeleteInFlight(projectId)", handle_click)
        self.assertIn('setProjectDeleteInFlight("")', handle_click)
        self.assertIn("finally", handle_click)
        self.assertIn(
            "state.projectDeleteInFlightId = String(projectId ?? \"\").trim()",
            set_project_delete_in_flight,
        )
        self.assertIn('data-action="delete-project"', set_project_delete_in_flight)
        self.assertIn('busyLabel: "删除中..."', set_project_delete_in_flight)
        self.assertIn("projectDeleteIdleLabel", set_project_delete_in_flight)
        self.assertIn(
            "isTarget: (button) => button.dataset.projectId === state.projectDeleteInFlightId",
            set_project_delete_in_flight,
        )
        self.assertIn("button.textContent = busyLabel", set_action_button_busy_state)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(projectId, label) {{
                this.dataset = {{ projectId }};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ projectDeleteInFlightId: "" }};
            const target = new HTMLButtonElement("project-a", "删除项目");
            const other = new HTMLButtonElement("project-b", "删除项目");
            const document = {{
              querySelectorAll(selector) {{
                return selector === '[data-action="delete-project"]' ? [target, other] : [];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setProjectDeleteInFlight(projectId) {set_project_delete_in_flight}
            setProjectDeleteInFlight("project-a");
            const busy = {{
              inFlight: state.projectDeleteInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"],
              targetAriaDisabled: target.attrs["aria-disabled"],
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            setProjectDeleteInFlight("");
            const idle = {{
              inFlight: state.projectDeleteInFlightId,
              targetDisabled: target.disabled,
              targetText: target.textContent,
              targetBusy: target.attrs["aria-busy"] ?? null,
              targetAriaDisabled: target.attrs["aria-disabled"] ?? null,
              targetClasses: Array.from(target.classes),
              otherDisabled: other.disabled,
              otherText: other.textContent,
              otherBusy: other.attrs["aria-busy"] ?? null,
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertEqual(payload["busy"]["inFlight"], "project-a")
        self.assertTrue(payload["busy"]["targetDisabled"])
        self.assertEqual(payload["busy"]["targetText"], "删除中...")
        self.assertEqual(payload["busy"]["targetBusy"], "true")
        self.assertEqual(payload["busy"]["targetAriaDisabled"], "true")
        self.assertIn("is-busy", payload["busy"]["targetClasses"])
        self.assertFalse(payload["busy"]["otherDisabled"])
        self.assertEqual(payload["busy"]["otherText"], "删除项目")
        self.assertIsNone(payload["busy"]["otherBusy"])
        self.assertEqual(payload["idle"]["inFlight"], "")
        self.assertFalse(payload["idle"]["targetDisabled"])
        self.assertEqual(payload["idle"]["targetText"], "删除项目")
        self.assertIsNone(payload["idle"]["targetBusy"])
        self.assertIsNone(payload["idle"]["targetAriaDisabled"])
        self.assertNotIn("is-busy", payload["idle"]["targetClasses"])
        self.assertFalse(payload["idle"]["otherDisabled"])
        self.assertEqual(payload["idle"]["otherText"], "删除项目")
        self.assertIsNone(payload["idle"]["otherBusy"])

    def test_blank_project_dashboard_promotes_first_chapter_action(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        render_dashboard = _extract_function_source(source, "renderDashboard")
        render_dashboard_actions = _extract_function_source(source, "renderDashboardPrimaryActions")

        self.assertIn("renderDashboardPrimaryActions(isBlankProject)", render_dashboard)
        self.assertIn('data-action="create-first-chapter"', render_dashboard_actions)
        self.assertIn('data-action="create-first-chapter-custom"', render_dashboard_actions)
        self.assertIn('data-step-index="1"', render_dashboard_actions)
        self.assertIn('data-action="switch-screen" data-screen="story"', render_dashboard_actions)

        script = textwrap.dedent(
            f"""
            const state = {{ chapterCreateInFlight: false }};
            function renderDashboardPrimaryActions(isBlankProject) {render_dashboard_actions}
            const blankMarkup = renderDashboardPrimaryActions(true);
            const activeMarkup = renderDashboardPrimaryActions(false);
            state.chapterCreateInFlight = true;
            const busyBlankMarkup = renderDashboardPrimaryActions(true);
            process.stdout.write(JSON.stringify({{ blankMarkup, activeMarkup, busyBlankMarkup }}));
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
        self.assertIn("创建第一章和第一场", payload["blankMarkup"])
        self.assertIn('data-action="create-first-chapter"', payload["blankMarkup"])
        self.assertIn('data-action="create-first-chapter-custom"', payload["blankMarkup"])
        self.assertIn('data-action="open-beginner-tutorial"', payload["blankMarkup"])
        self.assertIn('data-step-index="1"', payload["blankMarkup"])
        self.assertNotIn('data-screen="story"', payload["blankMarkup"])
        self.assertNotIn('aria-busy="true"', payload["blankMarkup"])
        self.assertIn('aria-busy="true"', payload["busyBlankMarkup"])
        self.assertIn('disabled aria-disabled="true"', payload["busyBlankMarkup"])
        self.assertIn("进入剧情编辑", payload["activeMarkup"])
        self.assertIn('data-action="switch-screen" data-screen="story"', payload["activeMarkup"])
        self.assertIn("查看试玩页", payload["activeMarkup"])
        self.assertIn("打开素材页", payload["activeMarkup"])
        self.assertNotIn('data-action="create-first-chapter"', payload["activeMarkup"])

    def test_create_chapter_ignores_duplicate_clicks_while_pending(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        create_chapter = _extract_function_source(source, "createChapter")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_chapter_create_in_flight = _extract_function_source(source, "setChapterCreateInFlight")

        self.assertIn("state.chapterCreateInFlight", source)
        self.assertIn("正在创建章节，请稍等", create_chapter)
        self.assertIn("setChapterCreateInFlight(true)", create_chapter)
        self.assertIn("setChapterCreateInFlight(false)", create_chapter)
        self.assertIn("state.chapterCreateInFlight = Boolean(isInFlight)", set_chapter_create_in_flight)
        self.assertIn('busyLabel: "创建中..."', set_chapter_create_in_flight)
        self.assertIn('button.setAttribute("aria-busy", "true")', set_action_button_busy_state)
        self.assertIn("finally", create_chapter)

        script = textwrap.dedent(
            f"""
            const API_CREATE_CHAPTER = "/api/create-chapter";
            const state = {{
              data: {{ chapters: [], scenes: [] }},
              chapterCreateInFlight: false,
            }};
            const statuses = [];
            const toasts = [];
            const reloads = [];
            let postCount = 0;
            function setSaveStatus(message, isError = false) {{
              statuses.push({{ message, isError }});
            }}
            function showToast(message) {{
              toasts.push(message);
            }}
            function getCurrentUiState() {{
              return {{ selectedSceneId: null, selectedBlockId: null }};
            }}
            async function reloadProjectData(payload) {{
              reloads.push(payload);
            }}
            function switchScreen(screen) {{
              statuses.push({{ message: `screen:${{screen}}`, isError: false }});
            }}
            async function showEditorOperationFailure(error) {{
              throw error;
            }}
            async function promptForText() {{
              throw new Error("skipPrompts should avoid prompts");
            }}
            async function postJson(url, payload) {{
              postCount += 1;
              await new Promise((resolve) => setTimeout(resolve, 20));
              return {{
                sceneId: "scene-1",
                scene: {{ blocks: [{{ id: "block-1" }}] }},
                payload,
              }};
            }}
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setChapterCreateInFlight(isInFlight) {set_chapter_create_in_flight}
            async function createChapter(options = {{}}) {create_chapter}
            Promise.all([
              createChapter({{ skipPrompts: true, defaultChapterName: "第一章 开场", defaultSceneName: "第一场 相遇", afterCreateScreen: "story" }}),
              createChapter({{ skipPrompts: true, defaultChapterName: "第一章 开场", defaultSceneName: "第一场 相遇", afterCreateScreen: "story" }}),
            ]).then(() => {{
              process.stdout.write(JSON.stringify({{
                postCount,
                statuses,
                toasts,
                reloads,
                inFlight: state.chapterCreateInFlight,
              }}));
            }}).catch((error) => {{
              console.error(error);
              process.exit(1);
            }});
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
        self.assertEqual(payload["postCount"], 1)
        self.assertFalse(payload["inFlight"])
        self.assertEqual(len(payload["reloads"]), 1)
        self.assertIn("正在创建章节，请稍等...", [status["message"] for status in payload["statuses"]])
        self.assertIn("正在创建章节，请稍等...", payload["toasts"])

    def test_chapter_create_busy_state_disables_visible_buttons(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        set_action_button_busy_state = _extract_function_source(source, "setActionButtonBusyState")
        set_chapter_create_in_flight = _extract_function_source(source, "setChapterCreateInFlight")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".toolbar-button.is-busy", style_source)
        self.assertIn("querySelectorAll", set_action_button_busy_state)
        self.assertIn('data-action="create-first-chapter"', set_chapter_create_in_flight)
        self.assertIn("chapterCreateIdleLabel", set_chapter_create_in_flight)
        self.assertIn("classList.add(\"is-busy\")", set_action_button_busy_state)
        self.assertIn("classList.remove(\"is-busy\")", set_action_button_busy_state)

        script = textwrap.dedent(
            f"""
            class HTMLButtonElement {{
              constructor(action, label) {{
                this.dataset = {{ action }};
                this.textContent = label;
                this.disabled = false;
                this.attrs = {{}};
                this.classes = new Set();
                this.classList = {{
                  add: (name) => this.classes.add(name),
                  remove: (name) => this.classes.delete(name),
                }};
              }}
              setAttribute(name, value) {{
                this.attrs[name] = value;
              }}
              removeAttribute(name) {{
                delete this.attrs[name];
              }}
            }}
            const state = {{ chapterCreateInFlight: false }};
            const direct = new HTMLButtonElement("create-first-chapter", "创建第一章和第一场");
            const custom = new HTMLButtonElement("create-first-chapter-custom", "自定义名字再创建");
            const document = {{
              querySelectorAll(selector) {{
                return [direct, custom];
              }},
            }};
            function setActionButtonBusyState(options = {{}}) {set_action_button_busy_state}
            function setChapterCreateInFlight(isInFlight) {set_chapter_create_in_flight}
            setChapterCreateInFlight(true);
            const busy = {{
              inFlight: state.chapterCreateInFlight,
              directDisabled: direct.disabled,
              directText: direct.textContent,
              customText: custom.textContent,
              directBusy: direct.attrs["aria-busy"],
              directClass: Array.from(direct.classes),
            }};
            setChapterCreateInFlight(false);
            const idle = {{
              inFlight: state.chapterCreateInFlight,
              directDisabled: direct.disabled,
              directText: direct.textContent,
              customText: custom.textContent,
              directBusy: direct.attrs["aria-busy"] ?? null,
              directClass: Array.from(direct.classes),
            }};
            process.stdout.write(JSON.stringify({{ busy, idle }}));
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
        self.assertTrue(payload["busy"]["inFlight"])
        self.assertTrue(payload["busy"]["directDisabled"])
        self.assertEqual(payload["busy"]["directText"], "创建中...")
        self.assertEqual(payload["busy"]["customText"], "创建中...")
        self.assertEqual(payload["busy"]["directBusy"], "true")
        self.assertIn("is-busy", payload["busy"]["directClass"])
        self.assertFalse(payload["idle"]["inFlight"])
        self.assertFalse(payload["idle"]["directDisabled"])
        self.assertEqual(payload["idle"]["directText"], "创建第一章和第一场")
        self.assertEqual(payload["idle"]["customText"], "自定义名字再创建")
        self.assertIsNone(payload["idle"]["directBusy"])
        self.assertNotIn("is-busy", payload["idle"]["directClass"])

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

    def test_starter_kit_success_message_mentions_first_scene_bootstrap(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        create_starter_kit = _extract_function_source(source, "createStarterKit")

        self.assertIn("const bootstrap = result.sceneBootstrap ?? {}", create_starter_kit)
        self.assertIn("const insertedBlockIds = Array.isArray(bootstrap.insertedBlockIds)", create_starter_kit)
        self.assertIn("selectedSceneId: bootstrap.sceneId ?? state.selectedSceneId", create_starter_kit)
        self.assertIn("selectedBlockId: insertedBlockIds[0] ?? state.selectedBlockId", create_starter_kit)
        self.assertIn("previewStartSceneId: bootstrap.sceneId ?? state.previewStartSceneId", create_starter_kit)
        self.assertIn("const insertedLabels = Array.isArray(bootstrap.insertedLabels)", create_starter_kit)
        self.assertIn("const createdAssets = Array.isArray(result.createdAssets)", create_starter_kit)
        self.assertIn("readyPlaceholderAssets.length", create_starter_kit)
        self.assertIn("可替换占位素材已生成，可直接试玩和导出", create_starter_kit)
        self.assertIn("bootstrap.applied && insertedLabels.length > 0", create_starter_kit)
        self.assertIn("并已接入${sceneLabel}", create_starter_kit)
        self.assertIn("insertedLabels.join", create_starter_kit)

    def test_starter_kit_success_message_only_promises_ready_placeholder_assets(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        create_starter_kit = _extract_function_source(source, "createStarterKit")
        script = textwrap.dedent(
            f"""
            const createStarterKit = eval(
              "(async function createStarterKit(options = {{}}) " + {json.dumps(create_starter_kit)} + ")"
            );

            const saveStatuses = [];
            const toasts = [];
            const reloads = [];
            let backendResult = null;

            const API_CREATE_STARTER_KIT = "/api/create-starter-kit";
            const state = {{
              selectedSceneId: "old_scene",
              selectedBlockId: "old_block",
              previewSceneId: "old_preview",
              previewStartSceneId: "old_start",
              selectedCharacterId: "old_character",
            }};

            function getStarterKitOverview() {{
              return {{ needsStarterKit: true, missingCharacter: false, missingBackground: false, missingBgm: false }};
            }}

            function getStarterKitDefaults() {{
              return {{ characterName: "女主角", backgroundName: "第一场背景", bgmName: "开场 BGM" }};
            }}

            async function promptForText() {{
              throw new Error("prompt should be skipped");
            }}

            async function postJson(url, payload) {{
              if (url !== API_CREATE_STARTER_KIT) {{
                throw new Error(`unexpected url ${{url}}`);
              }}
              return backendResult;
            }}

            function getCurrentUiState() {{
              return {{ keep: "ui" }};
            }}

            async function reloadProjectData(nextState) {{
              reloads.push(nextState);
            }}

            function setSaveStatus(message) {{
              saveStatuses.push(message);
            }}

            function showToast(message, type) {{
              toasts.push({{ message, type: type ?? null }});
            }}

            async function showEditorOperationFailure(error) {{
              throw error;
            }}

            async function runCase(createdAssets) {{
              saveStatuses.length = 0;
              toasts.length = 0;
              reloads.length = 0;
              backendResult = {{
                createdLabels: ["第一个角色", "第一张背景"],
                createdAssets,
                createdCharacter: {{ id: "char_hero" }},
                sceneBootstrap: {{
                  applied: true,
                  sceneId: "scene_intro",
                  sceneName: "开场",
                  insertedBlockIds: ["block_bgm"],
                  insertedLabels: ["BGM 卡片"],
                }},
              }};
              await createStarterKit({{ skipPrompts: true }});
              return {{
                finalStatus: saveStatuses.at(-1),
                toast: toasts.at(-1)?.message,
                reload: reloads.at(-1),
              }};
            }}

            (async () => {{
              const ready = await runCase([
                {{ fileExists: true, tags: ["占位素材", "可替换"] }},
                {{ fileExists: true, tags: ["占位素材"] }},
                {{ fileExists: false, tags: ["占位素材"] }},
                {{ fileExists: true, tags: ["正式素材"] }},
              ]);
              if (!ready.finalStatus.includes("2 个可替换占位素材已生成，可直接试玩和导出")) {{
                throw new Error(`ready placeholder summary missing: ${{ready.finalStatus}}`);
              }}
              if (ready.toast !== ready.finalStatus) {{
                throw new Error("toast and save status should match");
              }}
              if (ready.reload.selectedSceneId !== "scene_intro" || ready.reload.selectedBlockId !== "block_bgm") {{
                throw new Error("starter kit should focus the bootstrapped scene and first inserted block");
              }}

              const notReady = await runCase([
                {{ fileExists: false, tags: ["占位素材"] }},
                {{ fileExists: true, tags: ["正式素材"] }},
              ]);
              if (notReady.finalStatus.includes("可直接试玩和导出")) {{
                throw new Error(`non-ready assets should not be promised as playable: ${{notReady.finalStatus}}`);
              }}
              console.log(JSON.stringify({{ ready: ready.finalStatus, notReady: notReady.finalStatus }}));
            }})().catch((error) => {{
              console.error(error.stack || error.message);
              process.exit(1);
            }});
            """
        )
        completed = subprocess.run(["node", "-e", script], text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("可直接试玩和导出", payload["ready"])
        self.assertNotIn("可直接试玩和导出", payload["notReady"])

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

    def test_openai_asset_generation_has_busy_guard(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        handle_change = _extract_function_source(source, "handleChange")
        handle_input = _extract_function_source(source, "handleInput")
        is_openai_asset_generation_field_id = _extract_function_source(
            source,
            "isOpenAiAssetGenerationFieldId",
        )
        compatibility_warning = _extract_function_source(
            source,
            "getOpenAiAssetGenerationCompatibilityWarning",
        )
        prompt_length_warning = _extract_function_source(
            source,
            "getOpenAiAssetPromptLengthWarning",
        )
        built_in_prompt_sample = _extract_function_source(
            source,
            "isOpenAiAssetBuiltInPromptSample",
        )
        model_warning = _extract_function_source(
            source,
            "getOpenAiAssetModelWarning",
        )
        sync_prompt_length_status = _extract_function_source(
            source,
            "syncOpenAiAssetPromptLengthStatus",
        )
        sync_style_hint_length_status = _extract_function_source(
            source,
            "syncOpenAiAssetStyleHintLengthStatus",
        )
        generate_openai_asset = _extract_function_source(source, "generateOpenAiAsset")
        forget_openai_asset_key = _extract_function_source(source, "forgetOpenAiAssetKey")

        self.assertIn('"openAiAssetPrompt"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetApiKey"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetStyleHint"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetBindCharacterId"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetBindExpressionId"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetBindExpressionName"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetBindAsDefaultSprite"', is_openai_asset_generation_field_id)
        self.assertIn('"openAiAssetOutputFormat"', is_openai_asset_generation_field_id)
        self.assertIn("OPENAI_ASSET_GENERATION_TYPES", built_in_prompt_sample)
        self.assertIn("getOpenAiAssetPromptSample(assetType)", built_in_prompt_sample)
        self.assertIn("提示词超过 ${info.max} 字，请缩短后再生成。", prompt_length_warning)
        self.assertIn("模型名只能包含英文字母、数字、点、下划线、冒号或短横线", model_warning)
        self.assertIn("/^[A-Za-z0-9._:-]+$/.test(value)", model_warning)
        self.assertIn('document.getElementById("openAiAssetPromptLengthStatus")', sync_prompt_length_status)
        self.assertIn("status.classList.toggle", sync_prompt_length_status)
        self.assertIn('document.getElementById("openAiAssetStyleHintLengthStatus")', sync_style_hint_length_status)
        self.assertIn("getOpenAiAssetStyleHintLengthWarning()", sync_style_hint_length_status)
        self.assertIn("status.classList.toggle", sync_style_hint_length_status)
        self.assertIn("openAiAssetBackground === \"transparent\"", compatibility_warning)
        self.assertIn("openAiAssetOutputFormat === \"jpeg\"", compatibility_warning)
        self.assertIn("if (state.openAiAssetLoading)", generate_openai_asset)
        self.assertIn('setSaveStatus("AI 素材正在生成，请稍等...")', generate_openai_asset)
        self.assertIn('showToast("AI 素材正在生成，请稍等...")', generate_openai_asset)
        self.assertLess(
            generate_openai_asset.index("if (state.openAiAssetLoading)"),
            generate_openai_asset.index('document.getElementById("openAiAssetType")'),
        )
        self.assertIn("const compatibilityWarning = getOpenAiAssetGenerationCompatibilityWarning()", generate_openai_asset)
        self.assertIn('showToast("生图格式和背景不兼容", "error")', generate_openai_asset)
        self.assertLess(
            generate_openai_asset.index("const compatibilityWarning = getOpenAiAssetGenerationCompatibilityWarning()"),
            generate_openai_asset.index("if (!state.openAiAssetPrompt.trim())"),
        )
        self.assertLess(
            generate_openai_asset.index("const compatibilityWarning = getOpenAiAssetGenerationCompatibilityWarning()"),
            generate_openai_asset.index("postJson("),
        )
        self.assertIn("const modelWarning = getOpenAiAssetModelWarning(state.openAiAssetModel)", generate_openai_asset)
        self.assertIn('showToast("生图模型名不合法", "error")', generate_openai_asset)
        self.assertLess(
            generate_openai_asset.index("const modelWarning = getOpenAiAssetModelWarning(state.openAiAssetModel)"),
            generate_openai_asset.index("const promptLengthWarning = getOpenAiAssetPromptLengthWarning(state.openAiAssetPrompt)"),
        )
        self.assertLess(
            generate_openai_asset.index("const modelWarning = getOpenAiAssetModelWarning(state.openAiAssetModel)"),
            generate_openai_asset.index("postJson("),
        )
        self.assertIn("const promptLengthWarning = getOpenAiAssetPromptLengthWarning(state.openAiAssetPrompt)", generate_openai_asset)
        self.assertIn('showToast("生图提示词太长", "error")', generate_openai_asset)
        self.assertIn('document.getElementById("openAiAssetStyleHint")', generate_openai_asset)
        self.assertIn("styleHint: state.openAiAssetStyleHint", generate_openai_asset)
        self.assertIn('document.getElementById("openAiAssetBindCharacterId")', generate_openai_asset)
        self.assertIn('document.getElementById("openAiAssetBindExpressionId")', generate_openai_asset)
        self.assertIn('document.getElementById("openAiAssetBindExpressionName")', generate_openai_asset)
        self.assertIn('document.getElementById("openAiAssetBindAsDefaultSprite")', generate_openai_asset)
        self.assertIn("const styleHintLengthWarning = getOpenAiAssetStyleHintLengthWarning(state.openAiAssetStyleHint)", generate_openai_asset)
        self.assertIn('showToast("生图画风补充太长", "error")', generate_openai_asset)
        self.assertLess(
            generate_openai_asset.index("const promptLengthWarning = getOpenAiAssetPromptLengthWarning(state.openAiAssetPrompt)"),
            generate_openai_asset.index("const styleHintLengthWarning = getOpenAiAssetStyleHintLengthWarning(state.openAiAssetStyleHint)"),
        )
        self.assertLess(
            generate_openai_asset.index("const styleHintLengthWarning = getOpenAiAssetStyleHintLengthWarning(state.openAiAssetStyleHint)"),
            generate_openai_asset.index("if (!state.openAiAssetApiKey.trim())"),
        )
        self.assertLess(
            generate_openai_asset.index("const styleHintLengthWarning = getOpenAiAssetStyleHintLengthWarning(state.openAiAssetStyleHint)"),
            generate_openai_asset.index("postJson("),
        )
        self.assertIn("characterBinding:", generate_openai_asset)
        self.assertIn("state.openAiAssetType === \"sprite\" && state.openAiAssetBindCharacterId", generate_openai_asset)
        self.assertIn("expressionId: state.openAiAssetBindExpressionId", generate_openai_asset)
        self.assertIn("setAsDefaultSprite: state.openAiAssetBindAsDefaultSprite", generate_openai_asset)
        self.assertIn("const binding = result.characterBinding", generate_openai_asset)
        self.assertIn("已生成并绑定角色", generate_openai_asset)
        self.assertIn('action === "apply-openai-asset-prompt-sample"', handle_click)
        self.assertIn('action === "apply-openai-asset-style-preset"', handle_click)
        self.assertIn("getOpenAiAssetStyleHintPreset", handle_click)
        self.assertIn("state.openAiAssetStyleHint = preset.value", handle_click)
        self.assertIn("已套用 AI 生图画风", handle_click)
        self.assertIn('action === "apply-openai-asset-expression-preset"', handle_click)
        self.assertIn("getOpenAiAssetExpressionBindPreset", handle_click)
        self.assertIn("state.openAiAssetBindExpressionId = preset.id", handle_click)
        self.assertIn("state.openAiAssetBindExpressionName = preset.name", handle_click)
        self.assertIn("已套用绑定表情", handle_click)
        self.assertIn("if (state.openAiAssetLoading)", handle_click)
        self.assertLess(
            handle_click.index('action === "apply-openai-asset-prompt-sample"'),
            handle_click.index('action === "apply-openai-asset-style-preset"'),
        )
        self.assertLess(
            handle_click.index('action === "apply-openai-asset-style-preset"'),
            handle_click.index('action === "apply-openai-asset-expression-preset"'),
        )
        self.assertLess(
            handle_click.index('action === "apply-openai-asset-expression-preset"'),
            handle_click.index('action === "generate-openai-asset"'),
        )
        self.assertIn('action === "forget-openai-asset-key"', handle_click)
        self.assertIn("forgetOpenAiAssetKey()", handle_click)
        self.assertLess(
            handle_click.index('action === "forget-openai-asset-key"'),
            handle_click.index('action === "generate-openai-asset"'),
        )
        self.assertIn("if (state.openAiAssetLoading)", forget_openai_asset_key)
        self.assertIn('state.openAiAssetApiKey = ""', forget_openai_asset_key)
        self.assertIn('state.openAiAssetError = ""', forget_openai_asset_key)
        self.assertIn('setSaveStatus("已清空本次 AI 生图 Key")', forget_openai_asset_key)
        self.assertIn("state.openAiAssetLoading && isOpenAiAssetGenerationFieldId(target.id)", handle_change)
        self.assertIn("state.openAiAssetLoading && isOpenAiAssetGenerationFieldId(event.target.id)", handle_input)
        self.assertIn("syncOpenAiAssetPromptLengthStatus()", handle_input)
        self.assertIn('event.target.id === "openAiAssetStyleHint"', handle_input)
        self.assertIn('state.openAiAssetStyleHint = event.target.value ?? ""', handle_input)
        self.assertIn("syncOpenAiAssetStyleHintLengthStatus()", handle_input)
        self.assertIn('event.target.id === "openAiAssetBindExpressionId"', handle_input)
        self.assertIn('event.target.id === "openAiAssetBindExpressionName"', handle_input)
        self.assertIn('target.id === "openAiAssetBindCharacterId"', handle_change)
        self.assertIn('target.id === "openAiAssetBindAsDefaultSprite"', handle_change)
        self.assertIn("const shouldRefreshPromptSample = isOpenAiAssetBuiltInPromptSample(state.openAiAssetPrompt)", handle_change)
        self.assertIn("if (shouldRefreshPromptSample)", handle_change)
        self.assertLess(
            handle_change.index("state.openAiAssetLoading && isOpenAiAssetGenerationFieldId(target.id)"),
            handle_change.index('target.id === "openAiAssetType"'),
        )
        self.assertLess(
            handle_input.index("state.openAiAssetLoading && isOpenAiAssetGenerationFieldId(event.target.id)"),
            handle_input.index('event.target.id === "openAiAssetPrompt"'),
        )

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
        self.assertIn("这个入口当前无法执行", source)
        self.assertNotIn("按钮暂未接线", source)
        self.assertNotIn("这个按钮暂时还没有接上功能", source)
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

    def test_beginner_tutorial_dialog_keeps_keyboard_navigation(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        index_source = INDEX_PATH.read_text(encoding="utf-8")
        style_source = (EDITOR_DIR / "styles.css").read_text(encoding="utf-8")
        open_tutorial = _extract_function_source(source, "openBeginnerTutorial")
        set_step = _extract_function_source(source, "setBeginnerTutorialStep")
        focus_tutorial = _extract_function_source(source, "focusBeginnerTutorialDialog")
        step_keyboard = _extract_function_source(source, "handleBeginnerTutorialStepKeyboardNavigation")
        focusable_elements = _extract_function_source(source, "getBeginnerTutorialFocusableElements")
        dialog_tab = _extract_function_source(source, "handleBeginnerTutorialDialogTab")
        keydown_handler = _extract_function_source(source, "handleGlobalKeydown")

        self.assertIn('aria-labelledby="beginnerTutorialTitle"', index_source)
        self.assertIn('tabindex="-1"', index_source)
        self.assertIn("focusBeginnerTutorialDialog()", open_tutorial)
        self.assertIn("focusBeginnerTutorialDialog()", set_step)
        self.assertIn(".beginner-tutorial-step-button.is-active", focus_tutorial)
        self.assertIn('[data-action="close-beginner-tutorial"]', focus_tutorial)
        self.assertIn('[role="dialog"]', focus_tutorial)
        self.assertIn("preventScroll: true", focus_tutorial)
        self.assertIn("requestAnimationFrame", focus_tutorial)
        self.assertIn('"ArrowUp"', step_keyboard)
        self.assertIn('"ArrowDown"', step_keyboard)
        self.assertIn('"Home"', step_keyboard)
        self.assertIn('"End"', step_keyboard)
        self.assertIn("setBeginnerTutorialStep(nextIndex)", step_keyboard)
        self.assertIn("button:not(:disabled)", focusable_elements)
        self.assertIn("focusableElements.length <= 0", dialog_tab)
        self.assertIn("focusableElements.indexOf(activeElement)", dialog_tab)
        self.assertIn("preventScroll: true", dialog_tab)
        self.assertIn("handleBeginnerTutorialStepKeyboardNavigation(event)", keydown_handler)
        self.assertIn("handleBeginnerTutorialDialogTab(event)", keydown_handler)
        self.assertIn('event.code === "Tab"', keydown_handler)
        self.assertIn(".beginner-tutorial-step-button:focus-visible", style_source)

        script = textwrap.dedent(
            f"""
            const state = {{ beginnerTutorialOpen: true }};
            const systemDialogController = null;
            const calls = [];
            const navCalls = [];
            const tabCalls = [];
            function closeBeginnerTutorial() {{
              calls.push("close");
            }}
            function handleBeginnerTutorialStepKeyboardNavigation(event) {{
              navCalls.push(event.code);
              if (event.code === "ArrowDown") {{
                event.preventDefault();
                return true;
              }}
              return false;
            }}
            function handleBeginnerTutorialDialogTab(event) {{
              tabCalls.push(event.code);
              return false;
            }}
            function handleCommandPaletteKeydown() {{
              return false;
            }}
            function isKeyboardTypingTarget(target) {{
              return Boolean(target?.isTypingTarget);
            }}
            function handleCharacterStageKeyboardNudge() {{
              throw new Error("tutorial keyboard guard should stop before stage shortcuts");
            }}
            function handleGlobalKeydown(event) {keydown_handler}
            const makeEvent = (code, target = {{}}) => ({{
              code,
              target,
              prevented: false,
              preventDefault() {{
                this.prevented = true;
              }},
            }});
            const tabEvent = makeEvent("Tab");
            const letterEvent = makeEvent("KeyA");
            const arrowEvent = makeEvent("ArrowDown");
            const escapeEvent = makeEvent("Escape");
            handleGlobalKeydown(tabEvent);
            handleGlobalKeydown(letterEvent);
            handleGlobalKeydown(arrowEvent);
            handleGlobalKeydown(escapeEvent);
            process.stdout.write(JSON.stringify({{
              tabPrevented: tabEvent.prevented,
              letterPrevented: letterEvent.prevented,
              arrowPrevented: arrowEvent.prevented,
              escapePrevented: escapeEvent.prevented,
              calls,
              navCalls,
              tabCalls,
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
        self.assertFalse(payload["tabPrevented"])
        self.assertTrue(payload["letterPrevented"])
        self.assertTrue(payload["arrowPrevented"])
        self.assertTrue(payload["escapePrevented"])
        self.assertEqual(payload["calls"], ["close"])
        self.assertEqual(payload["navCalls"], ["Tab", "KeyA", "ArrowDown"])
        self.assertEqual(payload["tabCalls"], ["Tab", "KeyA"])

        script = textwrap.dedent(
            f"""
            class HTMLElement {{}}
            const calls = [];
            const state = {{ beginnerTutorialOpen: true }};
            const steps = [{{}}, {{}}, {{}}];
            const refs = {{
              beginnerTutorialStepList: {{
                contains(node) {{
                  return Boolean(node?.inStepList);
                }},
              }},
            }};
            const beginnerTutorialTools = {{
              clampBeginnerTutorialStepIndex(value, items) {{
                return Math.min(Math.max(Number.parseInt(value ?? "0", 10) || 0, 0), items.length - 1);
              }},
            }};
            function getBeginnerTutorialSteps() {{
              return steps;
            }}
            function setBeginnerTutorialStep(index) {{
              calls.push({{ type: "set", index }});
            }}
            class StepButton extends HTMLElement {{
              constructor(index) {{
                super();
                this.dataset = {{ stepIndex: String(index) }};
                this.inStepList = true;
              }}
              closest(selector) {{
                return selector === ".beginner-tutorial-step-button" ? this : null;
              }}
            }}
            function makeEvent(code, index = 1) {{
              return {{
                code,
                target: new StepButton(index),
                prevented: false,
                preventDefault() {{
                  this.prevented = true;
                }},
              }};
            }}
            function handleBeginnerTutorialStepKeyboardNavigation(event) {step_keyboard}
            const down = makeEvent("ArrowDown", 1);
            const up = makeEvent("ArrowUp", 1);
            const home = makeEvent("Home", 2);
            const end = makeEvent("End", 0);
            const enter = makeEvent("Enter", 1);
            const results = [down, up, home, end, enter].map((event) => ({{
              code: event.code,
              handled: handleBeginnerTutorialStepKeyboardNavigation(event),
              prevented: event.prevented,
            }}));
            process.stdout.write(JSON.stringify({{ results, calls }}));
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
        self.assertEqual(
            payload["results"],
            [
                {"code": "ArrowDown", "handled": True, "prevented": True},
                {"code": "ArrowUp", "handled": True, "prevented": True},
                {"code": "Home", "handled": True, "prevented": True},
                {"code": "End", "handled": True, "prevented": True},
                {"code": "Enter", "handled": False, "prevented": False},
            ],
        )
        self.assertEqual(
            payload["calls"],
            [
                {"type": "set", "index": 2},
                {"type": "set", "index": 0},
                {"type": "set", "index": 0},
                {"type": "set", "index": 2},
            ],
        )

        script = textwrap.dedent(
            f"""
            class HTMLElement {{}}
            const state = {{ beginnerTutorialOpen: true }};
            const focusCalls = [];
            const root = {{
              focus(options) {{
                focusCalls.push({{ type: "root", options }});
              }},
              querySelectorAll() {{
                return elements;
              }},
            }};
            const refs = {{
              beginnerTutorialDialog: {{
                querySelector(selector) {{
                  return selector === ".beginner-tutorial-dialog" ? root : null;
                }},
              }},
            }};
            class FocusableElement extends HTMLElement {{
              constructor(id, options = {{}}) {{
                super();
                this.id = id;
                this.hidden = Boolean(options.hidden);
                this.disabled = Boolean(options.disabled);
                this.tabIndex = options.tabIndex ?? 0;
                this.ariaHidden = options.ariaHidden ?? "false";
              }}
              getAttribute(name) {{
                return name === "aria-hidden" ? this.ariaHidden : null;
              }}
              focus(options) {{
                document.activeElement = this;
                focusCalls.push({{ type: "focus", id: this.id, options }});
              }}
            }}
            const first = new FocusableElement("first");
            const middle = new FocusableElement("middle");
            const last = new FocusableElement("last");
            const hidden = new FocusableElement("hidden", {{ hidden: true }});
            const disabled = new FocusableElement("disabled", {{ disabled: true }});
            const elements = [first, hidden, middle, disabled, last];
            const document = {{ activeElement: first }};
            function getBeginnerTutorialFocusableElements() {focusable_elements}
            function handleBeginnerTutorialDialogTab(event) {dialog_tab}
            function makeTabEvent(options = {{}}) {{
              return {{
                code: "Tab",
                shiftKey: Boolean(options.shiftKey),
                prevented: false,
                preventDefault() {{
                  this.prevented = true;
                }},
              }};
            }}
            const shiftFromFirst = makeTabEvent({{ shiftKey: true }});
            const handledShiftFromFirst = handleBeginnerTutorialDialogTab(shiftFromFirst);
            const shiftFromFirstResult = {{
              handled: handledShiftFromFirst,
              prevented: shiftFromFirst.prevented,
              active: document.activeElement.id,
            }};
            document.activeElement = last;
            const tabFromLast = makeTabEvent();
            const handledTabFromLast = handleBeginnerTutorialDialogTab(tabFromLast);
            const tabFromLastResult = {{
              handled: handledTabFromLast,
              prevented: tabFromLast.prevented,
              active: document.activeElement.id,
            }};
            document.activeElement = middle;
            const tabFromMiddle = makeTabEvent();
            const handledTabFromMiddle = handleBeginnerTutorialDialogTab(tabFromMiddle);
            const tabFromMiddleResult = {{
              handled: handledTabFromMiddle,
              prevented: tabFromMiddle.prevented,
              active: document.activeElement.id,
            }};
            document.activeElement = new FocusableElement("outside");
            const tabFromOutside = makeTabEvent();
            const handledTabFromOutside = handleBeginnerTutorialDialogTab(tabFromOutside);
            const tabFromOutsideResult = {{
              handled: handledTabFromOutside,
              prevented: tabFromOutside.prevented,
              active: document.activeElement.id,
            }};
            process.stdout.write(JSON.stringify({{
              focusableIds: getBeginnerTutorialFocusableElements().map((element) => element.id),
              results: [shiftFromFirstResult, tabFromLastResult, tabFromMiddleResult, tabFromOutsideResult],
              focusCalls,
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
        self.assertEqual(payload["focusableIds"], ["first", "middle", "last"])
        self.assertEqual(
            payload["results"],
            [
                {"handled": True, "prevented": True, "active": "last"},
                {"handled": True, "prevented": True, "active": "first"},
                {"handled": False, "prevented": False, "active": "middle"},
                {"handled": True, "prevented": True, "active": "first"},
            ],
        )

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

        self.assertIn("const previewRegressionTools = window.CanvasiaEditorPreviewRegression", source)
        self.assertIn("previewRegressionTools.buildPreviewRegressionSeeds", source)
        self.assertIn("previewRegressionTools.buildConditionVariableOverrides", source)
        self.assertIn("previewRegressionTools.chooseRegressionOption", source)
        self.assertIn("createPreviewRegressionSession(seed.sceneId, variableOverrides)", source)
        self.assertIn("variableOverrideSummary", source)
        self.assertIn("state.inspectionRegressionResult = runPreviewRegressionSmokeTest", regression_block)
        self.assertIn('state.currentScreen === "preview"', regression_block)
        self.assertIn("renderPreviewScreen();", regression_block)
        self.assertIn('state.currentScreen === "dashboard"', regression_block)
        self.assertIn("renderDashboard();", regression_block)

    def test_audio_cue_sheet_export_actions_are_wired(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        markdown_block_start = click_handler.index('action === "export-audio-cue-sheet-markdown"')
        csv_block_start = click_handler.index('action === "export-audio-cue-sheet-csv"')
        csv_block_end = click_handler.index('action === "export-release-control-report"', csv_block_start)
        markdown_block = click_handler[markdown_block_start:csv_block_start]
        csv_block = click_handler[csv_block_start:csv_block_end]

        self.assertIn("const audioCueSheetTools = window.CanvasiaEditorAudioCueSheet", source)
        self.assertIn('data-action="export-audio-cue-sheet-markdown"', source)
        self.assertIn('data-action="export-audio-cue-sheet-csv"', source)
        self.assertIn("exportAudioCueSheetMarkdown();", markdown_block)
        self.assertIn("exportAudioCueSheetCsv();", csv_block)
        self.assertIn("function buildAudioCueSheet()", source)
        self.assertIn("function renderAudioCueSheetPanel()", source)
        self.assertIn("function exportAudioCueSheetMarkdown()", source)
        self.assertIn("function exportAudioCueSheetCsv()", source)
        self.assertIn("audioCueSheetTools.buildAudioCueSheet", source)
        self.assertIn("audioCueSheetTools.getAudioCueSheetStatusDigest", source)

    def test_choice_consequence_sheet_export_actions_are_wired(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        markdown_block_start = click_handler.index('action === "export-choice-consequence-markdown"')
        csv_block_start = click_handler.index('action === "export-choice-consequence-csv"')
        csv_block_end = click_handler.index('action === "export-audio-cue-sheet-markdown"', csv_block_start)
        markdown_block = click_handler[markdown_block_start:csv_block_start]
        csv_block = click_handler[csv_block_start:csv_block_end]

        self.assertIn("const choiceConsequenceSheetTools = window.CanvasiaEditorChoiceConsequenceSheet", source)
        self.assertIn('data-action="export-choice-consequence-markdown"', source)
        self.assertIn('data-action="export-choice-consequence-csv"', source)
        self.assertIn("exportChoiceConsequenceMarkdown();", markdown_block)
        self.assertIn("exportChoiceConsequenceCsv();", csv_block)
        self.assertIn("function buildChoiceConsequenceSheet()", source)
        self.assertIn("function renderChoiceConsequencePanel()", source)
        self.assertIn("function exportChoiceConsequenceMarkdown()", source)
        self.assertIn("function exportChoiceConsequenceCsv()", source)
        self.assertIn("choiceConsequenceSheetTools.buildChoiceConsequenceSheet", source)
        self.assertIn("choiceConsequenceSheetTools.getChoiceConsequenceStatusDigest", source)

    def test_stage_direction_sheet_export_actions_are_wired(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        markdown_block_start = click_handler.index('action === "export-stage-direction-sheet-markdown"')
        csv_block_start = click_handler.index('action === "export-stage-direction-sheet-csv"')
        csv_block_end = click_handler.index('action === "export-release-control-report"', csv_block_start)
        markdown_block = click_handler[markdown_block_start:csv_block_start]
        csv_block = click_handler[csv_block_start:csv_block_end]

        self.assertIn("const stageDirectionSheetTools = window.CanvasiaEditorStageDirectionSheet", source)
        self.assertIn('data-action="export-stage-direction-sheet-markdown"', source)
        self.assertIn('data-action="export-stage-direction-sheet-csv"', source)
        self.assertIn("exportStageDirectionSheetMarkdown();", markdown_block)
        self.assertIn("exportStageDirectionSheetCsv();", csv_block)
        self.assertIn("function buildStageDirectionSheet()", source)
        self.assertIn("function renderStageDirectionSheetPanel()", source)
        self.assertIn("function exportStageDirectionSheetMarkdown()", source)
        self.assertIn("function exportStageDirectionSheetCsv()", source)
        self.assertIn("stageDirectionSheetTools.buildStageDirectionSheet", source)
        self.assertIn("stageDirectionSheetTools.getStageDirectionStatusDigest", source)

    def test_presentation_timeline_export_actions_are_wired(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        markdown_block_start = click_handler.index('action === "export-presentation-timeline-markdown"')
        csv_block_start = click_handler.index('action === "export-presentation-timeline-csv"')
        csv_block_end = click_handler.index('action === "export-localization-coverage-markdown"', csv_block_start)
        markdown_block = click_handler[markdown_block_start:csv_block_start]
        csv_block = click_handler[csv_block_start:csv_block_end]

        self.assertIn("const presentationTimelineTools = window.CanvasiaEditorPresentationTimeline", source)
        self.assertIn('data-action="export-presentation-timeline-markdown"', source)
        self.assertIn('data-action="export-presentation-timeline-csv"', source)
        self.assertIn("exportPresentationTimelineMarkdown();", markdown_block)
        self.assertIn("exportPresentationTimelineCsv();", csv_block)
        self.assertIn("function buildPresentationTimeline()", source)
        self.assertIn("function renderPresentationTimelinePanel()", source)
        self.assertIn("function exportPresentationTimelineMarkdown()", source)
        self.assertIn("function exportPresentationTimelineCsv()", source)
        self.assertIn("presentationTimelineTools.buildPresentationTimeline", source)
        self.assertIn("presentationTimelineTools.getPresentationTimelineStatusDigest", source)

    def test_localization_coverage_export_actions_are_wired(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        markdown_block_start = click_handler.index('action === "export-localization-coverage-markdown"')
        csv_block_start = click_handler.index('action === "export-localization-coverage-csv"')
        import_block_start = click_handler.index('action === "import-localization-coverage-csv"')
        csv_block_end = import_block_start
        import_block_end = click_handler.index('action === "export-release-control-report"', import_block_start)
        markdown_block = click_handler[markdown_block_start:csv_block_start]
        csv_block = click_handler[csv_block_start:csv_block_end]
        import_block = click_handler[import_block_start:import_block_end]

        self.assertIn("const localizationCoverageTools = window.CanvasiaEditorLocalizationCoverage", source)
        self.assertIn('data-action="export-localization-coverage-markdown"', source)
        self.assertIn('data-action="export-localization-coverage-csv"', source)
        self.assertIn('data-action="import-localization-coverage-csv"', source)
        self.assertIn('id="localizationCoverageImportInput"', INDEX_PATH.read_text(encoding="utf-8"))
        self.assertIn("exportLocalizationCoverageMarkdown();", markdown_block)
        self.assertIn("exportLocalizationCoverageCsv();", csv_block)
        self.assertIn('document.getElementById("localizationCoverageImportInput")?.click();', import_block)
        self.assertIn("function buildLocalizationCoverage()", source)
        self.assertIn("function renderLocalizationCoveragePanel()", source)
        self.assertIn("function exportLocalizationCoverageMarkdown()", source)
        self.assertIn("function exportLocalizationCoverageCsv()", source)
        self.assertIn("function importLocalizationCoverageCsv(file)", source)
        self.assertIn('const API_IMPORT_LOCALIZATION_PATCHES = "/api/import-localization-patches"', source)
        self.assertIn("postJson(API_IMPORT_LOCALIZATION_PATCHES", source)
        self.assertIn("localizationCoverageTools.buildLocalizationCoverage", source)
        self.assertIn("localizationCoverageTools.getLocalizationCoverageStatusDigest", source)
        self.assertIn("localizationCoverageTools.buildLocalizationImportPlan", source)

    def test_scene_save_payload_preserves_scene_name_translations(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        strip_scene_for_save = _extract_function_source(source, "stripSceneForSave")

        self.assertIn("nameTranslations", strip_scene_for_save)
        self.assertIn("scene.nameTranslations", strip_scene_for_save)

    def test_playtest_handoff_export_actions_are_wired(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")
        markdown_block_start = click_handler.index('action === "export-playtest-handoff-markdown"')
        csv_block_start = click_handler.index('action === "export-playtest-handoff-csv"')
        feedback_markdown_block_start = click_handler.index('action === "export-playtest-feedback-template-markdown"')
        feedback_csv_block_start = click_handler.index('action === "export-playtest-feedback-template-csv"')
        import_feedback_block_start = click_handler.index('action === "import-playtest-feedback-csv"')
        feedback_intake_markdown_block_start = click_handler.index('action === "export-playtest-feedback-intake-markdown"')
        feedback_intake_csv_block_start = click_handler.index('action === "export-playtest-feedback-intake-csv"')
        feedback_intake_csv_block_end = click_handler.index('action === "clear-inspection-filters"', feedback_intake_csv_block_start)
        markdown_block = click_handler[markdown_block_start:csv_block_start]
        csv_block = click_handler[csv_block_start:feedback_markdown_block_start]
        feedback_markdown_block = click_handler[feedback_markdown_block_start:feedback_csv_block_start]
        feedback_csv_block = click_handler[feedback_csv_block_start:import_feedback_block_start]
        import_feedback_block = click_handler[import_feedback_block_start:feedback_intake_markdown_block_start]
        feedback_intake_markdown_block = click_handler[feedback_intake_markdown_block_start:feedback_intake_csv_block_start]
        feedback_intake_csv_block = click_handler[feedback_intake_csv_block_start:feedback_intake_csv_block_end]
        handle_change = _extract_function_source(source, "handleChange")

        self.assertIn("const playtestHandoffReportTools = window.CanvasiaEditorPlaytestHandoffReport", source)
        self.assertIn('id="playtestFeedbackImportInput"', (EDITOR_DIR / "index.html").read_text(encoding="utf-8"))
        self.assertIn('data-action="export-playtest-handoff-markdown"', source)
        self.assertIn('data-action="export-playtest-handoff-csv"', source)
        self.assertIn('data-action="export-playtest-feedback-template-markdown"', source)
        self.assertIn('data-action="export-playtest-feedback-template-csv"', source)
        self.assertIn('data-action="import-playtest-feedback-csv"', source)
        self.assertIn('data-action="export-playtest-feedback-intake-markdown"', source)
        self.assertIn('data-action="export-playtest-feedback-intake-csv"', source)
        self.assertIn("exportPlaytestHandoffMarkdown();", markdown_block)
        self.assertIn("exportPlaytestHandoffCsv();", csv_block)
        self.assertIn("exportPlaytestFeedbackTemplateMarkdown();", feedback_markdown_block)
        self.assertIn("exportPlaytestFeedbackTemplateCsv();", feedback_csv_block)
        self.assertIn('document.getElementById("playtestFeedbackImportInput")?.click();', import_feedback_block)
        self.assertIn("exportPlaytestFeedbackIntakeMarkdown();", feedback_intake_markdown_block)
        self.assertIn("exportPlaytestFeedbackIntakeCsv();", feedback_intake_csv_block)
        self.assertIn('target.id === "playtestFeedbackImportInput"', handle_change)
        self.assertIn("importPlaytestFeedbackCsv", handle_change)
        self.assertIn('state.currentScreen === "inspection"', markdown_block)
        self.assertIn('state.currentScreen === "preview"', markdown_block)
        self.assertIn('state.currentScreen === "inspection"', csv_block)
        self.assertIn('state.currentScreen === "preview"', csv_block)
        self.assertIn('state.currentScreen === "inspection"', feedback_markdown_block)
        self.assertIn('state.currentScreen === "preview"', feedback_markdown_block)
        self.assertIn('state.currentScreen === "inspection"', feedback_csv_block)
        self.assertIn('state.currentScreen === "preview"', feedback_csv_block)
        self.assertIn("function buildPlaytestHandoffContext()", source)
        self.assertIn("function exportPlaytestHandoffMarkdown()", source)
        self.assertIn("function exportPlaytestHandoffCsv()", source)
        self.assertIn("function exportPlaytestFeedbackTemplateMarkdown()", source)
        self.assertIn("function exportPlaytestFeedbackTemplateCsv()", source)
        self.assertIn("function importPlaytestFeedbackCsv(file)", source)
        self.assertIn("function exportPlaytestFeedbackIntakeMarkdown()", source)
        self.assertIn("function exportPlaytestFeedbackIntakeCsv()", source)

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

    def test_native_export_surface_links_vn_baseline_quality_reports(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("vnBaselineQualityMarkdownPublicUrl", source)
        self.assertIn("打开 VN 基础质感报告", source)
        self.assertIn("vnBaselineQualityReportPublicUrl", source)
        self.assertIn("打开 VN 质感 JSON", source)
        self.assertIn("VN 基础质感报告：", source)
        self.assertIn("VN 基础质感 JSON：", source)
        self.assertIn("VN 基础质感状态：", source)

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
