import unittest
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

PUBLIC_SURFACE_ROOTS = (
    "README.md",
    "README.zh-CN.md",
    "README.ja-JP.md",
    "LICENSE",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs",
    "prototype_editor",
    "native_runtime",
    "export_player_template",
    "desktop_runtime",
    "run_editor.py",
    "editor_distribution.json",
    "tools",
    ".github",
)

PUBLIC_TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

PUBLIC_TEXT_FILENAMES = {
    "LICENSE",
}

PUBLIC_RELEASE_LITERAL_BLOCKLIST = (
    "按钮暂未接线",
    "这个按钮暂时还没有接上功能",
    "项目中心模块暂时不可用",
    "这组演出级预设暂时不可用",
    "najinxiang",
    "/Users/na",
    "ChatGPT",
    "AI对我",
    "对我说",
    "TODO",
    "FIXME",
)

PUBLIC_RELEASE_PATTERN_BLOCKLIST = (
    ("openai_api_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github_classic_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github_fine_grained_token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("license_claim_open_source_visible", re.compile(r"开源可见")),
    ("mac_or_linux_home_path", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+(?:/|$)")),
    ("windows_user_path", re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\")),
)


def iter_public_text_files():
    for relative_root in PUBLIC_SURFACE_ROOTS:
        root = ROOT_DIR / relative_root
        if root.is_file():
            candidates = [root]
        elif root.is_dir():
            candidates = [path for path in root.rglob("*") if path.is_file()]
        else:
            continue

        for path in candidates:
            if path.suffix.lower() in PUBLIC_TEXT_SUFFIXES or path.name in PUBLIC_TEXT_FILENAMES:
                yield path


def collect_public_surface_findings(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    relative_path = path.relative_to(ROOT_DIR)

    for blocked in PUBLIC_RELEASE_LITERAL_BLOCKLIST:
        if blocked in text:
            findings.append(f"{relative_path}: {blocked}")

    for label, pattern in PUBLIC_RELEASE_PATTERN_BLOCKLIST:
        if pattern.search(text):
            findings.append(f"{relative_path}: {label}")

    return findings


class ReleasePublicSurfaceTests(unittest.TestCase):
    def test_public_onboarding_copy_stays_demo_first(self) -> None:
        surfaces = {
            "README.md": (ROOT_DIR / "README.md").read_text(encoding="utf-8"),
            "README.zh-CN.md": (ROOT_DIR / "README.zh-CN.md").read_text(encoding="utf-8"),
            "README.ja-JP.md": (ROOT_DIR / "README.ja-JP.md").read_text(encoding="utf-8"),
            "docs/creator_quick_start_zh-CN.md": (ROOT_DIR / "docs" / "creator_quick_start_zh-CN.md").read_text(
                encoding="utf-8"
            ),
            "docs/index.html": (ROOT_DIR / "docs" / "index.html").read_text(encoding="utf-8"),
            "prototype_editor/modules/project_center.js": (
                ROOT_DIR / "prototype_editor" / "modules" / "project_center.js"
            ).read_text(encoding="utf-8"),
            "prototype_editor/modules/beginner_tutorial.js": (
                ROOT_DIR / "prototype_editor" / "modules" / "beginner_tutorial.js"
            ).read_text(encoding="utf-8"),
        }

        expected_snippets = {
            "README.md": ["create a playable Demo project", "create a blank project"],
            "README.zh-CN.md": ["新建“可试玩 Demo”", "新建空白项目"],
            "README.ja-JP.md": ["プレイ可能な Demo プロジェクト", "空白プロジェクト"],
            "docs/creator_quick_start_zh-CN.md": ["新建可试玩 Demo", "替换或上传背景、人物、音乐"],
            "docs/index.html": ["View Preview Releases"],
            "prototype_editor/modules/project_center.js": ["推荐从可试玩 Demo 开始", "新建空白项目"],
            "prototype_editor/modules/beginner_tutorial.js": ["第一次建议先生成可试玩 Demo", "新建空白项目"],
        }
        stale_first_run_copy = (
            "Create or open a project.",
            "从“项目中心”新建空白项目。",
            "点“新建空白项目”。",
            "默认从空白项目开始",
            "可先创建一个空白项目，或继续已有作品。",
            "空のプロジェクトでは、まず starter kit",
            "Download Preview",
        )

        for relative_path, snippets in expected_snippets.items():
            text = surfaces[relative_path]
            for snippet in snippets:
                self.assertIn(snippet, text, f"{relative_path} should keep Demo-first onboarding copy aligned")

        joined_surface = "\n".join(surfaces.values())
        for stale_copy in stale_first_run_copy:
            self.assertNotIn(stale_copy, joined_surface)

    def test_public_release_surface_has_no_draft_or_internal_copy(self) -> None:
        findings: list[str] = []
        for path in iter_public_text_files():
            text = path.read_text(encoding="utf-8")
            findings.extend(collect_public_surface_findings(path, text))

        self.assertEqual(
            findings,
            [],
            "Public-facing release files should not contain draft, internal, or sensitive copy:\n"
            + "\n".join(findings),
        )

    def test_public_release_surface_guard_catches_privacy_and_secret_shapes(self) -> None:
        synthetic_path = ROOT_DIR / "docs" / "synthetic.md"
        sample = "\n".join(
            [
                "local path /Users/na/Game Engine",
                "old account najinxiang",
                "temporary ChatGPT image name",
                "linux home /home/demo-user/project",
                r"windows home C:\Users\demo-user\project",
                "token sk-" + "a" * 24,
                "github ghp_" + "b" * 24,
                "fine github_pat_" + "c" * 32,
                "-----BEGIN PRIVATE KEY-----",
                "license drift 开源可见",
            ]
        )

        findings = collect_public_surface_findings(synthetic_path, sample)

        self.assertIn("docs/synthetic.md: /Users/na", findings)
        self.assertIn("docs/synthetic.md: najinxiang", findings)
        self.assertIn("docs/synthetic.md: ChatGPT", findings)
        self.assertIn("docs/synthetic.md: mac_or_linux_home_path", findings)
        self.assertIn("docs/synthetic.md: windows_user_path", findings)
        self.assertIn("docs/synthetic.md: openai_api_key", findings)
        self.assertIn("docs/synthetic.md: github_classic_token", findings)
        self.assertIn("docs/synthetic.md: github_fine_grained_token", findings)
        self.assertIn("docs/synthetic.md: private_key", findings)
        self.assertIn("docs/synthetic.md: license_claim_open_source_visible", findings)


if __name__ == "__main__":
    unittest.main()
