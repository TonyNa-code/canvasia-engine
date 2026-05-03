#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "release_preview"
RELEASE_DRAFT_PATH = ROOT_DIR / "docs" / "github" / "preview-release-draft.md"
DOWNLOAD_GUIDE_MARKER = "<!-- TNE_GENERATED_DOWNLOAD_GUIDE -->"

EXCLUDED_PRIVACY_DIRS = {
    ".git",
    ".export_runtime_cache",
    ".pytest_cache",
    ".tmp_brand_preview",
    "__pycache__",
    "exports",
    "playwright-report",
    "projects",
    "release_preview",
    "test-results",
}

SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("mac_local_user_path", re.compile(r"/Users/[^/\\s]+(?:/|\\b)")),
    ("windows_local_user_path", re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\\\\s]+", re.IGNORECASE)),
    ("private_key", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
    ("github_token", re.compile(r"(?:ghp_|github_pat_)[A-Za-z0-9_]+")),
    ("api_key_assignment", re.compile(r"api[_-]?key\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE)),
    ("password_assignment", re.compile(r"password\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE)),
    ("secret_assignment", re.compile(r"secret\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE)),
]


def run_command(args: list[str], *, cwd: Path = ROOT_DIR) -> tuple[int, str, str]:
    try:
        result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def current_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def human_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError:
        return str(path)


def git_info() -> dict[str, Any]:
    _, branch, _ = run_command(["git", "branch", "--show-current"])
    _, commit, _ = run_command(["git", "rev-parse", "HEAD"])
    _, short_commit, _ = run_command(["git", "rev-parse", "--short", "HEAD"])
    _, status, _ = run_command(["git", "status", "--short"])
    _, remote, _ = run_command(["git", "config", "--get", "remote.origin.url"])
    _, tags, _ = run_command(["git", "tag", "--points-at", "HEAD"])
    return {
        "branch": branch,
        "commit": commit,
        "shortCommit": short_commit,
        "remote": remote,
        "tagsAtHead": [line.strip() for line in tags.splitlines() if line.strip()],
        "workingTreeClean": not bool(status.strip()),
        "statusLines": [line for line in status.splitlines() if line.strip()],
    }


def parse_github_repo(remote_url: str) -> str:
    remote_url = remote_url.strip()
    patterns = [
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
        r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
        r"git@[^:]+:(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
        r"ssh://git@[^/]+/(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote_url)
        if match:
            return f"{match.group('owner')}/{match.group('repo')}"
    return ""


def github_ci_status(git: dict[str, Any], *, skip_network: bool = False) -> dict[str, Any]:
    if skip_network:
        return {"checked": False, "reason": "network skipped"}
    repo = parse_github_repo(str(git.get("remote") or ""))
    if not repo:
        return {"checked": False, "reason": "remote is not a GitHub repository"}
    url = f"https://api.github.com/repos/{repo}/actions/runs?branch={git.get('branch')}&per_page=5"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.load(response)
    except Exception as exc:  # noqa: BLE001 - release prep should report, not crash.
        return {"checked": False, "reason": f"{type(exc).__name__}: {exc}"}
    commit = str(git.get("commit") or "")
    for run in data.get("workflow_runs", []):
        if run.get("head_sha") == commit:
            return {
                "checked": True,
                "name": run.get("name") or "",
                "status": run.get("status") or "",
                "conclusion": run.get("conclusion") or "",
                "url": run.get("html_url") or "",
            }
    latest = data.get("workflow_runs", [{}])[0] if data.get("workflow_runs") else {}
    return {
        "checked": True,
        "status": "not_found_for_commit",
        "conclusion": "",
        "latestRun": {
            "shortCommit": str(latest.get("head_sha") or "")[:7],
            "status": latest.get("status") or "",
            "conclusion": latest.get("conclusion") or "",
            "url": latest.get("html_url") or "",
        },
    }


def choose_release_tag(git: dict[str, Any], release_tag: str) -> str:
    explicit_tag = release_tag.strip()
    if explicit_tag:
        return explicit_tag
    tags = [str(tag).strip() for tag in git.get("tagsAtHead") or [] if str(tag).strip()]
    return sorted(tags)[0] if tags else ""


def github_release_status(
    git: dict[str, Any],
    artifacts: list[dict[str, Any]],
    *,
    release_tag: str,
    skip_reason: str = "",
) -> dict[str, Any]:
    if skip_reason:
        return {"checked": False, "reason": skip_reason}
    repo = parse_github_repo(str(git.get("remote") or ""))
    if not repo:
        return {"checked": False, "reason": "remote is not a GitHub repository"}
    tag = choose_release_tag(git, release_tag)
    if not tag:
        return {"checked": False, "reason": "no release tag provided and current commit has no tag"}

    encoded_tag = urllib.parse.quote(tag, safe="")
    url = f"https://api.github.com/repos/{repo}/releases/tags/{encoded_tag}"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {
                "checked": True,
                "exists": False,
                "tag": tag,
                "url": "",
                "assets": [],
                "matchedAssets": [],
                "missingAssets": sorted({artifact["name"] for artifact in artifacts}),
                "extraAssets": [],
                "sizeMismatches": [],
            }
        return {"checked": False, "tag": tag, "reason": f"HTTPError {exc.code}: {exc.reason}"}
    except Exception as exc:  # noqa: BLE001 - release prep should report, not crash.
        return {"checked": False, "tag": tag, "reason": f"{type(exc).__name__}: {exc}"}

    remote_assets = [
        {
            "name": str(asset.get("name") or ""),
            "size": int(asset.get("size") or 0),
            "sizeLabel": human_size(int(asset.get("size") or 0)),
            "updatedAt": asset.get("updated_at") or "",
            "url": asset.get("browser_download_url") or "",
        }
        for asset in data.get("assets", [])
        if asset.get("name")
    ]
    local_by_name = {artifact["name"]: artifact for artifact in artifacts}
    remote_by_name = {asset["name"]: asset for asset in remote_assets}
    local_names = set(local_by_name)
    remote_names = set(remote_by_name)
    matched = sorted(local_names & remote_names)
    size_mismatches = []
    for name in matched:
        local_size = int(local_by_name[name].get("size") or 0)
        remote_size = int(remote_by_name[name].get("size") or 0)
        if local_size != remote_size:
            size_mismatches.append(
                {
                    "name": name,
                    "localSize": local_size,
                    "localSizeLabel": human_size(local_size),
                    "releaseSize": remote_size,
                    "releaseSizeLabel": human_size(remote_size),
                }
            )

    return {
        "checked": True,
        "exists": True,
        "tag": tag,
        "name": data.get("name") or "",
        "url": data.get("html_url") or "",
        "draft": bool(data.get("draft")),
        "prerelease": bool(data.get("prerelease")),
        "publishedAt": data.get("published_at") or "",
        "assets": remote_assets,
        "matchedAssets": matched,
        "missingAssets": sorted(local_names - remote_names),
        "extraAssets": sorted(remote_names - local_names),
        "sizeMismatches": size_mismatches,
    }


def tracked_files() -> list[Path]:
    code, stdout, _ = run_command(["git", "ls-files", "-z"])
    if code != 0:
        return []
    return [ROOT_DIR / name for name in stdout.split("\0") if name]


def is_excluded(path: Path) -> bool:
    try:
        parts = path.relative_to(ROOT_DIR).parts
    except ValueError:
        parts = path.parts
    return any(part in EXCLUDED_PRIVACY_DIRS for part in parts)


def build_sensitive_patterns(extra_patterns: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    patterns = list(SENSITIVE_PATTERNS)
    for index, pattern in enumerate(extra_patterns, start=1):
        pattern = pattern.strip()
        if not pattern:
            continue
        patterns.append((f"extra_sensitive_{index}", re.compile(re.escape(pattern), re.IGNORECASE)))
    return patterns


def scan_privacy(extra_patterns: list[str]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    large_files: list[dict[str, Any]] = []
    patterns = build_sensitive_patterns(extra_patterns)
    for path in tracked_files():
        if is_excluded(path) or not path.is_file():
            continue
        size = path.stat().st_size
        if size > 20 * 1024 * 1024:
            large_files.append({"path": relative(path), "size": size, "sizeLabel": human_size(size)})
        if size > 2 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for label, pattern in patterns:
                if pattern.search(line):
                    if relative(path) == "tools/release/prepare_preview_release.py" and "re.compile" in line:
                        continue
                    findings.append(
                        {
                            "type": label,
                            "path": relative(path),
                            "line": line_number,
                            "preview": line.strip()[:180],
                        }
                    )
    return {
        "sensitiveFindings": findings,
        "largeTrackedFiles": large_files,
        "passed": not findings and not large_files,
    }


def classify_artifact(path: Path) -> str:
    text = path.as_posix().lower()
    if "editor_suite" in text:
        return "editor-suite"
    if "editor_build" in text:
        return "editor-package"
    if "native_runtime" in text:
        return "native-runtime"
    if "web_build" in text:
        return "web-runtime"
    if "windows" in text:
        return "windows-package"
    if "macos" in text:
        return "macos-package"
    if "linux" in text:
        return "linux-package"
    return "other"


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def archive_companion_dir(path: Path) -> Path:
    exports_dir = ROOT_DIR / "exports"
    if path.parent != exports_dir:
        return path.parent
    for suffix in (".tar.gz", ".tgz", ".zip"):
        if path.name.endswith(suffix):
            return path.parent / path.name[: -len(suffix)]
    return path.parent / path.stem


def artifact_metadata(path: Path) -> dict[str, Any]:
    companion_dir = archive_companion_dir(path)
    export_manifest = load_json(companion_dir / "export_manifest.json")
    suite_manifest = load_json(companion_dir / "editor_suite_manifest.json")
    release_check = load_json(companion_dir / "native-runtime-release-check.json")
    stat = path.stat()
    metadata = {
        "path": relative(path),
        "name": path.name,
        "kind": classify_artifact(path),
        "size": stat.st_size,
        "sizeLabel": human_size(stat.st_size),
        "modifiedAt": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
        "sha256": file_sha256(path),
        "manifest": relative(companion_dir / "export_manifest.json") if export_manifest else "",
        "suiteManifest": relative(companion_dir / "editor_suite_manifest.json") if suite_manifest else "",
        "releaseCheck": relative(companion_dir / "native-runtime-release-check.json") if release_check else "",
        "releaseCheckSummary": (release_check or {}).get("summary") or {},
    }
    if export_manifest:
        metadata["releaseVersion"] = (export_manifest.get("engine") or {}).get("releaseVersion") or ""
        metadata["projectTitle"] = (export_manifest.get("project") or {}).get("title") or ""
        metadata["targetLabel"] = (export_manifest.get("engine") or {}).get("exportTargetLabel") or ""
    if suite_manifest:
        metadata["releaseVersion"] = (suite_manifest.get("engine") or {}).get("releaseVersion") or ""
        metadata["targetLabel"] = (suite_manifest.get("engine") or {}).get("packageTargetLabel") or ""
    return metadata


def discover_artifacts(max_artifacts: int) -> list[dict[str, Any]]:
    exports_dir = ROOT_DIR / "exports"
    if not exports_dir.exists():
        return []
    candidates: list[Path] = []
    for path in exports_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(exports_dir).parts
        except ValueError:
            continue
        if len(relative_parts) > 2:
            continue
        if path.name.endswith((".zip", ".tar.gz", ".tgz")):
            candidates.append(path)
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return [artifact_metadata(path) for path in candidates[:max_artifacts]]


def has_release_check_errors(artifact: dict[str, Any]) -> bool:
    summary = artifact.get("releaseCheckSummary") or {}
    return int(summary.get("errors") or 0) > 0


ARTIFACT_KIND_LABELS = {
    "editor-suite": "Editor app bundle",
    "editor-package": "Editor package",
    "native-runtime": "Native Runtime package",
    "web-runtime": "Web runtime package",
    "windows-package": "Windows package",
    "macos-package": "macOS package",
    "linux-package": "Linux package",
    "other": "Release asset",
}


def artifact_download_hint(artifact: dict[str, Any]) -> str:
    kind = str(artifact.get("kind") or "other")
    name = str(artifact.get("name") or "").lower()
    if kind in {"editor-suite", "editor-package"}:
        return "Download this if you want to try the editor as an app."
    if kind == "native-runtime":
        return "Download this if you want to test a game exported with the Native Runtime."
    if kind == "web-runtime":
        return "Download this if you want a browser-playable game build."
    if kind == "windows-package" or "windows" in name:
        return "Windows users should choose this package."
    if kind == "macos-package" or "macos" in name:
        return "macOS users should choose this package."
    if kind == "linux-package" or "linux" in name:
        return "Linux users should choose this package."
    return "Supplementary release asset."


PLATFORM_ORDER = {"macos": 0, "windows": 1, "linux": 2, "unknown": 9}
PUBLIC_ARTIFACT_KIND_ORDER = {
    "editor-suite": 0,
    "editor-package": 0,
    "macos-package": 1,
    "windows-package": 1,
    "linux-package": 1,
    "native-runtime": 2,
    "web-runtime": 3,
    "other": 9,
}


def artifact_platform(artifact: dict[str, Any]) -> str:
    text = f"{artifact.get('name') or ''} {artifact.get('path') or ''}".lower()
    if "macos" in text or "darwin" in text or text.endswith(".app"):
        return "macos"
    if "windows" in text or text.endswith(".exe") or text.endswith(".msi"):
        return "windows"
    if "linux" in text or "appimage" in text:
        return "linux"
    return "unknown"


def public_artifact_bucket(artifact: dict[str, Any]) -> tuple[str, str]:
    kind = str(artifact.get("kind") or "other")
    if kind in {"editor-suite", "editor-package", "macos-package", "windows-package", "linux-package"}:
        return kind, artifact_platform(artifact)
    if kind in {"native-runtime", "web-runtime"}:
        return kind, "latest"
    return kind, str(artifact.get("name") or "")


def public_artifact_sort_key(artifact: dict[str, Any]) -> tuple[int, int, str]:
    kind = str(artifact.get("kind") or "other")
    return (
        PUBLIC_ARTIFACT_KIND_ORDER.get(kind, PUBLIC_ARTIFACT_KIND_ORDER["other"]),
        PLATFORM_ORDER.get(artifact_platform(artifact), PLATFORM_ORDER["unknown"]),
        str(artifact.get("name") or "").lower(),
    )


def select_public_release_artifacts(artifacts: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    selected_by_bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for artifact in artifacts:
        bucket = public_artifact_bucket(artifact)
        if bucket not in selected_by_bucket:
            selected_by_bucket[bucket] = artifact
    selected = sorted(selected_by_bucket.values(), key=public_artifact_sort_key)
    return selected[:limit]


def build_warnings(report: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    git = report["git"]
    ci = report["githubActions"]
    release = report.get("githubRelease") or {}
    privacy = report["privacy"]
    if not git["workingTreeClean"]:
        warnings.append("Working tree is not clean; commit or discard local changes before tagging a release.")
    if ci.get("checked") and not (ci.get("status") == "completed" and ci.get("conclusion") == "success"):
        warnings.append("GitHub Actions is not green for the current commit.")
    if not ci.get("checked"):
        warnings.append(f"GitHub Actions status was not checked: {ci.get('reason')}")
    if privacy["sensitiveFindings"]:
        warnings.append("Privacy scan found potential sensitive strings.")
    if privacy["largeTrackedFiles"]:
        warnings.append("Tracked files larger than 20 MB were found.")
    if not report["artifacts"]:
        warnings.append("No local release artifacts were found under exports/.")
    if release.get("checked"):
        if not release.get("exists", True):
            warnings.append(f"GitHub Release `{release.get('tag')}` does not exist yet.")
        elif release.get("exists"):
            if release.get("draft"):
                warnings.append(f"GitHub Release `{release.get('tag')}` is still a draft.")
            if not release.get("prerelease"):
                warnings.append(f"GitHub Release `{release.get('tag')}` is not marked as a prerelease.")
            if release.get("missingAssets"):
                names = ", ".join(f"`{name}`" for name in release["missingAssets"])
                warnings.append(f"GitHub Release `{release.get('tag')}` is missing suggested artifacts: {names}.")
            if release.get("extraAssets"):
                names = ", ".join(f"`{name}`" for name in release["extraAssets"])
                warnings.append(f"GitHub Release `{release.get('tag')}` has assets not in the current local manifest: {names}.")
            if release.get("sizeMismatches"):
                names = ", ".join(f"`{item['name']}`" for item in release["sizeMismatches"])
                warnings.append(f"GitHub Release `{release.get('tag')}` has asset size mismatches: {names}.")
    return warnings


def render_download_guide(report: dict[str, Any]) -> str:
    lines = [
        "## Download Guide",
        "",
        "Choose the package that matches what you want to do:",
        "",
        "| Goal | Recommended file | Notes |",
        "| --- | --- | --- |",
        "| Try the editor without cloning source | Editor package for your OS, if attached | Preview packages may be unsigned. See the notes below before opening them. |",
        "| Run from source | Source code archive | Requires Python 3. Use the start script for your OS. |",
        "| Test an exported game | Native Runtime or web runtime package, if attached | Native Runtime packages include their own validation reports and integrity checks. |",
        "| Verify a download | `.sha256`, `.checksum.json`, or `.verify.*` companion files | These are optional but recommended for public releases. |",
        "",
    ]
    artifacts = report.get("artifacts") or []
    public_artifacts = report.get("publicArtifacts") or select_public_release_artifacts(artifacts)
    if public_artifacts:
        lines.extend(["### Recommended Assets", "", "| File | Type | Size | Best for |", "| --- | --- | --- | --- |"])
        for artifact in public_artifacts:
            kind = str(artifact.get("kind") or "other")
            lines.append(
                "| "
                f"`{artifact.get('name') or ''}` | "
                f"{ARTIFACT_KIND_LABELS.get(kind, ARTIFACT_KIND_LABELS['other'])} | "
                f"{artifact.get('sizeLabel') or 'n/a'} | "
                f"{artifact_download_hint(artifact)} |"
            )
        omitted_count = max(0, len(artifacts) - len(public_artifacts))
        if omitted_count:
            lines.extend(
                [
                    "",
                    f"{omitted_count} additional local artifact(s) are available in the generated upload manifest. Keep the public Release page focused on the newest recommended downloads.",
                ]
            )
        lines.append("")
    else:
        lines.extend(
            [
                "No binary package is attached in this generated draft yet. Use the source code archive, or wait for platform packages to be uploaded to the Release assets area.",
                "",
            ]
        )
    lines.extend(
        [
            "### First Launch",
            "",
            "- macOS: if an unsigned app is blocked, right-click the app and choose Open. Only do this for packages downloaded from the official Release page.",
            "- Windows: unsigned Preview builds may show a SmartScreen warning. Verify the package checksum before opening it.",
            "- Linux: extract the archive, make the launcher executable if needed, then run it from the extracted folder.",
            "- Source mode: install Python 3, then run `start_editor.command`, `start_editor.cmd`, or `start_editor.sh` for your platform.",
            "",
        ]
    )
    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    git = git_info()
    extra_sensitive = list(args.extra_sensitive or [])
    discovered_artifacts = discover_artifacts(args.max_artifacts)
    accepted_artifacts = [artifact for artifact in discovered_artifacts if not has_release_check_errors(artifact)]
    rejected_artifacts = [artifact for artifact in discovered_artifacts if has_release_check_errors(artifact)]
    public_artifacts = select_public_release_artifacts(accepted_artifacts)
    release_skip_reason = ""
    if args.skip_network:
        release_skip_reason = "network skipped"
    elif args.skip_release_check:
        release_skip_reason = "release check skipped"
    report = {
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "git": git,
        "githubActions": github_ci_status(git, skip_network=args.skip_network),
        "privacy": scan_privacy(extra_sensitive),
        "artifacts": accepted_artifacts,
        "publicArtifacts": public_artifacts,
        "rejectedArtifacts": rejected_artifacts,
        "githubRelease": github_release_status(
            git,
            public_artifacts,
            release_tag=args.release_tag,
            skip_reason=release_skip_reason,
        ),
    }
    report["warnings"] = build_warnings(report)
    report["readyForPreviewTag"] = not report["warnings"]
    return report


def render_upload_manifest(report: dict[str, Any]) -> str:
    lines = [
        "# Preview Release Upload Manifest",
        "",
        f"- Generated: `{report['generatedAt']}`",
        f"- Branch: `{report['git']['branch']}`",
        f"- Commit: `{report['git']['shortCommit']}`",
        f"- Working tree clean: `{report['git']['workingTreeClean']}`",
        "",
        "## GitHub Actions",
        "",
    ]
    ci = report["githubActions"]
    if ci.get("checked"):
        lines.extend(
            [
                f"- Status: `{ci.get('status', '')}`",
                f"- Conclusion: `{ci.get('conclusion', '')}`",
                f"- URL: {ci.get('url', '') or 'n/a'}",
            ]
        )
    else:
        lines.append(f"- Not checked: {ci.get('reason')}")
    lines.extend(["", "## GitHub Release Page", ""])
    release = report.get("githubRelease") or {}
    if release.get("checked"):
        if release.get("exists"):
            lines.extend(
                [
                    f"- Tag: `{release.get('tag', '')}`",
                    f"- Name: `{release.get('name', '')}`",
                    f"- URL: {release.get('url', '') or 'n/a'}",
                    f"- Prerelease: `{release.get('prerelease')}`",
                    f"- Assets on GitHub: `{len(release.get('assets') or [])}`",
                    f"- Matched suggested assets: `{len(release.get('matchedAssets') or [])}`",
                ]
            )
            if release.get("missingAssets"):
                lines.append(f"- Missing suggested assets: {', '.join(f'`{name}`' for name in release['missingAssets'])}")
            if release.get("extraAssets"):
                lines.append(f"- Extra release assets: {', '.join(f'`{name}`' for name in release['extraAssets'])}")
            if release.get("sizeMismatches"):
                names = ", ".join(f"`{item['name']}`" for item in release["sizeMismatches"])
                lines.append(f"- Size mismatches: {names}")
        else:
            lines.extend(
                [
                    f"- Tag: `{release.get('tag', '')}`",
                    "- Release page was not found yet.",
                ]
            )
    else:
        lines.append(f"- Not checked: {release.get('reason')}")
    lines.extend(["", "## Privacy Gate", ""])
    privacy = report["privacy"]
    lines.append(f"- Passed: `{privacy['passed']}`")
    lines.append(f"- Sensitive findings: `{len(privacy['sensitiveFindings'])}`")
    lines.append(f"- Large tracked files: `{len(privacy['largeTrackedFiles'])}`")
    lines.extend(["", "## Suggested Upload Artifacts", ""])
    if not report["artifacts"]:
        lines.append("- No local artifacts found. Generate fresh exports before publishing.")
    public_artifact_names = {artifact["name"] for artifact in report.get("publicArtifacts") or []}
    if public_artifact_names:
        lines.extend(
            [
                "These are the public Release assets checked against GitHub:",
                "",
                *[f"- `{name}`" for name in sorted(public_artifact_names)],
                "",
                "All accepted local artifacts are listed below for maintenance and archival review:",
                "",
            ]
        )
    for artifact in report["artifacts"]:
        summary = artifact.get("releaseCheckSummary") or {}
        release_note = ""
        if summary:
            release_note = f" release-check errors={summary.get('errors', 0)} warnings={summary.get('warnings', 0)}"
        visibility_note = " public-release" if artifact["name"] in public_artifact_names else " local-only"
        lines.extend(
            [
                f"### `{artifact['name']}`",
                "",
                f"- Path: `{artifact['path']}`",
                f"- Kind: `{artifact['kind']}`",
                f"- Size: `{artifact['sizeLabel']}`",
                f"- SHA256: `{artifact['sha256']}`",
                f"- Modified: `{artifact['modifiedAt']}`",
                f"- Notes:{visibility_note}{release_note}",
                "",
            ]
        )
    rejected = report.get("rejectedArtifacts") or []
    if rejected:
        lines.extend(["## Rejected Local Artifacts", ""])
        for artifact in rejected:
            summary = artifact.get("releaseCheckSummary") or {}
            lines.append(
                f"- `{artifact['path']}` rejected because release-check errors={summary.get('errors', 0)} warnings={summary.get('warnings', 0)}."
            )
        lines.append("")
    lines.extend(["## Warnings", ""])
    if report["warnings"]:
        lines.extend(f"- {warning}" for warning in report["warnings"])
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def render_release_body(report: dict[str, Any]) -> str:
    body = RELEASE_DRAFT_PATH.read_text(encoding="utf-8") if RELEASE_DRAFT_PATH.exists() else "# Tony Na Engine Preview\n"
    download_guide = render_download_guide(report).rstrip()
    body = body.rstrip()
    if DOWNLOAD_GUIDE_MARKER in body:
        body = body.replace(DOWNLOAD_GUIDE_MARKER, download_guide)
        lines = [body, "", "## Verification", ""]
    else:
        lines = [body, "", download_guide, "", "## Verification", ""]
    ci = report["githubActions"]
    if ci.get("checked"):
        lines.append(f"- GitHub Actions: `{ci.get('status')}` / `{ci.get('conclusion')}`")
    else:
        lines.append(f"- GitHub Actions: not checked ({ci.get('reason')})")
    lines.append(f"- Privacy scan findings: `{len(report['privacy']['sensitiveFindings'])}`")
    lines.append(f"- Working tree clean when prepared: `{report['git']['workingTreeClean']}`")
    lines.extend(["", "## Artifact Checksums", ""])
    public_artifacts = report.get("publicArtifacts") or select_public_release_artifacts(report["artifacts"])
    if not public_artifacts:
        lines.append("- Attach freshly generated artifacts and paste their hashes here.")
    for artifact in public_artifacts:
        lines.append(f"- `{artifact['name']}`: `{artifact['sha256']}`")
    lines.append("")
    return "\n".join(lines)


def render_public_checksums_text(report: dict[str, Any]) -> str:
    public_artifacts = report.get("publicArtifacts") or select_public_release_artifacts(report.get("artifacts") or [])
    lines = [
        f"# Generated: {report['generatedAt']}",
        f"# Commit: {report['git']['shortCommit']}",
    ]
    lines.extend(f"{artifact['sha256']}  {artifact['name']}" for artifact in public_artifacts)
    return "\n".join(lines) + "\n"


def public_checksums_payload(report: dict[str, Any]) -> dict[str, Any]:
    public_artifacts = report.get("publicArtifacts") or select_public_release_artifacts(report.get("artifacts") or [])
    return {
        "generatedAt": report["generatedAt"],
        "commit": report["git"]["commit"],
        "shortCommit": report["git"]["shortCommit"],
        "branch": report["git"]["branch"],
        "artifacts": [
            {
                "name": artifact["name"],
                "path": artifact["path"],
                "kind": artifact["kind"],
                "size": artifact["size"],
                "sizeLabel": artifact["sizeLabel"],
                "sha256": artifact["sha256"],
            }
            for artifact in public_artifacts
        ],
    }


def write_outputs(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "preview-release-readiness.json"
    manifest_path = output_dir / "preview-release-upload-manifest.md"
    body_path = output_dir / "preview-release-body.md"
    sha256_path = output_dir / "preview-release-public-assets.sha256"
    checksum_json_path = output_dir / "preview-release-public-assets.checksum.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(render_upload_manifest(report), encoding="utf-8")
    body_path.write_text(render_release_body(report), encoding="utf-8")
    sha256_path.write_text(render_public_checksums_text(report), encoding="utf-8")
    checksum_json_path.write_text(
        json.dumps(public_checksums_payload(report), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "json": relative(json_path),
        "manifest": relative(manifest_path),
        "releaseBody": relative(body_path),
        "sha256": relative(sha256_path),
        "checksumJson": relative(checksum_json_path),
    }


def print_summary(report: dict[str, Any], outputs: dict[str, str]) -> None:
    print("Tony Na Engine Preview release prep")
    print(f"- Commit: {report['git']['shortCommit']}")
    print(f"- Working tree clean: {report['git']['workingTreeClean']}")
    ci = report["githubActions"]
    if ci.get("checked"):
        print(f"- GitHub Actions: {ci.get('status')} / {ci.get('conclusion')}")
    else:
        print(f"- GitHub Actions: not checked ({ci.get('reason')})")
    release = report.get("githubRelease") or {}
    if release.get("checked"):
        if release.get("exists"):
            print(
                "- GitHub Release: "
                f"{release.get('tag')} / matched {len(release.get('matchedAssets') or [])} "
                f"of {len(report.get('publicArtifacts') or [])} public assets"
            )
        else:
            print(f"- GitHub Release: {release.get('tag')} not found")
    else:
        print(f"- GitHub Release: not checked ({release.get('reason')})")
    print(f"- Privacy findings: {len(report['privacy']['sensitiveFindings'])}")
    print(f"- Artifacts listed: {len(report['artifacts'])}")
    print(f"- Public release artifacts: {len(report.get('publicArtifacts') or [])}")
    print(f"- Rejected artifacts: {len(report.get('rejectedArtifacts') or [])}")
    print(f"- Ready for Preview tag: {report['readyForPreviewTag']}")
    if report["warnings"]:
        print("")
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"- {warning}")
    print("")
    print("Generated files:")
    for label, path in outputs.items():
        print(f"- {label}: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Tony Na Engine Preview release notes and upload manifest")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory, default release_preview/<timestamp>")
    parser.add_argument("--max-artifacts", type=int, default=12, help="Maximum local artifacts to list from exports/")
    parser.add_argument("--skip-network", action="store_true", help="Do not query GitHub Actions status")
    parser.add_argument("--release-tag", default="", help="GitHub Release tag to compare against; default uses a tag at HEAD")
    parser.add_argument("--skip-release-check", action="store_true", help="Do not compare GitHub Release assets")
    parser.add_argument(
        "--extra-sensitive",
        action="append",
        default=[],
        help="Additional sensitive literal to scan for; repeat or pass via TNE_PRIVACY_EXTRA_PATTERNS",
    )
    args = parser.parse_args()
    env_patterns = [item.strip() for item in os.environ.get("TNE_PRIVACY_EXTRA_PATTERNS", "").split(",") if item.strip()]
    args.extra_sensitive.extend(env_patterns)

    output_dir = args.output_dir or (DEFAULT_OUTPUT_DIR / current_timestamp())
    report = build_report(args)
    outputs = write_outputs(report, output_dir)
    print_summary(report, outputs)
    return 0 if report["readyForPreviewTag"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
