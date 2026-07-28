# Inline Text Pacing / 句内节奏

Inline text pacing is optional. Existing dialogue and narration keep their original behavior until an author adds a pacing cue.

句内节奏默认关闭，旧项目不需要迁移。

## Author workflow / 作者操作

1. Open a dialogue or narration card. / 打开台词或旁白卡片。
2. Put the caret where the line should pause, then choose **Short pause** or **Long pause**. / 把光标放在停顿位置，点击“稍停一下”或“停久一点”。
3. Select a phrase and choose **Slow**, **Fast**, or **Instant**. / 选中文字后，点击慢速、快速或瞬间显示。
4. Preview the section before export. / 导出前使用“试玩此段”确认节奏。

The editor inserts portable markers, so authors normally do not need to type syntax manually:

```text
我一直想告诉你，[[pause=0.35]][[speed=slow]]其实从很久以前就开始了。[[speed=inherit]]
```

## Runtime behavior / 播放规则

- `[[pause=seconds]]` adds a bounded pause at that position.
- `[[speed=slow|normal|fast|instant|inherit]]` changes reveal speed from that position; `inherit` returns to the player's current speed.
- Editor preview, Web Runtime, native Runtime, saves, history, archives, and Ren'Py draft export use the same parser contract.
- Supported markers never appear in player-facing text. Unknown or malformed markers remain literal instead of silently deleting author text.
- A player's **Instant** text-speed setting overrides all authored pauses and local speeds for accessibility.
- Ren'Py drafts translate supported cues to native `{w=...}` and `{cps=...}` text tags.

## Maintenance contract / 维护约定

- Shared Web parsing lives in `export_player_template/runtime_text_pacing.js`.
- Native parsing lives in `native_runtime/runtime_text_pacing.py` and is parity-tested against the Web parser.
- Editor insertion UI lives in `prototype_editor/modules/text_pacing_editor.js`; it does not duplicate parser rules.
- Package manifests and CI must include all three modules before a release can pass.

Focused verification:

```bash
python3 -m unittest \
  tests.test_frontend_runtime_text_pacing_module \
  tests.test_native_runtime_text_pacing \
  tests.test_frontend_text_pacing_editor_module \
  tests.test_text_pacing_contract -v
```
