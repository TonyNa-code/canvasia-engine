# Rich Story Text

Canvasia can style a selected part of one dialogue or narration line without adding extra story cards or writing HTML. The same authored text is interpreted by editor preview, Web Runtime, native Runtime, save/history summaries, and Ren'Py draft export.

## No-code authoring

1. Open a dialogue or narration card and expand **文字表现**.
2. Select only the words you want to style in the text box.
3. Choose **强调这段**, **低声说**, **应用颜色**, or **加入注音**.
4. For ruby/furigana, enter the reading first, then apply it to the selected base text.
5. Use **移除所选表现** to return the selection to plain text.

The existing **句内节奏** panel can be used in the same sentence. Pauses and local speed changes keep their visible positions even when emphasis, color, whisper, or ruby markers are present.

## 中文提示

- **强调这段**：适合关键词、重要线索和情绪重音。
- **低声说**：适合内心话、耳语和弱化语气。
- **应用颜色**：只接受安全的六位十六进制颜色，例如 `#ff6699`。
- **加入注音**：给汉字补假名或读音；网页使用语义化 ruby，原生 Runtime 会在正文上方绘制小号注音。

历史记录、存档摘要和回想馆会显示干净正文，不会暴露内部控制标记。无法识别或不完整的标记会按普通文字保留，不会吞掉作者原稿。

## Internal format

The editor writes a small marker format into the story text:

```text
[[em=important]]
[[whisper=quiet words]]
[[color=#ff6699|heart]]
[[ruby=漢字|かんじ]]
```

Authors normally do not need to type these markers. Raw HTML is never accepted, user text is escaped before Web rendering, and color values are allowlisted.

## Maintenance contract

- `export_player_template/runtime_rich_text.js` owns safe Web parsing and HTML rendering.
- `export_player_template/runtime_story_text.js` composes rich text with inline pacing and maps all controls onto visible-text offsets.
- `prototype_editor/modules/rich_text_editor.js` owns the no-code authoring controls.
- `native_runtime/runtime_rich_text.py`, `runtime_story_text.py`, and `runtime_rich_text_renderer.py` own native parsing, layout, and drawing.
- `prototype_editor/modules/renpy_exporter.js` and `renpy_export.py` map the shared plan to Ren'Py text tags.
- `tests/test_story_text_contract.py` locks parser semantics, Ren'Py conversion, editor entrypoints, and package manifests together.

Run the focused checks with:

```bash
python3 -m unittest tests.test_story_text_contract tests.test_native_runtime_story_text tests.test_frontend_runtime_story_text_module tests.test_frontend_rich_text_editor_module -v
```
