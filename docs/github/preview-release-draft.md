# Tony Na Engine Preview Release Draft

## Tony Na Engine Preview

Tony Na Engine is a source-available visual novel / galgame creation toolkit with a visual editor, runtime exports, archive systems, particle effects, project checks, and automated smoke tests.

This release is intended for creators who want to try the editor, build a small project, test the export flow, and report issues before a fully stable signed release.

## Highlights

- Visual story editor with beginner / advanced mode separation.
- Project center with blank project creation.
- Character, asset, script, voice placeholder, and batch voice matching workflows.
- Save / load, quick save, system menu, player profile, auto resume, and project-level save slot count.
- EXTRA / archive surfaces for replay, gallery, music room, voice replay, endings, and achievements.
- Advanced particle presets and project-level particle preset library.
- Project-level game UI skins, layout positioning, and visual novel text box styling.
- Web runtime export and NW.js desktop package paths.
- Native Runtime Preview with title screen, save/load, settings, archives, crash logs, PyInstaller packaging scripts, optional embedded video playback, and fallback system-player bridge.
- Automated tests covering backend smoke paths and browser Playwright smoke paths.

## Downloads

Release assets appear below this text on GitHub. If a platform package is not attached, that platform is not included in this specific Preview upload. The source code archive remains available for users who want to run the editor with Python 3.

<!-- TNE_GENERATED_DOWNLOAD_GUIDE -->

## Important Notes

- This is a Preview / Early Access release, not a final stable commercial build.
- macOS apps may be unsigned / unnotarized and can trigger Gatekeeper warnings.
- Windows apps may be unsigned and can trigger SmartScreen warnings.
- Linux packages are Preview archives unless stated otherwise.
- Native Runtime video supports optional PyAV / FFmpeg embedded playback, OpenCV visual fallback, and system-player bridge fallback. Encoding compatibility still needs real-device testing.
- Mobile APK / IPA export is not included in this release.

## Recommended First Test

1. Start the editor.
2. Create a blank project.
3. Add one chapter, one scene, one background, one line, and one choice.
4. Run preview.
5. Export a web build.
6. Export a native Runtime build.
7. Check `native-runtime-release-check.json`.

## Reporting Issues

When filing an issue, include:

- Operating system and version
- Python version
- Browser, if the issue is in web preview
- Which package or export target was used
- Steps to reproduce
- Screenshots or logs if available
