export function isFormalSaveSlotProtected(slot) {
  return Boolean(slot && typeof slot === "object" && slot.protected === true);
}

export function canMutateFormalSaveSlot(slot) {
  return !isFormalSaveSlotProtected(slot);
}

export function sanitizeFormalSaveSlotMetadata(source) {
  return {
    protected: isFormalSaveSlotProtected(source),
  };
}

export function serializeFormalSaveSlot(slot, cloneSession = (session) => session) {
  if (!slot || typeof slot !== "object") {
    return null;
  }
  return {
    savedAt: slot.savedAt,
    session: cloneSession(slot.session),
    thumbnailDataUrl: typeof slot.thumbnailDataUrl === "string" ? slot.thumbnailDataUrl : "",
    protected: isFormalSaveSlotProtected(slot),
  };
}

export function setFormalSaveSlotProtection(slots, rawIndex, protectedValue) {
  const index = Number(rawIndex);
  if (!Array.isArray(slots) || !Number.isInteger(index) || index < 0 || index >= slots.length) {
    return null;
  }
  const slot = slots[index];
  if (!slot || typeof slot !== "object") {
    return null;
  }
  slot.protected = Boolean(protectedValue);
  return slot.protected;
}

export function toggleFormalSaveSlotProtection(slots, rawIndex) {
  const index = Number(rawIndex);
  if (!Array.isArray(slots) || !Number.isInteger(index) || index < 0 || index >= slots.length) {
    return null;
  }
  const slot = slots[index];
  if (!slot || typeof slot !== "object") {
    return null;
  }
  return setFormalSaveSlotProtection(slots, index, !isFormalSaveSlotProtected(slot));
}

export function getFormalSaveProtectionCopy(slot, protectedValue) {
  if (!slot || typeof slot !== "object") {
    return null;
  }
  return {
    ...slot,
    protected: Boolean(protectedValue),
  };
}
