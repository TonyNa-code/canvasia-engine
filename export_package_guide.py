from __future__ import annotations

import re
from pathlib import Path


EXPORT_PLAYTEST_GUIDE_FILE_NAME = "README_试玩验收先看这里.md"


def clean_guide_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def normalize_guide_items(items: list[object] | tuple[object, ...] | None) -> list[str]:
    return [clean_guide_text(item) for item in (items or []) if clean_guide_text(item)]


def build_export_playtest_guide(
    *,
    project: dict,
    target_label: str,
    release_version: str,
    launch_steps: list[str],
    manifest_name: str,
    unlockable_manifest_name: str,
    unlockable_report_name: str,
    provenance_name: str,
    extra_reports: list[str] | None = None,
    runtime_notes: list[str] | None = None,
    missing_assets: list[dict] | None = None,
) -> str:
    project_title = clean_guide_text(project.get("title"), "未命名项目")
    safe_target_label = clean_guide_text(target_label, "导出包")
    safe_release_version = clean_guide_text(release_version, "preview")
    safe_launch_steps = normalize_guide_items(launch_steps)
    safe_runtime_notes = normalize_guide_items(runtime_notes)
    safe_extra_reports = normalize_guide_items(extra_reports)
    missing_assets = missing_assets or []

    lines = [
        "# 试玩与发布验收指南",
        "",
        f"- 项目：{project_title}",
        f"- 导出目标：{safe_target_label}",
        f"- 版本：{safe_release_version}",
        "",
        "## 打开方式",
        "",
    ]
    if safe_launch_steps:
        lines.extend(f"{index}. {step}" for index, step in enumerate(safe_launch_steps, start=1))
    else:
        lines.append("1. 打开导出包中的入口文件或启动脚本。")

    lines.extend(
        [
            "",
            "## 先验这几项",
            "",
            "- 能正常进入标题页或第一段剧情。",
            "- 背景、角色立绘、BGM、音效和语音没有明显缺失。",
            "- 选项、跳转、条件分支和结局路线可以按预期走通。",
            "- 存档 / 读档、自动播放、快进、历史文本和语言切换按项目需求正常工作。",
            "- EXTRA / 回想 / 图鉴 / 成就相关内容可参考随包报告复查。",
            "",
            "## 随包文件怎么用",
            "",
            f"- `{manifest_name}`：机器可读导出清单，记录目标平台、版本、素材缺口和运行信息。",
            f"- `{unlockable_report_name}`：给测试员看的 EXTRA / 回想 / 图鉴 / 结局 / 成就覆盖报告。",
            f"- `{unlockable_manifest_name}`：机器可读可解锁内容清单，适合自动化验收或二次工具读取。",
            f"- `{provenance_name}`：文件指纹和低调来源标记，用于检查导出包是否被改动。",
        ]
    )
    for report in safe_extra_reports:
        lines.append(f"- `{report}`：补充发布检查报告。")

    lines.extend(["", "## 当前素材缺口", ""])
    if missing_assets:
        for asset in missing_assets[:12]:
            asset_name = clean_guide_text(asset.get("name") or asset.get("id"), "未命名素材")
            asset_type = clean_guide_text(asset.get("type"), "未知类型")
            lines.append(f"- {asset_name}（{asset_type}）")
        if len(missing_assets) > 12:
            lines.append(f"- 还有 {len(missing_assets) - 12} 个素材缺口，请查看 `{manifest_name}`。")
    else:
        lines.append("- 当前导出流程没有记录到素材缺口。")

    lines.extend(
        [
            "",
            "## 分发提醒",
            "",
            "- 对外发送时请保留整个导出文件夹，不要只拷贝单个入口文件。",
            "- 如果压缩包、文件指纹或完整性校验失败，请重新导出或重新下载后再分发。",
            "- 未签名的预览包可能被系统安全提示拦截，这是 Preview 阶段的常见情况。",
        ]
    )
    if safe_runtime_notes:
        lines.extend(["", "## 平台备注", ""])
        lines.extend(f"- {note}" for note in safe_runtime_notes)
    lines.append("")
    return "\n".join(lines)


def write_export_playtest_guide_file(
    target_dir: Path,
    *,
    project: dict,
    target_label: str,
    release_version: str,
    launch_steps: list[str],
    manifest_name: str,
    unlockable_manifest_name: str,
    unlockable_report_name: str,
    provenance_name: str,
    extra_reports: list[str] | None = None,
    runtime_notes: list[str] | None = None,
    missing_assets: list[dict] | None = None,
) -> Path:
    path = target_dir / EXPORT_PLAYTEST_GUIDE_FILE_NAME
    path.write_text(
        build_export_playtest_guide(
            project=project,
            target_label=target_label,
            release_version=release_version,
            launch_steps=launch_steps,
            manifest_name=manifest_name,
            unlockable_manifest_name=unlockable_manifest_name,
            unlockable_report_name=unlockable_report_name,
            provenance_name=provenance_name,
            extra_reports=extra_reports,
            runtime_notes=runtime_notes,
            missing_assets=missing_assets,
        ),
        encoding="utf-8",
    )
    return path


__all__ = [
    "EXPORT_PLAYTEST_GUIDE_FILE_NAME",
    "build_export_playtest_guide",
    "write_export_playtest_guide_file",
]
