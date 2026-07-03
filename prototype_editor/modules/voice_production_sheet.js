(function attachVoiceProductionSheetTools(global) {
  const LONG_VOICE_LINE_LENGTH = 90;
  const VERY_LONG_VOICE_LINE_LENGTH = 140;

  const STATUS_LABELS = Object.freeze({
    ready: "已配音",
    missing_voice: "待配音",
    missing_asset: "语音条目缺失",
    missing_file: "语音文件缺失",
    wrong_type: "素材类型不对",
    unknown_speaker: "说话人未知",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function truncateText(value, maxLength = 80) {
    const text = cleanText(value);
    if (text.length <= maxLength) {
      return text;
    }
    return `${text.slice(0, Math.max(0, maxLength - 1))}…`;
  }

  function buildCollectionMap(source, idField = "id") {
    const result = new Map();
    if (source instanceof Map) {
      source.forEach((value, id) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    if (source && typeof source === "object" && !Array.isArray(source)) {
      Object.entries(source).forEach(([id, value]) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    toArray(source).forEach((item) => {
      if (item?.[idField]) {
        result.set(String(item[idField]), item);
      }
    });
    return result;
  }

  function getAssetList(data = {}) {
    return Array.isArray(data.assetList)
      ? data.assetList
      : Array.isArray(data.assets?.assets)
        ? data.assets.assets
        : [];
  }

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
        : [];
  }

  function buildAssetMap(data = {}) {
    const assetMap = new Map();
    getAssetList(data).forEach((asset) => {
      if (asset?.id) {
        assetMap.set(String(asset.id), asset);
      }
    });
    buildCollectionMap(data.assetsById).forEach((asset, id) => assetMap.set(id, asset));
    return assetMap;
  }

  function buildCharacterMap(data = {}) {
    const characterMap = new Map();
    getCharacterList(data).forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });
    buildCollectionMap(data.charactersById).forEach((character, id) => characterMap.set(id, character));
    return characterMap;
  }

  function buildSceneMap(data = {}) {
    const sceneMap = new Map();
    toArray(data.scenes).forEach((scene) => {
      if (scene?.id) {
        sceneMap.set(String(scene.id), scene);
      }
    });
    buildCollectionMap(data.scenesById).forEach((scene, id) => sceneMap.set(id, scene));
    toArray(data.chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => {
        if (scene?.id) {
          sceneMap.set(String(scene.id), scene);
        }
      });
    });
    return sceneMap;
  }

  function buildChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? chapter?.chapterId ?? ""),
        {
          id: String(chapter?.id ?? chapter?.chapterId ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
          sceneOrder: toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean),
        },
      ])
    );
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const chapterMap = buildChapterMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = String(chapter?.id ?? chapter?.chapterId ?? "");
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);

      scenes.forEach((scene, sceneIndex) => {
        if (!scene?.id || seenSceneIds.has(String(scene.id))) {
          return;
        }
        seenSceneIds.add(String(scene.id));
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      if (!scene?.id || seenSceneIds.has(String(scene.id))) {
        return;
      }
      const chapter = chapterMap.get(String(scene.chapterId ?? ""));
      seenSceneIds.add(String(scene.id));
      records.push({
        scene,
        sceneIndex,
        chapterId: String(scene.chapterId ?? ""),
        chapterName: chapter?.name ?? "未分章",
        chapterOrder: chapter?.order ?? 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function getCharacterName(characterMap, speakerId) {
    const cleanId = cleanText(speakerId);
    if (!cleanId) {
      return "未指定说话人";
    }
    const character = characterMap.get(cleanId);
    return cleanText(character?.displayName ?? character?.name, cleanId);
  }

  function getAssetName(asset, fallback = "") {
    return cleanText(asset?.name ?? asset?.fileName ?? asset?.path, fallback);
  }

  function getVoiceLineStatusLabel(status = "") {
    return STATUS_LABELS[status] ?? cleanText(status, "未知");
  }

  function getVoiceLineStatus(block = {}, characterMap = new Map(), assetMap = new Map()) {
    const speakerId = cleanText(block.speakerId);
    const voiceAssetId = cleanText(block.voiceAssetId ?? block.voice?.assetId);
    const asset = voiceAssetId ? assetMap.get(voiceAssetId) : null;

    if (voiceAssetId && !asset) {
      return "missing_asset";
    }
    if (asset && asset.type && asset.type !== "voice") {
      return "wrong_type";
    }
    if (asset && asset.fileExists === false) {
      return "missing_file";
    }
    if (!voiceAssetId) {
      return "missing_voice";
    }
    if (!speakerId || !characterMap.has(speakerId)) {
      return "unknown_speaker";
    }
    return "ready";
  }

  function pushIssue(issues, severity, code, title, detail, context = {}) {
    issues.push({ severity, code, title, detail, ...context });
  }

  function getIssueWeight(issue = {}) {
    if (issue.severity === "blocker") {
      return 100;
    }
    if (issue.severity === "warn") {
      return 60;
    }
    return 20;
  }

  function createLineIssues(line, block = {}, characterMap = new Map(), assetMap = new Map()) {
    const issues = [];
    const context = {
      lineId: line.id,
      blockId: line.blockId,
      chapterName: line.chapterName,
      sceneName: line.sceneName,
      speakerName: line.speakerName,
      blockIndex: line.blockIndex,
    };

    if (!line.speakerId || !characterMap.has(line.speakerId)) {
      pushIssue(
        issues,
        "warn",
        "voice_unknown_speaker",
        "说话人没有对应角色",
        line.speakerId ? `说话人 ${line.speakerId} 不在角色表中。` : "这句台词没有指定说话人，后续分配声优会不清楚。",
        context
      );
    }

    if (!line.voiceAssetId) {
      pushIssue(issues, "warn", "voice_missing_binding", "台词还没绑定语音", "需要先创建语音占位或绑定已有语音素材。", context);
    } else {
      const asset = assetMap.get(line.voiceAssetId);
      if (!asset) {
        pushIssue(
          issues,
          "blocker",
          "voice_missing_asset",
          "绑定的语音条目不存在",
          `语音条目 ${line.voiceAssetId} 不在素材库中，导出后会播放失败。`,
          context
        );
      } else if (asset.type && asset.type !== "voice") {
        pushIssue(
          issues,
          "blocker",
          "voice_wrong_asset_type",
          "绑定的素材不是语音",
          `当前绑定的是 ${asset.type} 类型素材，请改成语音素材。`,
          context
        );
      } else if (asset.fileExists === false) {
        pushIssue(
          issues,
          "blocker",
          "voice_missing_file",
          "语音条目还没有真实文件",
          `语音条目“${getAssetName(asset, line.voiceAssetId)}”存在，但文件还没有上传或已经丢失。`,
          context
        );
      }
    }

    if (line.textLength > VERY_LONG_VOICE_LINE_LENGTH) {
      pushIssue(issues, "warn", "voice_line_very_long", "台词过长，建议拆句", `这句有 ${line.textLength} 字，录音与打字机节奏都容易拖。`, context);
    } else if (line.textLength > LONG_VOICE_LINE_LENGTH) {
      pushIssue(issues, "tip", "voice_line_long", "台词偏长", `这句有 ${line.textLength} 字，可以视演出节奏拆成两句。`, context);
    }

    return issues;
  }

  function buildSpeakerSummary(lines = []) {
    const speakerMap = new Map();
    toArray(lines).forEach((line) => {
      const speakerKey = line.speakerId || "__unknown__";
      const record =
        speakerMap.get(speakerKey) ??
        {
          speakerId: line.speakerId,
          speakerName: line.speakerName,
          totalLines: 0,
          readyLines: 0,
          missingLines: 0,
          blockerLines: 0,
          longLines: 0,
          totalCharacters: 0,
          readyPercent: 0,
        };
      record.totalLines += 1;
      record.totalCharacters += line.textLength;
      if (line.status === "ready") {
        record.readyLines += 1;
      } else {
        record.missingLines += 1;
      }
      if (["missing_asset", "missing_file", "wrong_type"].includes(line.status)) {
        record.blockerLines += 1;
      }
      if (line.isLong) {
        record.longLines += 1;
      }
      record.readyPercent = record.totalLines ? Math.round((record.readyLines / record.totalLines) * 100) : 100;
      speakerMap.set(speakerKey, record);
    });

    return Array.from(speakerMap.values()).sort((left, right) => {
      if (right.blockerLines !== left.blockerLines) {
        return right.blockerLines - left.blockerLines;
      }
      if (right.missingLines !== left.missingLines) {
        return right.missingLines - left.missingLines;
      }
      return right.totalLines - left.totalLines || left.speakerName.localeCompare(right.speakerName, "zh-CN");
    });
  }

  function buildVoiceProductionSheet(data = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = buildCharacterMap(data);
    const lines = [];
    const issues = [];

    getSceneRecords(data).forEach((record) => {
      const scene = record.scene ?? {};
      const sceneName = cleanText(scene.name ?? scene.title, scene.id ?? "未命名场景");
      toArray(scene.blocks).forEach((block, blockIndex) => {
        if (block?.type !== "dialogue") {
          return;
        }
        const speakerId = cleanText(block.speakerId);
        const voiceAssetId = cleanText(block.voiceAssetId ?? block.voice?.assetId);
        const voiceAsset = voiceAssetId ? assetMap.get(voiceAssetId) : null;
        const text = cleanText(block.text);
        const status = getVoiceLineStatus(block, characterMap, assetMap);
        const line = {
          id: `${scene.id || "scene"}:${block.id || blockIndex}`,
          blockId: block.id,
          blockIndex,
          chapterId: record.chapterId,
          chapterName: record.chapterName ?? "未分章",
          sceneId: scene.id,
          sceneName,
          speakerId,
          speakerName: getCharacterName(characterMap, speakerId),
          text,
          textPreview: truncateText(text, 72),
          textLength: text.length,
          voiceAssetId,
          voiceAssetName: voiceAsset ? getAssetName(voiceAsset, voiceAssetId) : "",
          voiceAssetPath: cleanText(voiceAsset?.path ?? voiceAsset?.url),
          voiceFileExists: voiceAsset ? voiceAsset.fileExists !== false : false,
          status,
          statusLabel: getVoiceLineStatusLabel(status),
          isLong: text.length > LONG_VOICE_LINE_LENGTH,
          isVeryLong: text.length > VERY_LONG_VOICE_LINE_LENGTH,
          issueSummary: "",
        };
        const lineIssues = createLineIssues(line, block, characterMap, assetMap);
        line.issueSummary = lineIssues.map((issue) => issue.title).join(" / ") || "OK";
        lines.push(line);
        issues.push(...lineIssues);
      });
    });

    issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || cleanText(left.title).localeCompare(cleanText(right.title), "zh-CN"));

    const summary = {
      lineCount: lines.length,
      readyLineCount: lines.filter((line) => line.status === "ready").length,
      missingVoiceCount: lines.filter((line) => line.status === "missing_voice").length,
      missingAssetCount: lines.filter((line) => line.status === "missing_asset").length,
      missingFileCount: lines.filter((line) => line.status === "missing_file").length,
      wrongTypeCount: lines.filter((line) => line.status === "wrong_type").length,
      unknownSpeakerCount: issues.filter((issue) => issue.code === "voice_unknown_speaker").length,
      longLineCount: lines.filter((line) => line.isLong).length,
      veryLongLineCount: lines.filter((line) => line.isVeryLong).length,
      speakerCount: buildSpeakerSummary(lines).length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
      readyPercent: lines.length ? Math.round((lines.filter((line) => line.status === "ready").length / lines.length) * 100) : 100,
    };

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      summary,
      speakers: buildSpeakerSummary(lines),
      lines,
      issues,
    };
  }

  function getVoiceProductionStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.lineCount ?? 0) === 0) {
      return {
        status: "empty",
        title: "还没有可配音台词",
        detail: "项目里暂时没有角色台词。添加第一句台词后，这里会生成配音制作清单。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: `${summary.blockerCount} 个语音阻塞项`,
        detail: "优先处理不存在的语音条目、缺失文件和类型错误，否则导出试玩时可能没有声音。",
      };
    }
    if ((summary.missingVoiceCount ?? 0) > 0 || (summary.unknownSpeakerCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.readyPercent ?? 0}% 台词已就绪`,
        detail: "语音流程可以推进，但仍有台词待建占位或说话人需要确认。",
      };
    }
    if ((summary.longLineCount ?? 0) > 0) {
      return {
        status: "warn",
        title: "语音已齐，建议复查长句",
        detail: "全部台词已经绑定语音，但仍有长句可以按录音节奏拆分。",
      };
    }
    return {
      status: "ready",
      title: "语音生产状态稳定",
      detail: "台词语音绑定、文件和角色分配都比较完整，可以进入试听和发布前确认。",
    };
  }

  function escapeMarkdownTableCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br />")
      .trim();
  }

  function buildMarkdownTable(headers = [], rows = []) {
    const safeRows = toArray(rows);
    if (!safeRows.length) {
      return "";
    }
    return [
      `| ${toArray(headers).map(escapeMarkdownTableCell).join(" | ")} |`,
      `| ${toArray(headers).map(() => "---").join(" | ")} |`,
      ...safeRows.map((row) => `| ${toArray(row).map(escapeMarkdownTableCell).join(" | ")} |`),
    ].join("\n");
  }

  function csvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [headers, ...rows].map((row) => toArray(row).map(csvCell).join(",")).join("\n");
  }

  function buildVoiceProductionMarkdown(sheet = {}, options = {}) {
    const summary = sheet.summary ?? {};
    const digest = getVoiceProductionStatusDigest(sheet);
    const generatedAt = cleanText(options.generatedAt);
    const projectTitle = cleanText(options.projectTitle ?? sheet.projectTitle, "Canvasia Project");
    const speakerRows = toArray(sheet.speakers).map((speaker) => [
      speaker.speakerName,
      speaker.totalLines,
      speaker.readyLines,
      speaker.missingLines,
      speaker.blockerLines,
      speaker.longLines,
      `${speaker.readyPercent}%`,
      speaker.totalCharacters,
    ]);
    const lineRows = toArray(sheet.lines).map((line, index) => [
      index + 1,
      line.statusLabel,
      line.chapterName,
      line.sceneName,
      line.speakerName,
      line.textPreview,
      line.voiceAssetName || line.voiceAssetId || "未绑定",
      line.issueSummary,
    ]);
    const issueRows = toArray(sheet.issues).slice(0, 60).map((issue, index) => [
      index + 1,
      issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "复查" : "润色",
      issue.chapterName,
      issue.sceneName,
      issue.speakerName,
      issue.title,
      issue.detail,
    ]);

    return [
      `# ${projectTitle} 语音制作清单`,
      "",
      generatedAt ? `生成时间：${generatedAt}` : "",
      "",
      `状态：${digest.title}`,
      "",
      digest.detail,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["台词", "已配音", "待配音", "缺条目", "缺文件", "说话人待确认", "长句", "完成度"],
        [
          [
            summary.lineCount ?? 0,
            summary.readyLineCount ?? 0,
            summary.missingVoiceCount ?? 0,
            summary.missingAssetCount ?? 0,
            (summary.missingFileCount ?? 0) + (summary.wrongTypeCount ?? 0),
            summary.unknownSpeakerCount ?? 0,
            summary.longLineCount ?? 0,
            `${summary.readyPercent ?? 0}%`,
          ],
        ]
      ),
      "",
      "## 角色配音进度",
      "",
      buildMarkdownTable(["角色", "台词", "已就绪", "待处理", "阻塞项", "长句", "完成度", "字数"], speakerRows) || "当前还没有可统计的角色台词。",
      "",
      "## 台词清单",
      "",
      buildMarkdownTable(["序号", "状态", "章节", "场景", "角色", "台词", "语音素材", "问题"], lineRows) || "当前没有台词。",
      "",
      "## 优先问题",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "角色", "问题", "说明"], issueRows) || "当前没有明显语音生产问题。",
      "",
    ].join("\n");
  }

  function buildVoiceProductionCsv(sheet = {}) {
    const rows = toArray(sheet.lines).map((line, index) => [
      index + 1,
      line.statusLabel,
      line.chapterName,
      line.sceneName,
      line.blockIndex + 1,
      line.speakerName,
      line.text,
      line.textLength,
      line.voiceAssetId,
      line.voiceAssetName,
      line.voiceAssetPath,
      line.voiceFileExists ? "有文件" : "缺文件",
      line.issueSummary,
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "状态", "章节", "场景", "卡片序号", "角色", "台词全文", "字数", "语音素材 ID", "语音素材名", "语音路径", "文件状态", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorVoiceProductionSheet = Object.freeze({
    LONG_VOICE_LINE_LENGTH,
    VERY_LONG_VOICE_LINE_LENGTH,
    buildVoiceProductionSheet,
    getVoiceProductionStatusDigest,
    buildVoiceProductionMarkdown,
    buildVoiceProductionCsv,
    getVoiceLineStatusLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
