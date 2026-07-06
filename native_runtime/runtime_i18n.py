from __future__ import annotations

import re


DEFAULT_PROJECT_LANGUAGE = "zh-CN"

RUNTIME_LANGUAGE_LABELS = {
    "zh-CN": "简体中文",
    "ja-JP": "日本語",
    "en-US": "English",
}


def normalize_language_code(value: object, fallback: str = DEFAULT_PROJECT_LANGUAGE) -> str:
    raw_value = str(value or "").strip()
    if not raw_value or not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}", raw_value):
        return fallback
    parts = raw_value.split("-")
    normalized = [parts[0].lower()]
    for index, part in enumerate(parts[1:], start=1):
        normalized.append(part.upper() if index == 1 and len(part) in {2, 3} else part)
    return "-".join(normalized)


def normalize_supported_languages(value: object, default_language: str = DEFAULT_PROJECT_LANGUAGE) -> list[str]:
    safe_default_language = normalize_language_code(default_language, DEFAULT_PROJECT_LANGUAGE)
    languages: list[str] = []
    for raw_language in value if isinstance(value, list) else []:
        language = normalize_language_code(raw_language, "")
        if language and language not in languages:
            languages.append(language)
    if safe_default_language and safe_default_language not in languages:
        languages.insert(0, safe_default_language)
    return languages or [DEFAULT_PROJECT_LANGUAGE]


def build_runtime_language_labels(custom_labels: object = None) -> dict[str, str]:
    labels = dict(RUNTIME_LANGUAGE_LABELS)
    if isinstance(custom_labels, dict):
        for raw_language, raw_label in custom_labels.items():
            language = normalize_language_code(raw_language, "")
            label = str(raw_label or "").strip()
            if language and label:
                labels[language] = label
    return labels


def build_runtime_language_fallback_chain(
    *,
    language: object = "",
    fallback_language: object = "",
    default_language: object = DEFAULT_PROJECT_LANGUAGE,
    default_project_language: object = DEFAULT_PROJECT_LANGUAGE,
) -> list[str]:
    chain: list[str] = []
    for candidate in (language, fallback_language, default_language, default_project_language):
        safe_language = normalize_language_code(candidate, "")
        if safe_language and safe_language not in chain:
            chain.append(safe_language)
    return chain or [DEFAULT_PROJECT_LANGUAGE]


def resolve_localized_runtime_value(
    source: dict | None,
    key: str,
    *,
    language: object = "",
    fallback_language: object = "",
    default_language: object = DEFAULT_PROJECT_LANGUAGE,
    fallback: object = "",
) -> dict:
    safe_source = source if isinstance(source, dict) else {}
    translations = safe_source.get(f"{key}Translations")
    fallback_chain = build_runtime_language_fallback_chain(
        language=language,
        fallback_language=fallback_language,
        default_language=default_language,
    )
    requested_language = normalize_language_code(language, "")
    safe_default_language = normalize_language_code(default_language, DEFAULT_PROJECT_LANGUAGE)

    if isinstance(translations, dict):
        for candidate in fallback_chain:
            text = str(translations.get(candidate) or "").strip()
            if text:
                return {
                    "value": text,
                    "requestedLanguage": requested_language,
                    "usedLanguage": candidate,
                    "fallbackChain": fallback_chain,
                    "fallbackUsed": bool(requested_language and candidate != requested_language),
                    "missingRequestedLanguage": bool(
                        requested_language
                        and requested_language != safe_default_language
                        and not str(translations.get(requested_language) or "").strip()
                    ),
                }

    value = str(safe_source.get(key) or fallback or "").strip()
    return {
        "value": value,
        "requestedLanguage": requested_language,
        "usedLanguage": "",
        "fallbackChain": fallback_chain,
        "fallbackUsed": bool(requested_language and requested_language != safe_default_language),
        "missingRequestedLanguage": bool(requested_language and requested_language != safe_default_language),
    }


def get_localized_runtime_value(
    source: dict | None,
    key: str,
    *,
    language: object = "",
    fallback_language: object = "",
    default_language: object = DEFAULT_PROJECT_LANGUAGE,
    fallback: object = "",
) -> str:
    return str(
        resolve_localized_runtime_value(
            source,
            key,
            language=language,
            fallback_language=fallback_language,
            default_language=default_language,
            fallback=fallback,
        ).get("value", "")
    )
