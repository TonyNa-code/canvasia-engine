from __future__ import annotations

import shutil
import socket
import subprocess
import sys
import tempfile
import time
import os
import json
import tarfile
import unittest
import re
import plistlib
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def read_server_log_tail(process: subprocess.Popen[str], log_path: Path | None = None, limit: int = 4000) -> str:
    if log_path and log_path.exists():
        try:
            return log_path.read_text(encoding="utf-8", errors="replace")[-limit:]
        except Exception:
            return ""
    if process.stdout:
        try:
            return process.stdout.read()[-limit:]
        except Exception:
            return ""
    return ""


def wait_for_server_ready(
    url: str,
    process: subprocess.Popen[str],
    timeout_seconds: float = 20.0,
    log_path: Path | None = None,
) -> None:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            output = read_server_log_tail(process, log_path)
            raise RuntimeError(f"测试服务提前退出。\n{output}")
        try:
            with urlopen(url, timeout=1.5) as response:
                if 200 <= getattr(response, "status", 200) < 500:
                    return
        except Exception as error:  # pragma: no cover - readiness polling
            last_error = str(error)
            time.sleep(0.25)
    output = read_server_log_tail(process, log_path)
    raise RuntimeError(f"测试服务没有在规定时间内启动：{last_error}\n{output}")


def create_fake_runtime_archive(archive_path: Path, platform_key: str) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "python"
        if platform_key == "windows":
            executable = root / "python.exe"
        else:
            executable = root / "bin" / "python3"
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("fake-python", encoding="utf-8")
        if platform_key != "windows":
            executable.chmod(0o755)
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(root, arcname="python")
    return archive_path


