# Timed Choices / 限时选项

Timed choices are optional. Existing projects remain unlimited unless an author enables the timer on a choice card.

限时选项默认关闭，旧项目不会自动出现倒计时。

## Author workflow / 作者操作

1. Open a choice card in the story editor. / 在剧情编辑器中打开一张选项卡。
2. In **Timed Choice / 限时选择**, choose 5, 10, 15, or 30 seconds, or enter a custom value from 1 to 300 seconds. / 选择预设时长，或输入 1–300 秒。
3. Choose the branch used when time runs out. Leaving it on the recommended default selects the first currently available branch. / 选择超时分支；保留推荐默认值时，会进入第一个当前可选分支。
4. Use **Play this section / 试玩此段** to verify the countdown, locked branches, and result. / 使用“试玩此段”确认倒计时、锁定分支和最终结果。

## Runtime behavior / 播放规则

- If the configured timeout branch is hidden or locked at runtime, the player safely falls back to the first selectable branch.
- Opening system menus, save / load, tutorials, command overlays, or moving the app to the background pauses the countdown.
- Quick saves, formal saves, auto-resume, and native saves preserve the remaining time instead of restarting the full timer.
- Editor preview, Web Runtime, native Runtime, and Ren'Py export use the same duration and fallback contract.
- 若目标分支届时不可用，会安全回退；菜单和后台状态会暂停；存档会保存剩余时间，而不是读档后重新计时。

## Project data contract / 项目字段

```json
{
  "type": "choice",
  "timeoutSeconds": 10,
  "timeoutOptionId": "route_normal",
  "options": []
}
```

- `timeoutSeconds`: `0` or missing disables the timer; enabled values are clamped to `1-300` seconds.
- `timeoutOptionId`: optional stable option ID. Missing or unavailable targets fall back safely.
- Legacy aliases `choiceTimeoutSeconds` and `choiceTimeoutOptionId` are read for compatibility and rewritten to the canonical fields when edited.
