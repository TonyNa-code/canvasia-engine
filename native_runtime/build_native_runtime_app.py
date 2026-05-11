from __future__ import annotations

import argparse
import datetime
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_APP_NAME = "CanvasiaNativeGame"
GAME_DATA_NAME = "game_data.json"
RUNTIME_PLAYER_NAME = "runtime_player.py"
PACKAGE_MANIFEST_NAME = "native_app_package_manifest.json"
ENGINE_BRAND_LOGO_RELATIVE_PATH = "assets/brand-logo.png"
VIDEO_REQUIREMENTS_CANDIDATES = ("requirements-native-runtime-video.txt", "requirements-video.txt")
ASSET3D_REPORT_NAME = "native-runtime-3d-asset-report.json"
ASSET3D_SUMMARY_NAME = "native-runtime-3d-asset-summary.md"
ASSET3D_DIGEST_NAME = "native-runtime-3d-risk-digest.json"
RELEASE_CONTROL_REPORT_NAME = "native-runtime-release-control-report.md"
RELEASE_CONTROL_JSON_NAME = "native-runtime-release-control-report.json"
FILE_INTEGRITY_REPORT_NAME = "native-runtime-file-integrity.json"
FILE_INTEGRITY_MARKDOWN_NAME = "native-runtime-file-integrity.md"
RELEASE_CONTROL_REFRESHER_NAMES = (
    "生成原生Runtime发布总控报告.command",
    "generate_native_runtime_release_control.sh",
    "generate_native_runtime_release_control.bat",
)
FILE_INTEGRITY_CHECKER_NAMES = (
    "校验原生Runtime文件完整性.command",
    "verify_native_runtime_file_integrity.sh",
    "verify_native_runtime_file_integrity.bat",
)


class NativeAppBuildError(RuntimeError):
    pass


def get_requirements_install_command(bundle_dir: Path) -> str:
    runtime_requirements = (
        "requirements-native-runtime.txt"
        if (bundle_dir / "requirements-native-runtime.txt").is_file()
        else "requirements.txt"
    )
    build_requirements = (
        "requirements-native-runtime-build.txt"
        if (bundle_dir / "requirements-native-runtime-build.txt").is_file()
        else "requirements-build.txt"
    )
    return f"python -m pip install -r {runtime_requirements} -r {build_requirements}"


def get_optional_video_requirements_name(bundle_dir: Path) -> str:
    return next((file_name for file_name in VIDEO_REQUIREMENTS_CANDIDATES if (bundle_dir / file_name).is_file()), "")


def get_optional_video_requirements_install_command(bundle_dir: Path) -> str:
    requirements_name = get_optional_video_requirements_name(bundle_dir)
    return f"python -m pip install -r {requirements_name}" if requirements_name else ""


def load_game_data(bundle_dir: Path) -> dict:
    game_data_path = bundle_dir / GAME_DATA_NAME
    if not game_data_path.is_file():
        raise NativeAppBuildError(f"没有找到 {GAME_DATA_NAME}：{game_data_path}")
    return json.loads(game_data_path.read_text(encoding="utf-8"))


def sanitize_app_name(value: str | None) -> str:
    raw_value = str(value or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9_. -]+", "-", raw_value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .-")
    if not cleaned or not re.search(r"[A-Za-z0-9]", cleaned):
        return DEFAULT_APP_NAME
    return cleaned[:64].strip(" .-") or DEFAULT_APP_NAME


def get_project_app_name(payload: dict) -> str:
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    return sanitize_app_name(
        project.get("title")
        or project.get("name")
        or project.get("projectName")
        or project.get("id")
        or DEFAULT_APP_NAME
    )


def sanitize_bundle_identifier(value: str | None) -> str:
    raw_value = str(value or DEFAULT_APP_NAME).lower()
    suffix_parts = re.findall(r"[a-z0-9]+", raw_value)
    suffix = ".".join(suffix_parts).strip(".") or "game"
    suffix = suffix[:80].strip(".") or "game"
    return f"com.canvasia.{suffix}"


def sanitize_archive_stem(value: str | None) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or DEFAULT_APP_NAME).strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip(".-") or DEFAULT_APP_NAME
    return cleaned[:72].strip(".-") or DEFAULT_APP_NAME


def get_platform_tag() -> str:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return re.sub(r"[^a-z0-9]+", "-", sys.platform.lower()).strip("-") or "unknown"


