from __future__ import annotations

from collections.abc import Callable


MAX_STORY_CALL_DEPTH = 64


def clean_story_flow_text(value: object) -> str:
    return str(value or "").strip()


def get_safe_story_call_depth(value: object = None) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return MAX_STORY_CALL_DEPTH
    return min(max(numeric, 1), MAX_STORY_CALL_DEPTH)


def sanitize_story_return_point(
    source: object,
    *,
    has_scene: Callable[[str], bool] | None = None,
) -> dict | None:
    if not isinstance(source, dict):
        return None
    scene_id = clean_story_flow_text(source.get("sceneId"))
    try:
        block_index = int(source.get("blockIndex"))
    except (TypeError, ValueError):
        return None
    scene_exists = has_scene if callable(has_scene) else lambda _scene_id: True
    if not scene_id or block_index < 0 or not scene_exists(scene_id):
        return None
    return {
        "sceneId": scene_id,
        "blockIndex": block_index,
        "callerBlockId": clean_story_flow_text(source.get("callerBlockId")),
        "targetSceneId": clean_story_flow_text(source.get("targetSceneId")),
    }


def sanitize_story_call_stack(
    source: object,
    *,
    has_scene: Callable[[str], bool] | None = None,
    max_depth: object = None,
) -> list[dict]:
    if not isinstance(source, list):
        return []
    safe_depth = get_safe_story_call_depth(max_depth)
    frames = [
        frame
        for item in source
        if (frame := sanitize_story_return_point(item, has_scene=has_scene)) is not None
    ]
    return frames[-safe_depth:]


def create_story_call_transition(
    *,
    call_stack: object,
    source_scene_id: object,
    source_block_index: object,
    source_block_id: object,
    target_scene_id: object,
    has_scene: Callable[[str], bool] | None = None,
    max_depth: object = None,
) -> dict:
    scene_exists = has_scene if callable(has_scene) else lambda _scene_id: True
    safe_depth = get_safe_story_call_depth(max_depth)
    stack = sanitize_story_call_stack(call_stack, has_scene=scene_exists, max_depth=safe_depth)
    target_id = clean_story_flow_text(target_scene_id)
    if not target_id or not scene_exists(target_id):
        return {"ok": False, "errorCode": "missing_call_target", "callStack": stack}
    if len(stack) >= safe_depth:
        return {"ok": False, "errorCode": "call_depth_exceeded", "callStack": stack}
    try:
        return_block_index = int(source_block_index) + 1
    except (TypeError, ValueError):
        return {"ok": False, "errorCode": "invalid_return_point", "callStack": stack}
    return_point = sanitize_story_return_point(
        {
            "sceneId": source_scene_id,
            "blockIndex": return_block_index,
            "callerBlockId": source_block_id,
            "targetSceneId": target_id,
        },
        has_scene=scene_exists,
    )
    if return_point is None:
        return {"ok": False, "errorCode": "invalid_return_point", "callStack": stack}
    next_stack = [*stack, return_point]
    return {
        "ok": True,
        "kind": "call",
        "targetSceneId": target_id,
        "targetBlockIndex": 0,
        "callStack": next_stack,
        "depth": len(next_stack),
    }


def create_story_return_transition(
    call_stack: object,
    *,
    has_scene: Callable[[str], bool] | None = None,
    max_depth: object = None,
) -> dict:
    stack = sanitize_story_call_stack(call_stack, has_scene=has_scene, max_depth=max_depth)
    if not stack:
        return {"ok": False, "errorCode": "empty_call_stack", "callStack": []}
    return_point = stack[-1]
    return {
        "ok": True,
        "kind": "return",
        "targetSceneId": return_point["sceneId"],
        "targetBlockIndex": return_point["blockIndex"],
        "callStack": stack[:-1],
        "depth": len(stack) - 1,
        "returnPoint": return_point,
    }


def get_story_flow_error_message(error_code: object) -> str:
    return {
        "missing_call_target": "调用的子场景不存在，剧情已安全停止。",
        "call_depth_exceeded": "子场景调用层级过深，可能存在循环调用，剧情已安全停止。",
        "invalid_return_point": "当前调用位置无法记录返回点，剧情已安全停止。",
        "empty_call_stack": "这里没有可返回的调用位置，剧情已在当前场景结束。",
    }.get(clean_story_flow_text(error_code), "剧情流程无法继续，已安全停止。")


def is_story_scene_ending_candidate(
    scene: object,
    *,
    choice_continue_target: str = "__continue__",
) -> bool:
    blocks = scene.get("blocks") if isinstance(scene, dict) else []
    safe_blocks = [block for block in (blocks or []) if isinstance(block, dict)]
    if any(clean_story_flow_text(block.get("type")) == "scene_return" for block in safe_blocks):
        return False
    for block in safe_blocks:
        block_type = clean_story_flow_text(block.get("type"))
        if block_type == "jump" and clean_story_flow_text(block.get("targetSceneId")):
            return False
        if block_type == "choice" and any(
            clean_story_flow_text(option.get("gotoSceneId"))
            and clean_story_flow_text(option.get("gotoSceneId")) != choice_continue_target
            for option in block.get("options") or []
            if isinstance(option, dict)
        ):
            return False
        if block_type == "condition":
            has_branch_target = any(
                clean_story_flow_text(branch.get("gotoSceneId"))
                for branch in block.get("branches") or []
                if isinstance(branch, dict)
            )
            if has_branch_target or clean_story_flow_text(block.get("elseGotoSceneId")):
                return False
    return True
