(function attachAssetImportRules(global) {
  const ASSET_REPLACE_ACCEPTS = Object.freeze({
    background: "image/*,.png,.jpg,.jpeg,.webp,.gif,.avif",
    sprite: "image/*,.png,.jpg,.jpeg,.webp,.gif,.avif",
    cg: "image/*,.png,.jpg,.jpeg,.webp,.gif,.avif",
    ui: "image/*,.png,.jpg,.jpeg,.webp,.gif,.avif",
    bgm: "audio/*,.mp3,.ogg,.wav,.m4a,.aac,.flac",
    sfx: "audio/*,.mp3,.ogg,.wav,.m4a,.aac,.flac",
    voice: "audio/*,.mp3,.ogg,.wav,.m4a,.aac,.flac",
    video: "video/*,.mp4,.webm,.mov,.m4v",
    font: ".ttf,.otf,.ttc",
    live2d: "application/json,.model3.json,.moc3,.motion3.json,.physics3.json,.cdi3.json,.pose3.json,.exp3.json,.userdata3.json",
    model3d: ".glb,.gltf,.vrm,.fbx,.obj",
    scene3d: ".glb,.gltf,.vrm,.fbx,.obj",
  });

  const ASSET_SMART_IMPORT_ACCEPT = Array.from(
    new Set(
      Object.values(ASSET_REPLACE_ACCEPTS)
        .flatMap((accept) => accept.split(","))
        .map((item) => item.trim())
        .filter(Boolean)
    )
  ).join(",");

  const ASSET_REPLACE_FORMAT_LABELS = Object.freeze({
    background: "PNG / JPG / WebP / GIF / AVIF",
    sprite: "PNG / JPG / WebP / GIF / AVIF",
    cg: "PNG / JPG / WebP / GIF / AVIF",
    ui: "PNG / JPG / WebP / GIF / AVIF",
    bgm: "MP3 / OGG / WAV / M4A / AAC / FLAC",
    sfx: "MP3 / OGG / WAV / M4A / AAC / FLAC",
    voice: "MP3 / OGG / WAV / M4A / AAC / FLAC",
    video: "MP4 / WebM / MOV / M4V",
    font: "TTF / OTF / TTC",
    live2d: "model3.json / moc3 / motion3.json / physics3.json / exp3.json",
    model3d: "GLB / GLTF / VRM / FBX / OBJ",
    scene3d: "GLB / GLTF / VRM / FBX / OBJ",
  });

  function getAssetReplaceAccept(assetType) {
    return ASSET_REPLACE_ACCEPTS[String(assetType ?? "")] ?? "";
  }

  function getAssetReplaceFormatLabel(assetType, fallback = "与素材类型匹配的文件") {
    return ASSET_REPLACE_FORMAT_LABELS[String(assetType ?? "")] ?? fallback;
  }

  global.CanvasiaEditorAssetImportRules = Object.freeze({
    ASSET_REPLACE_ACCEPTS,
    ASSET_SMART_IMPORT_ACCEPT,
    ASSET_REPLACE_FORMAT_LABELS,
    getAssetReplaceAccept,
    getAssetReplaceFormatLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