def create_fake_nwjs_runtime_dir(runtime_dir: Path, platform_key: str) -> Path:
    runtime_dir.mkdir(parents=True, exist_ok=True)

    if platform_key == "macos":
        app_bundle = runtime_dir / "nwjs.app"
        (app_bundle / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
        (app_bundle / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)
        executable_path = app_bundle / "Contents" / "MacOS" / "nwjs"
        executable_path.write_text("fake-nwjs", encoding="utf-8")
        executable_path.chmod(0o755)
        with (app_bundle / "Contents" / "Info.plist").open("wb") as plist_file:
            plistlib.dump({"CFBundleExecutable": "nwjs", "CFBundleName": "nwjs"}, plist_file)
        return runtime_dir

    required_files = {
        "windows": ["nw.exe", "icudtl.dat", "libEGL.dll", "libGLESv2.dll", "nw_100_percent.pak", "resources.pak", "v8_context_snapshot.bin"],
        "linux": ["nw", "icudtl.dat", "resources.pak", "v8_context_snapshot.bin"],
    }
    for file_name in required_files[platform_key]:
        file_path = runtime_dir / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("fake-runtime", encoding="utf-8")
        if file_name in {"nw", "nw.exe"}:
            file_path.chmod(0o755)
    (runtime_dir / "locales").mkdir(parents=True, exist_ok=True)
    return runtime_dir


def create_fake_iscc_script(script_path: Path) -> Path:
    script_path.write_text(
        """#!/bin/sh
set -eu
output_dir=""
output_base="CanvasiaEngineEditorSetup"
for arg in "$@"; do
  case "$arg" in
    /O*) output_dir="${arg#/O}" ;;
    /F*) output_base="${arg#/F}" ;;
  esac
done
if [ -z "$output_dir" ]; then
  output_dir="$(pwd)"
fi
mkdir -p "$output_dir"
printf 'fake-windows-installer' > "$output_dir/$output_base.exe"
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


def create_fake_signtool_script(script_path: Path) -> Path:
    script_path.write_text(
        """#!/bin/sh
set -eu
exit 0
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


class BrowserPlaywrightSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.repo_source = Path(__file__).resolve().parents[1]
        cls.repo_copy = Path(cls.temp_dir.name) / "browser_test_repo"
        shutil.copytree(
            cls.repo_source,
            cls.repo_copy,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                ".DS_Store",
                "exports",
                ".export_runtime_cache",
                ".tmp_brand_preview",
                "projects",
            ),
        )
        cls.fake_runtime_archives = {
            "macos": create_fake_runtime_archive(cls.repo_copy / ".tmp_fake_macos_runtime.tar.gz", "macos"),
            "windows": create_fake_runtime_archive(cls.repo_copy / ".tmp_fake_windows_runtime.tar.gz", "windows"),
            "linux": create_fake_runtime_archive(cls.repo_copy / ".tmp_fake_linux_runtime.tar.gz", "linux"),
        }
        cls.fake_nwjs_runtime_dirs = {
            "macos": create_fake_nwjs_runtime_dir(cls.repo_copy / ".tmp_fake_nwjs_macos", "macos"),
            "windows": create_fake_nwjs_runtime_dir(cls.repo_copy / ".tmp_fake_nwjs_windows", "windows"),
            "linux": create_fake_nwjs_runtime_dir(cls.repo_copy / ".tmp_fake_nwjs_linux", "linux"),
        }
        cls.fake_iscc = create_fake_iscc_script(cls.repo_copy / ".tmp_fake_iscc.sh")
        cls.fake_signtool = create_fake_signtool_script(cls.repo_copy / ".tmp_fake_signtool.sh")

        cls.port = find_free_port()
        cls.editor_url = f"http://127.0.0.1:{cls.port}/prototype_editor/index.html"
        server_env = os.environ.copy()
        server_env.update(
            {
                "CANVASIA_EDITOR_RUNTIME_ARCHIVE_MACOS": str(cls.fake_runtime_archives["macos"]),
                "CANVASIA_EDITOR_RUNTIME_ARCHIVE_WINDOWS": str(cls.fake_runtime_archives["windows"]),
                "CANVASIA_EDITOR_RUNTIME_ARCHIVE_LINUX": str(cls.fake_runtime_archives["linux"]),
                "CANVASIA_NWJS_RUNTIME_DIR_MACOS": str(cls.fake_nwjs_runtime_dirs["macos"]),
                "CANVASIA_NWJS_RUNTIME_DIR_WINDOWS": str(cls.fake_nwjs_runtime_dirs["windows"]),
                "CANVASIA_NWJS_RUNTIME_DIR_LINUX": str(cls.fake_nwjs_runtime_dirs["linux"]),
                "CANVASIA_EDITOR_WINDOWS_ISCC": str(cls.fake_iscc),
                "CANVASIA_EDITOR_WINDOWS_SIGNTOOL": str(cls.fake_signtool),
                "CANVASIA_EDITOR_WINDOWS_CERT_SUBJECT": "Canvasia Engine Project",
            }
        )
        cls.server_log_path = cls.repo_copy / ".tmp_browser_smoke_server.log"
        cls.server_log_file = cls.server_log_path.open("w", encoding="utf-8")
        cls.server_process = subprocess.Popen(
            [sys.executable, str(cls.repo_copy / "run_editor.py"), "--port", str(cls.port), "--no-open"],
            cwd=cls.repo_copy,
            env=server_env,
            stdout=cls.server_log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_server_ready(cls.editor_url, cls.server_process, log_path=cls.server_log_path)

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.browser.close()
        except Exception:
            pass
        try:
            cls.playwright.stop()
        except Exception:
            pass
        try:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
        except Exception:
            try:
                cls.server_process.kill()
            except Exception:
                pass
        try:
            cls.server_log_file.close()
        except Exception:
            pass
        cls.temp_dir.cleanup()

    def setUp(self) -> None:
        self.context = self.browser.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        self.page = self.context.new_page()

    def tearDown(self) -> None:
        self.context.close()

    def open_editor(self) -> None:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                wait_for_server_ready(
                    self.editor_url,
                    self.server_process,
                    timeout_seconds=8.0,
                    log_path=self.server_log_path,
                )
                self.page.goto(self.editor_url, wait_until="domcontentloaded", timeout=45000)
                self.page.get_by_text("先选项目，再进入编辑器").wait_for(timeout=15000)
                return
            except Exception as error:
                last_error = error
                if attempt >= 2:
                    break
                try:
                    self.page.goto("about:blank", wait_until="domcontentloaded", timeout=5000)
                except Exception:
                    pass
                time.sleep(0.5)
        raise RuntimeError(f"编辑器页面没有稳定打开：{last_error}") from last_error

    def create_blank_project(self, name: str) -> None:
        self.open_editor()
        self.page.get_by_role("button", name="新建空白项目").click()
        dialog = self.page.locator(".system-dialog").filter(has_text="给这个新项目起个名字").first
        dialog.wait_for(timeout=15000)
        dialog.locator(".system-dialog-input").fill(name)
        dialog.get_by_role("button", name="确认").click()
        self.page.get_by_role("button", name="一键创建第一章").first.wait_for(timeout=15000)

    def test_editor_system_prompt_requires_text(self) -> None:
        self.open_editor()
        self.page.get_by_role("button", name="新建空白项目").click()
        dialog = self.page.locator(".system-dialog").filter(has_text="给这个新项目起个名字").first
        dialog.wait_for(timeout=15000)
        dialog.locator(".system-dialog-input").fill("")
        self.assertTrue(dialog.get_by_role("button", name="确认").is_disabled())
        dialog.locator(".system-dialog-input").fill("浏览器烟测项目_PromptRequired")
        dialog.get_by_role("button", name="确认").click()
        self.page.get_by_role("button", name="一键创建第一章").first.wait_for(timeout=15000)

    def create_first_chapter(self) -> None:
        self.page.get_by_role("button", name="一键创建第一章").first.click()
        self.page.locator("#screen-story").get_by_role("button", name="加台词").first.wait_for(timeout=15000)

    def test_editor_system_dialog_replaces_native_alert(self) -> None:
        self.open_editor()
        self.page.evaluate("window.alert('系统弹窗测试：统一提示层')")
        dialog = self.page.locator(".system-dialog").filter(has_text="系统弹窗测试：统一提示层").first
        dialog.wait_for(timeout=15000)
        dialog.get_by_role("button", name="知道了").click()
        self.page.locator(".system-dialog").wait_for(state="detached", timeout=15000)

    def test_editor_system_alert_infers_failure_dialog(self) -> None:
        self.open_editor()
        self.page.evaluate("window.alert('导出失败：素材文件缺失\\n详情：missing background.png')")
        dialog = self.page.locator(".system-dialog").filter(has_text="导出失败").first
        dialog.wait_for(timeout=15000)
        dialog.get_by_text("操作失败").wait_for(timeout=15000)
        dialog.get_by_role("button", name="复制详情").wait_for(timeout=15000)
        dialog.get_by_role("button", name="知道了").click()
        self.page.locator(".system-dialog").wait_for(state="detached", timeout=15000)

    def test_editor_unknown_action_shows_runtime_fallback(self) -> None:
        self.create_blank_project("浏览器烟测项目_UnknownAction")
        self.page.evaluate(
            """() => {
                const button = document.createElement("button");
                button.type = "button";
                button.dataset.action = "codex-unwired-action";
                button.textContent = "未接线按钮";
                document.body.append(button);
                button.click();
                button.remove();
            }"""
        )
        self.page.get_by_text("这个按钮暂时还没有接上功能").wait_for(timeout=15000)
        self.page.get_by_text("按钮暂未接线：codex-unwired-action").wait_for(timeout=15000)

    def open_project_by_title(self, title: str) -> None:
        self.open_editor()
        card = self.page.locator(".project-card").filter(has_text=title).first
        card.wait_for(timeout=15000)
        card.locator("[data-action='open-project']").click()
        self.page.wait_for_function(
            """() => {
                const appMain = document.querySelector("#appMain");
                const previewButton = Array.from(document.querySelectorAll("button")).find(
                    (button) => button.textContent?.trim() === "试玩收尾"
                );
                return Boolean(appMain)
                    && !appMain.classList.contains("is-hidden")
                    && Boolean(previewButton)
                    && !previewButton.disabled;
            }""",
            timeout=15000,
        )
        self.dismiss_optional_recovery_prompt()

    def dismiss_optional_recovery_prompt(self) -> None:
        dialog = self.page.locator(".system-dialog").filter(has_text="恢复到这份版本").first
        try:
            dialog.wait_for(timeout=1200)
        except Exception:
            return
        dialog.get_by_role("button", name="先不恢复").click()
        self.page.locator(".system-dialog").wait_for(state="detached", timeout=10000)

    def open_inspection_screen(self) -> None:
        inspection_button = self.page.get_by_role("button", name="项目巡检").first
        if not inspection_button.is_visible():
            advanced_button = self.page.get_by_role("button", name="打开高级工具").first
            advanced_button.wait_for(timeout=10000)
            advanced_button.click()
            inspection_button.wait_for(timeout=10000)
        inspection_button.click()
        self.page.get_by_role("heading", name="一键巡检中心").wait_for(timeout=15000)

    def open_preview_screen(self) -> None:
        self.page.get_by_role("button", name="试玩收尾").click()
        self.page.get_by_text("新手收尾顺序").wait_for(timeout=15000)

    def test_dashboard_scene_preview_button_opens_preview_without_runtime_error(self) -> None:
        page_errors: list[str] = []
        console_errors: list[str] = []
        self.page.on("pageerror", lambda error: page_errors.append(str(error)))
        self.page.on(
            "console",
            lambda message: console_errors.append(message.text) if message.type == "error" else None,
        )

        self.open_project_by_title("心跳时差")
        scene_preview_buttons = self.page.locator("button[data-action='preview-scene-from-map']:visible")
        scene_preview_buttons.first.wait_for(timeout=15000)
        self.assertGreater(scene_preview_buttons.count(), 0)

        scene_preview_buttons.first.click()
        self.page.wait_for_function(
            """() => {
                const previewScreen = document.querySelector("#screen-preview");
                const previewMeta = document.querySelector("#previewMeta")?.textContent || "";
                const previewStage = document.querySelector("#previewStage");
                return Boolean(previewScreen?.classList.contains("is-active"))
                  && Boolean(previewStage)
                  && previewMeta.includes("起点")
                  && previewMeta.includes("当前");
            }""",
            timeout=15000,
        )

        runtime_errors = [
            message
            for message in [*page_errors, *console_errors]
            if "ReferenceError" in message or "getBlockLabel" in message
        ]
        self.assertFalse(runtime_errors, "\n".join(runtime_errors))

    def export_web_build(self) -> str:
        self.open_preview_screen()
        self.page.get_by_role("button", name="导出试玩包").first.click()
        open_link = self.page.get_by_role("link", name="打开试玩包")
        open_link.wait_for(timeout=20000)
        href = open_link.get_attribute("href")
        self.assertTrue(href, "导出试玩包后没有拿到可打开链接")
        return urljoin(self.editor_url, href)

    def unlock_sample_player_title_features(
        self,
        player_page,
        *,
        include_voice_replay: bool = False,
        include_endings: bool = False,
        include_gallery: bool = False,
    ) -> None:
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=20000)
        player_page.evaluate(
            """(options) => {
                const now = new Date().toISOString();
                window.localStorage.setItem(
                    "canvasia-engine:player-chapters:心跳时差",
                    JSON.stringify({ chapter_opening: now })
                );
                window.localStorage.setItem(
                    "canvasia-engine:player-extra:心跳时差",
                    JSON.stringify({
                        cg: options?.includeGallery ? ["cg_twilight_memory"] : [],
                        bgm: ["bgm_after_school"],
                    })
                );
                if (options?.includeVoiceReplay) {
                    window.localStorage.setItem(
                        "canvasia-engine:player-voice-replay:心跳时差",
                        JSON.stringify({
                            "scene_classroom_sunset:block_005:6": {
                                unlockedAt: now,
                                lastHeardAt: now,
                                heardCount: 1,
                            },
                            "scene_classroom_sunset:block_006:7": {
                                unlockedAt: now,
                                lastHeardAt: now,
                                heardCount: 1,
                            },
                            "scene_classroom_sunset:block_007:8": {
                                unlockedAt: now,
                                lastHeardAt: now,
                                heardCount: 1,
                            },
                        })
                    );
                }

                if (options?.includeEndings) {
                    window.localStorage.setItem(
                        "canvasia-engine:player-endings:心跳时差",
                        JSON.stringify({
                            unlocked: {
                                scene_normal_goodnight: now,
                            },
                            completionCount: 1,
                            lastCompletedAt: now,
                        })
                    );
                }
            }""",
            {
                "includeVoiceReplay": include_voice_replay,
                "includeEndings": include_endings,
                "includeGallery": include_gallery,
            },
        )
        player_page.reload(wait_until="domcontentloaded")
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)
        player_page.wait_for_function(
            """(options) => {
                const chapterText = document.querySelector("#startChapterButton")?.textContent || "";
                const musicText = document.querySelector("#startMusicRoomButton")?.textContent || "";
                const voiceText = document.querySelector("#startVoiceReplayButton")?.textContent || "";
                const endingText = document.querySelector("#startEndingButton")?.textContent || "";
                const galleryText = document.querySelector("#startGalleryButton")?.textContent || "";

                if (!chapterText.includes("1/1") || !musicText.includes("1/1")) {
                    return false;
                }

                if (options?.includeVoiceReplay && !voiceText.includes("3/3")) {
                    return false;
                }

                if (options?.includeEndings && !endingText.includes("1/2")) {
                    return false;
                }

                if (options?.includeGallery && !galleryText.includes("1/1")) {
                    return false;
                }

                return true;
            }""",
            arg={
                "includeVoiceReplay": include_voice_replay,
                "includeEndings": include_endings,
                "includeGallery": include_gallery,
            },
            timeout=10000,
        )

    def unlock_sample_player_collection_archives(self, player_page) -> None:
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=20000)
        player_page.evaluate(
            """() => {
                const now = new Date().toISOString();
                window.localStorage.setItem(
                    "canvasia-engine:player-locations:心跳时差",
                    JSON.stringify({
                        bg_classroom_sunset: now,
                        bg_hallway_after_school: now,
                        bg_rooftop_evening: now,
                    })
                );
                window.localStorage.setItem(
                    "canvasia-engine:player-narrations:心跳时差",
                    JSON.stringify({
                        "scene_rooftop_breeze:block_014:1": now,
                        "scene_normal_goodnight:block_023:1": now,
                    })
                );
                window.localStorage.setItem(
                    "canvasia-engine:player-relations:心跳时差",
                    JSON.stringify({
                        "char_linruoxi__char_player": now,
                    })
                );
                window.localStorage.setItem(
                    "canvasia-engine:player-characters:心跳时差",
                    JSON.stringify(["char_linruoxi", "char_player"])
                );
            }"""
        )
        player_page.reload(wait_until="domcontentloaded")
        player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)
        player_page.wait_for_function(
            """() => {
                const locationText = document.querySelector("#startLocationButton")?.textContent || "";
                const narrationText = document.querySelector("#startNarrationButton")?.textContent || "";
                const relationText = document.querySelector("#startRelationButton")?.textContent || "";
                const characterText = document.querySelector("#startCharacterButton")?.textContent || "";
                return locationText.includes("3/3")
                  && narrationText.includes("2/2")
                  && relationText.includes("1/1")
                  && characterText.includes("2/2");
            }""",
            timeout=10000,
        )

    def test_beginner_flow_reaches_story_editor_and_adds_block(self) -> None:
        self.create_blank_project("浏览器烟测项目_A")
        self.create_first_chapter()

        block_cards = self.page.locator("#storyBlockList .block-card")
        initial_count = block_cards.count()
        self.page.locator("#screen-story").get_by_role("button", name="加台词").first.click()
        self.page.wait_for_function(
            """([selector, expected]) => {
                const cards = document.querySelectorAll(selector);
                return cards.length > expected;
            }""",
            arg=["#storyBlockList .block-card", initial_count],
            timeout=15000,
        )

        self.assertGreater(block_cards.count(), initial_count)

    def test_story_editor_can_split_long_dialogue_into_multiple_cards(self) -> None:
        self.create_blank_project("浏览器烟测项目_Split")
        self.create_first_chapter()

        block_cards = self.page.locator("#storyBlockList .block-card")
        self.page.locator("#screen-story").get_by_role("button", name="加台词").first.click()
        self.page.locator("#editorDialogueText").wait_for(timeout=15000)
        split_button = self.page.get_by_role("button", name="拆成长文本卡片")
        self.assertTrue(split_button.is_disabled())

        initial_count = block_cards.count()
        long_dialogue = (
            "我把这段话故意写得很长，是为了模拟正式项目里常见的一大段情绪独白。"
            "如果全部塞进同一张卡片，玩家阅读节奏会变慢，配音和回看也会变得不好管理。"
            "拆成多张卡片之后，每一次点击都会更像真正的视觉小说节拍。"
            "这样编辑器不仅能发现问题，也能立刻把问题处理掉。"
            "尤其是后期接入语音、自动播放和历史文本时，短卡片会比一大坨长文本可靠得多。"
            "这条测试要确认拆分以后仍然会写回项目文件，而不是只在界面上临时变化。"
        )
        self.page.locator("#editorDialogueText").fill(long_dialogue)
        self.page.locator("[data-readable-status]").filter(has_text="可拆卡").wait_for(timeout=10000)
        split_button.click()
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length > expected""",
            arg=["#storyBlockList .block-card", initial_count],
            timeout=15000,
        )

        self.assertGreater(block_cards.count(), initial_count)

    def test_story_editor_choice_quality_and_delete_option(self) -> None:
        self.create_blank_project("浏览器烟测项目_Choice")
        self.create_first_chapter()

        self.page.locator("#screen-story").get_by_role("button", name="加选项").first.click()
        option_editors = self.page.locator("[data-choice-option]")
        option_editors.first.wait_for(timeout=15000)
        initial_count = option_editors.count()
        self.assertGreaterEqual(initial_count, 2)

        long_choice = "这是一条故意写得很长的选项文案，用来确认按钮布局体检会实时提醒创作者把说明放回前一句对白里"
        option_editors.first.locator('[data-field="choice-text"]').fill(long_choice)
        option_editors.first.locator("[data-choice-text-status]").filter(has_text="文案偏长").wait_for(
            timeout=10000
        )
        option_editors.nth(1).locator('[data-field="choice-text"]').fill("短选项 B")
        option_editors.nth(1).get_by_role("button", name="上移选项").click()
        self.page.wait_for_function(
            """() => document.querySelector('[data-choice-option] [data-field="choice-text"]')?.value === '短选项 B'""",
            timeout=15000,
        )

        first_option = self.page.locator("[data-choice-option]").first
        first_option.get_by_role("button", name="给这个选项加效果").click()
        first_option.get_by_role("button", name="给这个选项加效果").click()
        effects = first_option.locator("[data-choice-effect]")
        self.page.wait_for_function(
            """() => document.querySelectorAll('[data-choice-option]:first-child [data-choice-effect]').length === 2""",
            timeout=15000,
        )
        effects.nth(0).locator('[data-field="choice-effect-type"]').select_option("variable_set")
        effects.nth(1).locator('[data-field="choice-effect-type"]').select_option("variable_add")
        effects.nth(1).get_by_role("button", name="上移效果").click()
        self.page.wait_for_function(
            """() => document.querySelector('[data-choice-option]:first-child [data-choice-effect] [data-field="choice-effect-type"]')?.value === 'variable_add'""",
            timeout=15000,
        )
        effects.last.get_by_role("button", name="删除这条效果").click()
        self.page.wait_for_function(
            """() => document.querySelectorAll('[data-choice-option]:first-child [data-choice-effect]').length === 1""",
            timeout=15000,
        )

        self.page.get_by_role("button", name="再加一个选项").click()
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length > expected""",
            arg=["[data-choice-option]", initial_count],
            timeout=15000,
        )
        self.page.locator("[data-choice-option]").last.get_by_role("button", name="删除这个选项").click()
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length === expected""",
            arg=["[data-choice-option]", initial_count],
            timeout=15000,
        )

        self.assertEqual(option_editors.count(), initial_count)

    def test_story_editor_condition_branch_and_rule_controls(self) -> None:
        self.create_blank_project("浏览器烟测项目_Condition")
        self.create_first_chapter()

        advanced_button = self.page.get_by_role("button", name="打开高级工具").first
        if advanced_button.is_visible():
            advanced_button.click()

        self.page.locator("#screen-story").get_by_role("button", name="条件判断").click()
        branches = self.page.locator("[data-condition-branch]")
        branches.first.wait_for(timeout=15000)
        self.page.locator('[data-field="condition-variable"] option[value="var_affection"]').first.wait_for(
            state="attached",
            timeout=15000
        )
        initial_branch_count = branches.count()
        self.assertEqual(initial_branch_count, 1)

        self.page.get_by_role("button", name="再加一条分支").click()
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length > expected""",
            arg=["[data-condition-branch]", initial_branch_count],
            timeout=15000,
        )
        moved_branch_id = branches.nth(1).get_attribute("data-branch-id")
        branches.nth(1).get_by_role("button", name="上移分支").click()
        self.page.wait_for_function(
            """(branchId) => document.querySelector("[data-condition-branch]")?.dataset.branchId === branchId""",
            arg=moved_branch_id,
            timeout=15000,
        )

        first_branch = branches.first
        first_branch.get_by_role("button", name="再加一个判断").click()
        rules = first_branch.locator("[data-condition-rule]")
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length > expected""",
            arg=["[data-condition-branch]:first-child [data-condition-rule]", 1],
            timeout=15000,
        )
        rules.nth(0).locator('[data-field="condition-value-number"]').fill("1")
        rules.nth(1).locator('[data-field="condition-value-number"]').fill("2")
        rules.nth(1).get_by_role("button", name="上移判断").click()
        self.page.wait_for_function(
            """() => document.querySelector('[data-condition-branch]:first-child [data-condition-rule] [data-field="condition-value-number"]')?.value === '2'""",
            timeout=15000,
        )
        rules.last.get_by_role("button", name="删除这个判断").click()
        self.page.wait_for_function(
            """() => document.querySelectorAll('[data-condition-branch]:first-child [data-condition-rule]').length === 1""",
            timeout=15000,
        )

        branches.last.get_by_role("button", name="删除这条分支").click()
        self.page.wait_for_function(
            """() => document.querySelectorAll('[data-condition-branch]').length === 1""",
            timeout=15000,
        )

    def test_creative_assistant_can_generate_restore_export_and_insert(self) -> None:
        self.create_blank_project("浏览器烟测项目_Assistant")
        self.create_first_chapter()

        panel = self.page.locator("#creativeAssistantPanel")
        block_cards = self.page.locator("#storyBlockList .block-card")
        initial_count = block_cards.count()
        search_query = "浏览器烟测灵感"

        panel.locator("#creativeAssistantPrompt").fill(f"雨夜校园悬疑恋爱，{search_query}")
        panel.get_by_role("button", name="生成建议").click()
        panel.get_by_text("可插入").wait_for(timeout=15000)
        panel.get_by_text("剧情卡片预览").wait_for(timeout=10000)
        panel.locator(".creative-assistant-history").wait_for(timeout=10000)
        history_cards = panel.locator(".creative-history-card")
        history_cards.first.wait_for(timeout=15000)
        history_cards.first.get_by_role("button", name="收藏", exact=True).click()
        history_cards.first.get_by_role("button", name="已收藏", exact=True).wait_for(timeout=10000)
        panel.locator("#creativeAssistantHistorySearchInput").fill(search_query)
        self.page.wait_for_function(
            """(query) => {
                const panel = document.querySelector("#creativeAssistantPanel");
                const input = panel?.querySelector("#creativeAssistantHistorySearchInput");
                const cards = Array.from(panel?.querySelectorAll(".creative-history-card") ?? []);
                return input?.value === query && cards.some((card) => card.innerText.includes(query));
            }""",
            arg=search_query,
            timeout=15000,
        )
        panel.locator("#creativeAssistantHistorySearchInput").fill("找不到的灵感关键词")
        panel.get_by_text("没有匹配的灵感").wait_for(timeout=10000)
        panel.locator("#creativeAssistantHistorySearchInput").fill("")
        panel.get_by_role("button", name="只看收藏").click()
        panel.get_by_role("button", name="显示全部").wait_for(timeout=10000)
        panel.locator(".creative-history-card").first.wait_for(timeout=10000)
        history_meta = panel.locator(".creative-history-meta").first
        history_meta.wait_for(timeout=10000)
        self.assertRegex(history_meta.inner_text(), r"(张卡片|仅建议)")
        self.assertIn("本地模板", history_meta.inner_text())
        panel.get_by_role("button", name="显示全部").click()

        with self.page.expect_download() as download_info:
            panel.get_by_role("button", name="导出最新灵感").click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))
        self.assertTrue(download_path.exists())
        self.assertIn("creative_assistant_idea", download_path.read_text(encoding="utf-8"))

        with self.page.expect_download() as archive_download_info:
            panel.get_by_role("button", name="导出全部").click()
        archive_download = archive_download_info.value
        archive_path = self.repo_copy / archive_download.suggested_filename
        archive_download.save_as(str(archive_path))
        archive_payload = archive_path.read_text(encoding="utf-8")
        self.assertIn("creative_assistant_history_archive", archive_payload)
        self.assertIn('"containsApiKey": false', archive_payload)

        with self.page.expect_download() as view_download_info:
            panel.get_by_role("button", name="导出当前视图").click()
        view_download = view_download_info.value
        view_path = self.repo_copy / view_download.suggested_filename
        view_download.save_as(str(view_path))
        view_payload = view_path.read_text(encoding="utf-8")
        self.assertIn("creative_assistant_history_archive", view_payload)

        with self.page.expect_download() as markdown_download_info:
            panel.get_by_role("button", name="导出 Markdown").click()
        markdown_download = markdown_download_info.value
        markdown_path = self.repo_copy / markdown_download.suggested_filename
        markdown_download.save_as(str(markdown_path))
        markdown_payload = markdown_path.read_text(encoding="utf-8")
        self.assertIn("Canvasia Assistant 灵感档案", markdown_payload)
        self.assertIn("隐私说明", markdown_payload)

        panel.get_by_role("button", name="复制文档").first.click()
        self.page.get_by_text("单条灵感 Markdown 已复制").wait_for(timeout=10000)

        panel.get_by_role("button", name="OpenAI 真模型").click()
        panel.locator("#creativeAssistantOpenAiKey").fill("sk-browser-smoke-test")
        panel.locator("#creativeAssistantRememberKey").check()
        self.assertEqual(
            self.page.evaluate(
                """() => localStorage.getItem("canvasia-engine:creative-assistant-openai-key")"""
            ),
            "sk-browser-smoke-test",
        )
        panel.get_by_role("button", name="忘记本机 Key").click()
        self.assertEqual(panel.locator("#creativeAssistantOpenAiKey").input_value(), "")
        self.assertTrue(panel.get_by_role("button", name="忘记本机 Key").is_disabled())
        self.assertIsNone(
            self.page.evaluate(
                """() => localStorage.getItem("canvasia-engine:creative-assistant-openai-key")"""
            )
        )

        panel.get_by_role("button", name="清空").click()
        self.page.get_by_role("button", name="清空灵感盒").click()
        self.page.wait_for_function(
            """() => document.querySelectorAll("#creativeAssistantPanel .creative-history-card").length === 0""",
            timeout=15000,
        )
        panel.get_by_role("button", name="恢复上次清理").click()
        panel.locator(".creative-history-card").first.wait_for(timeout=10000)
        panel.get_by_role("button", name="清空").click()
        self.page.get_by_role("button", name="清空灵感盒").click()
        self.page.wait_for_function(
            """() => document.querySelectorAll("#creativeAssistantPanel .creative-history-card").length === 0""",
            timeout=15000,
        )
        panel.locator("#creativeAssistantHistoryImportInput").set_input_files(str(archive_path))
        panel.locator(".creative-assistant-history").wait_for(timeout=10000)
        panel.get_by_role("button", name="已收藏", exact=True).first.wait_for(timeout=10000)
        panel.locator('[data-action="set-creative-assistant-provider"][data-creative-provider="local"]').click()
        panel.locator("#creativeAssistantPrompt").fill("黄昏天台，青梅竹马终于谈起三年前的误会")
        panel.get_by_role("button", name="生成建议").click()
        panel.locator(".creative-history-card").nth(1).wait_for(timeout=10000)
        panel.get_by_role("button", name="清理未收藏").click()
        self.page.get_by_role("button", name="确认清理").click()
        self.page.get_by_text("未收藏灵感已清理").wait_for(timeout=10000)
        self.assertEqual(panel.locator(".creative-history-card").count(), 1)
        panel.get_by_role("button", name="恢复上次清理").click()
        self.page.get_by_role("button", name="恢复灵感盒").click()
        self.page.get_by_text("已恢复，当前灵感盒已转存为恢复点").wait_for(timeout=10000)
        self.assertGreater(panel.locator(".creative-history-card").count(), 1)

        panel.locator(".creative-history-card").first.get_by_role("button", name="恢复", exact=True).click()
        panel.get_by_role("button", name="插入到当前场景").click()
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length > expected""",
            arg=["#storyBlockList .block-card", initial_count],
            timeout=15000,
        )
        self.assertGreater(block_cards.count(), initial_count)

    def test_beginner_flow_can_export_web_build(self) -> None:
        self.create_blank_project("浏览器烟测项目_B")
        self.create_first_chapter()

        player_url = self.export_web_build()
        self.assertIn("/exports/", player_url)

    def test_preview_variable_library_can_create_and_save_variable(self) -> None:
        self.create_blank_project("浏览器烟测项目_VariableLibrary")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_text("变量库管理台").wait_for(timeout=15000)
        initial_count = self.page.locator("[data-project-variable-row]").count()
        self.page.get_by_role("button", name="新增数字").click()
        self.page.wait_for_function(
            """([selector, expected]) => document.querySelectorAll(selector).length > expected""",
            arg=["[data-project-variable-row]", initial_count],
            timeout=15000,
        )

        variable_row = self.page.locator("[data-project-variable-row]").filter(has_text="新数字变量").last
        variable_row.locator('[data-field="project-variable-name"]').fill("压力值")
        variable_row.locator('[data-field="project-variable-group"]').fill("数值组")
        variable_row.locator('[data-field="project-variable-description"]').fill("测试变量说明")
        variable_row.locator('[data-field="project-variable-default"]').fill("140")
        variable_row.locator('[data-field="project-variable-min"]').fill("0")
        variable_row.locator('[data-field="project-variable-max"]').fill("120")
        variable_row.get_by_role("button", name="保存变量").click()
        self.page.wait_for_function(
            """() => {
                return Array.from(document.querySelectorAll('[data-project-variable-row]')).some((row) => {
                    const name = row.querySelector('[data-field="project-variable-name"]')?.value;
                    const defaultValue = row.querySelector('[data-field="project-variable-default"]')?.value;
                    const minValue = row.querySelector('[data-field="project-variable-min"]')?.value;
                    const maxValue = row.querySelector('[data-field="project-variable-max"]')?.value;
                    return name === '压力值' && defaultValue === '120' && minValue === '0' && maxValue === '120';
                });
            }""",
            timeout=15000,
        )
        saved_row = self.page.locator("[data-project-variable-row]").filter(has_text="压力值").first
        self.assertEqual(saved_row.locator('[data-field="project-variable-type"]').input_value(), "number")
        self.assertEqual(saved_row.locator('[data-field="project-variable-default"]').input_value(), "120")
        self.assertEqual(saved_row.locator('[data-field="project-variable-min"]').input_value(), "0")
        self.assertEqual(saved_row.locator('[data-field="project-variable-max"]').input_value(), "120")
        self.assertEqual(saved_row.locator('[data-field="project-variable-group"]').input_value(), "数值组")
        self.assertEqual(saved_row.locator('[data-field="project-variable-description"]').input_value(), "测试变量说明")

    def test_preview_variable_library_can_rename_id_and_jump_to_reference(self) -> None:
        project_title = "浏览器烟测项目_VariableRename"
        self.create_blank_project(project_title)
        self.create_first_chapter()
        self.page.evaluate(
            """async () => {
                const bundleResponse = await fetch('/api/project-data');
                const bundle = await bundleResponse.json();
                const chapter = bundle.chapters[0];
                const scene = chapter.scenes[0];
                await fetch('/api/save-project-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        variables: {
                            variables: [
                                { id: 'var_score', name: '分数', type: 'number', defaultValue: 0, min: 0, max: 100 },
                            ],
                        },
                    }),
                });
                await fetch('/api/save-scene', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chapterId: chapter.chapterId,
                        sceneId: scene.id,
                        scene: {
                            ...scene,
                            blocks: [
                                { id: 'block_score', type: 'variable_add', variableId: 'var_score', value: 3 },
                            ],
                        },
                    }),
                });
            }"""
        )
        self.open_project_by_title(project_title)
        self.open_preview_screen()

        variable_row = self.page.locator('[data-project-variable-row][data-variable-id="var_score"]').first
        variable_row.locator('[data-field="project-variable-name"]').fill("积分")
        variable_row.get_by_role("button", name="根据变量名生成 ID").click()
        self.assertEqual(variable_row.locator('[data-field="project-variable-id"]').input_value(), "var_积分")
        variable_row.get_by_role("button", name="保存变量").click()
        self.page.locator(".system-dialog").filter(has_text="迁移变量逻辑 ID").first.wait_for(timeout=15000)
        self.page.get_by_role("button", name="迁移引用").click()
        self.page.wait_for_function(
            """async () => {
                const response = await fetch('/api/project-data');
                const bundle = await response.json();
                const variable = bundle.variables.variables.find((item) => item.id === 'var_积分');
                const block = bundle.chapters[0].scenes[0].blocks.find((item) => item.id === 'block_score');
                return variable?.name === '积分' && block?.variableId === 'var_积分';
            }""",
            timeout=15000,
        )

        saved_row = self.page.locator("[data-project-variable-row]").filter(has_text="积分").first
        saved_row.get_by_role("button", name="定位到卡片").first.click()
        self.page.wait_for_function(
            """() => {
                return document.querySelector('#screen-story')?.classList.contains('is-active')
                    && document.querySelector('.block-card.is-selected[data-block-id="block_score"]');
            }""",
            timeout=15000,
        )

    def test_preview_variable_library_can_delete_only_unused_variables(self) -> None:
        project_title = "浏览器烟测项目_UnusedVariables"
        self.create_blank_project(project_title)
        self.create_first_chapter()
        self.page.evaluate(
            """async () => {
                const bundleResponse = await fetch('/api/project-data');
                const bundle = await bundleResponse.json();
                const chapter = bundle.chapters[0];
                const scene = chapter.scenes[0];
                await fetch('/api/save-project-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        variables: {
                            variables: [
                                { id: 'var_used', name: '被使用变量', type: 'number', defaultValue: 0, group: '主线', status: 'active', description: '被剧情引用，不能清理' },
                                { id: 'var_unused', name: '未使用变量', type: 'string', defaultValue: 'draft', group: '临时', status: 'active', description: '应该被清理' },
                                { id: 'var_reserved', name: '预留变量', type: 'boolean', defaultValue: false, group: '系统', status: 'reserved', description: '未来路线使用，清理时要保留' },
                            ],
                        },
                    }),
                });
                await fetch('/api/save-scene', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chapterId: chapter.chapterId,
                        sceneId: scene.id,
                        scene: {
                            ...scene,
                            blocks: [
                                { id: 'block_used_variable', type: 'variable_add', variableId: 'var_used', value: 1 },
                            ],
                        },
                    }),
                });
            }"""
        )
        self.open_project_by_title(project_title)
        self.open_preview_screen()

        self.page.get_by_text("变量治理雷达").wait_for(timeout=15000)
        self.page.get_by_role("button", name=re.compile(r"未引用 · 2")).click()
        self.page.locator("[data-project-variable-row]").filter(has_text="未使用变量").first.wait_for(
            timeout=15000
        )
        self.page.locator("[data-project-variable-row]").filter(has_text="预留变量").first.wait_for(
            timeout=15000
        )
        self.assertEqual(self.page.locator("[data-project-variable-row]").filter(has_text="被使用变量").count(), 0)
        self.page.get_by_role("button", name=re.compile(r"已引用 · 1")).click()
        self.page.locator("[data-project-variable-row]").filter(has_text="被使用变量").first.wait_for(
            timeout=15000
        )
        self.assertEqual(self.page.locator("[data-project-variable-row]").filter(has_text="未使用变量").count(), 0)
        self.page.get_by_role("button", name=re.compile(r"预留 · 1")).click()
        self.page.locator("[data-project-variable-row]").filter(has_text="预留变量").first.wait_for(
            timeout=15000
        )
        self.page.get_by_role("button", name=re.compile(r"全部 · 3")).click()
        with self.page.expect_download() as download_info:
            self.page.get_by_role("button", name="导出治理报告").click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))
        report_content = download_path.read_text(encoding="utf-8-sig")
        self.assertIn("Canvasia Engine 变量治理报告", report_content)
        self.assertIn("被使用变量", report_content)
        self.assertIn("未使用变量", report_content)
        self.assertIn("预留变量", report_content)
        self.assertIn("未来路线使用，清理时要保留", report_content)

        self.page.get_by_role("button", name="清理未引用").click()
        self.page.locator(".system-dialog").filter(has_text="清理未引用变量").first.wait_for(timeout=15000)
        self.page.get_by_role("button", name="清理变量").click()
        self.page.wait_for_function(
            """async () => {
                const response = await fetch('/api/project-data');
                const bundle = await response.json();
                const variableIds = bundle.variables.variables.map((item) => item.id);
                return variableIds.includes('var_used') && variableIds.includes('var_reserved') && !variableIds.includes('var_unused');
            }""",
            timeout=15000,
        )

    def test_inspection_flow_can_run_regression_and_export_report(self) -> None:
        self.create_blank_project("浏览器烟测项目_C")
        self.create_first_chapter()
        self.open_inspection_screen()

        self.page.get_by_role("button", name="自动回归试玩路线测试").first.click()
        self.page.get_by_text("已测试路线").wait_for(timeout=15000)

        with self.page.expect_download() as download_info:
            self.page.get_by_role("button", name="导出巡检报告").first.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        report_content = download_path.read_text(encoding="utf-8-sig")
        self.assertIn("项目巡检报告", report_content)
        self.assertIn("自动回归试玩路线测试", report_content)

        with self.page.expect_download() as markdown_download_info:
            self.page.get_by_role("button", name="导出发布总控报告").first.click()
        markdown_download = markdown_download_info.value
        markdown_path = self.repo_copy / markdown_download.suggested_filename
        markdown_download.save_as(str(markdown_path))
        markdown_content = markdown_path.read_text(encoding="utf-8-sig")
        self.assertTrue(markdown_path.name.endswith(".md"))
        self.assertIn("# 浏览器烟测项目_C 发布前总控报告", markdown_content)
        self.assertIn("## 发布检查清单", markdown_content)
        self.assertIn("## 自动回归试玩路线", markdown_content)

        with self.page.expect_download() as json_download_info:
            self.page.get_by_role("button", name="导出 JSON 数据").first.click()
        json_download = json_download_info.value
        json_path = self.repo_copy / json_download.suggested_filename
        json_download.save_as(str(json_path))
        json_payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertTrue(json_path.name.endswith(".json"))
        self.assertEqual(json_payload["formatVersion"], 1)
        self.assertEqual(json_payload["project"]["title"], "浏览器烟测项目_C")
        self.assertIn("releaseChecklist", json_payload)
        self.assertIn("fixOrder", json_payload)
        self.assertIn("mediaBudget", json_payload["assets"])
        self.assertIn("summary", json_payload["regression"])

    def test_inspection_flags_number_variable_range_issues(self) -> None:
        self.create_blank_project("浏览器烟测项目_VariableRange")
        self.create_first_chapter()

        self.page.evaluate(
            """async (variables) => {
                const response = await fetch('/api/save-project-settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ variables: { variables } }),
                });
                if (!response.ok) {
                    throw new Error(await response.text());
                }
            }""",
            [
                {
                    "id": "var_score",
                    "name": "分数",
                    "type": "number",
                    "defaultValue": 150,
                    "min": 0,
                    "max": 100,
                },
                {
                    "id": "var_bad_range",
                    "name": "坏范围",
                    "type": "number",
                    "defaultValue": 5,
                    "min": 10,
                    "max": 1,
                },
                {
                    "id": "var_bad_bound",
                    "name": "坏边界",
                    "type": "number",
                    "defaultValue": 0,
                    "min": "oops",
                    "max": 10,
                },
            ],
        )
        self.open_project_by_title("浏览器烟测项目_VariableRange")

        self.open_inspection_screen()

        inspection = self.page.locator("#inspectionContent")
        inspection.get_by_text("数字变量默认值超出了范围，运行时会自动夹回范围内。").first.wait_for(
            timeout=15000
        )
        inspection.get_by_text("数字变量的范围上下限反了。").first.wait_for(timeout=15000)
        inspection.get_by_text("数字变量的最小值不是有效数字。").first.wait_for(timeout=15000)

    def test_preview_flow_can_export_windows_build(self) -> None:
        self.create_blank_project("浏览器烟测项目_D")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出 Windows 桌面包").click()
        download_link = self.page.get_by_role("link", name="下载桌面包压缩档")
        download_link.wait_for(timeout=60000)

        with self.page.expect_download() as download_info:
            download_link.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        self.assertGreater(download_path.stat().st_size, 0)

    def test_preview_flow_can_export_native_runtime_preview(self) -> None:
        self.create_blank_project("浏览器烟测项目_Native")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出原生 Runtime 包").click()
        self.page.locator(".detail-meta").filter(has_text="Python + pygame-ce 原生 Runtime").first.wait_for(
            timeout=20000
        )
        self.page.locator(".detail-meta").filter(has_text="RC 状态").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="压缩包 SHA-256").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="压缩包校验脚本").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="Release 附件索引").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="Release Notes 草稿").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="3D 资产清单").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="3D Markdown 摘要").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="3D 风险摘要文件").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="文件完整性状态").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="3D 风险摘要").first.wait_for(timeout=20000)
        self.page.locator(".detail-meta").filter(has_text="3D 风险拆分").first.wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开原生 RC 总报告").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开发布总控报告").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开发布总控 JSON").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开压缩包 SHA-256").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开压缩包校验 JSON").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 mac 压缩包校验脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Linux 压缩包校验脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Windows 压缩包校验脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Release 附件索引").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Release 附件 JSON").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Release Notes 草稿").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 mac 总控刷新脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Linux 总控刷新脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Windows 总控刷新脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开文件完整性报告").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开文件完整性 JSON").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 mac 完整性校验脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Linux 完整性校验脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 Windows 完整性校验脚本").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 3D 风险摘要").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 3D 资产清单").wait_for(timeout=20000)
        self.page.get_by_role("link", name="打开 3D 摘要").wait_for(timeout=20000)
        download_link = self.page.get_by_role("link", name="下载原生 Runtime 包压缩档")
        download_link.wait_for(timeout=40000)

        with self.page.expect_download() as download_info:
            download_link.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        self.assertGreater(download_path.stat().st_size, 0)

    def test_preview_flow_can_export_macos_and_linux_builds(self) -> None:
        self.create_blank_project("浏览器烟测项目_D2")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出 macOS 桌面包").click()
        self.page.locator(".detail-meta").filter(has_text="原生 .app 应用包").first.wait_for(timeout=20000)
        mac_download_link = self.page.get_by_role("link", name="下载桌面包压缩档")
        mac_download_link.wait_for(timeout=40000)

        with self.page.expect_download() as mac_download_info:
            mac_download_link.click()
        mac_download = mac_download_info.value
        mac_download_path = self.repo_copy / mac_download.suggested_filename
        mac_download.save_as(str(mac_download_path))
        self.assertTrue(mac_download_path.exists())
        self.assertGreater(mac_download_path.stat().st_size, 0)

        self.page.get_by_role("button", name="导出 Linux 桌面包").click()
        self.page.locator(".detail-meta").filter(has_text="原生 Linux 可执行目录").first.wait_for(timeout=20000)
        linux_download_link = self.page.get_by_role("link", name="下载桌面包压缩档")
        linux_download_link.wait_for(timeout=40000)

        with self.page.expect_download() as linux_download_info:
            linux_download_link.click()
        linux_download = linux_download_info.value
        linux_download_path = self.repo_copy / linux_download.suggested_filename
        linux_download.save_as(str(linux_download_path))
        self.assertTrue(linux_download_path.exists())
        self.assertGreater(linux_download_path.stat().st_size, 0)

    def test_preview_flow_can_export_editor_desktop_build(self) -> None:
        self.create_blank_project("浏览器烟测项目_Editor")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出编辑器桌面包").click()
        download_link = self.page.get_by_role("link", name="下载编辑器包压缩档")
        download_link.wait_for(timeout=90000)
        self.page.get_by_text("编辑器包目录：").wait_for(timeout=10000)
        if sys.platform == "darwin":
            self.page.get_by_role("link", name="下载 mac 安装包").wait_for(timeout=10000)
            self.page.get_by_text("mac 安装包：").wait_for(timeout=10000)

        with self.page.expect_download() as download_info:
            download_link.click()
        download = download_info.value
        download_path = self.repo_copy / download.suggested_filename
        download.save_as(str(download_path))

        self.assertTrue(download_path.exists())
        self.assertGreater(download_path.stat().st_size, 0)

    def test_preview_flow_can_export_editor_desktop_suite(self) -> None:
        self.create_blank_project("浏览器烟测项目_EditorSuite")
        self.create_first_chapter()
        self.open_preview_screen()

        self.page.get_by_role("button", name="导出三系统编辑器套装").click()
        self.page.get_by_role("link", name="打开三系统套装清单").wait_for(timeout=40000)
        self.page.get_by_text("已生成 3 组平台包").wait_for(timeout=15000)
        self.page.get_by_text("macOS：").wait_for(timeout=10000)
        self.page.get_by_text("Windows：").wait_for(timeout=10000)
        self.page.get_by_text("Linux：").wait_for(timeout=10000)
        self.page.get_by_text("安装器：已编译 Windows 安装器").wait_for(timeout=10000)
        self.page.get_by_text("已签名并加时间戳").wait_for(timeout=10000)
        self.page.get_by_role("link", name="打开维护者签名说明").wait_for(timeout=10000)
        self.page.get_by_role("link", name="打开维护者签名模板").wait_for(timeout=10000)
        self.page.get_by_role("link", name="打开签名自检脚本").wait_for(timeout=10000)

    def test_exported_player_can_formal_save_and_load(self) -> None:
        self.create_blank_project("浏览器烟测项目_E")
        self.create_first_chapter()
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            player_page.locator("#startButton").wait_for(timeout=20000)
            player_page.locator("#startButton").click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)

            player_page.locator("#systemMenuButton").click()
            player_page.locator("#systemMenu").wait_for(state="visible", timeout=10000)
            player_page.locator("#systemMenuOpenSaveButton").click()
            player_page.locator("#saveDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#saveDialog [data-save-slot='1']").click()
            player_page.wait_for_function(
                """() => {
                    const clearButton = document.querySelector("#saveDialog [data-clear-slot='1']");
                    return Boolean(clearButton) && !clearButton.disabled;
                }""",
                timeout=15000,
            )

            player_page.locator("#closeSaveDialogButton").click()
            player_page.locator("#saveDialog").wait_for(state="hidden", timeout=10000)

            player_page.locator("#systemMenuButton").click()
            player_page.locator("#systemMenuReturnTitleButton").click()
            player_page.locator("#returnTitleDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#confirmReturnTitleButton").click()
            player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)

            player_page.locator("#startLoadButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startLoadButton").click()
            player_page.locator("#saveDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#saveDialog [data-load-slot='1']").wait_for(timeout=10000)
            player_page.locator("#saveDialog [data-load-slot='1']").click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_open_archive_dialogs(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page)
            player_page.locator("#startVoiceReplayButton").wait_for(state="visible", timeout=10000)

            archive_buttons = [
                ("#startProfileButton", "#profileDialog", "#closeProfileDialogButton"),
                ("#startAchievementButton", "#achievementDialog", "#closeAchievementDialogButton"),
                ("#startChapterButton", "#chapterDialog", "#closeChapterDialogButton"),
                ("#startLocationButton", "#locationDialog", "#closeLocationDialogButton"),
                ("#startNarrationButton", "#narrationDialog", "#closeNarrationDialogButton"),
                ("#startRelationButton", "#relationDialog", "#closeRelationDialogButton"),
                ("#startCharacterButton", "#characterDialog", "#closeCharacterDialogButton"),
                ("#startEndingButton", "#endingDialog", "#closeEndingDialogButton"),
                ("#startGalleryButton", "#galleryDialog", "#closeGalleryDialogButton"),
                ("#startMusicRoomButton", "#musicRoomDialog", "#closeMusicRoomDialogButton"),
            ]

            for button_selector, dialog_selector, close_selector in archive_buttons:
                button = player_page.locator(button_selector)
                button.wait_for(state="visible", timeout=15000)
                button.click()
                player_page.locator(dialog_selector).wait_for(state="visible", timeout=10000)
                player_page.locator(close_selector).click()
                player_page.locator(dialog_selector).wait_for(state="hidden", timeout=10000)

        finally:
            player_page.close()

    def test_exported_player_sample_project_can_replay_chapter_and_open_music_room(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page)

            player_page.locator("#startChapterButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startChapterButton").click()
            player_page.locator("#chapterDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#chapterDialogList [data-chapter-replay]:not([disabled])").first.click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)

            player_page.locator("#systemMenuButton").click()
            player_page.locator("#systemMenu").wait_for(state="visible", timeout=10000)
            player_page.locator("#systemMenuReturnTitleButton").click()
            player_page.locator("#returnTitleDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#confirmReturnTitleButton").click()
            player_page.locator("#startOverlay").wait_for(state="visible", timeout=15000)

            player_page.locator("#startMusicRoomButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startMusicRoomButton").click()
            player_page.locator("#musicRoomDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#musicRoomDialog [data-music-room-play]:not([disabled])").first.click()
            player_page.wait_for_function(
                """() => {
                    const stopButton = document.querySelector("#musicRoomDialog [data-music-room-stop]");
                    const nowPlaying = document.querySelector("#musicRoomNowPlaying")?.textContent || "";
                    return Boolean(stopButton) && nowPlaying.includes("当前试听");
                }""",
                timeout=15000,
            )
            player_page.locator("#musicRoomDialog [data-music-room-stop]").click()
            player_page.locator("#closeMusicRoomDialogButton").click()
            player_page.locator("#musicRoomDialog").wait_for(state="hidden", timeout=10000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_replay_unlocked_ending(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_endings=True)

            player_page.locator("#startEndingButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startEndingButton").click()
            player_page.locator("#endingDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#endingDialogList [data-ending-replay]:not([disabled])").first.click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)
            player_page.wait_for_function(
                """() => {
                    const scene = document.querySelector("#sceneChip")?.textContent || "";
                    return scene.includes("普通告别");
                }""",
                timeout=10000,
            )
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_open_gallery_dialog(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_gallery=True)

            player_page.locator("#startGalleryButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startGalleryButton").click()
            player_page.locator("#galleryDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const summary = document.querySelector("#galleryDialogSummary")?.textContent || "";
                    const items = document.querySelectorAll("#galleryDialog [data-gallery-asset-id]");
                    return summary.includes("1 / 1") && items.length === 1;
                }""",
                timeout=10000,
            )
            player_page.locator("#closeGalleryDialogButton").click()
            player_page.locator("#galleryDialog").wait_for(state="hidden", timeout=10000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_can_open_voice_replay_dialog(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_voice_replay=True)

            player_page.locator("#startVoiceReplayButton").wait_for(state="visible", timeout=10000)
            player_page.locator("#startVoiceReplayButton").click()
            player_page.locator("#voiceReplayDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const summary = document.querySelector("#voiceReplayDialogSummary")?.textContent || "";
                    const entries = document.querySelectorAll("#voiceReplayDialog [data-voice-replay-id]");
                    return summary.includes("3 / 3") && entries.length === 3;
                }""",
                timeout=10000,
            )
            self.assertGreater(
                player_page.locator("#voiceReplayDialog [data-voice-replay-play]:not([disabled])").count(),
                0,
            )
            player_page.locator("#voiceReplayDialog [data-voice-replay-play]:not([disabled])").first.click()
            player_page.wait_for_timeout(300)
            player_page.locator("#closeVoiceReplayDialogButton").click()
            player_page.locator("#voiceReplayDialog").wait_for(state="hidden", timeout=10000)
        finally:
            player_page.close()

    def test_exported_player_sample_project_archive_dialogs_support_internal_selection(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_gallery=True)
            self.unlock_sample_player_collection_archives(player_page)

            player_page.locator("#startLocationButton").click()
            player_page.locator("#locationDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => document.querySelector("#locationDialogHero strong")?.textContent?.includes("教室黄昏")""",
                timeout=10000,
            )
            player_page.locator("#locationDialog [data-location-archive-id='bg_rooftop_evening']").click()
            player_page.wait_for_function(
                """() => document.querySelector("#locationDialogHero strong")?.textContent?.includes("屋顶晚风")""",
                timeout=10000,
            )
            player_page.locator("#closeLocationDialogButton").click()

            player_page.locator("#startNarrationButton").click()
            player_page.locator("#narrationDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#narrationDialog [data-narration-archive-id='scene_normal_goodnight:block_023:1']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#narrationDialogHero")?.textContent || "";
                    return hero.includes("今天的故事暂时停在这里");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeNarrationDialogButton").click()

            player_page.locator("#startRelationButton").click()
            player_page.locator("#relationDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#relationDialogHero")?.textContent || "";
                    return hero.includes("林若曦 × 顾言");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeRelationDialogButton").click()

            player_page.locator("#startCharacterButton").click()
            player_page.locator("#characterDialog").wait_for(state="visible", timeout=10000)
            player_page.locator("#characterDialog [data-character-archive-id='char_player']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#characterDialogHero")?.textContent || "";
                    return hero.includes("顾言") && hero.includes("默认站位");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeCharacterDialogButton").click()

            player_page.locator("#startGalleryButton").click()
            player_page.locator("#galleryDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#galleryDialogHero")?.textContent || "";
                    const image = document.querySelector("#galleryDialogHero img");
                    return hero.includes("黄昏回想") && Boolean(image);
                }""",
                timeout=10000,
            )
            player_page.locator("#closeGalleryDialogButton").click()
        finally:
            player_page.close()

    def test_exported_player_sample_project_voice_replay_selection_updates_hero(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            self.unlock_sample_player_title_features(player_page, include_voice_replay=True)

            player_page.locator("#startVoiceReplayButton").click()
            player_page.locator("#voiceReplayDialog").wait_for(state="visible", timeout=10000)
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#voiceReplayDialogHero")?.textContent || "";
                    return hero.includes("林若曦");
                }""",
                timeout=10000,
            )
            player_page.locator("#voiceReplayDialog [data-voice-replay-id='scene_classroom_sunset:block_006:7']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#voiceReplayDialogHero")?.textContent || "";
                    return hero.includes("顾言") && hero.includes("是吗？我怎么觉得是因为你心情很好");
                }""",
                timeout=10000,
            )
            player_page.locator("#voiceReplayDialog [data-voice-replay-id='scene_classroom_sunset:block_007:8']").click()
            player_page.wait_for_function(
                """() => {
                    const hero = document.querySelector("#voiceReplayDialogHero")?.textContent || "";
                    return hero.includes("林若曦") && hero.includes("那你要不要陪我一起走回去");
                }""",
                timeout=10000,
            )
            player_page.locator("#closeVoiceReplayDialogButton").click()
        finally:
            player_page.close()

    def test_exported_player_sample_project_renders_particle_effect_runtime(self) -> None:
        self.open_project_by_title("心跳时差")
        player_url = self.export_web_build()

        player_page = self.context.new_page()
        try:
            player_page.goto(player_url, wait_until="domcontentloaded")
            player_page.locator("#startButton").click()
            player_page.locator("#startOverlay").wait_for(state="hidden", timeout=15000)
            player_page.locator("#continueButton").click()
            player_page.wait_for_function(
                """() => {
                    const layer = document.querySelector("#particleLayer .particle-layer");
                    if (!layer) {
                        return false;
                    }
                    const particleCount = layer.querySelectorAll(".particle-item").length;
                    const speaker = document.querySelector("#speakerName")?.textContent || "";
                    return layer.dataset.particlePreset === "snow"
                      && layer.dataset.particleIntensity === "medium"
                      && layer.dataset.particleSpeed === "medium"
                      && layer.dataset.particleArea === "full"
                      && speaker.includes("粒子特效")
                      && particleCount > 0;
                }""",
                timeout=10000,
            )
            player_page.locator("#continueButton").click()
            player_page.wait_for_function(
                """() => Boolean(document.querySelector("#particleLayer .particle-layer"))""",
                timeout=10000,
            )
        finally:
            player_page.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
