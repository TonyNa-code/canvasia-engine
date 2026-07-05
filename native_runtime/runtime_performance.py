from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


PERFORMANCE_BUDGET_REPORT_NAME = "native-runtime-performance-budget.json"
PERFORMANCE_BUDGET_MARKDOWN_NAME = "native-runtime-performance-budget.md"
PERFORMANCE_BUDGET_FORMAT_VERSION = 1

IMAGE_ASSET_TYPES = {"background", "sprite", "cg", "ui"}
AUDIO_ASSET_TYPES = {"bgm", "sfx", "voice"}
VIDEO_ASSET_TYPES = {"video"}

DEFAULT_PERFORMANCE_BUDGETS = {
    "totalAssetBudgetBytes": 1024 * 1024 * 1024,
    "referencedAssetBudgetBytes": 768 * 1024 * 1024,
    "imageAssetBudgetBytes": 384 * 1024 * 1024,
    "audioAssetBudgetBytes": 384 * 1024 * 1024,
    "videoAssetBudgetBytes": 2048 * 1024 * 1024,
    "singleImageBudgetBytes": 18 * 1024 * 1024,
    "singleAudioBudgetBytes": 30 * 1024 * 1024,
    "singleVideoBudgetBytes": 300 * 1024 * 1024,
    "storyBlockWarningCount": 4000,
    "sceneWarningCount": 180,
    "maxBlocksPerSceneWarningCount": 160,
    "unreferencedAssetWarningCount": 30,
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def safe_text(value: object) -> str:
    return str(value or "").strip()


def to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_bytes(size_bytes: int) -> str:
    size = float(max(0, int(size_bytes or 0)))
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{int(size_bytes or 0)} B"


def format_markdown_value(value: object, default: str = "-") -> str:
    text = safe_text(value)
    if not text:
        return default
    return text.replace("|", "\\|").replace("\n", " ")


def merge_budgets(budgets: dict | None = None) -> dict:
    merged = dict(DEFAULT_PERFORMANCE_BUDGETS)
    if isinstance(budgets, dict):
        for key in merged:
            if key in budgets:
                merged[key] = max(0, to_int(budgets.get(key), merged[key]))
    return merged


def load_bundle_payload(bundle_dir: Path) -> dict:
    data_path = bundle_dir / "game_data.json"
    if not data_path.is_file():
        raise FileNotFoundError(f"没有找到游戏数据文件：{data_path}")
    return json.loads(data_path.read_text(encoding="utf-8"))


def get_assets(payload: dict) -> list[dict]:
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    return [asset for asset in assets_doc.get("assets", []) if isinstance(asset, dict)]


def iter_scenes(payload: dict) -> list[dict]:
    scenes: list[dict] = []
    for chapter in payload.get("chapters") or []:
        if not isinstance(chapter, dict):
            continue
        for scene in chapter.get("scenes") or []:
            if isinstance(scene, dict):
                scenes.append(scene)
    return scenes


def iter_story_blocks(payload: dict) -> list[dict]:
    blocks: list[dict] = []
    for scene in iter_scenes(payload):
        blocks.extend(block for block in scene.get("blocks") or [] if isinstance(block, dict))
    return blocks


def collect_asset_reference_ids(payload: dict) -> set[str]:
    references: set[str] = set()

    def visit(value: object, key: str = "") -> None:
        lowered = key.lower()
        is_asset_id_key = lowered == "assetid" or lowered.endswith("assetid")
        is_asset_ids_key = lowered == "assetids" or lowered.endswith("assetids")
        if is_asset_id_key and isinstance(value, str):
            asset_id = safe_text(value)
            if asset_id:
                references.add(asset_id)
        elif is_asset_ids_key and isinstance(value, list):
            for item in value:
                asset_id = safe_text(item)
                if asset_id:
                    references.add(asset_id)
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, safe_text(child_key))
        elif isinstance(value, list):
            for item in value:
                visit(item, key)

    visit(payload)
    return references


def resolve_asset_path(bundle_dir: Path, asset: dict) -> Path | None:
    export_url = safe_text(asset.get("exportUrl") or asset.get("path"))
    if not export_url:
        return None
    path = Path(export_url)
    if path.is_absolute():
        return path
    return bundle_dir / path


def get_asset_path_label(asset: dict) -> str:
    raw_path = safe_text(asset.get("exportUrl") or asset.get("path"))
    if not raw_path:
        return ""
    path = Path(raw_path)
    return path.name if path.is_absolute() else raw_path


