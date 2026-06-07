from __future__ import annotations

import base64
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


OPENAI_ASSET_GENERATION_ENDPOINT = "https://api.openai.com/v1/images/generations"
OPENAI_ASSET_GENERATION_DEFAULT_MODEL = "gpt-image-1.5"
OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS = 1400
OPENAI_ASSET_GENERATION_IMAGE_TYPES = {"background", "sprite", "cg", "ui"}
OPENAI_ASSET_GENERATION_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}
OPENAI_ASSET_GENERATION_QUALITIES = {"low", "medium", "high", "auto"}
OPENAI_ASSET_GENERATION_BACKGROUNDS = {"auto", "transparent", "opaque"}
OPENAI_ASSET_GENERATION_FORMATS = {"png", "webp", "jpeg"}


class OpenAiAssetGenerationError(RuntimeError):
    pass


def normalize_openai_asset_generation_type(value: object) -> str:
    asset_type = str(value or "background").strip()
    return asset_type if asset_type in OPENAI_ASSET_GENERATION_IMAGE_TYPES else "background"


def normalize_openai_asset_generation_size(value: object) -> str:
    size = str(value or "1024x1024").strip()
    return size if size in OPENAI_ASSET_GENERATION_SIZES else "1024x1024"


def normalize_openai_asset_generation_quality(value: object) -> str:
    quality = str(value or "medium").strip().lower()
    return quality if quality in OPENAI_ASSET_GENERATION_QUALITIES else "medium"


def normalize_openai_asset_generation_background(value: object) -> str:
    background = str(value or "auto").strip().lower()
    return background if background in OPENAI_ASSET_GENERATION_BACKGROUNDS else "auto"


def normalize_openai_asset_generation_format(value: object) -> str:
    output_format = str(value or "png").strip().lower()
    return output_format if output_format in OPENAI_ASSET_GENERATION_FORMATS else "png"


def validate_openai_asset_generation_format_background(output_format: str, background: str) -> None:
    if output_format == "jpeg" and background == "transparent":
        raise ValueError("JPEG 不支持透明背景。请改用 PNG / WebP，或把背景改为自动 / 不透明。")


def validate_openai_generated_image_bytes(image_bytes: bytes, output_format: str) -> None:
    if output_format == "png" and image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if output_format == "jpeg" and image_bytes.startswith(b"\xff\xd8\xff"):
        return
    if output_format == "webp" and image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return
    raise OpenAiAssetGenerationError(f"OpenAI 返回的图片不是可保存的 {output_format.upper()} 文件。")


def clean_openai_asset_generation_model(value: object) -> str:
    model = str(value or "").strip()
    if not model:
        return OPENAI_ASSET_GENERATION_DEFAULT_MODEL
    if len(model) > 80 or not re.fullmatch(r"[A-Za-z0-9._:-]+", model):
        raise ValueError("模型名只能包含英文字母、数字、点、下划线、冒号或短横线，且不超过 80 个字符。")
    return model


def clean_openai_asset_generation_prompt(value: object) -> str:
    prompt = str(value or "").strip()
    prompt = re.sub(r"\s+", " ", prompt)
    if not prompt:
        raise ValueError("请先写一句要生成什么素材。")
    if len(prompt) > OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS:
        raise ValueError(f"提示词超过 {OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS} 字，请缩短后再生成。")
    return prompt


def build_openai_asset_generation_prompt(payload: dict, asset_type: str) -> str:
    user_prompt = clean_openai_asset_generation_prompt(payload.get("prompt"))
    style_hint = str(payload.get("styleHint") or "").strip()
    asset_hints = {
        "background": (
            "Create an original visual novel background. No characters, no text, no watermark. "
            "Prioritize clean composition, usable stage depth, and 16:9 galgame framing."
        ),
        "sprite": (
            "Create an original visual novel character sprite. Transparent or clean simple background, "
            "front-facing readable silhouette, suitable for dialogue scenes. No text, no watermark."
        ),
        "cg": (
            "Create an original visual novel event CG. Cinematic composition, emotionally readable, "
            "safe for a story scene. No text, no watermark."
        ),
        "ui": (
            "Create an original visual novel UI asset. Clean edges, reusable interface component, "
            "no embedded words, no watermark."
        ),
    }
    parts = [
        user_prompt,
        asset_hints[asset_type],
        "Use an anime-inspired but original art direction. Do not copy copyrighted characters, studio logos, or existing IP.",
    ]
    if style_hint:
        parts.append(f"Additional art direction: {style_hint[:260]}")
    return "\n".join(parts)


def extract_openai_generated_image_bytes(response_payload: dict) -> bytes:
    data_items = response_payload.get("data")
    if not isinstance(data_items, list) or not data_items:
        raise OpenAiAssetGenerationError("OpenAI 没有返回图片数据。")

    first_item = data_items[0] if isinstance(data_items[0], dict) else {}
    image_base64 = first_item.get("b64_json")
    image_url = first_item.get("url")

    if image_base64:
        try:
            return base64.b64decode(str(image_base64).encode("utf-8"), validate=True)
        except Exception as error:  # pragma: no cover - defensive fallback
            raise OpenAiAssetGenerationError("OpenAI 返回的图片不是有效的 base64 数据。") from error

    if image_url:
        parsed = urlparse(str(image_url))
        if parsed.scheme != "https" or not parsed.netloc:
            raise OpenAiAssetGenerationError("OpenAI 返回了不可用的图片下载地址。")
        try:
            with urlopen(str(image_url), timeout=45) as response:
                return response.read(60 * 1024 * 1024)
        except (HTTPError, URLError, TimeoutError) as error:
            raise OpenAiAssetGenerationError(f"下载 OpenAI 生成图片失败：{error}") from error

    raise OpenAiAssetGenerationError("OpenAI 返回里没有可保存的图片。")


def call_openai_asset_generation_model(payload: dict, asset_type: str) -> tuple[bytes, dict]:
    api_key = str(payload.get("apiKey") or "").strip()
    if not api_key:
        raise ValueError("请先填写 OpenAI API Key。Key 只会用于本次生成，不会写入项目文件。")

    model = clean_openai_asset_generation_model(payload.get("model"))
    size = normalize_openai_asset_generation_size(payload.get("size"))
    quality = normalize_openai_asset_generation_quality(payload.get("quality"))
    background = normalize_openai_asset_generation_background(payload.get("background"))
    output_format = normalize_openai_asset_generation_format(payload.get("outputFormat"))
    validate_openai_asset_generation_format_background(output_format, background)
    prompt = build_openai_asset_generation_prompt(payload, asset_type)

    request_payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }
    if model.startswith("gpt-image"):
        request_payload["output_format"] = output_format
        if background != "auto":
            request_payload["background"] = background
    else:
        request_payload["response_format"] = "b64_json"

    request = Request(
        OPENAI_ASSET_GENERATION_ENDPOINT,
        data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise OpenAiAssetGenerationError(f"OpenAI 生图接口返回错误：{error.code} {error_body[:360]}") from error
    except (URLError, TimeoutError) as error:
        raise OpenAiAssetGenerationError(f"无法连接 OpenAI 生图接口：{error}") from error
    except json.JSONDecodeError as error:
        raise OpenAiAssetGenerationError("OpenAI 生图接口返回了无法解析的内容。") from error

    image_bytes = extract_openai_generated_image_bytes(response_payload)
    validate_openai_generated_image_bytes(image_bytes, output_format)

    return image_bytes, {
        "model": model,
        "size": size,
        "quality": quality,
        "background": background,
        "outputFormat": output_format,
        "prompt": prompt,
    }