def get_distribution_notes(platform_tag: str) -> list[str]:
    if platform_tag == "macos":
        return [
            "Preview 包可以下载测试，但未签名/未公证时普通用户可能会被 Gatekeeper 拦截。",
            "正式公开分发建议使用 Apple Developer ID 签名并完成 notarization。",
        ]
    if platform_tag == "windows":
        return [
            "Preview 包可以下载测试，但未签名时 Windows SmartScreen 可能提示未知发布者。",
            "正式公开分发建议使用代码签名证书给 exe/installer 签名。",
        ]
    if platform_tag == "linux":
        return [
            "Linux Preview 包通常可以直接分发压缩包，但仍建议在目标发行版上点测。",
            "正式公开分发可继续补 AppImage、deb/rpm 或 Flatpak 发行形态。",
        ]
    return ["当前平台不在主发布矩阵内，请把生成物视为内部测试包。"]


def normalize_export_url(value: object) -> str:
    export_url = str(value or "").replace("\\", "/").strip().lstrip("/")
    parts = [part for part in export_url.split("/") if part and part not in {".", ".."}]
    return "/".join(parts)


def iter_asset_export_urls(payload: dict) -> list[str]:
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    export_urls: list[str] = []
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("isMissing"):
            continue
        export_url = normalize_export_url(asset.get("exportUrl"))
        if export_url:
            export_urls.append(export_url)
    return sorted(set(export_urls))


def collect_data_entries(bundle_dir: Path, payload: dict) -> tuple[list[dict], list[str]]:
    entries_by_key: dict[tuple[str, str], dict] = {
        (GAME_DATA_NAME, "."): {
            "source": bundle_dir / GAME_DATA_NAME,
            "relativeSource": GAME_DATA_NAME,
            "dest": ".",
        }
    }
    brand_logo_path = bundle_dir / ENGINE_BRAND_LOGO_RELATIVE_PATH
    if brand_logo_path.is_file():
        entries_by_key[(ENGINE_BRAND_LOGO_RELATIVE_PATH, ".")] = {
            "source": brand_logo_path,
            "relativeSource": ENGINE_BRAND_LOGO_RELATIVE_PATH,
            "dest": "assets",
        }
    missing_assets: list[str] = []
    for export_url in iter_asset_export_urls(payload):
        asset_path = bundle_dir / export_url
        if not asset_path.exists():
            missing_assets.append(export_url)
            continue
        first_segment = export_url.split("/", 1)[0]
        source_path = bundle_dir / first_segment
        if source_path.is_dir():
            relative_source = first_segment
            dest = first_segment
        else:
            relative_source = export_url
            source_path = asset_path
            dest = "."
        entries_by_key[(relative_source, dest)] = {
            "source": source_path,
            "relativeSource": relative_source,
            "dest": dest,
        }
    entries = sorted(entries_by_key.values(), key=lambda entry: (entry["dest"], entry["relativeSource"]))
    return entries, missing_assets


def get_add_data_separator() -> str:
    return ";" if sys.platform.startswith("win") else ":"


def build_pyinstaller_command(
    bundle_dir: Path,
    app_name: str,
    mode: str,
    console: bool,
    icon_path: Path | None,
    bundle_identifier: str,
    data_entries: list[dict],
) -> list[str]:
    runtime_player_path = bundle_dir / RUNTIME_PLAYER_NAME
    if not runtime_player_path.is_file():
        raise NativeAppBuildError(f"没有找到 {RUNTIME_PLAYER_NAME}：{runtime_player_path}")

    dist_dir = bundle_dir / "native_app_dist"
    work_dir = bundle_dir / "native_app_build"
    add_data_separator = get_add_data_separator()
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        app_name,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir),
    ]
    command.append("--onefile" if mode == "onefile" else "--onedir")
    if not console:
        command.append("--windowed")
    if icon_path is not None:
        command.extend(["--icon", str(icon_path)])
    if sys.platform == "darwin":
        command.extend(["--osx-bundle-identifier", bundle_identifier])
    for entry in data_entries:
        command.extend(["--add-data", f"{entry['source']}{add_data_separator}{entry['dest']}"])
    command.append(str(runtime_player_path))
    return command


def format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def get_planned_archive_name(app_name: str, platform_tag: str, mode: str) -> str:
    return f"{sanitize_archive_stem(app_name)}-{platform_tag}-{mode}-preview.zip"


def get_dist_dir(bundle_dir: Path) -> Path:
    return bundle_dir / "native_app_dist"


def collect_output_entries(dist_dir: Path) -> list[dict]:
    if not dist_dir.is_dir():
        return []
    entries: list[dict] = []
    for child in sorted(dist_dir.iterdir(), key=lambda item: item.name.lower()):
        if child.name.startswith("."):
            continue
        if child.suffix == ".zip":
            continue
        try:
            if child.is_dir():
                size_bytes = sum(path.stat().st_size for path in child.rglob("*") if path.is_file())
            else:
                size_bytes = child.stat().st_size
        except OSError:
            size_bytes = 0
        entries.append(
            {
                "name": child.name,
                "path": str(child),
                "kind": "directory" if child.is_dir() else "file",
                "sizeBytes": size_bytes,
            }
        )
    return entries


