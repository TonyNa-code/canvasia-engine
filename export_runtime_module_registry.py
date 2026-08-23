from __future__ import annotations

from pathlib import PurePosixPath


EXPORT_RUNTIME_MODULE_SPECS = (
    ("Conditions", "runtime_conditions.js"),
    ("ChoiceAvailability", "runtime_choice_availability.js"),
    ("TimedChoices", "runtime_timed_choices.js"),
    ("StoryFlow", "runtime_story_flow.js"),
    ("Achievements", "runtime_achievements.js"),
    ("Data", "runtime_data.js"),
    ("Storage", "runtime_storage.js"),
    ("SaveSlots", "runtime_save_slots.js"),
    ("PersistentVariables", "runtime_persistent_variables.js"),
    ("CharacterMotion", "runtime_character_motion.js"),
    ("SpeakerFocus", "runtime_speaker_focus.js"),
    ("CharacterCards", "runtime_character_cards.js"),
    ("DialogueCamera", "runtime_dialogue_camera.js"),
    ("VoiceReactiveMotion", "runtime_voice_reactive_motion.js"),
    ("StageImages", "runtime_stage_images.js"),
    ("VisualConstants", "runtime_visual_constants.js"),
    ("ParticleQuality", "runtime_particle_quality.js"),
    ("ParticleRenderer", "runtime_particle_renderer.js"),
    ("Controls", "runtime_controls.js"),
    ("Gamepad", "runtime_gamepad.js"),
    ("MobileReader", "runtime_mobile_reader.js"),
    ("MobileReaderUi", "runtime_mobile_reader_ui.js"),
    ("Settings", "runtime_settings.js"),
    ("ReadingProfiles", "runtime_reading_profiles.js"),
    ("DialogueLayouts", "runtime_dialogue_layouts.js"),
    ("VisualComfort", "runtime_visual_comfort.js"),
    ("VoiceMixer", "runtime_voice_mixer.js"),
    ("UiSkin", "runtime_ui_skin.js"),
    ("I18n", "runtime_i18n.js"),
    ("Audio", "runtime_audio.js"),
    ("MusicTransport", "runtime_music_transport.js"),
    ("VideoTransport", "runtime_video_transport.js"),
    ("SfxTransport", "runtime_sfx_transport.js"),
    ("Preload", "runtime_preload.js"),
    ("ScenePrefetch", "runtime_scene_prefetch.js"),
    ("TextEffects", "runtime_text_effects.js"),
    ("TextPacing", "runtime_text_pacing.js"),
    ("RichText", "runtime_rich_text.js"),
    ("StoryText", "runtime_story_text.js"),
    ("TextHistory", "runtime_text_history.js"),
    ("TextVariables", "runtime_text_variables.js"),
)


def get_export_runtime_module_files() -> tuple[str, ...]:
    return tuple(file_name for _key_suffix, file_name in EXPORT_RUNTIME_MODULE_SPECS)


def build_export_runtime_module_manifest(
    key_prefix: str,
    path_prefix: str = "",
) -> dict[str, str]:
    safe_key_prefix = str(key_prefix or "").strip()
    if not safe_key_prefix or not safe_key_prefix.replace("_", "").isalnum():
        raise ValueError("Runtime manifest key prefix must be alphanumeric.")
    pure_path_prefix = PurePosixPath(str(path_prefix or ""))
    normalized_path_prefix = str(pure_path_prefix)
    if normalized_path_prefix == ".":
        normalized_path_prefix = ""
    if ".." in pure_path_prefix.parts or normalized_path_prefix.startswith("/"):
        raise ValueError("Runtime manifest path prefix must stay inside the export bundle.")
    if normalized_path_prefix:
        normalized_path_prefix = f"{normalized_path_prefix.rstrip('/')}/"
    return {
        f"{safe_key_prefix}{key_suffix}": f"{normalized_path_prefix}{file_name}"
        for key_suffix, file_name in EXPORT_RUNTIME_MODULE_SPECS
    }


__all__ = [
    "EXPORT_RUNTIME_MODULE_SPECS",
    "build_export_runtime_module_manifest",
    "get_export_runtime_module_files",
]
