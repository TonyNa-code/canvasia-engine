from __future__ import annotations

import re
from pathlib import Path


EXPORT_PLAYTEST_GUIDE_FILE_NAME = "README_试玩验收先看这里.md"

REPORT_DESCRIPTION_BY_NAME = {
    "README_试玩验收先看这里.md": "试玩验收入口：告诉作者和测试员导出后先打开什么、按什么顺序检查。",
    "release-evidence-pack.md": "发布证据包：把关键验收报告汇总成一份交接清单。",
    "release_readiness_summary.md": "发布试玩就绪摘要：综合剧情、素材、本地化、性能预算和 Runtime 覆盖，判断是否适合交给测试员。",
    "release_readiness_summary.json": "机器可读发布试玩就绪摘要：适合 CI、二次工具或自动化验收读取。",
    "performance-budget.md": "发布性能预算：复查包体、已引用素材、首屏预加载、早期路线加载和超大素材。",
    "performance-budget.json": "机器可读发布性能预算：适合自动化检查包体、首屏压力和素材体积风险。",
    "performance-budget.csv": "可导入表格的发布性能预算：方便按素材和问题分配优化任务。",
    "release-fix-order.md": "发布前修复顺序：把阻塞、复核和体验问题按优先级排好，告诉作者先修什么。",
    "release-fix-order.json": "机器可读发布前修复顺序：适合自动化读取修复任务。",
    "release-fix-order.csv": "可导入表格的发布前修复顺序：方便多人协作跟进修复状态。",
    "story_route_map.md": "剧情路线图：检查坏跳转、不可达场景、结局候选和路线覆盖。",
    "route-playtest-workbook.md": "路线试玩工作簿：把分支和结局整理成可手动点测的执行路线。",
    "route-playtest-workbook.csv": "可导入表格的路线试玩工作簿：方便测试员逐条记录结果。",
    "runtime-capability-matrix.md": "Runtime 覆盖矩阵：检查剧情卡片、VN 基础体验和 Web / 原生支持状态。",
    "localization_audit.md": "本地化覆盖报告：检查中日英等语言的漏译和覆盖率。",
    "asset-rights-report.md": "素材授权与署名报告：复查商用状态、来源、AI 生成记录和 Staff 草稿。",
    "audio-cue-report.md": "音频调度报告：复查 BGM 范围、淡入淡出、音效、语音缺口和人声混音风险。",
    "stage-direction-report.md": "角色舞台调度报告：复查背景、立绘、表情、位置、透明度和登退场。",
    "presentation-timeline-report.md": "演出时间轴报告：复查阅读时长、静态长文本、画面 / 音频锚点和硬切风险。",
    "choice-consequence-report.md": "选项后果表：复查选项文本、跳转目标、变量效果和无后果按钮。",
    "variable-influence-report.md": "变量影响表：复查变量定义、读写位置、条件引用和未使用路线旗标。",
    "voice-production-report.md": "语音制作清单：给录音、回听和长台词复核使用。",
    "unlockable_content_report.md": "可解锁内容报告：复查 CG、音乐、语音回听、图鉴、成就、章节和结局覆盖。",
    "runtime_preload_manifest.json": "Runtime 预加载清单：记录首屏和早期路线会预热的资源。",
    "RUNTIME_PRELOAD_REPORT.md": "Runtime 预加载报告：复查首屏和切场景加载压力。",
    "native-runtime-performance-budget.md": "原生 Runtime 性能预算：复查原生包体、素材体积和剧情规模。",
    "native-runtime-release-control-report.md": "原生 Runtime 发布总控：汇总发布候选、性能、文件完整性和验收状态。",
}


def clean_guide_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def normalize_guide_items(items: list[object] | tuple[object, ...] | None) -> list[str]:
    return [clean_guide_text(item) for item in (items or []) if clean_guide_text(item)]


def normalize_report_lookup_name(report_name: object) -> str:
    text = clean_guide_text(report_name).replace("\\", "/")
    return text.rsplit("/", 1)[-1]


def describe_export_report_file(report_name: object) -> str:
    lookup_name = normalize_report_lookup_name(report_name)
    if lookup_name in REPORT_DESCRIPTION_BY_NAME:
        return REPORT_DESCRIPTION_BY_NAME[lookup_name]
    if lookup_name.endswith(".csv"):
        return "可导入表格的补充检查报告。"
    if lookup_name.endswith(".json"):
        return "机器可读补充检查报告。"
    return "补充发布检查报告。"


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
        lines.append(f"- `{report}`：{describe_export_report_file(report)}")

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
    "describe_export_report_file",
    "write_export_playtest_guide_file",
]
