#!/usr/bin/env python3
"""Generate the Canvasia Engine GitHub social preview image."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "github" / "canvasia-social-preview.png"
LOGO_PATH = ROOT / "docs" / "branding" / "canvasia-engine-logo.png"
WIDTH = 1280
HEIGHT = 640


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size, index=1 if candidate.endswith(".ttc") and bold else 0)
            except Exception:
                continue
    return ImageFont.load_default()


def lerp(left: int, right: int, amount: float) -> int:
    return int(round(left + (right - left) * amount))


def draw_gradient_background(image: Image.Image) -> None:
    pixels = image.load()
    top_left = (246, 240, 223)
    mid = (233, 245, 237)
    bottom_right = (231, 236, 250)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            amount = (x / WIDTH * 0.52) + (y / HEIGHT * 0.48)
            if amount < 0.55:
                local = amount / 0.55
                color = tuple(lerp(top_left[i], mid[i], local) for i in range(3))
            else:
                local = (amount - 0.55) / 0.45
                color = tuple(lerp(mid[i], bottom_right[i], local) for i in range(3))
            pixels[x, y] = color


def rounded_rectangle_with_shadow(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
) -> None:
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((box[0] + 12, box[1] + 18, box[2] + 12, box[3] + 18), radius, fill=(32, 56, 68, 42))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
    draw.rounded_rectangle(box, radius, fill=(255, 253, 247, 232), outline=(43, 115, 109, 90), width=2)


def paste_logo(image: Image.Image) -> None:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo.thumbnail((330, 330), Image.Resampling.LANCZOS)
    mask = Image.new("L", logo.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, logo.width, logo.height), 42, fill=255)
    image.paste(logo, (116, 158), mask)


def draw_chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color: tuple[int, int, int]) -> int:
    font = load_font(24, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0] + 42
    draw.rounded_rectangle((x, y, x + width, y + 48), 18, fill=(255, 255, 255, 205), outline=(*color, 80), width=2)
    draw.text((x + 21, y + 12), text, fill=color, font=font)
    return width


def main() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw_gradient_background(image)
    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)

    for x in range(80, WIDTH, 120):
        draw.line((x, 70, x, HEIGHT - 70), fill=(49, 94, 136, 24), width=1)
    for y in range(82, HEIGHT, 118):
        draw.line((72, y, WIDTH - 72, y), fill=(49, 94, 136, 22), width=1)

    draw.arc((-180, 40, 560, 520), 285, 88, fill=(198, 110, 78, 70), width=5)
    draw.arc((640, 80, 1500, 760), 190, 338, fill=(43, 115, 109, 56), width=5)
    draw.ellipse((990, 78, 1400, 488), fill=(255, 255, 255, 58))

    rounded_rectangle_with_shadow(image, draw, (78, 94, 466, 546), 44)
    paste_logo(image)

    eyebrow_font = load_font(26, bold=True)
    title_font = load_font(82, bold=True)
    subtitle_font = load_font(33, bold=False)
    body_font = load_font(24, bold=False)
    url_font = load_font(23, bold=True)

    draw.text((548, 116), "NO-CODE VISUAL NOVEL ENGINE", fill=(43, 115, 109), font=eyebrow_font)
    draw.text((546, 180), "Canvasia Engine", fill=(22, 43, 52), font=title_font)
    draw.text((552, 292), "Build playable stories with assets, dialogue,", fill=(58, 89, 99), font=subtitle_font)
    draw.text((552, 334), "runtime exports, UI skins, and release checks.", fill=(58, 89, 99), font=subtitle_font)

    x = 552
    y = 430
    for label, color in [
        ("Visual editor", (43, 115, 109)),
        ("Native runtime", (49, 94, 136)),
        ("i18n", (198, 110, 78)),
        ("Creator-first", (22, 43, 52)),
    ]:
        width = draw_chip(draw, x, y, label, color)
        x += width + 16

    draw.text((554, 526), "github.com/TonyNa-code/canvasia-engine", fill=(39, 68, 76), font=url_font)
    draw.text((554, 558), "Source-available preview · macOS / Windows / Linux", fill=(91, 112, 118), font=body_font)

    output = image.convert("RGB")
    output.save(OUTPUT_PATH, optimize=True, quality=92)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
