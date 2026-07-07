from __future__ import annotations


def format_export_digest_number(value: object) -> str:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}"


def build_native_3d_asset_export_digest(report_payload: dict | None) -> dict:
    if not isinstance(report_payload, dict):
        return {
            "status": "unavailable",
            "headline": "3D 资产清单暂不可用",
            "summaryLine": "导出时没有拿到可读 3D 报告。",
            "metrics": [],
            "issueAssetIds": [],
            "issueAssets": [],
            "topIssues": [],
            "recommendations": ["手动打开 3D 资产清单确认具体问题。"],
        }

    status = str(report_payload.get("status") or "unavailable")
    summary = report_payload.get("summary") if isinstance(report_payload.get("summary"), dict) else {}
    entries = report_payload.get("entries") if isinstance(report_payload.get("entries"), list) else []
    recommendations = report_payload.get("recommendations") if isinstance(report_payload.get("recommendations"), list) else []

    if status == "no_3d_assets":
        headline = "当前项目没有 3D 资产"
    elif status == "ready":
        headline = "3D 资产发布体检通过"
    elif status == "needs_attention":
        headline = "3D 资产需要发布前处理"
    else:
        headline = "3D 资产清单需要复核"

    risk_counts = {
        "性能预算": int(summary.get("performanceBudgetIssueCount") or 0),
        "GLB/VRM 容器": int(summary.get("glbContainerIssueCount") or 0),
        "内部引用": int(summary.get("gltfIntegrityIssueCount") or 0),
        "贴图槽": int(summary.get("textureSlotIssueCount") or 0),
        "外部依赖": int(summary.get("missingDependencyCount") or 0),
        "空结构": int(summary.get("emptyStructureCount") or 0),
    }
    risk_preview = " / ".join(f"{label} {count}" for label, count in risk_counts.items() if count > 0)
    if not risk_preview:
        risk_preview = "暂无明显 3D 风险" if int(summary.get("assetCount") or 0) else "未检测到 3D 资产"
    summary_line = (
        f"资产 {int(summary.get('assetCount') or 0)} 个，问题 {int(summary.get('issueCount') or 0)} 个；{risk_preview}。"
    )

    metrics = [
        {"label": "3D 资产", "value": f"{int(summary.get('assetCount') or 0)} 个"},
        {"label": "问题", "value": f"{int(summary.get('issueCount') or 0)} 个"},
        {"label": "性能预算", "value": f"{int(summary.get('performanceBudgetIssueCount') or 0)} 项"},
        {"label": "估算三角面", "value": format_export_digest_number(summary.get("estimatedTriangleCount"))},
        {"label": "Draw Call", "value": format_export_digest_number(summary.get("drawCallCount"))},
        {"label": "未使用", "value": f"{int(summary.get('unusedCount') or 0)} 个"},
    ]

    issue_assets = []
    for entry in entries:
        if not isinstance(entry, dict) or str(entry.get("status") or "") == "ready":
            continue
        entry_name = str(entry.get("name") or entry.get("assetId") or "未命名 3D 资产")
        issue_parts: list[str] = []
        issue_breakdown: list[dict] = []
        dependency = entry.get("dependencyHealth") if isinstance(entry.get("dependencyHealth"), dict) else {}
        preview_probe = entry.get("previewProbe") if isinstance(entry.get("previewProbe"), dict) else {}
        integrity_probe = entry.get("gltfIntegrityProbe") if isinstance(entry.get("gltfIntegrityProbe"), dict) else {}
        container_probe = entry.get("glbContainerProbe") if isinstance(entry.get("glbContainerProbe"), dict) else {}
        budget_probe = entry.get("performanceBudgetProbe") if isinstance(entry.get("performanceBudgetProbe"), dict) else {}

        budget_issue_count = int(budget_probe.get("issueCount") or 0)
        if budget_issue_count:
            issue_parts.append(f"性能预算 {budget_issue_count} 项")
            issue_breakdown.append({"code": "performance_budget", "label": "性能预算", "count": budget_issue_count})
        container_issue_count = int(container_probe.get("issueCount") or 0)
        if container_issue_count:
            issue_parts.append(f"容器 {container_issue_count} 项")
            issue_breakdown.append({"code": "glb_container", "label": "GLB/VRM 容器", "count": container_issue_count})
        integrity_issue_count = int(integrity_probe.get("issueCount") or 0)
        if integrity_issue_count:
            issue_parts.append(f"内部引用 {integrity_issue_count} 项")
            issue_breakdown.append({"code": "gltf_integrity", "label": "内部引用", "count": integrity_issue_count})
        texture_issue_count = int(preview_probe.get("textureSlotIssueCount") or 0)
        if texture_issue_count:
            issue_parts.append(f"贴图槽 {texture_issue_count} 项")
            issue_breakdown.append({"code": "texture_slot", "label": "贴图槽", "count": texture_issue_count})
        dependency_gap_count = len(dependency.get("missing") or []) + len(dependency.get("unsafe") or [])
        if dependency_gap_count:
            issue_parts.append(f"依赖 {dependency_gap_count} 项")
            issue_breakdown.append({"code": "dependency", "label": "外部依赖", "count": dependency_gap_count})
        if not issue_parts:
            issue_parts.append(str(entry.get("statusLabel") or "需要复核"))

        usage_preview: list[str] = []
        usages = entry.get("usages") if isinstance(entry.get("usages"), list) else []
        for usage in usages[:3]:
            if not isinstance(usage, dict):
                continue
            if usage.get("kind") == "character_model":
                usage_preview.append(f"角色：{usage.get('characterName') or usage.get('characterId') or '未命名角色'}")
            else:
                scene_label = " / ".join(
                    str(part)
                    for part in [usage.get("chapterName"), usage.get("sceneName")]
                    if str(part or "").strip()
                )
                block_index = usage.get("blockIndex")
                if isinstance(block_index, int):
                    scene_label = f"{scene_label or '场景'} · 第 {block_index + 1} 张卡片"
                usage_preview.append(scene_label or str(usage.get("kindLabel") or "剧情引用"))

        issue_assets.append(
            {
                "assetId": str(entry.get("assetId") or ""),
                "type": str(entry.get("type") or ""),
                "name": entry_name,
                "typeLabel": str(entry.get("typeLabel") or "3D 资产"),
                "exportUrl": str(entry.get("exportUrl") or ""),
                "status": str(entry.get("status") or ""),
                "statusLabel": str(entry.get("statusLabel") or "需要复核"),
                "summary": " / ".join(issue_parts),
                "issueCount": sum(int(item.get("count") or 0) for item in issue_breakdown) or len(issue_parts),
                "issueBreakdown": issue_breakdown,
                "usageCount": int(entry.get("usageCount") or 0),
                "usagePreview": usage_preview,
                "recommendedAction": str(entry.get("recommendedAction") or "复核 3D 资产导入状态。"),
            }
        )

    issue_asset_ids = []
    seen_issue_asset_ids = set()
    for issue in issue_assets:
        asset_id = str(issue.get("assetId") or "").strip()
        if asset_id and asset_id not in seen_issue_asset_ids:
            seen_issue_asset_ids.add(asset_id)
            issue_asset_ids.append(asset_id)

    return {
        "status": status,
        "headline": headline,
        "summaryLine": summary_line,
        "metrics": metrics,
        "riskCounts": risk_counts,
        "issueAssetIds": issue_asset_ids[:50],
        "issueAssets": issue_assets[:50],
        "topIssues": issue_assets[:5],
        "recommendations": [str(recommendation) for recommendation in recommendations[:4]],
    }