def create_distribution_archive(bundle_dir: Path, app_name: str, platform_tag: str, mode: str) -> Path:
    dist_dir = get_dist_dir(bundle_dir)
    if not dist_dir.is_dir():
        raise NativeAppBuildError(f"没有找到打包输出目录：{dist_dir}")
    archive_path = bundle_dir / get_planned_archive_name(app_name, platform_tag, mode)
    if archive_path.exists():
        archive_path.unlink()
    created_archive = shutil.make_archive(str(archive_path.with_suffix("")), "zip", root_dir=dist_dir)
    return Path(created_archive)


def write_package_manifest(
    bundle_dir: Path,
    description: dict,
    archive_path: Path | None,
) -> Path:
    platform_tag = get_platform_tag()
    dist_dir = get_dist_dir(bundle_dir)
    manifest = {
        "formatVersion": 1,
        "createdAt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "appName": description.get("appName"),
        "platform": platform_tag,
        "platformLabel": platform.platform(),
        "mode": description.get("mode"),
        "bundleIdentifier": description.get("bundleIdentifier"),
        "outputDir": str(dist_dir),
        "outputEntries": collect_output_entries(dist_dir),
        "archiveName": archive_path.name if archive_path else "",
        "archivePath": str(archive_path) if archive_path else "",
        "releaseCheck": description.get("releaseCheck") or {},
        "releaseCandidateReport": description.get("releaseCandidateReport") or {},
        "releaseControl": description.get("releaseControl") or {},
        "fileIntegrity": description.get("fileIntegrity") or {},
        "video": description.get("video") or {},
        "asset3d": description.get("asset3d") or {},
        "signing": {
            "signed": False,
            "notarized": False,
            "statusLabel": "Preview unsigned package",
        },
        "distributionNotes": get_distribution_notes(platform_tag),
    }
    manifest_path = bundle_dir / PACKAGE_MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def run_bundle_release_check(bundle_dir: Path) -> dict:
    runtime_player_path = bundle_dir / RUNTIME_PLAYER_NAME
    command = [sys.executable, str(runtime_player_path), "--release-check", str(bundle_dir)]
    result = subprocess.run(command, cwd=bundle_dir, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {
            "status": "fail",
            "command": format_command(command),
            "summary": {"errors": 1, "warnings": 0},
            "issues": [
                {
                    "severity": "error",
                    "code": "release_check_command_failed",
                    "message": result.stderr.strip() or result.stdout.strip() or "发布前自检命令执行失败。",
                    "suggestion": "先运行 python runtime_player.py --release-check . 查看具体问题。",
                    "path": RUNTIME_PLAYER_NAME,
                }
            ],
        }
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "fail",
            "command": format_command(command),
            "summary": {"errors": 1, "warnings": 0},
            "issues": [
                {
                    "severity": "error",
                    "code": "release_check_json_invalid",
                    "message": "发布前自检没有返回有效 JSON。",
                    "suggestion": "检查 runtime_player.py 是否被手动修改或输出了额外调试文本。",
                    "path": RUNTIME_PLAYER_NAME,
                }
            ],
        }
    report["command"] = format_command(command)
    return report


def run_bundle_runtime_json_report(bundle_dir: Path, flag: str, report_label: str) -> dict:
    runtime_player_path = bundle_dir / RUNTIME_PLAYER_NAME
    command = [sys.executable, str(runtime_player_path), flag, str(bundle_dir)]
    result = subprocess.run(command, cwd=bundle_dir, capture_output=True, text=True, check=False)
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        if result.returncode != 0:
            return {
                "status": "unavailable",
                "command": format_command(command),
                "message": result.stderr.strip() or result.stdout.strip() or f"{report_label}命令执行失败。",
            }
        return {
            "status": "invalid_json",
            "command": format_command(command),
            "message": f"{report_label}没有返回有效 JSON。",
        }
    report["command"] = format_command(command)
    return report


def read_text_report_preview(path: Path, max_lines: int = 32) -> dict:
    if not path.is_file():
        return {"exists": False, "path": str(path), "lineCount": 0, "preview": ""}
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    return {
        "exists": True,
        "path": str(path),
        "lineCount": len(lines),
        "preview": "\n".join(lines[:max_lines]).strip(),
    }


