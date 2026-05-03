(function attachReleaseVersionTools(global) {
  const DEFAULT_PROJECT_RELEASE_VERSION = "1.0.0-preview";
  const DEFAULT_RELEASE_VERSION_BASE = "1.0.0";

  function getProjectReleaseVersion(project) {
    const releaseVersion = String(
      project?.releaseVersion ?? project?.buildVersion ?? project?.version ?? DEFAULT_PROJECT_RELEASE_VERSION
    ).trim();
    return releaseVersion || DEFAULT_PROJECT_RELEASE_VERSION;
  }

  function getReleaseVersionBase(version = DEFAULT_PROJECT_RELEASE_VERSION) {
    const cleanVersion = String(version ?? "").trim();
    const match = cleanVersion.match(/\d+\.\d+\.\d+/);
    return match?.[0] ?? DEFAULT_RELEASE_VERSION_BASE;
  }

  function buildReleaseVersionFromPreset(preset, currentVersion = DEFAULT_PROJECT_RELEASE_VERSION) {
    const baseVersion = getReleaseVersionBase(currentVersion);

    if (preset === "preview") {
      return `${baseVersion}-preview`;
    }

    if (preset === "beta") {
      return `${baseVersion}-beta`;
    }

    if (preset === "rc") {
      return `${baseVersion}-rc1`;
    }

    if (preset === "release") {
      return baseVersion;
    }

    return currentVersion;
  }

  global.TonyNaEditorReleaseVersion = Object.freeze({
    DEFAULT_PROJECT_RELEASE_VERSION,
    DEFAULT_RELEASE_VERSION_BASE,
    getProjectReleaseVersion,
    getReleaseVersionBase,
    buildReleaseVersionFromPreset,
  });
})(typeof window !== "undefined" ? window : globalThis);
