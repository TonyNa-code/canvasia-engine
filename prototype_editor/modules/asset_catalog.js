(function attachAssetCatalogTools(global) {
  const ASSET_TYPE_LABELS = Object.freeze({
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "音乐",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "界面素材",
    font: "字体",
    live2d: "Live2D",
    model3d: "3D 模型",
    scene3d: "3D 场景",
  });

  const ASSET_PRESET_TAGS = Object.freeze({
    background: Object.freeze(["校园", "教室", "走廊", "屋顶", "黄昏", "夜晚", "日常"]),
    sprite: Object.freeze(["默认", "微笑", "害羞", "生气", "悲伤", "女主", "主角"]),
    cg: Object.freeze(["主线", "回忆", "约会", "告白", "高潮", "甜蜜"]),
    bgm: Object.freeze(["日常", "温柔", "紧张", "恋爱", "悲伤", "高潮"]),
    sfx: Object.freeze(["学校", "脚步", "环境", "提示", "门", "点击"]),
    voice: Object.freeze(["女主", "主角", "日常", "情绪", "告白", "独白"]),
    video: Object.freeze(["OP", "ED", "PV", "过场"]),
    ui: Object.freeze(["按钮", "对话框", "名字框", "图标", "菜单"]),
    font: Object.freeze(["正文", "标题", "圆体", "宋体", "手写", "授权确认"]),
    live2d: Object.freeze(["角色", "模型", "表情", "呼吸", "口型"]),
    model3d: Object.freeze(["角色", "GLB", "VRM", "待机", "动作"]),
    scene3d: Object.freeze(["场景", "地图", "房间", "GLB", "交互"]),
  });

  const CHARACTER_PRESENTATION_MODE_LABELS = Object.freeze({
    sprite: "普通立绘",
    layered_sprite: "差分立绘",
    live2d: "Live2D",
    model3d: "3D 模型",
  });

  const ASSET_FILTER_MODE_LABELS = Object.freeze({
    all: "显示全部",
    unused: "仅看未使用",
    missing_file: "仅看待导入",
    urgent_missing: "仅看已引用缺口",
    duplicate: "仅看疑似重复",
    asset3d_risk: "仅看 3D 发布风险",
    media_budget: "仅看素材预算风险",
  });

  const ASSET_FILTER_MODE_STATUS_LABELS = Object.freeze({
    all: "全部素材",
    unused: "未使用素材",
    missing_file: "待导入素材",
    urgent_missing: "已被项目引用但缺文件的素材",
    duplicate: "疑似重复素材",
    asset3d_risk: "最近一次 3D 发布体检标记的风险素材",
    media_budget: "体积偏大、建议发布前压缩的素材",
  });

  const ASSET_MEDIA_BUDGET_LIMITS = Object.freeze({
    background: Object.freeze({ warnBytes: 8 * 1024 * 1024, blockerBytes: 24 * 1024 * 1024, label: "背景图" }),
    sprite: Object.freeze({ warnBytes: 6 * 1024 * 1024, blockerBytes: 18 * 1024 * 1024, label: "立绘" }),
    cg: Object.freeze({ warnBytes: 10 * 1024 * 1024, blockerBytes: 32 * 1024 * 1024, label: "CG" }),
    ui: Object.freeze({ warnBytes: 4 * 1024 * 1024, blockerBytes: 16 * 1024 * 1024, label: "界面素材" }),
    bgm: Object.freeze({ warnBytes: 18 * 1024 * 1024, blockerBytes: 60 * 1024 * 1024, label: "音乐" }),
    sfx: Object.freeze({ warnBytes: 6 * 1024 * 1024, blockerBytes: 18 * 1024 * 1024, label: "音效" }),
    voice: Object.freeze({ warnBytes: 8 * 1024 * 1024, blockerBytes: 24 * 1024 * 1024, label: "语音" }),
    video: Object.freeze({ warnBytes: 120 * 1024 * 1024, blockerBytes: 500 * 1024 * 1024, label: "视频" }),
    font: Object.freeze({ warnBytes: 20 * 1024 * 1024, blockerBytes: 60 * 1024 * 1024, label: "字体" }),
    live2d: Object.freeze({ warnBytes: 40 * 1024 * 1024, blockerBytes: 120 * 1024 * 1024, label: "Live2D" }),
    model3d: Object.freeze({ warnBytes: 80 * 1024 * 1024, blockerBytes: 300 * 1024 * 1024, label: "3D 模型" }),
    scene3d: Object.freeze({ warnBytes: 120 * 1024 * 1024, blockerBytes: 500 * 1024 * 1024, label: "3D 场景" }),
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeCharacterPresentationMode(mode) {
    return hasOwn(CHARACTER_PRESENTATION_MODE_LABELS, mode) ? mode : "sprite";
  }

  function getCharacterPresentationModeLabel(mode) {
    return CHARACTER_PRESENTATION_MODE_LABELS[getSafeCharacterPresentationMode(mode)] ?? CHARACTER_PRESENTATION_MODE_LABELS.sprite;
  }

  function getSafeAssetFilterMode(filterMode) {
    const safeMode = String(filterMode ?? "").trim();
    return hasOwn(ASSET_FILTER_MODE_LABELS, safeMode) ? safeMode : "all";
  }

  function getAssetFilterModeLabel(filterMode) {
    return ASSET_FILTER_MODE_LABELS[getSafeAssetFilterMode(filterMode)] ?? ASSET_FILTER_MODE_LABELS.all;
  }

  function getAssetFilterModeStatusLabel(filterMode) {
    return ASSET_FILTER_MODE_STATUS_LABELS[getSafeAssetFilterMode(filterMode)] ?? ASSET_FILTER_MODE_STATUS_LABELS.all;
  }

  function getAssetMediaBudgetLimit(asset) {
    if (!asset) {
      return null;
    }
    return ASSET_MEDIA_BUDGET_LIMITS[asset.type] ?? null;
  }

  function formatFileSize(bytes) {
    const size = Number(bytes);
    if (!Number.isFinite(size) || size < 0) {
      return "未知";
    }
    if (size < 1024) {
      return `${size} B`;
    }
    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(size < 10 * 1024 ? 1 : 0)} KB`;
    }
    return `${(size / (1024 * 1024)).toFixed(size < 10 * 1024 * 1024 ? 1 : 0)} MB`;
  }

  function getAssetList(data) {
    return Array.isArray(data?.assetList) ? data.assetList : [];
  }

  function getAssetUsageEntries(assetId, data) {
    if (!data?.assetUsage || !assetId) {
      return [];
    }
    if (typeof data.assetUsage.get === "function") {
      return data.assetUsage.get(assetId) ?? [];
    }
    return Object.prototype.hasOwnProperty.call(data.assetUsage, assetId) ? data.assetUsage[assetId] ?? [] : [];
  }

  function getDuplicateCountForType(duplicateOverview, assetType) {
    if (!duplicateOverview || !assetType) {
      return 0;
    }
    if (typeof duplicateOverview.perTypeMap?.get === "function") {
      return duplicateOverview.perTypeMap.get(assetType)?.duplicateCount ?? 0;
    }
    return duplicateOverview.perType?.find((entry) => entry.type === assetType)?.duplicateCount ?? 0;
  }

  function isImageAssetType(type) {
    return ["background", "sprite", "cg", "ui"].includes(type);
  }

  function isAudioAssetType(type) {
    return ["bgm", "sfx", "voice"].includes(type);
  }

  function isVideoAssetType(type) {
    return type === "video";
  }

  function isScene3dAssetType(type) {
    return type === "scene3d";
  }

  function isAssetMissingFile(asset) {
    return !Boolean(asset?.fileExists);
  }

  function getAssetUsageCount(assetId, data) {
    return getAssetUsageEntries(assetId, data).length;
  }

  function getAssetById(assetId, data) {
    if (!assetId) {
      return null;
    }
    if (typeof data?.assetsById?.get === "function") {
      return data.assetsById.get(assetId) ?? null;
    }
    if (data?.assetsById && Object.prototype.hasOwnProperty.call(data.assetsById, assetId)) {
      return data.assetsById[assetId] ?? null;
    }
    return getAssetList(data).find((asset) => asset.id === assetId) ?? null;
  }

  function normalizeAssetDuplicateToken(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/[\\/]+/g, "/")
      .replace(/\.[a-z0-9]{2,5}$/i, "")
      .replace(/(?:\s*[\(\[（【]?(copy|副本|复制|拷贝)\s*[\)\]）】]?|\s*[\(\[（【]\d+[\)\]）】])$/gi, "")
      .replace(/[\s_\-·.()[\]（）【】]+/g, "");
  }

  function getAssetPathBasename(assetPath) {
    const path = String(assetPath ?? "").trim();
    if (!path) {
      return "";
    }
    const parts = path.replace(/\\/g, "/").split("/");
    return parts[parts.length - 1] ?? "";
  }

  function getAssetDuplicateReasonLabels(info, relatedAssetId = null) {
    const labels = [];
    const matches = {
      exactPath: relatedAssetId ? info.pathMatchIds.has(relatedAssetId) : info.pathMatchIds.size > 0,
      sameName: relatedAssetId ? info.nameMatchIds.has(relatedAssetId) : info.nameMatchIds.size > 0,
      sameStem: relatedAssetId ? info.stemMatchIds.has(relatedAssetId) : info.stemMatchIds.size > 0,
    };

    if (matches.exactPath) {
      labels.push({ text: "同一路径", toneClass: "danger-text" });
    }
    if (matches.sameName) {
      labels.push({ text: "名字几乎一样", toneClass: "warn-text" });
    }
    if (matches.sameStem) {
      labels.push({ text: "文件名几乎一样", toneClass: "warn-text" });
    }

    return labels;
  }

  function getAssetDuplicatePreferenceScore(asset, data) {
    if (!asset) {
      return -1;
    }

    return (
      getAssetUsageCount(asset.id, data) * 100 +
      (asset.fileExists ? 40 : 0) +
      (asset.favorite ? 16 : 0) +
      Math.min((asset.tags ?? []).length, 4) * 4 +
      (asset.fileSizeBytes ? 1 : 0)
    );
  }

  function buildAssetDuplicatePreferenceNotes(asset, data) {
    if (!asset) {
      return [];
    }

    const notes = [];
    const usageCount = getAssetUsageCount(asset.id, data);

    if (usageCount > 0) {
      notes.push(`已经被剧情使用 ${usageCount} 处`);
    }
    if (asset.fileExists) {
      notes.push("真实文件已经就绪");
    }
    if (asset.favorite) {
      notes.push("你已经收藏过它");
    }
    if ((asset.tags ?? []).length > 0) {
      notes.push(`标签更完整（${(asset.tags ?? []).length} 个）`);
    }
    if (notes.length === 0) {
      notes.push(asset.path ? "路径更明确，适合作为主版本" : "名字更稳定，适合作为主版本");
    }

    return notes.slice(0, 3);
  }

  function buildAssetDuplicateOverview(data) {
    const pathGroups = new Map();
    const nameGroups = new Map();
    const stemGroups = new Map();
    const infoSeed = new Map();

    const ensureInfo = (assetId) => {
      if (!infoSeed.has(assetId)) {
        infoSeed.set(assetId, {
          assetId,
          relatedIds: new Set(),
          pathMatchIds: new Set(),
          nameMatchIds: new Set(),
          stemMatchIds: new Set(),
          score: 0,
        });
      }
      return infoSeed.get(assetId);
    };

    getAssetList(data).forEach((asset) => {
      const normalizedPath = String(asset.path ?? "").trim().toLowerCase().replace(/\\/g, "/");
      const nameKey = normalizeAssetDuplicateToken(asset.name);
      const stemKey = normalizeAssetDuplicateToken(getAssetPathBasename(asset.path));

      if (normalizedPath) {
        const group = pathGroups.get(normalizedPath) ?? [];
        group.push(asset);
        pathGroups.set(normalizedPath, group);
      }

      if (nameKey) {
        const group = nameGroups.get(`${asset.type}:${nameKey}`) ?? [];
        group.push(asset);
        nameGroups.set(`${asset.type}:${nameKey}`, group);
      }

      if (stemKey) {
        const group = stemGroups.get(`${asset.type}:${stemKey}`) ?? [];
        group.push(asset);
        stemGroups.set(`${asset.type}:${stemKey}`, group);
      }
    });

    const markGroup = (group, key, weight) => {
      if ((group?.length ?? 0) < 2) {
        return;
      }

      group.forEach((asset) => {
        const info = ensureInfo(asset.id);
        group.forEach((otherAsset) => {
          if (otherAsset.id === asset.id) {
            return;
          }
          info.relatedIds.add(otherAsset.id);
          if (key === "path") {
            info.pathMatchIds.add(otherAsset.id);
          } else if (key === "name") {
            info.nameMatchIds.add(otherAsset.id);
          } else if (key === "stem") {
            info.stemMatchIds.add(otherAsset.id);
          }
        });
        info.score += weight;
      });
    };

    pathGroups.forEach((group) => markGroup(group, "path", 5));
    nameGroups.forEach((group) => markGroup(group, "name", 3));
    stemGroups.forEach((group) => markGroup(group, "stem", 2));

    const rawEntries = Array.from(infoSeed.values())
      .filter((info) => info.relatedIds.size > 0)
      .map((info) => {
        const asset = getAssetById(info.assetId, data);
        const reasonParts = [];

        if (info.pathMatchIds.size > 0) {
          reasonParts.push(`和 ${info.pathMatchIds.size} 个素材指向同一路径`);
        }
        if (info.nameMatchIds.size > 0) {
          reasonParts.push(`名字和 ${info.nameMatchIds.size} 个素材几乎一样`);
        }
        if (info.stemMatchIds.size > 0) {
          reasonParts.push(`文件名和 ${info.stemMatchIds.size} 个素材几乎一样`);
        }

        return {
          ...info,
          asset,
          relatedIds: Array.from(info.relatedIds),
          tone: info.pathMatchIds.size > 0 ? "danger" : info.nameMatchIds.size > 0 ? "warn" : "soft",
          relatedCount: info.relatedIds.size,
          summary: reasonParts.join(" · "),
          reasonNote:
            info.pathMatchIds.size > 0
              ? "这组素材里至少有两项指向了同一个文件路径，通常很适合回头合并或确认是不是误导入。"
              : "这些素材的名字或文件名非常接近，可回头确认是不是同一组素材的重复版本。",
        };
      })
      .filter((entry) => entry.asset);

    const adjacency = new Map(rawEntries.map((entry) => [entry.assetId, new Set(entry.relatedIds)]));
    const visited = new Set();
    const clusters = [];

    adjacency.forEach((_, startId) => {
      if (visited.has(startId)) {
        return;
      }

      const stack = [startId];
      const assetIds = [];

      while (stack.length > 0) {
        const assetId = stack.pop();
        if (!assetId || visited.has(assetId)) {
          continue;
        }
        visited.add(assetId);
        assetIds.push(assetId);
        (adjacency.get(assetId) ?? new Set()).forEach((relatedId) => {
          if (!visited.has(relatedId)) {
            stack.push(relatedId);
          }
        });
      }

      const assets = assetIds
        .map((assetId) => getAssetById(assetId, data))
        .filter(Boolean)
        .sort((left, right) => {
          const scoreDiff = getAssetDuplicatePreferenceScore(right, data) - getAssetDuplicatePreferenceScore(left, data);
          if (scoreDiff !== 0) {
            return scoreDiff;
          }
          return left.name.localeCompare(right.name, "zh-Hans-CN");
        });

      if (!assets.length) {
        return;
      }

      const clusterEntries = assetIds
        .map((assetId) => rawEntries.find((entry) => entry.assetId === assetId))
        .filter(Boolean);
      const preferredAsset = assets[0];
      const preferredNotes = buildAssetDuplicatePreferenceNotes(preferredAsset, data);
      const usedAssetsCount = assets.filter((asset) => getAssetUsageCount(asset.id, data) > 0).length;
      const readyAssetsCount = assets.filter((asset) => asset.fileExists).length;
      const tone = clusterEntries.some((entry) => entry.pathMatchIds.size > 0)
        ? "danger"
        : usedAssetsCount > 1
          ? "warn"
          : "soft";
      const clusterId = `duplicate_cluster_${clusters.length + 1}`;

      clusters.push({
        id: clusterId,
        assetIds,
        assets,
        preferredAssetId: preferredAsset.id,
        preferredAsset,
        preferredNotes,
        tone,
        usedAssetsCount,
        readyAssetsCount,
        reasonLabels: getAssetDuplicateReasonLabels({
          pathMatchIds: new Set(clusterEntries.flatMap((entry) => Array.from(entry.pathMatchIds))),
          nameMatchIds: new Set(clusterEntries.flatMap((entry) => Array.from(entry.nameMatchIds))),
          stemMatchIds: new Set(clusterEntries.flatMap((entry) => Array.from(entry.stemMatchIds))),
        }),
        summary: `这一组共 ${assets.length} 项，优先保留 ${preferredAsset.name}`,
        recommendation:
          usedAssetsCount > 1
            ? `这一组里已经有 ${usedAssetsCount} 项被剧情引用，可先围着“${preferredAsset.name}”统一整理。`
            : `这一组可先以“${preferredAsset.name}”为主版本，再决定其他条目是删除、改名还是补标签。`,
        priorityScore:
          (clusterEntries.some((entry) => entry.pathMatchIds.size > 0) ? 120 : 0) +
          usedAssetsCount * 28 +
          readyAssetsCount * 10 +
          assets.length * 6,
      });
    });

    clusters.sort((left, right) => {
      if (right.priorityScore !== left.priorityScore) {
        return right.priorityScore - left.priorityScore;
      }
      return left.preferredAsset.name.localeCompare(right.preferredAsset.name, "zh-Hans-CN");
    });

    const clusterByAssetId = new Map();
    clusters.forEach((cluster) => {
      cluster.assetIds.forEach((assetId) => {
        clusterByAssetId.set(assetId, cluster);
      });
    });

    const entries = rawEntries
      .map((entry) => {
        const cluster = clusterByAssetId.get(entry.assetId);
        const isPreferred = cluster?.preferredAssetId === entry.assetId;
        const recommendationText = isPreferred
          ? "这一项更适合作为主版本保留。"
          : `优先保留：${cluster?.preferredAsset?.name ?? "另一项更完整的素材"}`;

        return {
          ...entry,
          clusterId: cluster?.id ?? "",
          preferredAssetId: cluster?.preferredAssetId ?? "",
          preferredAsset: cluster?.preferredAsset ?? null,
          preferredNotes: cluster?.preferredNotes ?? [],
          isPreferred,
          summary: `${entry.summary} · ${recommendationText}`,
          recommendationText,
        };
      })
      .sort((left, right) => {
        if (right.score !== left.score) {
          return right.score - left.score;
        }
        if (right.relatedCount !== left.relatedCount) {
          return right.relatedCount - left.relatedCount;
        }
        return left.asset.name.localeCompare(right.asset.name, "zh-Hans-CN");
      });

    const perType = Object.keys(ASSET_TYPE_LABELS).map((type) => ({
      type,
      label: getAssetTypeLabel(type),
      duplicateCount: entries.filter((entry) => entry.asset?.type === type).length,
    }));

    return {
      count: entries.length,
      entries,
      assetIdSet: new Set(entries.map((entry) => entry.assetId)),
      infoByAssetId: new Map(entries.map((entry) => [entry.assetId, entry])),
      clusters,
      clusterByAssetId,
      perType,
      perTypeMap: new Map(perType.map((entry) => [entry.type, entry])),
      priorityTypes: perType
        .filter((entry) => entry.duplicateCount > 0)
        .sort((left, right) => {
          if (right.duplicateCount !== left.duplicateCount) {
            return right.duplicateCount - left.duplicateCount;
          }
          return left.label.localeCompare(right.label, "zh-Hans-CN");
        })
        .slice(0, 4),
      priorityClusters: clusters.slice(0, 4),
    };
  }

  function isAssetUnused(assetId, data) {
    return getAssetUsageCount(assetId, data) === 0;
  }

  function getUnusedAssets(data) {
    return getAssetList(data).filter((asset) => isAssetUnused(asset.id, data));
  }

  function isAssetUrgentMissing(asset, data) {
    return isAssetMissingFile(asset) && getAssetUsageCount(asset?.id, data) > 0;
  }

  function getAssetMediaBudgetSuggestion(asset, severity = "warn") {
    switch (asset?.type) {
      case "background":
      case "sprite":
      case "cg":
      case "ui":
        return severity === "blocker"
          ? "建议先压到 WebP/高质量 JPEG，或拆分超大 PNG；否则桌面包体和加载峰值都会偏重。"
          : "建议发布前压缩图片，透明素材优先 WebP/PNGQuant，背景和 CG 可考虑高质量 JPEG/WebP。";
      case "bgm":
        return "建议将无压缩或超大音频转为 OGG/MP3，并确认循环点；音乐体积过大时会明显抬高下载包。";
      case "sfx":
      case "voice":
        return "建议把语音/音效批量转成 OGG/MP3，并按章节或角色整理，避免单文件过大影响加载。";
      case "video":
        return "建议用 H.264/H.265 重新编码，并控制码率、分辨率和时长；OP/ED 可保留高质版但最好另做预览压缩版。";
      case "font":
        return "建议确认字体授权并做子集化；只保留项目实际需要的字重和字符范围。";
      case "live2d":
        return "建议清理未用纹理和动作文件，压缩贴图，并保留一份可编辑源文件在项目外归档。";
      case "model3d":
      case "scene3d":
        return "建议压缩贴图、减少内嵌大纹理，并用 3D 资产清单同步确认面数、材质和 draw call 预算。";
      default:
        return "建议在正式发布前压缩这个素材，降低包体和加载风险。";
    }
  }

  function getAssetMediaBudgetRisk(asset) {
    const limit = getAssetMediaBudgetLimit(asset);
    const size = Number(asset?.fileSizeBytes ?? 0);
    if (!limit || !asset?.fileExists || !Number.isFinite(size) || size <= limit.warnBytes) {
      return null;
    }

    const severity = size >= limit.blockerBytes ? "blocker" : "warn";
    const overRatio = limit.warnBytes > 0 ? size / limit.warnBytes : 0;
    return {
      assetId: asset.id,
      type: asset.type,
      typeLabel: getAssetTypeLabel(asset.type),
      name: asset.name,
      fileSizeBytes: size,
      fileSizeLabel: formatFileSize(size),
      warnBytes: limit.warnBytes,
      warnLabel: formatFileSize(limit.warnBytes),
      blockerBytes: limit.blockerBytes,
      blockerLabel: formatFileSize(limit.blockerBytes),
      severity,
      severityLabel: severity === "blocker" ? "明显超预算" : "建议压缩",
      overRatio,
      summary: `${getAssetTypeLabel(asset.type)} ${formatFileSize(size)}，建议控制在 ${formatFileSize(limit.warnBytes)} 左右。`,
      suggestion: getAssetMediaBudgetSuggestion(asset, severity),
    };
  }

  function buildAssetMediaBudgetReport(data) {
    const items = getAssetList(data)
      .map((asset) => getAssetMediaBudgetRisk(asset))
      .filter(Boolean)
      .sort((left, right) => {
        const severityDiff = Number(right.severity === "blocker") - Number(left.severity === "blocker");
        if (severityDiff !== 0) {
          return severityDiff;
        }
        return right.fileSizeBytes - left.fileSizeBytes;
      });
    const assetIds = new Set(items.map((item) => item.assetId));
    const totalBytes = items.reduce((sum, item) => sum + item.fileSizeBytes, 0);
    const blockerCount = items.filter((item) => item.severity === "blocker").length;
    const perType = Object.keys(ASSET_TYPE_LABELS)
      .map((type) => {
        const typeItems = items.filter((item) => item.type === type);
        return {
          type,
          label: getAssetTypeLabel(type),
          count: typeItems.length,
          totalBytes: typeItems.reduce((sum, item) => sum + item.fileSizeBytes, 0),
        };
      })
      .filter((item) => item.count > 0);

    return {
      items,
      assetIds,
      count: items.length,
      blockerCount,
      warnCount: Math.max(items.length - blockerCount, 0),
      totalBytes,
      totalLabel: formatFileSize(totalBytes),
      largest: items[0] ?? null,
      perType,
    };
  }

  function buildAssetGapOverview(data, duplicateOverview = null) {
    const assets = getAssetList(data);
    const perType = Object.keys(ASSET_TYPE_LABELS).map((type) => {
      const typeAssets = assets.filter((asset) => asset.type === type);
      const missingCount = typeAssets.filter((asset) => isAssetMissingFile(asset)).length;
      const urgentMissingCount = typeAssets.filter((asset) => isAssetUrgentMissing(asset, data)).length;
      const unusedCount = typeAssets.filter((asset) => isAssetUnused(asset.id, data)).length;
      const duplicateCount = getDuplicateCountForType(duplicateOverview, type);
      return {
        type,
        label: getAssetTypeLabel(type),
        totalCount: typeAssets.length,
        readyCount: typeAssets.length - missingCount,
        missingCount,
        urgentMissingCount,
        unusedCount,
        duplicateCount,
      };
    });

    return {
      totalCount: assets.length,
      readyCount: assets.filter((asset) => !isAssetMissingFile(asset)).length,
      missingCount: assets.filter((asset) => isAssetMissingFile(asset)).length,
      urgentMissingCount: assets.filter((asset) => isAssetUrgentMissing(asset, data)).length,
      unusedCount: getUnusedAssets(data).length,
      duplicateCount: duplicateOverview?.count ?? 0,
      perType,
      perTypeMap: new Map(perType.map((entry) => [entry.type, entry])),
      priorityTypes: perType
        .filter((entry) => entry.missingCount > 0 || entry.duplicateCount > 0)
        .sort((left, right) => {
          if (right.urgentMissingCount !== left.urgentMissingCount) {
            return right.urgentMissingCount - left.urgentMissingCount;
          }
          if (right.missingCount !== left.missingCount) {
            return right.missingCount - left.missingCount;
          }
          if (right.duplicateCount !== left.duplicateCount) {
            return right.duplicateCount - left.duplicateCount;
          }
          return left.label.localeCompare(right.label, "zh-Hans-CN");
        })
        .slice(0, 4),
    };
  }

  function getAssetTypeGapSummaryText(assetType, assetPool = null, data = {}, duplicateOverview = null) {
    const assets = assetPool ?? getAssetList(data).filter((asset) => asset.type === assetType);
    const totalCount = assets.length;
    const missingCount = assets.filter((asset) => isAssetMissingFile(asset)).length;
    const urgentMissingCount = assets.filter((asset) => isAssetUrgentMissing(asset, data)).length;
    const duplicateCount = getDuplicateCountForType(duplicateOverview, assetType);

    if (totalCount === 0) {
      return "这一类暂时还没有素材";
    }

    if (missingCount === 0 && duplicateCount === 0) {
      return `全量 ${totalCount} 个素材都已经导入完成`;
    }

    if (urgentMissingCount > 0) {
      return `全量 ${totalCount} 个里待导入 ${missingCount} 个，其中已引用缺口 ${urgentMissingCount} 个${
        duplicateCount > 0 ? `，另有疑似重复 ${duplicateCount} 个` : ""
      }`;
    }

    if (missingCount > 0) {
      return `全量 ${totalCount} 个里待导入 ${missingCount} 个${
        duplicateCount > 0 ? `，另有疑似重复 ${duplicateCount} 个` : ""
      }`;
    }

    return `全量 ${totalCount} 个素材都已经就绪，当前重点是整理疑似重复 ${duplicateCount} 个`;
  }

  function normalizeAssetSearchQuery(value) {
    return String(value ?? "").trim().toLowerCase();
  }

  function getAssetSortLabel(sortMode) {
    const labels = {
      default: "默认顺序",
      recent: "最近导入在前",
      name: "按名称排序",
      usage: "按使用次数排序",
      favorite: "收藏优先",
    };
    return labels[sortMode] ?? sortMode;
  }

  function getIdSet(value) {
    if (value instanceof Set) {
      return value;
    }
    if (Array.isArray(value)) {
      return new Set(value.map((item) => String(item ?? "").trim()).filter(Boolean));
    }
    return new Set();
  }

  function sortAssets(assets, sortMode = "default", data = {}) {
    const list = [...(Array.isArray(assets) ? assets : [])];

    if (sortMode === "recent") {
      return list.reverse();
    }

    if (sortMode === "name") {
      return list.sort((left, right) => left.name.localeCompare(right.name, "zh-Hans-CN"));
    }

    if (sortMode === "usage") {
      return list.sort((left, right) => {
        const usageDiff = getAssetUsageCount(right.id, data) - getAssetUsageCount(left.id, data);
        if (usageDiff !== 0) {
          return usageDiff;
        }
        return left.name.localeCompare(right.name, "zh-Hans-CN");
      });
    }

    if (sortMode === "favorite") {
      return list.sort((left, right) => {
        const favoriteDiff = Number(Boolean(right.favorite)) - Number(Boolean(left.favorite));
        if (favoriteDiff !== 0) {
          return favoriteDiff;
        }
        const usageDiff = getAssetUsageCount(right.id, data) - getAssetUsageCount(left.id, data);
        if (usageDiff !== 0) {
          return usageDiff;
        }
        return left.name.localeCompare(right.name, "zh-Hans-CN");
      });
    }

    return list;
  }

  function getVisibleAssets(data = {}, filters = {}) {
    const {
      filterMode = "all",
      searchQuery = "",
      tagFilter = "",
      sortMode = "default",
      favoriteOnly = false,
      nativeRuntime3dRiskAssetIds = [],
    } = filters;
    const assetList = getAssetList(data);
    const safeFilterMode = getSafeAssetFilterMode(filterMode);
    const duplicateOverview =
      safeFilterMode === "duplicate" ? filters.duplicateOverview ?? buildAssetDuplicateOverview(data) : null;
    const mediaBudgetReport =
      safeFilterMode === "media_budget" ? filters.mediaBudgetReport ?? buildAssetMediaBudgetReport(data) : null;
    const nativeRuntime3dRiskSet = getIdSet(nativeRuntime3dRiskAssetIds);
    let assets = [];

    if (safeFilterMode === "unused") {
      assets = getUnusedAssets(data);
    } else if (safeFilterMode === "missing_file") {
      assets = assetList.filter((asset) => isAssetMissingFile(asset));
    } else if (safeFilterMode === "urgent_missing") {
      assets = assetList.filter((asset) => isAssetUrgentMissing(asset, data));
    } else if (safeFilterMode === "duplicate") {
      assets = assetList.filter((asset) => duplicateOverview.assetIdSet.has(asset.id));
    } else if (safeFilterMode === "asset3d_risk") {
      assets = assetList.filter((asset) => nativeRuntime3dRiskSet.has(asset.id));
    } else if (safeFilterMode === "media_budget") {
      assets = assetList.filter((asset) => mediaBudgetReport.assetIds.has(asset.id));
    } else {
      assets = assetList;
    }

    const cleanTag = String(tagFilter ?? "").trim();
    if (cleanTag) {
      assets = assets.filter((asset) => (asset.tags ?? []).includes(cleanTag));
    }

    if (favoriteOnly) {
      assets = assets.filter((asset) => Boolean(asset.favorite));
    }

    const query = normalizeAssetSearchQuery(searchQuery);
    if (query) {
      assets = assets.filter((asset) => {
        const haystack = normalizeAssetSearchQuery([
          asset.name,
          asset.id,
          asset.path,
          ...(asset.tags ?? []),
          getAssetTypeLabel(asset.type),
        ].join(" "));
        return haystack.includes(query);
      });
    }

    if (safeFilterMode === "duplicate" && sortMode === "default") {
      return [...assets].sort((left, right) => {
        const leftInfo = duplicateOverview.infoByAssetId.get(left.id);
        const rightInfo = duplicateOverview.infoByAssetId.get(right.id);
        const scoreDiff = (rightInfo?.score ?? 0) - (leftInfo?.score ?? 0);
        if (scoreDiff !== 0) {
          return scoreDiff;
        }
        const relatedDiff = (rightInfo?.relatedCount ?? 0) - (leftInfo?.relatedCount ?? 0);
        if (relatedDiff !== 0) {
          return relatedDiff;
        }
        return left.name.localeCompare(right.name, "zh-Hans-CN");
      });
    }

    return sortAssets(assets, sortMode, data);
  }

  function pruneAssetCheckedIds(checkedIds = [], data = {}) {
    const validIds = new Set(getAssetList(data).map((asset) => asset.id));
    const nextIds = [];
    const seenIds = new Set();

    (checkedIds ?? []).forEach((assetId) => {
      const cleanId = String(assetId ?? "").trim();
      if (!cleanId || seenIds.has(cleanId) || !validIds.has(cleanId)) {
        return;
      }
      nextIds.push(cleanId);
      seenIds.add(cleanId);
    });

    return nextIds;
  }

  function getCheckedAssetIds(checkedIds = [], data = {}) {
    return pruneAssetCheckedIds(checkedIds, data);
  }

  function getCurrentFilteredAssetsOfSelectedType(data = {}, assetType = "", filters = {}) {
    return getVisibleAssets(data, filters).filter((asset) => asset.type === assetType);
  }

  function getCurrentCheckedAssetIds(checkedIds = [], data = {}, assetType = "", filters = {}) {
    const currentTypeIds = new Set(
      getCurrentFilteredAssetsOfSelectedType(data, assetType, filters).map((asset) => asset.id)
    );
    return getCheckedAssetIds(checkedIds, data).filter((assetId) => currentTypeIds.has(assetId));
  }

  function getCurrentCheckedAssetsOfSelectedType(checkedIds = [], data = {}, assetType = "", filters = {}) {
    const checkedIdSet = new Set(getCurrentCheckedAssetIds(checkedIds, data, assetType, filters));
    return getCurrentFilteredAssetsOfSelectedType(data, assetType, filters).filter((asset) => checkedIdSet.has(asset.id));
  }

  function isAssetChecked(assetId, checkedIds = [], data = {}) {
    return getCheckedAssetIds(checkedIds, data).includes(assetId);
  }

  function toggleAssetChecked(checkedIds = [], assetId, checked, data = {}) {
    const nextCheckedIds = new Set(getCheckedAssetIds(checkedIds, data));
    const cleanId = String(assetId ?? "").trim();
    if (!cleanId || !getAssetById(cleanId, data)) {
      return Array.from(nextCheckedIds);
    }

    if (checked) {
      nextCheckedIds.add(cleanId);
    } else {
      nextCheckedIds.delete(cleanId);
    }
    return Array.from(nextCheckedIds);
  }

  function parseAssetTagsInput(value, options = {}) {
    const rawLimit = Number(options.limit ?? 20);
    const limit = Number.isFinite(rawLimit) ? Math.max(0, Math.floor(rawLimit)) : 20;
    if (limit === 0) {
      return [];
    }

    return Array.from(
      new Set(
        String(value ?? "")
          .split(/[\n,，、;；]+/)
          .map((tag) => tag.trim())
          .filter(Boolean)
      )
    ).slice(0, limit);
  }

  function getSafeAssetIdByType(assetType, assetId = null, data = {}) {
    const assets = getAssetList(data).filter((asset) => asset.type === assetType);
    return assets.some((asset) => asset.id === assetId) ? assetId : assets[0]?.id ?? "";
  }

  function buildBulkAssetTagOperation(mode, rawTags, checkedAssets = [], filteredAssets = [], options = {}) {
    const tags = parseAssetTagsInput(rawTags, options);
    const safeMode = mode === "remove" ? "remove" : "add";
    const actionLabel = safeMode === "remove" ? "移除" : "添加";
    const checkedList = Array.isArray(checkedAssets) ? checkedAssets.filter(Boolean) : [];
    const filteredList = Array.isArray(filteredAssets) ? filteredAssets.filter(Boolean) : [];
    const assets = checkedList.length > 0 ? checkedList : filteredList;
    const targetScope = checkedList.length > 0 ? "checked" : "filtered";
    const targetLabel =
      targetScope === "checked"
        ? `当前勾选的 ${checkedList.length} 个素材`
        : `当前筛选结果里的 ${filteredList.length} 个素材`;

    return {
      mode: safeMode,
      tags,
      assets,
      assetIds: assets.map((asset) => asset.id).filter(Boolean),
      actionLabel,
      targetLabel,
      targetScope,
      canApply: assets.length > 0 && tags.length > 0,
      error: !assets.length ? "no_assets" : !tags.length ? "no_tags" : "",
      confirmationMessage: `确定要给${targetLabel}批量${actionLabel}标签吗？\n\n标签：${tags.join(" / ")}`,
    };
  }

  function buildPresetAssetTagOperation(rawTag, checkedAssets = [], selectedAsset = null) {
    const tag = String(rawTag ?? "").trim();
    const checkedList = Array.isArray(checkedAssets) ? checkedAssets.filter(Boolean) : [];
    const targetAssets = checkedList.length > 0 ? checkedList : selectedAsset ? [selectedAsset] : [];
    const targetLabel =
      checkedList.length > 0 ? `勾选的 ${checkedList.length} 个素材` : `当前素材：${selectedAsset?.name ?? ""}`;

    return {
      tag,
      tags: tag ? [tag] : [],
      targetAssets,
      assetIds: targetAssets.map((asset) => asset.id).filter(Boolean),
      targetLabel,
      targetScope: checkedList.length > 0 ? "checked" : "selected",
      canApply: Boolean(tag) && targetAssets.length > 0,
      error: !tag ? "no_tag" : !targetAssets.length ? "no_assets" : "",
    };
  }

  function getAssetPresetTags(assetType) {
    return ASSET_PRESET_TAGS[assetType] ?? [];
  }

  function getAssetTypeLabel(type) {
    return ASSET_TYPE_LABELS[type] ?? type;
  }

  global.TonyNaEditorAssetCatalog = Object.freeze({
    ASSET_TYPE_LABELS,
    ASSET_PRESET_TAGS,
    CHARACTER_PRESENTATION_MODE_LABELS,
    ASSET_FILTER_MODE_LABELS,
    ASSET_FILTER_MODE_STATUS_LABELS,
    ASSET_MEDIA_BUDGET_LIMITS,
    getSafeCharacterPresentationMode,
    getCharacterPresentationModeLabel,
    getSafeAssetFilterMode,
    getAssetFilterModeLabel,
    getAssetFilterModeStatusLabel,
    getAssetMediaBudgetLimit,
    formatFileSize,
    isImageAssetType,
    isAudioAssetType,
    isVideoAssetType,
    isScene3dAssetType,
    isAssetMissingFile,
    getAssetUsageCount,
    normalizeAssetDuplicateToken,
    getAssetPathBasename,
    getAssetDuplicateReasonLabels,
    getAssetDuplicatePreferenceScore,
    buildAssetDuplicatePreferenceNotes,
    buildAssetDuplicateOverview,
    isAssetUnused,
    getUnusedAssets,
    isAssetUrgentMissing,
    getAssetMediaBudgetSuggestion,
    getAssetMediaBudgetRisk,
    buildAssetMediaBudgetReport,
    buildAssetGapOverview,
    getAssetTypeGapSummaryText,
    normalizeAssetSearchQuery,
    getAssetSortLabel,
    sortAssets,
    getVisibleAssets,
    pruneAssetCheckedIds,
    getCheckedAssetIds,
    getCurrentFilteredAssetsOfSelectedType,
    getCurrentCheckedAssetIds,
    getCurrentCheckedAssetsOfSelectedType,
    isAssetChecked,
    toggleAssetChecked,
    parseAssetTagsInput,
    getSafeAssetIdByType,
    buildBulkAssetTagOperation,
    buildPresetAssetTagOperation,
    getAssetPresetTags,
    getAssetTypeLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
