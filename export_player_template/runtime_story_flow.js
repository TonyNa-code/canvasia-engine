(function attachRuntimeStoryFlow(global) {
  const MAX_STORY_CALL_DEPTH = 64;

  function cleanText(value) {
    return String(value ?? "").trim();
  }

  function getSafeCallDepth(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return MAX_STORY_CALL_DEPTH;
    }
    return Math.min(Math.max(Math.trunc(numeric), 1), MAX_STORY_CALL_DEPTH);
  }

  function sanitizeStoryReturnPoint(source, options = {}) {
    if (!source || typeof source !== "object") {
      return null;
    }

    const sceneId = cleanText(source.sceneId);
    const blockIndex = Number(source.blockIndex);
    const hasScene = typeof options.hasScene === "function" ? options.hasScene : () => true;
    if (!sceneId || !Number.isInteger(blockIndex) || blockIndex < 0 || !hasScene(sceneId)) {
      return null;
    }

    return {
      sceneId,
      blockIndex,
      callerBlockId: cleanText(source.callerBlockId),
      targetSceneId: cleanText(source.targetSceneId),
    };
  }

  function sanitizeStoryCallStack(source, options = {}) {
    const maxDepth = getSafeCallDepth(options.maxDepth);
    if (!Array.isArray(source)) {
      return [];
    }

    return source
      .map((frame) => sanitizeStoryReturnPoint(frame, options))
      .filter(Boolean)
      .slice(-maxDepth);
  }

  function createStoryCallTransition(config = {}) {
    const maxDepth = getSafeCallDepth(config.maxDepth);
    const hasScene = typeof config.hasScene === "function" ? config.hasScene : () => true;
    const callStack = sanitizeStoryCallStack(config.callStack, { hasScene, maxDepth });
    const targetSceneId = cleanText(config.targetSceneId);
    if (!targetSceneId || !hasScene(targetSceneId)) {
      return { ok: false, errorCode: "missing_call_target", callStack };
    }
    if (callStack.length >= maxDepth) {
      return { ok: false, errorCode: "call_depth_exceeded", callStack };
    }

    const returnPoint = sanitizeStoryReturnPoint(
      {
        sceneId: config.sourceSceneId,
        blockIndex: Number(config.sourceBlockIndex) + 1,
        callerBlockId: config.sourceBlockId,
        targetSceneId,
      },
      { hasScene }
    );
    if (!returnPoint) {
      return { ok: false, errorCode: "invalid_return_point", callStack };
    }

    const nextStack = [...callStack, returnPoint];
    return {
      ok: true,
      kind: "call",
      targetSceneId,
      targetBlockIndex: 0,
      callStack: nextStack,
      depth: nextStack.length,
    };
  }

  function createStoryReturnTransition(source, options = {}) {
    const hasScene = typeof options.hasScene === "function" ? options.hasScene : () => true;
    const callStack = sanitizeStoryCallStack(source, {
      hasScene,
      maxDepth: options.maxDepth,
    });
    if (callStack.length === 0) {
      return { ok: false, errorCode: "empty_call_stack", callStack };
    }

    const returnPoint = callStack[callStack.length - 1];
    return {
      ok: true,
      kind: "return",
      targetSceneId: returnPoint.sceneId,
      targetBlockIndex: returnPoint.blockIndex,
      callStack: callStack.slice(0, -1),
      depth: callStack.length - 1,
      returnPoint,
    };
  }

  function finalizeStoryMove(location, options = {}) {
    const hasScene = typeof options.hasScene === "function" ? options.hasScene : () => true;
    const hasNextBlock = typeof options.hasNextBlock === "function" ? options.hasNextBlock : () => false;
    let current = location;

    while (
      current?.kind === "move" &&
      hasScene(current.targetSceneId) &&
      !hasNextBlock(current.targetSceneId, current.targetBlockIndex) &&
      current.callStack.length > 0
    ) {
      const transition = createStoryReturnTransition(current.callStack, {
        hasScene,
        maxDepth: options.maxDepth,
      });
      if (!transition.ok) {
        return {
          kind: "error",
          errorCode: transition.errorCode,
          callStack: transition.callStack,
        };
      }
      current = {
        kind: "move",
        reason: "implicit_return",
        targetSceneId: transition.targetSceneId,
        targetBlockIndex: transition.targetBlockIndex,
        callStack: transition.callStack,
        applyTerminalScope: true,
      };
    }

    return current;
  }

  function resolveNextStoryLocation(currentSnapshot, options = {}) {
    const snapshot = currentSnapshot && typeof currentSnapshot === "object" ? currentSnapshot : {};
    const hasScene = typeof options.hasScene === "function" ? options.hasScene : () => true;
    const hasNextBlock = typeof options.hasNextBlock === "function" ? options.hasNextBlock : () => false;
    const callStack = sanitizeStoryCallStack(snapshot.callStack, {
      hasScene,
      maxDepth: options.maxDepth,
    });

    let transition = null;
    if (snapshot.blockType === "scene_call") {
      transition = createStoryCallTransition({
        callStack,
        sourceSceneId: snapshot.sceneId,
        sourceBlockIndex: snapshot.blockIndex,
        sourceBlockId: snapshot.blockId,
        targetSceneId: snapshot.block?.targetSceneId,
        hasScene,
        maxDepth: options.maxDepth,
      });
    } else if (snapshot.blockType === "scene_return") {
      transition = createStoryReturnTransition(callStack, {
        hasScene,
        maxDepth: options.maxDepth,
      });
    }

    if (transition) {
      if (!transition.ok) {
        return {
          kind: "error",
          errorCode: transition.errorCode,
          callStack: transition.callStack,
        };
      }
      return finalizeStoryMove({
        kind: "move",
        reason: transition.kind,
        targetSceneId: transition.targetSceneId,
        targetBlockIndex: transition.targetBlockIndex,
        callStack: transition.callStack,
        applyTerminalScope: true,
      }, { hasScene, hasNextBlock, maxDepth: options.maxDepth });
    }

    const transitionTargetSceneId = cleanText(snapshot.transitionTargetSceneId);
    if (transitionTargetSceneId) {
      return finalizeStoryMove({
        kind: "move",
        reason: "jump",
        targetSceneId: transitionTargetSceneId,
        targetBlockIndex: 0,
        callStack,
        applyTerminalScope: false,
      }, { hasScene, hasNextBlock, maxDepth: options.maxDepth });
    }

    const sceneId = cleanText(snapshot.sceneId);
    const nextBlockIndex = Number(snapshot.blockIndex) + 1;
    if (sceneId && Number.isInteger(nextBlockIndex) && hasNextBlock(sceneId, nextBlockIndex)) {
      return {
        kind: "move",
        reason: "next",
        targetSceneId: sceneId,
        targetBlockIndex: nextBlockIndex,
        callStack,
        applyTerminalScope: false,
      };
    }

    if (callStack.length > 0) {
      const implicitReturn = createStoryReturnTransition(callStack, {
        hasScene,
        maxDepth: options.maxDepth,
      });
      if (implicitReturn.ok) {
        return finalizeStoryMove({
          kind: "move",
          reason: "implicit_return",
          targetSceneId: implicitReturn.targetSceneId,
          targetBlockIndex: implicitReturn.targetBlockIndex,
          callStack: implicitReturn.callStack,
          applyTerminalScope: true,
        }, { hasScene, hasNextBlock, maxDepth: options.maxDepth });
      }
    }

    return { kind: "complete", callStack };
  }

  function getStoryFlowErrorMessage(errorCode) {
    return {
      missing_call_target: "调用的子场景不存在，剧情已安全停止。",
      call_depth_exceeded: "子场景调用层级过深，可能存在循环调用，剧情已安全停止。",
      invalid_return_point: "当前调用位置无法记录返回点，剧情已安全停止。",
      empty_call_stack: "这里没有可返回的调用位置，剧情已在当前场景结束。",
    }[cleanText(errorCode)] ?? "剧情流程无法继续，已安全停止。";
  }

  function isStoryFlowBlockType(blockType) {
    return blockType === "scene_call" || blockType === "scene_return";
  }

  global.CanvasiaRuntimeStoryFlow = Object.freeze({
    MAX_STORY_CALL_DEPTH,
    createStoryCallTransition,
    createStoryReturnTransition,
    getSafeCallDepth,
    getStoryFlowErrorMessage,
    isStoryFlowBlockType,
    resolveNextStoryLocation,
    sanitizeStoryCallStack,
    sanitizeStoryReturnPoint,
  });
})(typeof window !== "undefined" ? window : globalThis);
