(function attachUiKitPackageTools(global) {
  "use strict";

  const UI_KIT_FORMAT = "canvasia-ui-kit";
  const UI_KIT_FORMAT_VERSION = 1;
  const UI_KIT_ENGINE = "Canvasia Engine";
  const UI_KIT_KIND = "ui-kit";
  const UI_KIT_EXTENSION = ".canvasia-ui-kit.json";
  const UI_KIT_MAX_ASSET_COUNT = 12;
  const UI_KIT_MAX_ASSET_BYTES = 12 * 1024 * 1024;
  const UI_KIT_MAX_TOTAL_ASSET_BYTES = 32 * 1024 * 1024;
  const UI_KIT_MAX_FILE_BYTES = 48 * 1024 * 1024;

  const UI_KIT_BINDING_RULES = Object.freeze({
    "gameUiConfig.fontAssetId": Object.freeze(["font"]),
    "gameUiConfig.titleBackgroundAssetId": Object.freeze(["background", "cg", "ui"]),
    "gameUiConfig.titleLogoAssetId": Object.freeze(["ui", "sprite", "cg"]),
    "gameUiConfig.panelFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.buttonFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.buttonHoverFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.buttonPressedFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.buttonDisabledFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.saveSlotFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.systemPanelFrameAssetId": Object.freeze(["ui"]),
    "gameUiConfig.uiOverlayAssetId": Object.freeze(["ui"]),
    "dialogBoxConfig.panelAssetId": Object.freeze(["ui"]),
  });

  const UI_KIT_ROOT_FIELDS = Object.freeze([
    "assets",
    "config",
    "engine",
    "exportedAt",
    "format",
    "formatVersion",
    "integrity",
    "kind",
    "name",
  ]);
  const UI_KIT_ASSET_FIELDS = Object.freeze([
    "dataBase64",
    "fileName",
    "mimeType",
    "name",
    "rights",
    "roles",
    "sizeBytes",
    "sourceAssetId",
    "tags",
    "type",
  ]);
  const UI_KIT_RIGHTS_FIELDS = Object.freeze([
    "license",
    "sourceUrl",
    "author",
    "credit",
    "aiProvider",
    "prompt",
    "commercialUse",
    "generatedByAi",
    "attributionRequired",
  ]);
  const UI_KIT_RIGHTS_BOOLEAN_FIELDS = Object.freeze(["generatedByAi", "attributionRequired"]);

  function cleanText(value, limit = 240) {
    return String(value ?? "").trim().slice(0, Math.max(0, Number(limit) || 0));
  }

  function cloneJson(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function getPathValue(source, path) {
    return String(path ?? "")
      .split(".")
      .reduce((value, key) => (value && typeof value === "object" ? value[key] : undefined), source);
  }

  function getAssetMap(assetList = []) {
    return new Map(
      (Array.isArray(assetList) ? assetList : [])
        .filter((asset) => asset && typeof asset === "object" && cleanText(asset.id, 160))
        .map((asset) => [cleanText(asset.id, 160), asset])
    );
  }

  function collectUiKitRights(asset = {}) {
    return Object.fromEntries(
      UI_KIT_RIGHTS_FIELDS.filter((field) => Object.prototype.hasOwnProperty.call(asset, field)).map((field) => [
        field,
        typeof asset[field] === "boolean" ? asset[field] : cleanText(asset[field], field === "prompt" ? 2000 : 500),
      ])
    );
  }

  function collectUiKitAssetDependencies(model = {}) {
    const config = {
      gameUiConfig: model.gameUiConfig && typeof model.gameUiConfig === "object" ? model.gameUiConfig : {},
      dialogBoxConfig: model.dialogBoxConfig && typeof model.dialogBoxConfig === "object" ? model.dialogBoxConfig : {},
    };
    const assetsById = getAssetMap(model.assetList);
    const dependenciesById = new Map();
    const issues = [];

    Object.entries(UI_KIT_BINDING_RULES).forEach(([role, allowedTypes]) => {
      const assetId = cleanText(getPathValue(config, role), 160);
      if (!assetId) {
        return;
      }
      const asset = assetsById.get(assetId);
      if (!asset) {
        issues.push(`${role} 引用了素材 ${assetId}，但素材库里找不到它。`);
        return;
      }
      if (asset.fileExists === false || (!cleanText(asset.publicPath, 1000) && !cleanText(asset.path, 1000))) {
        issues.push(`${asset.name || assetId} 还没有可打包的本地文件。`);
        return;
      }
      if (!allowedTypes.includes(cleanText(asset.type, 40))) {
        issues.push(`${asset.name || assetId} 的素材类型不能用于 ${role}。`);
        return;
      }
      const dependency = dependenciesById.get(assetId) ?? { asset, roles: [] };
      dependency.roles.push(role);
      dependenciesById.set(assetId, dependency);
    });

    const dependencies = [...dependenciesById.values()].sort((left, right) =>
      cleanText(left.asset?.id, 160).localeCompare(cleanText(right.asset?.id, 160))
    );
    if (dependencies.length > UI_KIT_MAX_ASSET_COUNT) {
      issues.push(`UI Kit 最多打包 ${UI_KIT_MAX_ASSET_COUNT} 个素材，当前需要 ${dependencies.length} 个。`);
    }
    return {
      ok: issues.length === 0,
      dependencies,
      issues,
      referencedAssetCount: dependencies.length,
      bindingCount: dependencies.reduce((total, item) => total + item.roles.length, 0),
    };
  }

  function getMimeTypeFromFileName(fileName) {
    const extension = cleanText(fileName, 260).toLowerCase().split(".").pop();
    return {
      png: "image/png",
      jpg: "image/jpeg",
      jpeg: "image/jpeg",
      webp: "image/webp",
      gif: "image/gif",
      avif: "image/avif",
      ttf: "font/ttf",
      otf: "font/otf",
      ttc: "font/collection",
      woff: "font/woff",
      woff2: "font/woff2",
    }[extension] ?? "application/octet-stream";
  }

  function arrayBufferToBase64(buffer, options = {}) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let offset = 0; offset < bytes.length; offset += 0x8000) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
    }
    const encode = options.btoaImpl ?? global.btoa;
    if (typeof encode !== "function") {
      throw new Error("当前环境无法编码 UI Kit 素材。请在编辑器窗口中重试。");
    }
    return encode(binary);
  }

  function buildUiKitAssetFileName(asset = {}) {
    const pathName = cleanText(asset.path, 1000).replace(/\\/g, "/").split("/").pop();
    const fallbackName = cleanText(asset.name || asset.id || "ui-asset", 160).replace(/[\\/:*?"<>|]+/g, "_");
    return cleanText(pathName || fallbackName || "ui-asset.dat", 240);
  }

  async function loadUiKitAssetPayload(dependency, options = {}) {
    const asset = dependency?.asset ?? {};
    const getAssetUrl = typeof options.getAssetUrl === "function" ? options.getAssetUrl : (item) => item?.publicPath;
    const url = cleanText(getAssetUrl(asset), 2000);
    if (!url) {
      throw new Error(`无法读取 UI 素材：${asset.name || asset.id || "未命名素材"}。`);
    }
    const fetchImpl = options.fetchImpl ?? global.fetch;
    if (typeof fetchImpl !== "function") {
      throw new Error("当前环境无法读取 UI 素材文件。");
    }
    const response = await fetchImpl(url, { cache: "no-store" });
    if (!response?.ok) {
      throw new Error(`读取 UI 素材失败：${asset.name || asset.id || url}（HTTP ${response?.status ?? "?"}）。`);
    }
    const buffer = await response.arrayBuffer();
    const sizeBytes = Number(buffer.byteLength) || 0;
    if (!sizeBytes) {
      throw new Error(`UI 素材是空文件：${asset.name || asset.id || url}。`);
    }
    if (sizeBytes > UI_KIT_MAX_ASSET_BYTES) {
      throw new Error(`UI 素材超过单文件 ${Math.round(UI_KIT_MAX_ASSET_BYTES / 1024 / 1024)} MB 上限：${asset.name || asset.id}。`);
    }
    const fileName = buildUiKitAssetFileName(asset);
    const responseMime = cleanText(response.headers?.get?.("content-type"), 120).split(";")[0];
    return {
      sourceAssetId: cleanText(asset.id, 160),
      roles: [...new Set(dependency.roles ?? [])],
      name: cleanText(asset.name || asset.id || fileName, 160),
      fileName,
      type: cleanText(asset.type || "ui", 40),
      mimeType: responseMime || getMimeTypeFromFileName(fileName),
      sizeBytes,
      dataBase64: arrayBufferToBase64(buffer, options),
      tags: [...new Set((Array.isArray(asset.tags) ? asset.tags : []).map((tag) => cleanText(tag, 80)).filter(Boolean))].slice(0, 20),
      rights: collectUiKitRights(asset),
    };
  }

  function sortJsonValue(value) {
    if (Array.isArray(value)) {
      return value.map(sortJsonValue);
    }
    if (value && typeof value === "object") {
      return Object.fromEntries(
        Object.keys(value)
          .sort()
          .map((key) => [key, sortJsonValue(value[key])])
      );
    }
    return value;
  }

  function buildUiKitIntegritySource(source) {
    const copy = cloneJson(source);
    delete copy.integrity;
    return copy;
  }

  async function buildSha256Integrity(source, options = {}) {
    const cryptoApi = options.cryptoApi ?? global.crypto;
    const Encoder = options.TextEncoderClass ?? global.TextEncoder;
    if (!cryptoApi?.subtle?.digest || typeof Encoder !== "function") {
      throw new Error("当前环境不支持 UI Kit 完整性校验，请更新浏览器后重试。");
    }
    const canonical = JSON.stringify(sortJsonValue(buildUiKitIntegritySource(source)));
    const digest = await cryptoApi.subtle.digest("SHA-256", new Encoder().encode(canonical));
    const hex = [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    return `sha256:${hex}`;
  }

  async function buildUiKitPackage(model = {}, options = {}) {
    const dependencyReport = collectUiKitAssetDependencies(model);
    if (!dependencyReport.ok) {
      throw new Error(`UI Kit 还不能导出：\n- ${dependencyReport.issues.join("\n- ")}`);
    }
    const assets = [];
    let totalBytes = 0;
    for (const dependency of dependencyReport.dependencies) {
      const asset = await loadUiKitAssetPayload(dependency, options);
      totalBytes += asset.sizeBytes;
      if (totalBytes > UI_KIT_MAX_TOTAL_ASSET_BYTES) {
        throw new Error(`UI Kit 素材合计超过 ${Math.round(UI_KIT_MAX_TOTAL_ASSET_BYTES / 1024 / 1024)} MB 上限，请先压缩标题图或 UI 贴图。`);
      }
      assets.push(asset);
    }
    const sourceName = cleanText(model.name || model.projectTitle || "Canvasia UI Kit", 80) || "Canvasia UI Kit";
    const bundle = {
      format: UI_KIT_FORMAT,
      formatVersion: UI_KIT_FORMAT_VERSION,
      engine: UI_KIT_ENGINE,
      kind: UI_KIT_KIND,
      name: sourceName,
      exportedAt: cleanText(options.exportedAt || new Date().toISOString(), 80),
      config: {
        gameUiConfig: cloneJson(model.gameUiConfig && typeof model.gameUiConfig === "object" ? model.gameUiConfig : {}),
        dialogBoxConfig: cloneJson(model.dialogBoxConfig && typeof model.dialogBoxConfig === "object" ? model.dialogBoxConfig : {}),
      },
      assets,
    };
    bundle.integrity = await buildSha256Integrity(bundle, options);
    const Encoder = options.TextEncoderClass ?? global.TextEncoder;
    const packageBytes = new Encoder().encode(JSON.stringify(bundle)).byteLength;
    if (packageBytes > UI_KIT_MAX_FILE_BYTES) {
      throw new Error(`UI Kit 文件超过 ${Math.round(UI_KIT_MAX_FILE_BYTES / 1024 / 1024)} MB 上限，请先压缩 UI 素材。`);
    }
    return {
      bundle,
      summary: {
        name: sourceName,
        assetCount: assets.length,
        bindingCount: dependencyReport.bindingCount,
        totalBytes,
        packageBytes,
      },
    };
  }

  function hasExactFields(source, fields) {
    return Boolean(
      source &&
        typeof source === "object" &&
        !Array.isArray(source) &&
        Object.keys(source).sort().join("\n") === [...fields].sort().join("\n")
    );
  }

  function getBase64ByteLength(value) {
    const source = cleanText(value, UI_KIT_MAX_FILE_BYTES * 2);
    if (!source || source.length % 4 !== 0 || !/^[A-Za-z0-9+/]+={0,2}$/.test(source)) {
      return -1;
    }
    const padding = source.endsWith("==") ? 2 : source.endsWith("=") ? 1 : 0;
    return (source.length / 4) * 3 - padding;
  }

  function validateUiKitAsset(asset, index) {
    if (!hasExactFields(asset, UI_KIT_ASSET_FIELDS)) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材结构不完整。`);
    }
    const sourceAssetId = cleanText(asset.sourceAssetId, 160);
    const type = cleanText(asset.type, 40);
    const fileName = cleanText(asset.fileName, 240);
    const roles = Array.isArray(asset.roles) ? [...new Set(asset.roles.map((role) => cleanText(role, 120)).filter(Boolean))] : [];
    if (!sourceAssetId || !fileName || fileName.includes("/") || fileName.includes("\\") || fileName === "." || fileName === "..") {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材缺少安全的 ID 或文件名。`);
    }
    if (!roles.length || roles.some((role) => !UI_KIT_BINDING_RULES[role])) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材包含未知的界面绑定。`);
    }
    if (roles.some((role) => !UI_KIT_BINDING_RULES[role].includes(type))) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材类型与界面绑定不匹配。`);
    }
    const decodedBytes = getBase64ByteLength(asset.dataBase64);
    const declaredBytes = Math.max(0, Math.round(Number(asset.sizeBytes) || 0));
    if (decodedBytes <= 0 || decodedBytes !== declaredBytes || decodedBytes > UI_KIT_MAX_ASSET_BYTES) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材大小或编码不可信。`);
    }
    if (!asset.rights || typeof asset.rights !== "object" || Array.isArray(asset.rights)) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材缺少授权元数据容器。`);
    }
    if (Object.keys(asset.rights).some((field) => !UI_KIT_RIGHTS_FIELDS.includes(field))) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材包含未知的授权字段。`);
    }
    if (
      UI_KIT_RIGHTS_BOOLEAN_FIELDS.some(
        (field) => Object.prototype.hasOwnProperty.call(asset.rights, field) && typeof asset.rights[field] !== "boolean"
      )
    ) {
      throw new Error(`第 ${index + 1} 个 UI Kit 素材授权布尔字段格式无效。`);
    }
    return {
      sourceAssetId,
      roles,
      name: cleanText(asset.name || sourceAssetId, 160),
      fileName,
      type,
      mimeType: cleanText(asset.mimeType || getMimeTypeFromFileName(fileName), 120),
      sizeBytes: decodedBytes,
      dataBase64: cleanText(asset.dataBase64, UI_KIT_MAX_FILE_BYTES * 2),
      tags: [...new Set((Array.isArray(asset.tags) ? asset.tags : []).map((tag) => cleanText(tag, 80)).filter(Boolean))].slice(0, 20),
      rights: Object.fromEntries(
        UI_KIT_RIGHTS_FIELDS.filter((field) => Object.prototype.hasOwnProperty.call(asset.rights, field)).map((field) => [
          field,
          typeof asset.rights[field] === "boolean"
            ? asset.rights[field]
            : cleanText(asset.rights[field], field === "prompt" ? 2000 : 500),
        ])
      ),
    };
  }

  async function validateUiKitPackage(source, options = {}) {
    if (!hasExactFields(source, UI_KIT_ROOT_FIELDS)) {
      throw new Error("这不是完整的 Canvasia UI Kit 文件。\n请重新选择由编辑器导出的 .canvasia-ui-kit.json。");
    }
    if (
      source.format !== UI_KIT_FORMAT ||
      source.formatVersion !== UI_KIT_FORMAT_VERSION ||
      source.engine !== UI_KIT_ENGINE ||
      source.kind !== UI_KIT_KIND
    ) {
      throw new Error("UI Kit 格式或版本与当前编辑器不兼容。");
    }
    if (!Number.isFinite(Date.parse(source.exportedAt))) {
      throw new Error("UI Kit 缺少有效的导出时间。");
    }
    if (!source.config || typeof source.config !== "object" || Array.isArray(source.config)) {
      throw new Error("UI Kit 缺少成品界面配置。");
    }
    const gameUiConfig = source.config.gameUiConfig;
    const dialogBoxConfig = source.config.dialogBoxConfig;
    if (!gameUiConfig || typeof gameUiConfig !== "object" || !dialogBoxConfig || typeof dialogBoxConfig !== "object") {
      throw new Error("UI Kit 的游戏界面或文本框配置不完整。");
    }
    if (!Array.isArray(source.assets) || source.assets.length > UI_KIT_MAX_ASSET_COUNT) {
      throw new Error(`UI Kit 素材数量超过安全上限 ${UI_KIT_MAX_ASSET_COUNT} 个。`);
    }
    const expectedIntegrity = await buildSha256Integrity(source, options);
    if (cleanText(source.integrity, 100).toLowerCase() !== expectedIntegrity) {
      throw new Error("UI Kit 完整性校验失败，文件可能不完整或已被改写。");
    }

    const assets = source.assets.map(validateUiKitAsset);
    const totalBytes = assets.reduce((total, asset) => total + asset.sizeBytes, 0);
    if (totalBytes > UI_KIT_MAX_TOTAL_ASSET_BYTES) {
      throw new Error(`UI Kit 素材合计超过 ${Math.round(UI_KIT_MAX_TOTAL_ASSET_BYTES / 1024 / 1024)} MB 上限。`);
    }
    const seenSourceIds = new Set();
    const roleBindings = new Map();
    assets.forEach((asset, assetIndex) => {
      if (seenSourceIds.has(asset.sourceAssetId)) {
        throw new Error(`UI Kit 重复打包了素材 ${asset.sourceAssetId}。`);
      }
      seenSourceIds.add(asset.sourceAssetId);
      asset.roles.forEach((role) => {
        if (roleBindings.has(role)) {
          throw new Error(`UI Kit 的 ${role} 被多个素材重复绑定。`);
        }
        if (cleanText(getPathValue({ gameUiConfig, dialogBoxConfig }, role), 160) !== asset.sourceAssetId) {
          throw new Error(`UI Kit 的 ${role} 配置与素材清单不一致。`);
        }
        roleBindings.set(role, assetIndex);
      });
    });
    Object.keys(UI_KIT_BINDING_RULES).forEach((role) => {
      const sourceAssetId = cleanText(getPathValue({ gameUiConfig, dialogBoxConfig }, role), 160);
      if (sourceAssetId && !roleBindings.has(role)) {
        throw new Error(`UI Kit 缺少 ${role} 所引用的素材文件。`);
      }
    });

    return {
      ok: true,
      bundle: {
        ...cloneJson(source),
        name: cleanText(source.name || "Canvasia UI Kit", 80) || "Canvasia UI Kit",
        assets,
      },
      roleBindings: Object.fromEntries(roleBindings),
      summary: {
        name: cleanText(source.name || "Canvasia UI Kit", 80) || "Canvasia UI Kit",
        assetCount: assets.length,
        bindingCount: roleBindings.size,
        totalBytes,
      },
    };
  }

  function buildUiKitImportRequest(validation) {
    if (!validation?.ok || !validation.bundle) {
      throw new Error("UI Kit 尚未通过完整性校验，不能写入项目。");
    }
    const bundle = validation.bundle;
    return {
      name: bundle.name,
      gameUiConfig: cloneJson(bundle.config.gameUiConfig),
      dialogBoxConfig: cloneJson(bundle.config.dialogBoxConfig),
      bindings: cloneJson(validation.roleBindings),
      files: bundle.assets.map((asset) => ({
        name: asset.fileName,
        displayName: asset.name,
        dataBase64: asset.dataBase64,
        assetType: asset.type,
        tags: [...new Set([...(asset.tags ?? []), "Canvasia UI Kit", bundle.name])].slice(0, 20),
        rights: cloneJson(asset.rights),
      })),
    };
  }

  function createUiKitWorkflow(options = {}) {
    const packageApi = options.packageApi ?? {
      UI_KIT_EXTENSION,
      UI_KIT_MAX_FILE_BYTES,
      buildUiKitImportRequest,
      buildUiKitPackage,
      validateUiKitPackage,
    };
    const requiredCallbacks = [
      "confirmImport",
      "downloadJsonFile",
      "formatFileSize",
      "getAssetUrl",
      "getProjectModel",
      "parseJsonImportText",
      "postImport",
      "readFileAsText",
      "reloadProjectData",
      "renderAll",
      "sanitizeFileName",
      "setSaveStatus",
      "showFailure",
      "showToast",
    ];
    const missingCallback = requiredCallbacks.find((name) => typeof options[name] !== "function");
    if (missingCallback) {
      throw new Error(`UI Kit 工作流缺少 ${missingCallback} 回调。`);
    }

    async function exportPackage() {
      try {
        options.setSaveStatus("正在整理 UI Kit 与引用素材...");
        const model = options.getProjectModel() ?? {};
        const projectTitle = cleanText(model.projectTitle || "Canvasia UI", 160) || "Canvasia UI";
        const result = await packageApi.buildUiKitPackage(
          {
            ...model,
            name: cleanText(model.name || `${projectTitle} UI Kit`, 80),
            projectTitle,
          },
          { getAssetUrl: options.getAssetUrl }
        );
        const safeTitle = options.sanitizeFileName(projectTitle) || "canvasia-ui";
        options.downloadJsonFile(`${safeTitle}${packageApi.UI_KIT_EXTENSION}`, result.bundle);
        const message = `UI Kit 已导出：${result.summary.assetCount} 个素材，${result.summary.bindingCount} 处绑定`;
        options.setSaveStatus(message);
        options.showToast(message);
        return result;
      } catch (error) {
        await options.showFailure(error, "导出 UI Kit 失败", "UI Kit 没有导出成功");
        return null;
      }
    }

    async function importPackage(file) {
      if (!file) {
        return null;
      }
      try {
        if (Number(file.size) > packageApi.UI_KIT_MAX_FILE_BYTES) {
          throw new Error(`UI Kit 文件超过 ${options.formatFileSize(packageApi.UI_KIT_MAX_FILE_BYTES)} 上限。`);
        }
        options.setSaveStatus("正在检查 UI Kit 完整性...");
        const source = options.parseJsonImportText(await options.readFileAsText(file), "UI Kit");
        const validation = await packageApi.validateUiKitPackage(source);
        const confirmed = await options.confirmImport({
          title: `导入「${validation.summary.name}」？`,
          message: [
            `将导入 ${validation.summary.assetCount} 个素材（${options.formatFileSize(validation.summary.totalBytes)}），恢复 ${validation.summary.bindingCount} 处界面绑定。`,
            "当前项目的成品 UI 皮肤和文本框样式会被替换；剧情、角色及其他素材不会改变。",
          ].join("\n\n"),
          tone: "warning",
          confirmLabel: "导入并替换界面",
          cancelLabel: "先不导入",
        });
        if (!confirmed) {
          options.setSaveStatus("已取消导入 UI Kit");
          return null;
        }

        options.setSaveStatus("正在原子导入 UI Kit...");
        const result = await options.postImport(packageApi.buildUiKitImportRequest(validation));
        await options.reloadProjectData();
        options.renderAll();
        const message = `UI Kit 已导入：${result.importedCount ?? 0} 个素材，${result.bindingCount ?? 0} 处绑定`;
        options.setSaveStatus(message);
        options.showToast(message);
        return result;
      } catch (error) {
        await options.showFailure(error, "导入 UI Kit 失败", "项目保持在导入前状态");
        return null;
      }
    }

    return Object.freeze({ exportPackage, importPackage });
  }

  global.CanvasiaEditorUiKitPackage = Object.freeze({
    UI_KIT_ASSET_FIELDS,
    UI_KIT_BINDING_RULES,
    UI_KIT_ENGINE,
    UI_KIT_EXTENSION,
    UI_KIT_FORMAT,
    UI_KIT_FORMAT_VERSION,
    UI_KIT_MAX_ASSET_BYTES,
    UI_KIT_MAX_ASSET_COUNT,
    UI_KIT_MAX_FILE_BYTES,
    UI_KIT_MAX_TOTAL_ASSET_BYTES,
    UI_KIT_RIGHTS_BOOLEAN_FIELDS,
    arrayBufferToBase64,
    buildSha256Integrity,
    buildUiKitImportRequest,
    buildUiKitPackage,
    collectUiKitAssetDependencies,
    createUiKitWorkflow,
    getBase64ByteLength,
    loadUiKitAssetPayload,
    validateUiKitPackage,
  });
})(typeof window !== "undefined" ? window : globalThis);
