function collectIdRefs(documentRef) {
  const refs = {};
  for (const element of documentRef?.querySelectorAll?.("[id]") ?? []) {
    const id = String(element?.id ?? "").trim();
    if (id && !Object.prototype.hasOwnProperty.call(refs, id)) {
      refs[id] = element;
    }
  }
  return refs;
}

export function createRuntimeDomRefs(documentRef = globalThis.document) {
  const refs = collectIdRefs(documentRef);
  refs.dialogPanel = documentRef?.querySelector?.(".dialog-panel") ?? null;
  refs.runtimeThemeButtons = Array.from(
    documentRef?.querySelectorAll?.(".player-theme-button") ?? [],
  );
  return refs;
}