def read_json_report_file(path: Path) -> dict:
    if not path.is_file():
        return {"exists": False, "path": str(path), "status": "missing"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        return {"exists": True, "path": str(path), "status": "invalid", "message": str(error)}
    if isinstance(payload, dict):
        return {"exists": True, "path": str(path), **payload}
    return {"exists": True, "path": str(path), "status": "invalid", "message": "JSON 根节点不是对象。"}


def describe_build(
    bundle_dir: Path,
    app_name: str | None,
    mode: str,
    console: bool,
    icon_path: Path | None,
    bundle_identifier: str | None = None,
    include_release_check: bool = True,
) -> dict:
    payload = load_game_data(bundle_dir)
    resolved_app_name = sanitize_app_name(app_name) if app_name else get_project_app_name(payload)
    resolved_bundle_identifier = sanitize_bundle_identifier(bundle_identifier or resolved_app_name)
    platform_tag = get_platform_tag()
    data_entries, missing_assets = collect_data_entries(bundle_dir, payload)
    command = build_pyinstaller_command(
        bundle_dir,
        resolved_app_name,
        mode,
        console,
        icon_path,
        resolved_bundle_identifier,
        data_entries,
    )
    release_check = (
        run_bundle_release_check(bundle_dir)
        if include_release_check
        else {"status": "skipped", "summary": {"errors": 0, "warnings": 0}, "issues": []}
    )
    video_backend_report = run_bundle_runtime_json_report(bundle_dir, "--describe-video-backends", "视频后端报告")
    video_preview_probe = run_bundle_runtime_json_report(bundle_dir, "--probe-video-preview", "视频帧预览探针")
    release_candidate_report = run_bundle_runtime_json_report(
        bundle_dir,
        "--release-candidate-report",
        "发布候选总报告",
    )
    asset3d_report = run_bundle_runtime_json_report(bundle_dir, "--describe-3d-assets", "3D 资产清单")
    asset3d_summary_path = bundle_dir / ASSET3D_SUMMARY_NAME
    asset3d_summary = read_text_report_preview(asset3d_summary_path)
    asset3d_digest = read_json_report_file(bundle_dir / ASSET3D_DIGEST_NAME)
    release_control_report = read_text_report_preview(bundle_dir / RELEASE_CONTROL_REPORT_NAME)
    release_control_json = read_json_report_file(bundle_dir / RELEASE_CONTROL_JSON_NAME)
    file_integrity_report = read_json_report_file(bundle_dir / FILE_INTEGRITY_REPORT_NAME)
    file_integrity_markdown = read_text_report_preview(bundle_dir / FILE_INTEGRITY_MARKDOWN_NAME)
    return {
        "appName": resolved_app_name,
        "bundleIdentifier": resolved_bundle_identifier,
        "platform": platform_tag,
        "mode": mode,
        "console": console,
        "gameData": GAME_DATA_NAME,
        "runtimePlayer": RUNTIME_PLAYER_NAME,
        "outputDir": "native_app_dist",
        "workDir": "native_app_build",
        "packageManifest": PACKAGE_MANIFEST_NAME,
        "plannedArchiveName": get_planned_archive_name(resolved_app_name, platform_tag, mode),
        "distributionNotes": get_distribution_notes(platform_tag),
        "optionalVideoRequirements": get_optional_video_requirements_name(bundle_dir),
        "optionalVideoInstallCommand": get_optional_video_requirements_install_command(bundle_dir),
        "video": {
            "backendReport": video_backend_report,
            "previewProbe": video_preview_probe,
        },
        "asset3d": {
            "reportName": ASSET3D_REPORT_NAME,
            "summaryName": ASSET3D_SUMMARY_NAME,
            "digestName": ASSET3D_DIGEST_NAME,
            "report": asset3d_report,
            "summary": asset3d_summary,
            "digest": asset3d_digest,
        },
        "releaseControl": {
            "reportName": RELEASE_CONTROL_REPORT_NAME,
            "jsonName": RELEASE_CONTROL_JSON_NAME,
            "refreshers": [
                {"name": name, "exists": (bundle_dir / name).is_file()}
                for name in RELEASE_CONTROL_REFRESHER_NAMES
            ],
            "report": release_control_report,
            "json": release_control_json,
        },
        "fileIntegrity": {
            "reportName": FILE_INTEGRITY_REPORT_NAME,
            "markdownName": FILE_INTEGRITY_MARKDOWN_NAME,
            "checkers": [
                {"name": name, "exists": (bundle_dir / name).is_file()}
                for name in FILE_INTEGRITY_CHECKER_NAMES
            ],
            "report": file_integrity_report,
            "markdown": file_integrity_markdown,
        },
        "dataEntries": [
            {"source": entry["relativeSource"], "dest": entry["dest"]}
            for entry in data_entries
        ],
        "missingAssetPaths": missing_assets,
        "releaseCheck": release_check,
        "releaseCandidateReport": release_candidate_report,
        "commandPreview": format_command(command),
    }


def run_build(bundle_dir: Path, args: argparse.Namespace) -> int:
    description = describe_build(
        bundle_dir,
        args.app_name,
        args.mode,
        args.console,
        args.icon,
        args.bundle_id,
        include_release_check=not args.skip_release_check,
    )
    if description["missingAssetPaths"] and not args.allow_missing_assets:
        print("以下素材在导出包里不存在，已停止打包：")
        for export_url in description["missingAssetPaths"]:
            print(f"- {export_url}")
        print("如果你确认这些素材本来就不需要，可加 --allow-missing-assets。")
        return 1
    release_check = description.get("releaseCheck") or {}
    release_check_status = release_check.get("status")
    if release_check_status == "fail" and not args.allow_release_check_failures:
        print("发布前自检没有通过，已停止打包。")
        for issue in release_check.get("issues", []):
            print(f"- [{issue.get('severity')}] {issue.get('message')}")
        print("修复后再打包；如果只是临时测试，可加 --allow-release-check-failures。")
        return 1
    if release_check_status == "warn":
        warning_count = (release_check.get("summary") or {}).get("warnings", 0)
        print(f"发布前自检有 {warning_count} 条警告，仍会继续打包。正式发布前建议处理。")

    payload = load_game_data(bundle_dir)
    data_entries, _missing_assets = collect_data_entries(bundle_dir, payload)
    app_name = description["appName"]
    dist_dir = get_dist_dir(bundle_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    command = build_pyinstaller_command(
        bundle_dir,
        app_name,
        args.mode,
        args.console,
        args.icon,
        description["bundleIdentifier"],
        data_entries,
    )
    print("正在打包原生 Runtime 应用：")
    print(format_command(command))
    result = subprocess.run(command, cwd=bundle_dir, check=False)
    if result.returncode != 0:
        print(f"PyInstaller 打包失败。可以先执行：{get_requirements_install_command(bundle_dir)}")
        return result.returncode
    archive_path = None
    if not args.no_zip:
        archive_path = create_distribution_archive(bundle_dir, app_name, description["platform"], args.mode)
    manifest_path = write_package_manifest(bundle_dir, description, archive_path)
    print(f"打包完成：{bundle_dir / 'native_app_dist'}")
    print(f"包清单：{manifest_path}")
    if archive_path:
        print(f"Preview 分发压缩包：{archive_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 Canvasia Engine 原生 Runtime 导出包打成桌面应用")
    parser.add_argument("bundle_dir", nargs="?", default=".", help="原生 Runtime 导出包目录，默认当前目录")
    parser.add_argument("--mode", choices=("onedir", "onefile"), default="onedir", help="PyInstaller 输出模式")
    parser.add_argument("--app-name", dest="app_name", help="覆盖应用名称；默认使用项目名")
    parser.add_argument("--bundle-id", dest="bundle_id", help="覆盖 macOS Bundle Identifier，默认自动生成 com.canvasia.*")
    parser.add_argument("--console", action="store_true", help="保留控制台窗口，便于排错")
    parser.add_argument("--icon", type=Path, help="可选应用图标路径")
    parser.add_argument("--allow-missing-assets", action="store_true", help="允许素材缺失时继续打包")
    parser.add_argument("--skip-release-check", action="store_true", help="跳过发布前自检，通常只用于临时调试")
    parser.add_argument("--allow-release-check-failures", action="store_true", help="发布前自检失败时仍继续打包")
    parser.add_argument("--no-zip", action="store_true", help="只生成 PyInstaller 输出目录，不额外生成 Preview 分发 zip")
    parser.add_argument("--describe", action="store_true", help="只输出打包计划 JSON，不实际运行 PyInstaller")
    args = parser.parse_args(argv)

    bundle_dir = Path(args.bundle_dir).resolve()
    icon_path = args.icon.resolve() if args.icon else None
    args.icon = icon_path
    try:
        description = describe_build(
            bundle_dir,
            args.app_name,
            args.mode,
            args.console,
            icon_path,
            args.bundle_id,
            include_release_check=not args.skip_release_check,
        )
        if args.describe:
            print(json.dumps(description, ensure_ascii=False, indent=2))
            return 0
        return run_build(bundle_dir, args)
    except NativeAppBuildError as error:
        print(f"原生 Runtime 应用打包准备失败：{error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