def get_asset_type_group(asset_type: str) -> str:
    if asset_type in IMAGE_ASSET_TYPES:
        return "image"
    if asset_type in AUDIO_ASSET_TYPES:
        return "audio"
    if asset_type in VIDEO_ASSET_TYPES:
        return "video"
    if asset_type == "font":
        return "font"
    return "other"


def describe_budget_status(current: int, budget: int) -> dict:
    over = budget > 0 and current > budget
    ratio = round(current / budget, 3) if budget else 0
    return {
        "currentBytes": current,
        "currentLabel": format_bytes(current),
        "budgetBytes": budget,
        "budgetLabel": format_bytes(budget),
        "ratio": ratio,
        "overBudget": over,
    }


def add_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, suggestion: str) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "title": title,
            "detail": detail,
            "suggestion": suggestion,
        }
    )


def build_native_runtime_performance_budget_report(
    bundle_dir: Path,
    *,
    payload: dict | None = None,
    budgets: dict | None = None,
) -> dict:
    payload = payload if isinstance(payload, dict) else load_bundle_payload(bundle_dir)
    budget = merge_budgets(budgets)
    assets = get_assets(payload)
    referenced_asset_ids = collect_asset_reference_ids(payload)
    scenes = iter_scenes(payload)
    blocks = iter_story_blocks(payload)
    issues: list[dict] = []
    asset_reports: list[dict] = []
    totals_by_group = {"image": 0, "audio": 0, "video": 0, "font": 0, "other": 0}
    counts_by_group = {"image": 0, "audio": 0, "video": 0, "font": 0, "other": 0}
    total_bytes = 0
    referenced_bytes = 0
    missing_referenced_assets: list[dict] = []
    unreferenced_existing_count = 0

    for asset in assets:
        asset_id = safe_text(asset.get("id"))
        asset_type = safe_text(asset.get("type")) or "unknown"
        group = get_asset_type_group(asset_type)
        path = resolve_asset_path(bundle_dir, asset)
        exists = bool(path and path.is_file()) and not bool(asset.get("isMissing"))
        size_bytes = path.stat().st_size if exists and path else 0
        referenced = asset_id in referenced_asset_ids
        total_bytes += size_bytes
        totals_by_group[group] = totals_by_group.get(group, 0) + size_bytes
        counts_by_group[group] = counts_by_group.get(group, 0) + 1
        if referenced:
            referenced_bytes += size_bytes
        elif exists:
            unreferenced_existing_count += 1
        report = {
            "assetId": asset_id,
            "name": safe_text(asset.get("name")) or asset_id or "未命名素材",
            "type": asset_type,
            "group": group,
            "path": get_asset_path_label(asset),
            "exists": exists,
            "referenced": referenced,
            "sizeBytes": size_bytes,
            "sizeLabel": format_bytes(size_bytes),
        }
        asset_reports.append(report)
        if referenced and not exists:
            missing_referenced_assets.append(report)

    max_blocks_per_scene = 0
    longest_scene_name = ""
    for scene in scenes:
        block_count = len([block for block in scene.get("blocks") or [] if isinstance(block, dict)])
        if block_count > max_blocks_per_scene:
            max_blocks_per_scene = block_count
            longest_scene_name = safe_text(scene.get("name") or scene.get("id")) or "未命名场景"

    budget_rows = {
        "totalAssets": describe_budget_status(total_bytes, budget["totalAssetBudgetBytes"]),
        "referencedAssets": describe_budget_status(referenced_bytes, budget["referencedAssetBudgetBytes"]),
        "images": describe_budget_status(totals_by_group["image"], budget["imageAssetBudgetBytes"]),
        "audio": describe_budget_status(totals_by_group["audio"], budget["audioAssetBudgetBytes"]),
        "video": describe_budget_status(totals_by_group["video"], budget["videoAssetBudgetBytes"]),
    }

    if missing_referenced_assets:
        add_issue(
            issues,
            "hard",
            "missing_referenced_assets",
            "已引用素材缺失",
            f"有 {len(missing_referenced_assets)} 个被剧情或 UI 引用的素材在导出包里找不到文件。",
            "重新导入或替换这些素材后再导出，避免 Runtime 中出现空画面、静音或占位提示。",
        )

    for code, row in budget_rows.items():
        if row["overBudget"]:
            add_issue(
                issues,
                "warn",
                f"{code}_over_budget",
                "资源体积超过建议预算",
                f"{code} 当前 {row['currentLabel']}，建议预算 {row['budgetLabel']}。",
                "压缩图片、转码音频/视频，或拆分大体积资源到后续章节再加载。",
            )

    single_budget_by_group = {
        "image": budget["singleImageBudgetBytes"],
        "audio": budget["singleAudioBudgetBytes"],
        "video": budget["singleVideoBudgetBytes"],
    }
    oversized_assets = [
        asset
        for asset in asset_reports
        if asset["group"] in single_budget_by_group
        and asset["sizeBytes"] > single_budget_by_group[asset["group"]]
    ]
    if oversized_assets:
        add_issue(
            issues,
            "warn",
            "oversized_single_assets",
            "存在单个过大素材",
            f"{len(oversized_assets)} 个图片、音频或视频素材超过单文件建议预算。",
            "优先处理最大素材；大图可降低分辨率，大音频可转码，大视频建议压缩码率或拆分。",
        )

    if len(scenes) > budget["sceneWarningCount"]:
        add_issue(
            issues,
            "soft",
            "many_scenes",
            "场景数量较多",
            f"当前有 {len(scenes)} 个场景，后续维护和测试成本会明显上升。",
            "建议按章节拆分测试批次，并用路线图报告检查不可达与坏跳转。",
        )
    if len(blocks) > budget["storyBlockWarningCount"]:
        add_issue(
            issues,
            "soft",
            "many_story_blocks",
            "剧情卡片数量较多",
            f"当前有 {len(blocks)} 张剧情卡片。",
            "建议发布前跑路线测试，并把长章节拆成更短的可测单元。",
        )
    if max_blocks_per_scene > budget["maxBlocksPerSceneWarningCount"]:
        add_issue(
            issues,
            "soft",
            "long_scene",
            "存在过长场景",
            f"「{longest_scene_name}」包含 {max_blocks_per_scene} 张卡片。",
            "把长场景拆成多个自然段落，方便跳转、回看和崩溃后恢复。",
        )
    if unreferenced_existing_count > budget["unreferencedAssetWarningCount"]:
        add_issue(
            issues,
            "soft",
            "many_unreferenced_assets",
            "未使用素材较多",
            f"当前有 {unreferenced_existing_count} 个已随包但未被剧情或 UI 引用的素材。",
            "发布前清理废弃素材，减少包体和素材管理噪音。",
        )

    hard_count = sum(1 for issue in issues if issue["severity"] == "hard")
    warn_count = sum(1 for issue in issues if issue["severity"] == "warn")
    soft_count = sum(1 for issue in issues if issue["severity"] == "soft")
    status = "needs_fix" if hard_count else "needs_review" if warn_count else "ready"
    status_label = "需要修复" if status == "needs_fix" else "建议复核" if status == "needs_review" else "预算健康"
    largest_assets = sorted(asset_reports, key=lambda item: item["sizeBytes"], reverse=True)[:12]

    return {
        "formatVersion": PERFORMANCE_BUDGET_FORMAT_VERSION,
        "generatedAt": now_iso(),
        "status": status,
        "summary": {
            "statusLabel": status_label,
            "assetCount": len(assets),
            "existingAssetCount": sum(1 for asset in asset_reports if asset["exists"]),
            "referencedAssetCount": len([asset for asset in asset_reports if asset["referenced"]]),
            "missingReferencedAssetCount": len(missing_referenced_assets),
            "unreferencedExistingAssetCount": unreferenced_existing_count,
            "sceneCount": len(scenes),
            "storyBlockCount": len(blocks),
            "maxBlocksPerScene": max_blocks_per_scene,
            "longestSceneName": longest_scene_name,
            "totalAssetBytes": total_bytes,
            "totalAssetLabel": format_bytes(total_bytes),
            "referencedAssetBytes": referenced_bytes,
            "referencedAssetLabel": format_bytes(referenced_bytes),
            "hardCount": hard_count,
            "warnCount": warn_count,
            "softCount": soft_count,
        },
        "assetGroups": {
            group: {
                "count": counts_by_group[group],
                "bytes": totals_by_group[group],
                "label": format_bytes(totals_by_group[group]),
            }
            for group in ["image", "audio", "video", "font", "other"]
        },
        "budgets": {
            key: {
                **value,
                "label": key,
            }
            for key, value in budget_rows.items()
        },
        "issues": issues,
        "largestAssets": largest_assets,
        "missingReferencedAssets": missing_referenced_assets[:20],
        "oversizedAssets": oversized_assets[:20],
    }


