from __future__ import annotations

import struct
import zlib
from pathlib import Path


def clamp_color_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def mix_rgb(color_a: tuple[int, int, int], color_b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    safe_ratio = max(0.0, min(1.0, ratio))
    return tuple(
        clamp_color_channel(color_a[index] + (color_b[index] - color_a[index]) * safe_ratio)
        for index in range(3)
    )


def blend_rgba(
    background: tuple[int, int, int, int], overlay: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    overlay_alpha = max(0.0, min(1.0, overlay[3] / 255.0))
    background_alpha = max(0.0, min(1.0, background[3] / 255.0))
    out_alpha = overlay_alpha + background_alpha * (1.0 - overlay_alpha)

    if out_alpha <= 0:
        return 0, 0, 0, 0

    return (
        clamp_color_channel(
            (overlay[0] * overlay_alpha + background[0] * background_alpha * (1.0 - overlay_alpha)) / out_alpha
        ),
        clamp_color_channel(
            (overlay[1] * overlay_alpha + background[1] * background_alpha * (1.0 - overlay_alpha)) / out_alpha
        ),
        clamp_color_channel(
            (overlay[2] * overlay_alpha + background[2] * background_alpha * (1.0 - overlay_alpha)) / out_alpha
        ),
        clamp_color_channel(out_alpha * 255.0),
    )


def rounded_rect_signed_distance(
    px: float, py: float, left: float, top: float, width: float, height: float, radius: float
) -> float:
    center_x = left + width * 0.5
    center_y = top + height * 0.5
    inner_half_width = max(0.0, width * 0.5 - radius)
    inner_half_height = max(0.0, height * 0.5 - radius)
    qx = abs(px - center_x) - inner_half_width
    qy = abs(py - center_y) - inner_half_height
    outside_x = max(qx, 0.0)
    outside_y = max(qy, 0.0)
    return (outside_x * outside_x + outside_y * outside_y) ** 0.5 + min(max(qx, qy), 0.0) - radius


def distance_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    dy = y2 - y1
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

    projection = ((px - x1) * dx + (py - y1) * dy) / length_squared
    clamped = max(0.0, min(1.0, projection))
    closest_x = x1 + dx * clamped
    closest_y = y1 + dy * clamped
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5


def build_export_icon_palette(project: dict) -> dict:
    presets = [
        {
            "backgroundTop": (13, 18, 44),
            "backgroundBottom": (42, 54, 128),
            "panelTop": (18, 24, 58),
            "panelBottom": (12, 14, 32),
            "heart": (255, 176, 223),
            "shadow": (4, 7, 20),
            "highlight": (154, 234, 255),
            "spark": (255, 214, 248),
            "ring": (223, 235, 255),
            "grid": (118, 134, 219),
            "monogram": (245, 250, 255),
            "monogramAccent": (159, 228, 255),
            "orbit": (122, 118, 255),
        },
        {
            "backgroundTop": (18, 22, 56),
            "backgroundBottom": (95, 82, 186),
            "panelTop": (24, 22, 60),
            "panelBottom": (13, 14, 35),
            "heart": (255, 188, 233),
            "shadow": (5, 6, 18),
            "highlight": (194, 220, 255),
            "spark": (255, 224, 244),
            "ring": (229, 233, 255),
            "grid": (136, 133, 218),
            "monogram": (247, 249, 255),
            "monogramAccent": (180, 224, 255),
            "orbit": (154, 120, 255),
        },
        {
            "backgroundTop": (8, 28, 49),
            "backgroundBottom": (24, 88, 126),
            "panelTop": (12, 27, 48),
            "panelBottom": (8, 17, 30),
            "heart": (255, 180, 216),
            "shadow": (2, 9, 15),
            "highlight": (167, 240, 237),
            "spark": (238, 214, 255),
            "ring": (221, 248, 255),
            "grid": (96, 174, 190),
            "monogram": (243, 251, 249),
            "monogramAccent": (170, 236, 244),
            "orbit": (84, 176, 223),
        },
    ]
    seed_source = f"{project.get('projectId') or ''}:{project.get('title') or ''}"
    preset_index = sum(ord(character) for character in seed_source) % len(presets)
    return presets[preset_index]


def build_export_icon_png(project: dict, size: int = 256) -> bytes:
    palette = build_export_icon_palette(project)
    pixels: list[tuple[int, int, int, int]] = []
    center_x = size * 0.5
    center_y = size * 0.5
    outer_margin = size * 0.06
    outer_left = outer_margin
    outer_top = outer_margin
    outer_size = size - outer_margin * 2
    outer_radius = size * 0.19
    inner_margin = size * 0.14
    inner_left = inner_margin
    inner_top = inner_margin
    inner_size = size - inner_margin * 2
    inner_radius = size * 0.14
    ring_radius_a = size * 0.31
    ring_radius_b = size * 0.23
    ring_thickness = size * 0.012
    aura_a_x = size * 0.24
    aura_a_y = size * 0.18
    aura_b_x = size * 0.82
    aura_b_y = size * 0.22
    aura_radius_a = size * 0.44
    aura_radius_b = size * 0.36
    sparkle_center_x = size * 0.77
    sparkle_center_y = size * 0.22
    sparkle_radius = size * 0.058

    crest_center_x = size * 0.5
    crest_center_y = size * 0.49
    crest_radius = size * 0.205
    crest_inner_radius = size * 0.168
    crest_glow_radius = size * 0.29

    moon_outer_radius = size * 0.11
    moon_inner_radius = size * 0.088
    moon_center_x = size * 0.44
    moon_center_y = size * 0.43
    moon_cut_x = moon_center_x + size * 0.04
    moon_cut_y = moon_center_y - size * 0.012

    petal_a_center_x = size * 0.62
    petal_a_center_y = size * 0.34
    petal_b_center_x = size * 0.67
    petal_b_center_y = size * 0.405
    petal_rx = size * 0.03
    petal_ry = size * 0.075
    petal_a_cos = 0.819
    petal_a_sin = 0.574
    petal_b_cos = 0.643
    petal_b_sin = 0.766

    t_bar_left = size * 0.34
    t_bar_top = size * 0.515
    t_bar_width = size * 0.14
    t_bar_height = size * 0.038
    t_stem_left = size * 0.392
    t_stem_top = size * 0.515
    t_stem_width = size * 0.041
    t_stem_height = size * 0.18
    n_left_left = size * 0.515
    n_left_top = size * 0.515
    n_bar_width = size * 0.041
    n_bar_height = size * 0.18
    n_right_left = size * 0.63
    n_diag_thickness = size * 0.02
    n_diag_x1 = size * 0.536
    n_diag_y1 = size * 0.53
    n_diag_x2 = size * 0.651
    n_diag_y2 = size * 0.69

    def circle_distance(px: float, py: float, cx: float, cy: float, radius: float) -> float:
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 - radius

    def rotated_ellipse_distance(
        px: float,
        py: float,
        cx: float,
        cy: float,
        radius_x: float,
        radius_y: float,
        cos_angle: float,
        sin_angle: float,
    ) -> float:
        dx = px - cx
        dy = py - cy
        rotated_x = dx * cos_angle + dy * sin_angle
        rotated_y = -dx * sin_angle + dy * cos_angle
        return ((rotated_x / max(1.0, radius_x)) ** 2 + (rotated_y / max(1.0, radius_y)) ** 2) ** 0.5 - 1.0

    for y in range(size):
        for x in range(size):
            outer_distance = rounded_rect_signed_distance(x, y, outer_left, outer_top, outer_size, outer_size, outer_radius)
            if outer_distance > 1.4:
                pixels.append((0, 0, 0, 0))
                continue

            outer_alpha = 255 if outer_distance <= -0.8 else clamp_color_channel((1.4 - outer_distance) / 2.2 * 255)
            vertical_ratio = (y - outer_top) / max(1.0, outer_size)
            gradient_color = mix_rgb(palette["backgroundTop"], palette["backgroundBottom"], vertical_ratio)
            pixel = (*gradient_color, outer_alpha)

            dx = (x - center_x) / size
            dy = (y - center_y) / size
            distance_factor = min(1.0, (dx * dx + dy * dy) * 3.2)
            vignette_strength = 1.0 - distance_factor * 0.2
            pixel = (
                clamp_color_channel(pixel[0] * vignette_strength),
                clamp_color_channel(pixel[1] * vignette_strength),
                clamp_color_channel(pixel[2] * vignette_strength),
                pixel[3],
            )

            top_light = max(0.0, 1.0 - (x + y) / max(1.0, size * 0.9))
            if top_light > 0:
                pixel = blend_rgba(pixel, (255, 255, 255, clamp_color_channel(top_light * 48)))

            aura_distance_a = ((x - aura_a_x) ** 2 + (y - aura_a_y) ** 2) ** 0.5
            if aura_distance_a <= aura_radius_a:
                aura_alpha_a = clamp_color_channel((1.0 - aura_distance_a / aura_radius_a) * 52)
                pixel = blend_rgba(pixel, (*palette["spark"], aura_alpha_a))

            aura_distance_b = ((x - aura_b_x) ** 2 + (y - aura_b_y) ** 2) ** 0.5
            if aura_distance_b <= aura_radius_b:
                aura_alpha_b = clamp_color_channel((1.0 - aura_distance_b / aura_radius_b) * 44)
                pixel = blend_rgba(pixel, (*palette["orbit"], aura_alpha_b))

            if outer_distance >= -2.2:
                edge_alpha = clamp_color_channel((1.0 - max(outer_distance, 0.0) / 1.6) * 72)
                pixel = blend_rgba(pixel, (*palette["ring"], edge_alpha))

            inner_distance = rounded_rect_signed_distance(x, y, inner_left, inner_top, inner_size, inner_size, inner_radius)
            if inner_distance <= 0:
                inner_ratio = (y - inner_top) / max(1.0, inner_size)
                inner_color = mix_rgb(palette["panelTop"], palette["panelBottom"], inner_ratio)
                panel_alpha = 255 if inner_distance <= -1.0 else clamp_color_channel((1.0 - max(inner_distance, 0.0)) * 190)
                pixel = blend_rgba(pixel, (*inner_color, panel_alpha))

                grid_step = max(8, int(round(size * 0.105)))
                if ((x - inner_left) % grid_step <= 1) or ((y - inner_top) % grid_step <= 1):
                    pixel = blend_rgba(pixel, (*palette["grid"], 18))

                if inner_distance >= -1.6:
                    inner_stroke_alpha = clamp_color_channel((1.0 - max(inner_distance, 0.0) / 1.4) * 54)
                    pixel = blend_rgba(pixel, (*palette["ring"], inner_stroke_alpha))

            ring_distance_a = abs(((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5 - ring_radius_a)
            if ring_distance_a <= ring_thickness * 2.2:
                ring_alpha_a = clamp_color_channel((1.0 - ring_distance_a / max(1.0, ring_thickness * 2.2)) * 52)
                pixel = blend_rgba(pixel, (*palette["ring"], ring_alpha_a))

            ring_distance_b = abs(((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5 - ring_radius_b)
            if ring_distance_b <= ring_thickness * 1.8:
                ring_alpha_b = clamp_color_channel((1.0 - ring_distance_b / max(1.0, ring_thickness * 1.8)) * 36)
                pixel = blend_rgba(pixel, (*palette["orbit"], ring_alpha_b))

            crest_glow_distance = circle_distance(x, y, crest_center_x, crest_center_y, crest_glow_radius)
            if crest_glow_distance <= 0:
                crest_glow_alpha = clamp_color_channel((1.0 - max(crest_glow_distance, -crest_glow_radius) / crest_glow_radius) * 22)
                pixel = blend_rgba(pixel, (*palette["highlight"], crest_glow_alpha))

            crest_distance = circle_distance(x, y, crest_center_x, crest_center_y, crest_radius)
            if crest_distance <= 0:
                crest_ratio = max(0.0, min(1.0, (y - (crest_center_y - crest_radius)) / max(1.0, crest_radius * 2)))
                crest_color = mix_rgb(palette["panelTop"], palette["backgroundBottom"], crest_ratio * 0.68)
                crest_alpha = 255 if crest_distance <= -1.0 else clamp_color_channel((1.0 - max(crest_distance, 0.0)) * 196)
                pixel = blend_rgba(pixel, (*crest_color, crest_alpha))

            crest_inner_distance = circle_distance(x, y, crest_center_x, crest_center_y, crest_inner_radius)
            if crest_inner_distance <= 0:
                inner_crest_alpha = 255 if crest_inner_distance <= -0.8 else clamp_color_channel((1.0 - max(crest_inner_distance, 0.0)) * 168)
                pixel = blend_rgba(pixel, (*palette["shadow"], inner_crest_alpha))

            crest_ring_distance = abs(((x - crest_center_x) ** 2 + (y - crest_center_y) ** 2) ** 0.5 - crest_radius)
            if crest_ring_distance <= size * 0.018:
                crest_ring_alpha = clamp_color_channel((1.0 - crest_ring_distance / max(1.0, size * 0.018)) * 148)
                pixel = blend_rgba(pixel, (*palette["ring"], crest_ring_alpha))

            moon_outer_distance = circle_distance(x, y, moon_center_x, moon_center_y, moon_outer_radius)
            moon_inner_distance = circle_distance(x, y, moon_cut_x, moon_cut_y, moon_inner_radius)
            if moon_outer_distance <= 0 and moon_inner_distance > 0:
                moon_alpha = 255 if moon_outer_distance <= -0.8 else clamp_color_channel((1.0 - max(moon_outer_distance, 0.0)) * 255)
                moon_color = mix_rgb(palette["ring"], palette["highlight"], 0.18)
                pixel = blend_rgba(pixel, (*moon_color, moon_alpha))
            elif moon_outer_distance <= size * 0.03 and moon_inner_distance > -size * 0.02:
                moon_glow_alpha = clamp_color_channel((1.0 - max(moon_outer_distance, 0.0) / max(1.0, size * 0.03)) * 88)
                pixel = blend_rgba(pixel, (*palette["highlight"], moon_glow_alpha))

            petal_a_distance = rotated_ellipse_distance(
                x, y, petal_a_center_x, petal_a_center_y, petal_rx, petal_ry, petal_a_cos, petal_a_sin
            )
            petal_b_distance = rotated_ellipse_distance(
                x, y, petal_b_center_x, petal_b_center_y, petal_rx * 0.95, petal_ry * 0.92, petal_b_cos, petal_b_sin
            )
            petal_distance = min(petal_a_distance, petal_b_distance)
            if petal_distance <= 0:
                petal_alpha = 255 if petal_distance <= -0.08 else clamp_color_channel((1.0 - max(petal_distance, 0.0)) * 255)
                petal_ratio = max(0.0, min(1.0, (y - size * 0.28) / max(1.0, size * 0.2)))
                petal_color = mix_rgb(palette["heart"], palette["spark"], petal_ratio * 0.55)
                pixel = blend_rgba(pixel, (*petal_color, petal_alpha))
            elif petal_distance <= 0.24:
                petal_glow_alpha = clamp_color_channel((1.0 - petal_distance / 0.24) * 68)
                pixel = blend_rgba(pixel, (*palette["heart"], petal_glow_alpha))

            t_bar_distance = rounded_rect_signed_distance(
                x, y, t_bar_left, t_bar_top, t_bar_width, t_bar_height, size * 0.016
            )
            t_stem_distance = rounded_rect_signed_distance(
                x, y, t_stem_left, t_stem_top, t_stem_width, t_stem_height, size * 0.016
            )
            n_left_distance = rounded_rect_signed_distance(
                x, y, n_left_left, n_left_top, n_bar_width, n_bar_height, size * 0.016
            )
            n_right_distance = rounded_rect_signed_distance(
                x, y, n_right_left, n_left_top, n_bar_width, n_bar_height, size * 0.016
            )
            n_diag_distance = distance_to_segment(x, y, n_diag_x1, n_diag_y1, n_diag_x2, n_diag_y2) - n_diag_thickness

            monogram_distance = min(
                t_bar_distance,
                t_stem_distance,
                n_left_distance,
                n_right_distance,
                n_diag_distance,
            )
            if monogram_distance <= 0:
                monogram_ratio = max(0.0, min(1.0, (y - size * 0.5) / max(1.0, size * 0.22)))
                monogram_color = mix_rgb(palette["monogram"], palette["monogramAccent"], monogram_ratio)
                monogram_alpha = 255 if monogram_distance <= -0.6 else clamp_color_channel((1.0 - max(monogram_distance, 0.0)) * 255)
                pixel = blend_rgba(pixel, (*monogram_color, monogram_alpha))

                highlight_distance = ((x - size * 0.39) ** 2 + (y - size * 0.53) ** 2) ** 0.5
                highlight_radius = size * 0.085
                if highlight_distance <= highlight_radius:
                    highlight_alpha = clamp_color_channel((1.0 - highlight_distance / highlight_radius) * 126)
                    pixel = blend_rgba(pixel, (*palette["highlight"], highlight_alpha))
            elif monogram_distance <= size * 0.035:
                glow_alpha = clamp_color_channel((1.0 - monogram_distance / (size * 0.035)) * 58)
                pixel = blend_rgba(pixel, (*palette["spark"], glow_alpha))

            sparkle_dx = abs(x - sparkle_center_x)
            sparkle_dy = abs(y - sparkle_center_y)
            sparkle_cross = min(
                sparkle_dx / max(1.0, size * 0.016) + sparkle_dy / max(1.0, sparkle_radius),
                sparkle_dx / max(1.0, sparkle_radius) + sparkle_dy / max(1.0, size * 0.016),
            )
            sparkle_diamond = (sparkle_dx + sparkle_dy) / max(1.0, sparkle_radius)
            sparkle_strength = max(0.0, 1.0 - min(sparkle_cross, sparkle_diamond))
            if sparkle_strength > 0:
                sparkle_alpha = clamp_color_channel(sparkle_strength * 228)
                pixel = blend_rgba(pixel, (*palette["spark"], sparkle_alpha))

            pixels.append(pixel)

    scanlines = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            red, green, blue, alpha = pixels[y * size + x]
            row.extend((red, green, blue, alpha))
        scanlines.append(bytes(row))

    raw_image = b"".join(scanlines)
    compressed = zlib.compress(raw_image, level=9)

    def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + chunk_type
            + payload
            + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )


def build_export_icon_ico(png_bytes: bytes, size: int = 256) -> bytes:
    icon_directory = struct.pack(
        "<HHHBBBBHHII",
        0,
        1,
        1,
        0 if size >= 256 else size,
        0 if size >= 256 else size,
        0,
        0,
        1,
        32,
        len(png_bytes),
        22,
    )
    return icon_directory + png_bytes


def write_export_icon_files(
    target_dir: Path, png_bytes: bytes, ico_bytes: bytes, file_stem: str = "app_icon"
) -> dict:
    png_path = target_dir / f"{file_stem}.png"
    ico_path = target_dir / f"{file_stem}.ico"
    png_path.write_bytes(png_bytes)
    ico_path.write_bytes(ico_bytes)
    return {
        "pngPath": png_path,
        "icoPath": ico_path,
        "pngFileName": png_path.name,
        "icoFileName": ico_path.name,
        "pngRelativePath": png_path.name,
        "icoRelativePath": ico_path.name,
    }
