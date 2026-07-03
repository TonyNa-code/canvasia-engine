(function attachScriptImporterTools(global) {
  const SCRIPT_IMPORT_MAX_LINES = 120;
  const SCRIPT_IMPORT_MAX_BLOCKS = 80;
  const SCRIPT_IMPORT_MAX_OPTIONS = 6;

  function normalizeScriptImportText(value) {
    return String(value ?? "")
      .replace(/\r\n?/g, "\n")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }

  function trimImportedText(value, maxLength = 800) {
    return String(value ?? "").trim().slice(0, maxLength).trim();
  }

  function parseChoiceLine(line) {
    const match = String(line ?? "").match(/^(?:[-*•]|[0-9]+[.)、])\s*(.+)$/u);
    return match ? trimImportedText(match[1], 160) : "";
  }

  function parseDialogueLine(line) {
    const match = String(line ?? "").match(/^([^:：]{1,24})[:：]\s*(.+)$/u);
    if (!match) {
      return null;
    }

    const speakerName = trimImportedText(match[1], 80);
    const text = trimImportedText(match[2], 800);
    if (!speakerName || !text || ["旁白", "narration", "旁述"].includes(speakerName.toLowerCase())) {
      return text ? { type: "narration", text } : null;
    }

    return {
      type: "dialogue",
      speakerName,
      text,
    };
  }

  function flushChoiceOptions(blocks, choiceOptions) {
    if (!choiceOptions.length) {
      return;
    }

    blocks.push({
      type: "choice",
      options: choiceOptions.slice(0, SCRIPT_IMPORT_MAX_OPTIONS).map((text) => ({ text })),
    });
    choiceOptions.length = 0;
  }

  function parseScriptDraftToBlocks(text, options = {}) {
    const maxLines = Math.max(1, Number.parseInt(options.maxLines ?? SCRIPT_IMPORT_MAX_LINES, 10) || SCRIPT_IMPORT_MAX_LINES);
    const maxBlocks = Math.max(1, Number.parseInt(options.maxBlocks ?? SCRIPT_IMPORT_MAX_BLOCKS, 10) || SCRIPT_IMPORT_MAX_BLOCKS);
    const lines = normalizeScriptImportText(text).slice(0, maxLines);
    const blocks = [];
    const choiceOptions = [];

    lines.forEach((line) => {
      if (blocks.length >= maxBlocks) {
        return;
      }

      const choiceText = parseChoiceLine(line);
      if (choiceText) {
        choiceOptions.push(choiceText);
        if (choiceOptions.length >= SCRIPT_IMPORT_MAX_OPTIONS) {
          flushChoiceOptions(blocks, choiceOptions);
        }
        return;
      }

      flushChoiceOptions(blocks, choiceOptions);

      const dialogue = parseDialogueLine(line);
      if (dialogue) {
        blocks.push(dialogue);
        return;
      }

      const narration = trimImportedText(line);
      if (narration) {
        blocks.push({
          type: "narration",
          text: narration,
        });
      }
    });

    flushChoiceOptions(blocks, choiceOptions);
    return blocks.slice(0, maxBlocks);
  }

  function summarizeScriptDraftBlocks(blocks = []) {
    const counts = (Array.isArray(blocks) ? blocks : []).reduce(
      (summary, block) => {
        if (block?.type === "dialogue") {
          summary.dialogue += 1;
        } else if (block?.type === "choice") {
          summary.choice += 1;
        } else if (block?.type === "narration") {
          summary.narration += 1;
        }
        return summary;
      },
      { dialogue: 0, narration: 0, choice: 0 }
    );

    return {
      ...counts,
      total: counts.dialogue + counts.narration + counts.choice,
    };
  }

  function buildScriptDraftPreviewLines(blocks = [], limit = 6) {
    return (Array.isArray(blocks) ? blocks : [])
      .slice(0, Math.max(0, Number.parseInt(limit, 10) || 0))
      .map((block, index) => {
        if (block?.type === "dialogue") {
          return `${index + 1}. ${block.speakerName || "角色"}：${block.text || ""}`;
        }
        if (block?.type === "choice") {
          return `${index + 1}. 选项：${(block.options ?? []).map((option) => option.text).join(" / ")}`;
        }
        return `${index + 1}. 旁白：${block?.text || ""}`;
      });
  }

  global.CanvasiaEditorScriptImporter = Object.freeze({
    SCRIPT_IMPORT_MAX_LINES,
    SCRIPT_IMPORT_MAX_BLOCKS,
    SCRIPT_IMPORT_MAX_OPTIONS,
    normalizeScriptImportText,
    parseChoiceLine,
    parseDialogueLine,
    parseScriptDraftToBlocks,
    summarizeScriptDraftBlocks,
    buildScriptDraftPreviewLines,
  });
})(typeof window !== "undefined" ? window : globalThis);