def render_native_runtime_performance_budget_markdown(report: dict) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    asset_groups = report.get("assetGroups") if isinstance(report.get("assetGroups"), dict) else {}
    budgets = report.get("budgets") if isinstance(report.get("budgets"), dict) else {}
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []
    largest_assets = report.get("largestAssets") if isinstance(report.get("largestAssets"), list) else []
    missing_assets = report.get("missingReferencedAssets") if isinstance(report.get("missingReferencedAssets"), list) else []
    lines = [
        "# 原生 Runtime 性能预算报告",
        "",
        f"- 状态：{format_markdown_value(summary.get('statusLabel'), report.get('status') or 'unknown')}",
        f"- 总素材：{int(summary.get('assetCount') or 0)} 个 / 已引用：{int(summary.get('referencedAssetCount') or 0)} 个",
        f"- 总体积：{format_markdown_value(summary.get('totalAssetLabel'), '0 B')}",
        f"- 已引用素材体积：{format_markdown_value(summary.get('referencedAssetLabel'), '0 B')}",
        f"- 场景 / 卡片：{int(summary.get('sceneCount') or 0)} / {int(summary.get('storyBlockCount') or 0)}",
        f"- 最长场景：{format_markdown_value(summary.get('longestSceneName'), '无')}（{int(summary.get('maxBlocksPerScene') or 0)} 张卡片）",
        "",
        "## 体积预算",
        "",
        "| 项目 | 状态 | 当前 | 建议预算 |",
        "| --- | --- | --- | --- |",
    ]
    for key, label in [
        ("totalAssets", "全部素材"),
        ("referencedAssets", "已引用素材"),
        ("images", "图片 / UI"),
        ("audio", "音频"),
        ("video", "视频"),
    ]:
        row = budgets.get(key) if isinstance(budgets.get(key), dict) else {}
        lines.append(
            f"| {label} | {'超出' if row.get('overBudget') else '正常'} | "
            f"{format_markdown_value(row.get('currentLabel'), '0 B')} | {format_markdown_value(row.get('budgetLabel'), '0 B')} |"
        )
    lines.extend(["", "## 素材分类", "", "| 类型 | 数量 | 体积 |", "| --- | --- | --- |"])
    for key, label in [("image", "图片 / UI"), ("audio", "音频"), ("video", "视频"), ("font", "字体"), ("other", "其他")]:
        row = asset_groups.get(key) if isinstance(asset_groups.get(key), dict) else {}
        lines.append(f"| {label} | {int(row.get('count') or 0)} | {format_markdown_value(row.get('label'), '0 B')} |")
    lines.extend(["", "## 待关注项", ""])
    if issues:
        lines.extend(["| 严重度 | 项目 | 说明 | 建议 |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if isinstance(issue, dict):
                lines.append(
                    f"| {format_markdown_value(issue.get('severity'), 'soft')} | "
                    f"{format_markdown_value(issue.get('title'), '待关注')} | "
                    f"{format_markdown_value(issue.get('detail'), '-')} | "
                    f"{format_markdown_value(issue.get('suggestion'), '-')} |"
                )
    else:
        lines.append("没有发现明显性能预算风险。")
    lines.extend(["", "## 最大素材", ""])
    if largest_assets:
        lines.extend(["| 素材 | 类型 | 体积 | 是否引用 |", "| --- | --- | --- | --- |"])
        for asset in largest_assets:
            if isinstance(asset, dict):
                lines.append(
                    f"| {format_markdown_value(asset.get('name') or asset.get('assetId'), '未命名素材')} | "
                    f"{format_markdown_value(asset.get('type'), '-')} | "
                    f"{format_markdown_value(asset.get('sizeLabel'), '0 B')} | "
                    f"{'是' if asset.get('referenced') else '否'} |"
                )
    else:
        lines.append("没有可统计素材。")
    if missing_assets:
        lines.extend(["", "## 缺失的已引用素材", "", "| 素材 | 类型 | 路径 |", "| --- | --- | --- |"])
        for asset in missing_assets:
            if isinstance(asset, dict):
                lines.append(
                    f"| {format_markdown_value(asset.get('name') or asset.get('assetId'), '未命名素材')} | "
                    f"{format_markdown_value(asset.get('type'), '-')} | "
                    f"`{format_markdown_value(asset.get('path'), '未声明路径')}` |"
                )
    lines.extend(
        [
            "",
            "## 重新生成",
            "",
            "```bash",
            "python3 runtime_player.py --write-performance-budget-reports .",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_native_runtime_performance_budget_reports(bundle_dir: Path) -> dict:
    report = build_native_runtime_performance_budget_report(bundle_dir)
    (bundle_dir / PERFORMANCE_BUDGET_REPORT_NAME).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / PERFORMANCE_BUDGET_MARKDOWN_NAME).write_text(
        render_native_runtime_performance_budget_markdown(report),
        encoding="utf-8",
    )
    return report
