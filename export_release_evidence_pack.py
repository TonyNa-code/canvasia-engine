from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from export_package_guide import clean_guide_text, describe_export_report_file, normalize_guide_items


EXPORT_RELEASE_EVIDENCE_PACK_NAME = "release-evidence-pack.md"


def build_export_release_evidence_pack(
    *,
    project: dict,
    target_label: str,
    release_version: str,
    manifest_name: str,
    playtest_guide_name: str,
    provenance_name: str,
    story_route_map_report_name: str,
    localization_audit_report_name: str,
    release_readiness_report_name: str,
    unlockable_report_name: str,
    unlockable_manifest_name: str,
    launch_steps: list[str] | None = None,
    runtime_notes: list[str] | None = None,
    extra_reports: list[str] | None = None,
    missing_assets: list[dict] | None = None,
) -> str:
    project_title = clean_guide_text(project.get("title"), "未命名项目")
    safe_target_label = clean_guide_text(target_label, "导出包")
    safe_release_version = clean_guide_text(release_version, "preview")
    safe_launch_steps = normalize_guide_items(launch_steps)
    safe_runtime_notes = normalize_guide_items(runtime_notes)
    safe_extra_reports = normalize_guide_items(extra_reports)
    missing_assets = missing_assets or []
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    required_reports = [
        (manifest_name, "导出清单：目标平台、版本、素材复制结果和运行信息。"),
        (playtest_guide_name, "试玩指南：给测试员的打开方式和最短验收路径。"),
        (release_readiness_report_name, "发布前验收：综合剧情、素材、本地化和解锁内容的试玩就绪度。"),
        (story_route_map_report_name, "剧情路线图：坏跳转、不可达场景、结局候选和路线覆盖。"),
        (localization_audit_report_name, "本地化覆盖：中日英等语言的漏译与覆盖率。"),
        (unlockable_report_name, "可解锁内容：CG、回想、图鉴、成就、结局等 EXTRA 覆盖。"),
        (unlockable_manifest_name, "可解锁内容清单：机器可读数据，方便自动化或二次工具检查。"),
        (provenance_name, "文件指纹与来源标记：用于复查导出包是否被改动。"),
    ]

    lines = [
        "# 发布证据包",
        "",
        f"- 项目：{project_title}",
        f"- 导出目标：{safe_target_label}",
        f"- 版本：{safe_release_version}",
        f"- 生成时间：{generated_at}",
        "",
        "## 一句话怎么用",
        "",
        "这个文件是导出包里的总入口。发布、试玩或交给朋友测试前，先从这里按顺序检查即可。",
        "",
        "## 最短验收顺序",
        "",
        f"1. 先按 `{playtest_guide_name}` 打开游戏，确认能进入标题页或第一段剧情。",
        f"2. 再看 `{release_readiness_report_name}`，如果状态不是 blocked，就可以进入试玩确认。",
        f"3. 需要追路线时看 `{story_route_map_report_name}`，需要查翻译时看 `{localization_audit_report_name}`。",
        f"4. 要复查 CG / 回想 / 图鉴 / 成就 / 结局覆盖时看 `{unlockable_report_name}`。",
        f"5. 对外分发前保留 `{provenance_name}`，方便之后确认文件完整性。",
        "",
        "## 打开方式摘要",
        "",
    ]
    if safe_launch_steps:
        lines.extend(f"- {step}" for step in safe_launch_steps)
    else:
        lines.append("- 打开导出包中的入口文件或启动脚本。")

    lines.extend(["", "## 证据目录", ""])
    seen_report_names: set[str] = set()
    for report_name, description in required_reports:
        safe_report_name = clean_guide_text(report_name)
        if not safe_report_name or safe_report_name in seen_report_names:
            continue
        seen_report_names.add(safe_report_name)
        lines.append(f"- `{safe_report_name}`：{description}")
    for report_name in safe_extra_reports:
        if report_name in seen_report_names:
            continue
        seen_report_names.add(report_name)
        lines.append(f"- `{report_name}`：{describe_export_report_file(report_name)}")

    lines.extend(["", "## 当前素材缺口", ""])
    if missing_assets:
        for asset in missing_assets[:10]:
            asset_name = clean_guide_text(asset.get("name") or asset.get("id"), "未命名素材")
            asset_type = clean_guide_text(asset.get("type"), "未知类型")
            lines.append(f"- {asset_name}（{asset_type}）")
        if len(missing_assets) > 10:
            lines.append(f"- 还有 {len(missing_assets) - 10} 个素材缺口，请查看 `{manifest_name}`。")
    else:
        lines.append("- 当前导出流程没有记录到素材缺口。")

    if safe_runtime_notes:
        lines.extend(["", "## 平台备注", ""])
        lines.extend(f"- {note}" for note in safe_runtime_notes)

    lines.extend(
        [
            "",
            "## 分发前提醒",
            "",
            "- 尽量发送整个导出文件夹或完整压缩包，不要只发送入口文件。",
            "- 如果目标平台拦截未签名预览包，请说明这是测试包，并优先提供校验文件。",
            "- 发现缺素材、路线断点或文本错位时，回编辑器修正后重新导出，不建议手改导出包。",
            "",
        ]
    )
    return "\n".join(lines)


def write_export_release_evidence_pack_file(
    target_dir: Path,
    *,
    project: dict,
    target_label: str,
    release_version: str,
    manifest_name: str,
    playtest_guide_name: str,
    provenance_name: str,
    story_route_map_report_name: str,
    localization_audit_report_name: str,
    release_readiness_report_name: str,
    unlockable_report_name: str,
    unlockable_manifest_name: str,
    launch_steps: list[str] | None = None,
    runtime_notes: list[str] | None = None,
    extra_reports: list[str] | None = None,
    missing_assets: list[dict] | None = None,
) -> Path:
    path = target_dir / EXPORT_RELEASE_EVIDENCE_PACK_NAME
    path.write_text(
        build_export_release_evidence_pack(
            project=project,
            target_label=target_label,
            release_version=release_version,
            manifest_name=manifest_name,
            playtest_guide_name=playtest_guide_name,
            provenance_name=provenance_name,
            story_route_map_report_name=story_route_map_report_name,
            localization_audit_report_name=localization_audit_report_name,
            release_readiness_report_name=release_readiness_report_name,
            unlockable_report_name=unlockable_report_name,
            unlockable_manifest_name=unlockable_manifest_name,
            launch_steps=launch_steps,
            runtime_notes=runtime_notes,
            extra_reports=extra_reports,
            missing_assets=missing_assets,
        ),
        encoding="utf-8",
    )
    return path


__all__ = [
    "EXPORT_RELEASE_EVIDENCE_PACK_NAME",
    "build_export_release_evidence_pack",
    "write_export_release_evidence_pack_file",
]
