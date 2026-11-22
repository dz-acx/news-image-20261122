"""
make.fun news-image-20261122 - LANGKAH D: revisi keterbacaan dan jarak
Deterministic 4x supersampled (4096x4096 -> 1024x1024) PNG renderer.
Standard library only.
"""

import math
import os
import struct
import sys
import time
import zlib

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
COLOR_BG = (246, 243, 235)         # Latar kertas krem terang
COLOR_INK = (20, 20, 24)            # Tinta hampir hitam
COLOR_RED = (186, 44, 32)           # Aksen merah bata
COLOR_NAVY = (24, 52, 92)           # Aksen biru navy
COLOR_DARK_GREEN = (24, 84, 48)     # Aksen hijau gelap (panel 3)
COLOR_GRAY = (128, 130, 134)        # Abu sedang
COLOR_LIGHT_GRAY = (216, 214, 208)  # Abu terang garis halus
COLOR_WHITE = (255, 255, 255)

# Aksen ilustrasi dan peta
COLOR_ORANGE = (235, 110, 40)       # Oranye hangat
COLOR_YELLOW = (245, 195, 55)       # Kuning keemasan
COLOR_DARK_NAVY = (14, 24, 44)      # Navy gelap malam
COLOR_SLATE_BLUE = (130, 150, 175)  # Abu-biru untuk titik peta
COLOR_SMOKE = (175, 178, 182)       # Abu asap

CANVAS_W = 4096
CANVAS_H = 4096

# ---------------------------------------------------------------------------
# Vector Font: 5 wide x 7 high grid (x in [0..4], y in [0..6])
# Each glyph is defined as a list of polylines.
# ---------------------------------------------------------------------------
GLYPHS = {
    'A': [
        [(0, 6), (0, 2), (2, 0), (4, 2), (4, 6)],
        [(0, 3.5), (4, 3.5)]
    ],
    'B': [
        [(0, 0), (0, 6)],
        [(0, 0), (2.5, 0), (4, 1), (4, 2), (2.5, 3), (0, 3)],
        [(0, 3), (2.5, 3), (4, 4), (4, 5), (2.5, 6), (0, 6)]
    ],
    'C': [
        [(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]
    ],
    'D': [
        [(0, 0), (0, 6)],
        [(0, 0), (2.5, 0), (4, 1.5), (4, 4.5), (2.5, 6), (0, 6)]
    ],
    'E': [
        [(4, 0), (0, 0), (0, 6), (4, 6)],
        [(0, 3), (3, 3)]
    ],
    'F': [
        [(0, 6), (0, 0), (4, 0)],
        [(0, 3), (2.5, 3)]
    ],
    'G': [
        [(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3), (2, 3)]
    ],
    'H': [
        [(0, 0), (0, 6)],
        [(4, 0), (4, 6)],
        [(0, 3), (4, 3)]
    ],
    'I': [
        [(2, 0), (2, 6)],
        [(0.5, 0), (3.5, 0)],
        [(0.5, 6), (3.5, 6)]
    ],
    'J': [
        [(1.5, 0), (4, 0)],
        [(3, 0), (3, 5), (2, 6), (1, 6), (0, 5)]
    ],
    'K': [
        [(0, 0), (0, 6)],
        [(4, 0), (0.5, 3), (4, 6)]
    ],
    'L': [
        [(0, 0), (0, 6), (4, 6)]
    ],
    'M': [
        [(0, 6), (0, 0), (2, 3), (4, 0), (4, 6)]
    ],
    'N': [
        [(0, 6), (0, 0), (4, 6), (4, 0)]
    ],
    'O': [
        [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]
    ],
    'P': [
        [(0, 6), (0, 0), (2.5, 0), (4, 1), (4, 2), (2.5, 3), (0, 3)]
    ],
    'Q': [
        [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)],
        [(2.5, 4.5), (4, 6)]
    ],
    'R': [
        [(0, 6), (0, 0), (2.5, 0), (4, 1), (4, 2), (2.5, 3), (0, 3)],
        [(2, 3), (4, 6)]
    ],
    'S': [
        [(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]
    ],
    'T': [
        [(0, 0), (4, 0)],
        [(2, 0), (2, 6)]
    ],
    'U': [
        [(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]
    ],
    'V': [
        [(0, 0), (2, 6), (4, 0)]
    ],
    'W': [
        [(0, 0), (1, 6), (2, 3), (3, 6), (4, 0)]
    ],
    'X': [
        [(0, 0), (4, 6)],
        [(4, 0), (0, 6)]
    ],
    'Y': [
        [(0, 0), (2, 3), (4, 0)],
        [(2, 3), (2, 6)]
    ],
    'Z': [
        [(0, 0), (4, 0), (0, 6), (4, 6)]
    ],
    '0': [
        [(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)],
        [(3, 1.5), (1, 4.5)]
    ],
    '1': [
        [(1, 1.5), (2, 0), (2, 6)],
        [(0.5, 6), (3.5, 6)]
    ],
    '2': [
        [(0, 1.5), (1, 0), (3, 0), (4, 1.5), (4, 2.5), (0, 6), (4, 6)]
    ],
    '3': [
        [(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (2.5, 3)],
        [(2.5, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]
    ],
    '4': [
        [(3, 0), (3, 6)],
        [(3, 0), (0, 4), (4, 4)]
    ],
    '5': [
        [(4, 0), (0, 0), (0, 2.5), (3, 2.5), (4, 3.5), (4, 5), (3, 6), (1, 6), (0, 5)]
    ],
    '6': [
        [(3, 0), (1, 0), (0, 1.5), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.5), (3, 2.5), (0, 2.5)]
    ],
    '7': [
        [(0, 0), (4, 0), (1.5, 6)]
    ],
    '8': [
        [(1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 2), (0, 1), (1, 0)],
        [(1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3)]
    ],
    '9': [
        [(4, 3.5), (1, 3.5), (0, 2.5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 4.5), (3, 6), (1, 6)]
    ],
    '.': [
        [(2, 5.5), (2, 6)]
    ],
    ',': [
        [(2, 5), (2, 6), (1, 7)]
    ],
    "'": [
        [(2, 0), (1.5, 2)]
    ],
    '-': [
        [(0.5, 3), (3.5, 3)]
    ],
    ':': [
        [(2, 1.8), (2, 2.2)],
        [(2, 4.8), (2, 5.2)]
    ],
    '/': [
        [(0, 6), (4, 0)]
    ],
    '%': [
        [(0, 6), (4, 0)],
        [(1, 1), (1.5, 1.5)],
        [(2.5, 4.5), (3, 5)]
    ],
    '$': [
        [(2, -0.5), (2, 6.5)],
        [(3.5, 1), (2.5, 0.5), (1.5, 0.5), (0.5, 1.5), (1, 2.5), (3, 3.5), (3.5, 4.5), (2.5, 5.5), (1.5, 5.5), (0.5, 5)]
    ],
    '+': [
        [(2, 1), (2, 5)],
        [(0, 3), (4, 3)]
    ],
    '(': [
        [(3, 0), (1.5, 2), (1.5, 4), (3, 6)]
    ],
    ')': [
        [(1, 0), (2.5, 2), (2.5, 4), (1, 6)]
    ],
    '!': [
        [(2, 0), (2, 4)],
        [(2, 5.5), (2, 6)]
    ],
    '"': [
        [(1, 0), (1, 2)],
        [(3, 0), (3, 2)]
    ],
    ';': [
        [(2, 1.8), (2, 2.2)],
        [(2, 4.8), (2, 5.8), (1, 6.8)]
    ],
}

# ---------------------------------------------------------------------------
# Shape Rasterization (Slice-based bytearray operations with clipping support)
# ---------------------------------------------------------------------------
def draw_line(canvas, W, H, x0, y0, x1, y1, thickness, color_bytes, clip=None):
    r = thickness / 2.0
    dx = x1 - x0
    dy = y1 - y0
    l2 = dx * dx + dy * dy
    if l2 == 0:
        y_start = max(0, int(math.floor(y0 - r)))
        y_end = min(H - 1, int(math.ceil(y0 + r)))
        if clip is not None:
            y_start = max(y_start, clip[1])
            y_end = min(y_end, clip[3] - 1)
        if y_end < y_start:
            return
        r2 = r * r
        for y in range(y_start, y_end + 1):
            dy_c = y - y0
            if abs(dy_c) <= r:
                span = math.sqrt(max(0.0, r2 - dy_c * dy_c))
                xa = max(0, int(math.floor(x0 - span)))
                xb = min(W, int(math.ceil(x0 + span)))
                if clip is not None:
                    xa = max(xa, clip[0])
                    xb = min(xb, clip[2])
                if xb > xa:
                    canvas[(y * W + xa) * 3 : (y * W + xb) * 3] = color_bytes * (xb - xa)
        return

    length = math.sqrt(l2)
    nx = -dy / length * r
    ny = dx / length * r

    poly = [
        (x0 + nx, y0 + ny),
        (x1 + nx, y1 + ny),
        (x1 - nx, y1 - ny),
        (x0 - nx, y0 - ny)
    ]

    y_start = max(0, int(math.floor(min(y0, y1) - r)))
    y_end = min(H - 1, int(math.ceil(max(y0, y1) + r)))
    if clip is not None:
        y_start = max(y_start, clip[1])
        y_end = min(y_end, clip[3] - 1)
    if y_end < y_start:
        return
    r2 = r * r

    for y in range(y_start, y_end + 1):
        candidates = []
        dy0 = y - y0
        if abs(dy0) <= r:
            span = math.sqrt(max(0.0, r2 - dy0 * dy0))
            candidates.append(x0 - span)
            candidates.append(x0 + span)
        dy1 = y - y1
        if abs(dy1) <= r:
            span = math.sqrt(max(0.0, r2 - dy1 * dy1))
            candidates.append(x1 - span)
            candidates.append(x1 + span)
        for i in range(4):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % 4]
            if (ay <= y <= by) or (by <= y <= ay):
                if ay != by:
                    candidates.append(ax + (y - ay) * (bx - ax) / (by - ay))

        if candidates:
            xa = max(0, int(math.floor(min(candidates))))
            xb = min(W, int(math.ceil(max(candidates))))
            if clip is not None:
                xa = max(xa, clip[0])
                xb = min(xb, clip[2])
            if xb > xa:
                canvas[(y * W + xa) * 3 : (y * W + xb) * 3] = color_bytes * (xb - xa)


def fill_rect(canvas, W, H, x, y, w, h, color, clip=None):
    x0 = max(0, int(round(x)))
    y0 = max(0, int(round(y)))
    x1 = min(W, int(round(x + w)))
    y1 = min(H, int(round(y + h)))
    if clip is not None:
        x0 = max(x0, clip[0])
        y0 = max(y0, clip[1])
        x1 = min(x1, clip[2])
        y1 = min(y1, clip[3])
    if x1 <= x0 or y1 <= y0:
        return
    span_bytes = bytes(color) * (x1 - x0)
    for cy in range(y0, y1):
        idx0 = (cy * W + x0) * 3
        idx1 = (cy * W + x1) * 3
        canvas[idx0:idx1] = span_bytes


def stroke_rect(canvas, W, H, x, y, w, h, thickness, color, clip=None):
    t = int(round(thickness))
    fill_rect(canvas, W, H, x, y, w, t, color, clip=clip)
    fill_rect(canvas, W, H, x, y + h - t, w, t, color, clip=clip)
    fill_rect(canvas, W, H, x, y + t, t, h - 2 * t, color, clip=clip)
    fill_rect(canvas, W, H, x + w - t, y + t, t, h - 2 * t, color, clip=clip)


def fill_circle(canvas, W, H, cx, cy, r, color, clip=None):
    y0 = max(0, int(math.floor(cy - r)))
    y1 = min(H, int(math.ceil(cy + r)) + 1)
    if clip is not None:
        y0 = max(y0, clip[1])
        y1 = min(y1, clip[3])
    if y1 <= y0:
        return
    color_bytes = bytes(color)
    r2 = r * r
    for y in range(y0, y1):
        dy = y - cy
        d2 = dy * dy
        if d2 <= r2:
            dx = math.sqrt(r2 - d2)
            x0 = max(0, int(math.floor(cx - dx)))
            x1 = min(W, int(math.ceil(cx + dx)))
            if clip is not None:
                x0 = max(x0, clip[0])
                x1 = min(x1, clip[2])
            if x1 > x0:
                canvas[(y * W + x0) * 3 : (y * W + x1) * 3] = color_bytes * (x1 - x0)


def fill_polygon(canvas, W, H, points, color, clip=None):
    if len(points) < 3:
        return
    min_y = max(0, int(math.floor(min(p[1] for p in points))))
    max_y = min(H - 1, int(math.ceil(max(p[1] for p in points))))
    if clip is not None:
        min_y = max(min_y, clip[1])
        max_y = min(max_y, clip[3] - 1)
    if max_y < min_y:
        return
    color_bytes = bytes(color)
    n = len(points)
    for y in range(min_y, max_y + 1):
        x_inters = []
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            y1 = p1[1]
            y2 = p2[1]
            if y1 == y2:
                continue
            if (y1 <= y < y2) or (y2 <= y < y1):
                x = p1[0] + (y - y1) * (p2[0] - p1[0]) / (y2 - y1)
                x_inters.append(x)
        x_inters.sort()
        for j in range(0, len(x_inters) - 1, 2):
            xa = max(0, int(math.floor(x_inters[j])))
            xb = min(W, int(math.ceil(x_inters[j + 1])))
            if clip is not None:
                xa = max(xa, clip[0])
                xb = min(xb, clip[2])
            if xb > xa:
                canvas[(y * W + xa) * 3 : (y * W + xb) * 3] = color_bytes * (xb - xa)


def get_star_points(cx, cy, r_outer, r_inner, num_points=5, angle_offset=-math.pi / 2.0):
    pts = []
    for i in range(num_points * 2):
        angle = angle_offset + i * math.pi / num_points
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts

# ---------------------------------------------------------------------------
# Text Layout and Measurement
# ---------------------------------------------------------------------------
def get_char_width(ch, scale):
    if ch == ' ':
        return int(scale * 3.5)
    if ch in ('.', ':', '!', "'", ',', ';'):
        return int(scale * 3.2)
    if ch in ('"',):
        return int(scale * 4.5)
    if ch == 'I':
        return int(scale * 4.5)
    if ch in ('M', 'W'):
        return int(scale * 6.5)
    return int(scale * 5.5)


def measure_text(text, scale):
    total = 0
    for ch in text.upper():
        total += get_char_width(ch, scale)
    return total


def draw_text(canvas, text, x, y, scale, color, thickness=None, clip=None):
    if thickness is None:
        thickness = max(1.5, scale * 0.72)
    color_bytes = bytes(color)
    cur_x = x
    for ch in text.upper():
        if ch == ' ':
            cur_x += get_char_width(' ', scale)
            continue
        polylines = GLYPHS.get(ch)
        if polylines:
            for poly in polylines:
                for i in range(len(poly) - 1):
                    x0 = cur_x + poly[i][0] * scale
                    y0 = y + poly[i][1] * scale
                    x1 = cur_x + poly[i+1][0] * scale
                    y1 = y + poly[i+1][1] * scale
                    draw_line(canvas, CANVAS_W, CANVAS_H, x0, y0, x1, y1, thickness, color_bytes, clip=clip)
        cur_x += get_char_width(ch, scale)
    return cur_x - x


def draw_text_centered(canvas, text, y, scale, color, thickness=None, clip=None):
    w = measure_text(text, scale)
    x = (CANVAS_W - w) // 2
    draw_text(canvas, text, x, y, scale, color, thickness, clip=clip)
    return x, w


def draw_text_in_box(canvas, text, bx, by, bw, bh, scale, color, align="center", thickness=None, clip=None):
    w = measure_text(text, scale)
    gh = int(round(scale * 6.0))
    if align == "center":
        x = bx + (bw - w) // 2
    elif align == "right":
        x = bx + bw - w
    else:
        x = bx
    y = by + (bh - gh) // 2
    draw_text(canvas, text, x, y, scale, color, thickness, clip=clip)
    return x, y, w

# ---------------------------------------------------------------------------
# Downsampler: 4x4 box average (4096x4096 -> 1024x1024)
# Fast row slicing & accumulation, strictly avoiding per-pixel Python loops
# ---------------------------------------------------------------------------
def downscale_4x(canvas, w_src=4096, h_src=4096):
    w_out = w_src // 4
    h_out = h_src // 4
    row_stride = w_src * 3
    out_stride = 1 + w_out * 3
    raw_scanlines = bytearray(h_out * out_stride)

    for oy in range(h_out):
        base = oy * 4 * row_stride
        r0 = canvas[base : base + row_stride]
        r1 = canvas[base + row_stride : base + 2 * row_stride]
        r2 = canvas[base + 2 * row_stride : base + 3 * row_stride]
        r3 = canvas[base + 3 * row_stride : base + 4 * row_stride]

        vsum = [a + b + c + d for a, b, c, d in zip(r0, r1, r2, r3)]

        r_val = [(a + b + c + d + 8) >> 4 for a, b, c, d in zip(vsum[0::12], vsum[3::12], vsum[6::12], vsum[9::12])]
        g_val = [(a + b + c + d + 8) >> 4 for a, b, c, d in zip(vsum[1::12], vsum[4::12], vsum[7::12], vsum[10::12])]
        b_val = [(a + b + c + d + 8) >> 4 for a, b, c, d in zip(vsum[2::12], vsum[5::12], vsum[8::12], vsum[11::12])]

        out_offset = oy * out_stride
        raw_scanlines[out_offset + 1 : out_offset + out_stride : 3] = bytes(r_val)
        raw_scanlines[out_offset + 2 : out_offset + out_stride : 3] = bytes(g_val)
        raw_scanlines[out_offset + 3 : out_offset + out_stride : 3] = bytes(b_val)

    return raw_scanlines

# ---------------------------------------------------------------------------
# PNG Output (Direct binary chunk construction with struct and crc32)
# ---------------------------------------------------------------------------
def write_png(width, height, raw_scanlines, filepath):
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    compressed_data = zlib.compress(raw_scanlines, level=6)
    idat_crc = zlib.crc32(b"IDAT" + compressed_data) & 0xFFFFFFFF
    idat_chunk = struct.pack(">I", len(compressed_data)) + b"IDAT" + compressed_data + struct.pack(">I", idat_crc)

    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    png_data = b"\x89PNG\r\n\x1a\n" + ihdr_chunk + idat_chunk + iend_chunk
    with open(filepath, "wb") as f:
        f.write(png_data)

# ---------------------------------------------------------------------------
# Coordinate scaling helper: 1024-space to 4096-space
# ---------------------------------------------------------------------------
def S(v):
    return int(round(v * 4.0))

# ---------------------------------------------------------------------------
# Landmass classification helper for world dot-map
# Equirectangular projection: longitude [-180..180], latitude [75..-75]
# ---------------------------------------------------------------------------
def is_land(lat, lon):
    # Greenland & Arctic Islands
    if 60 <= lat <= 83 and -55 <= lon <= -15: return True
    # Iceland
    if 63 <= lat <= 67 and -25 <= lon <= -12: return True
    # Alaska
    if 55 <= lat <= 72 and -168 <= lon <= -130: return True
    # Canada
    if 49 <= lat <= 72 and -130 <= lon <= -55:
        if 51 <= lat <= 64 and -95 <= lon <= -78: return False  # Hudson Bay
        return True
    # USA Mainland
    if 25 <= lat <= 49 and -125 <= lon <= -68:
        if lat < 30 and -95 <= lon <= -82: return False  # Gulf of Mexico
        return True
    # Mexico & Central America
    if 15 <= lat <= 32 and -116 <= lon <= -87: return True
    if 8 <= lat <= 16 and -90 <= lon <= -77: return True
    if 18 <= lat <= 24 and -85 <= lon <= -72: return True  # Caribbean/Cuba
    # South America
    if -55 <= lat <= 12:
        if 0 <= lat <= 12 and -80 <= lon <= -35: return True
        if -15 <= lat < 0 and -81 <= lon <= -35: return True
        if -30 <= lat < -15 and -74 <= lon <= -42: return True
        if -42 <= lat < -30 and -74 <= lon <= -56: return True
        if -55 <= lat < -42 and -74 <= lon <= -64: return True
    # Europe
    if 55 <= lat <= 71 and 4 <= lon <= 32: return True    # Scandinavia / Baltics
    if 50 <= lat <= 59 and -10 <= lon <= 2: return True   # UK & Ireland
    if 36 <= lat <= 55 and -10 <= lon <= 35:
        if 36 <= lat <= 44 and -9 <= lon <= 3: return True   # Iberian peninsula
        if 42 <= lat <= 54 and -5 <= lon <= 15: return True  # France, Benelux, Germany
        if 37 <= lat <= 47 and 8 <= lon <= 18: return True   # Italy
        if 37 <= lat <= 55 and 15 <= lon <= 35: return True  # Balkans, Eastern Europe
    # Africa
    if -35 <= lat <= 37:
        if 15 <= lat <= 37 and -17 <= lon <= 35: return True  # North Africa
        if 4 <= lat < 15 and -17 <= lon <= 45: return True   # West & East Africa
        if -15 <= lat < 4 and 9 <= lon <= 43: return True    # Central Africa
        if -30 <= lat < -15 and 12 <= lon <= 38: return True # Southern Africa
        if -35 <= lat < -30 and 16 <= lon <= 33: return True # South Africa cape
    if -26 <= lat <= -12 and 43 <= lon <= 51: return True    # Madagascar
    # Middle East
    if 36 <= lat <= 42 and 26 <= lon <= 45: return True  # Turkey / Anatolia
    if 12 <= lat <= 34 and 35 <= lon <= 60: return True  # Arabian peninsula
    if 25 <= lat <= 40 and 44 <= lon <= 63: return True  # Iran & Iraq
    # Russia & Siberia
    if 50 <= lat <= 76 and 35 <= lon <= 180: return True
    # Central Asia
    if 36 <= lat <= 50 and 46 <= lon <= 88: return True
    # South Asia (India)
    if 8 <= lat <= 35 and 68 <= lon <= 90: return True
    # East Asia (China & Mongolia)
    if 20 <= lat <= 50 and 80 <= lon <= 130: return True
    # Japan & Korea
    if 31 <= lat <= 45 and 126 <= lon <= 145: return True
    # Southeast Asia
    if 8 <= lat <= 23 and 96 <= lon <= 110: return True
    # Philippines
    if 6 <= lat <= 19 and 120 <= lon <= 126: return True
    # Indonesia & New Guinea
    if -10 <= lat <= 5 and 95 <= lon <= 152: return True
    # Australia
    if -44 <= lat <= -11 and 113 <= lon <= 154: return True
    # New Zealand
    if -47 <= lat <= -34 and 166 <= lon <= 178: return True
    # Antarctica (daratan selatan merata sampai dekat bawah)
    if -85 <= lat <= -65:
        if -80 <= lat <= -72 and -170 <= lon <= -150: return False
        if -78 <= lat <= -70 and -50 <= lon <= -30: return False
        return True
    if -65 <= lat <= -62 and -66 <= lon <= -58: return True
    return False

# ---------------------------------------------------------------------------
# 3 Panel Illustrations (Flat style, strictly clipped to box)
# ---------------------------------------------------------------------------
def draw_panel1_illustration(canvas, ibox_x, ibox_y, ibox_w, ibox_h):
    """
    Panel 1 CLIMATE (COP31 Antalya, pemanasan):
    - latar krem
    - matahari oranye dengan sinar di kiri atas
    - termometer besar di kanan (tabung abu, kolom merah naik tinggi, label '1.5C' di samping)
    - tiga cerobong pabrik hitam mengeluarkan asap abu di bawah
    - garis gelombang laut biru di bawah
    """
    clip = (S(ibox_x), S(ibox_y), S(ibox_x + ibox_w), S(ibox_y + ibox_h))

    # Latar krem
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(ibox_y), S(ibox_w), S(ibox_h), COLOR_BG, clip=clip)

    # Matahari oranye di kiri atas
    sun_cx = ibox_x + 42
    sun_cy = ibox_y + 32
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(sun_cx), S(sun_cy), S(13.0), COLOR_ORANGE, clip=clip)
    # Sinar matahari
    for i in range(8):
        ang = i * math.pi / 4.0
        x0 = sun_cx + 17.0 * math.cos(ang)
        y0 = sun_cy + 17.0 * math.sin(ang)
        x1 = sun_cx + 25.0 * math.cos(ang)
        y1 = sun_cy + 25.0 * math.sin(ang)
        draw_line(canvas, CANVAS_W, CANVAS_H, S(x0), S(y0), S(x1), S(y1), 6, bytes(COLOR_ORANGE), clip=clip)

    # Tiga cerobong pabrik hitam mengeluarkan asap abu
    base_x = ibox_x + 85
    base_y = ibox_y + 68
    base_w = 105
    base_h = 26
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(base_x), S(base_y), S(base_w), S(base_h), COLOR_INK, clip=clip)
    # Jendela kecil pabrik
    for wx in [base_x + 8, base_x + 22, base_x + 78, base_x + 92]:
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(wx), S(base_y + 8), S(6), S(6), COLOR_YELLOW, clip=clip)

    # 3 cerobong hitam
    chims = [
        (ibox_x + 98, 11, ibox_y + 46, 22),
        (ibox_x + 125, 13, ibox_y + 38, 30),
        (ibox_x + 155, 11, ibox_y + 48, 20),
    ]
    for cx, cw, cy, ch in chims:
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx), S(cy), S(cw), S(ch), COLOR_INK, clip=clip)
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx - 1), S(cy), S(cw + 2), S(3), COLOR_INK, clip=clip)

    # Gumpalan asap abu
    puffs = [
        # Cerobong 1
        (ibox_x + 103, ibox_y + 38, 5.0),
        (ibox_x + 100, ibox_y + 29, 7.0),
        (ibox_x + 96, ibox_y + 19, 9.0),
        # Cerobong 2
        (ibox_x + 131, ibox_y + 30, 6.0),
        (ibox_x + 134, ibox_y + 21, 8.5),
        (ibox_x + 140, ibox_y + 12, 10.5),
        # Cerobong 3
        (ibox_x + 160, ibox_y + 40, 5.0),
        (ibox_x + 163, ibox_y + 31, 7.5),
        (ibox_x + 168, ibox_y + 21, 9.0),
    ]
    for px, py, pr in puffs:
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(px), S(py), S(pr), COLOR_SMOKE, clip=clip)
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(px - 1), S(py - 1), S(pr * 0.7), (200, 204, 208), clip=clip)

    # Termometer besar di kanan
    th_x = ibox_x + 236
    # Tabung abu luar
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(th_x), S(ibox_y + 78), S(12.0), COLOR_GRAY, clip=clip)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(th_x - 6), S(ibox_y + 16), S(12), S(64), COLOR_GRAY, clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(th_x), S(ibox_y + 16), S(6.0), COLOR_GRAY, clip=clip)
    # Latar tabung bagian dalam
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(th_x - 4), S(ibox_y + 16), S(8), S(64), COLOR_LIGHT_GRAY, clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(th_x), S(ibox_y + 78), S(10.0), COLOR_LIGHT_GRAY, clip=clip)
    # Kolom merah naik tinggi
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(th_x), S(ibox_y + 78), S(8.5), COLOR_RED, clip=clip)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(th_x - 3.5), S(ibox_y + 24), S(7), S(56), COLOR_RED, clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(th_x), S(ibox_y + 24), S(3.5), COLOR_RED, clip=clip)

    # Skala garis termometer di samping kiri
    for ty in [26, 36, 46, 56, 66]:
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(th_x - 12), S(ibox_y + ty), S(5), S(1.5), COLOR_INK, clip=clip)

    # Label "1.5C" di samping termometer
    draw_text(canvas, "1.5C", S(th_x + 11), S(ibox_y + 21), 4.6, COLOR_RED, thickness=3.0, clip=clip)

    # Garis gelombang laut biru di bawah
    sea_y = ibox_y + 94
    sea_h = 12
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(sea_y), S(ibox_w), S(sea_h), (50, 110, 175), clip=clip)
    # Garis ombak berulang
    for wx in range(ibox_x, ibox_x + ibox_w, 14):
        draw_line(canvas, CANVAS_W, CANVAS_H, S(wx), S(sea_y + 3), S(wx + 7), S(sea_y + 1), 3, bytes((120, 180, 235)), clip=clip)
        draw_line(canvas, CANVAS_W, CANVAS_H, S(wx + 7), S(sea_y + 1), S(wx + 14), S(sea_y + 3), 3, bytes((120, 180, 235)), clip=clip)


def draw_panel2_illustration(canvas, ibox_x, ibox_y, ibox_w, ibox_h):
    """
    Panel 2 MIDDLE EAST (Iran/Bahrain, serangan malam):
    - latar navy gelap
    - bulan sabit kuning kecil di kiri atas
    - dua garis lurus terang sebagai rudal melintas dengan jejak
    - satu ledakan bintang oranye/merah di kanan
    - siluet pabrik industri hitam di bawah dengan satu cerobong berasap
    - garis laut gelap di bawah
    """
    clip = (S(ibox_x), S(ibox_y), S(ibox_x + ibox_w), S(ibox_y + ibox_h))

    # Latar navy gelap
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(ibox_y), S(ibox_w), S(ibox_h), COLOR_DARK_NAVY, clip=clip)

    # Bulan sabit kuning kecil di kiri atas
    moon_cx = ibox_x + 36
    moon_cy = ibox_y + 24
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(moon_cx), S(moon_cy), S(9.5), COLOR_YELLOW, clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(moon_cx + 4.5), S(moon_cy - 2.5), S(8.5), COLOR_DARK_NAVY, clip=clip)

    # Siluet pabrik industri hitam di bawah
    fact_x = ibox_x + 75
    fact_y = ibox_y + 68
    fact_w = 150
    fact_h = 28
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(fact_x), S(fact_y), S(fact_w), S(fact_h), COLOR_INK, clip=clip)
    # Tangki industri kubah
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(fact_x + 35), S(fact_y + 10), S(15.0), COLOR_INK, clip=clip)
    # Satu cerobong berasap
    chim_x = fact_x + 95
    chim_y = fact_y - 20
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(chim_x), S(chim_y), S(12), S(22), COLOR_INK, clip=clip)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(chim_x - 1), S(chim_y), S(14), S(3), COLOR_INK, clip=clip)
    # Asap keluar cerobong
    for px, py, pr in [(chim_x + 6, chim_y - 6, 5.0), (chim_x + 12, chim_y - 14, 7.5), (chim_x + 20, chim_y - 23, 9.5)]:
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(px), S(py), S(pr), (70, 75, 88), clip=clip)

    # Dua garis lurus terang sebagai rudal melintas dengan jejak
    # Rudal 1
    draw_line(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 50), S(ibox_y + 54), S(ibox_x + 180), S(ibox_y + 36), 5, bytes(COLOR_ORANGE), clip=clip)
    draw_line(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 120), S(ibox_y + 44), S(ibox_x + 180), S(ibox_y + 36), 2.5, bytes(COLOR_YELLOW), clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 180), S(ibox_y + 36), S(2.5), COLOR_WHITE, clip=clip)
    # Rudal 2
    draw_line(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 70), S(ibox_y + 68), S(ibox_x + 205), S(ibox_y + 48), 5, bytes(COLOR_ORANGE), clip=clip)
    draw_line(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 140), S(ibox_y + 58), S(ibox_x + 205), S(ibox_y + 48), 2.5, bytes(COLOR_YELLOW), clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 205), S(ibox_y + 48), S(2.5), COLOR_WHITE, clip=clip)

    # Satu ledakan bintang oranye/merah di kanan
    exp_cx = ibox_x + 242
    exp_cy = ibox_y + 44
    # Bintang luar merah (12 sudut)
    pts_red = get_star_points(S(exp_cx), S(exp_cy), S(22.0), S(8.5), num_points=12)
    fill_polygon(canvas, CANVAS_W, CANVAS_H, pts_red, COLOR_RED, clip=clip)
    # Bintang tengah oranye (12 sudut diputar)
    pts_ora = get_star_points(S(exp_cx), S(exp_cy), S(15.0), S(6.0), num_points=12, angle_offset=math.pi / 12.0)
    fill_polygon(canvas, CANVAS_W, CANVAS_H, pts_ora, COLOR_ORANGE, clip=clip)
    # Inti kuning & putih
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(exp_cx), S(exp_cy), S(7.0), COLOR_YELLOW, clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(exp_cx), S(exp_cy), S(3.5), COLOR_WHITE, clip=clip)

    # Garis laut gelap di bawah
    sea_y = ibox_y + 96
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(sea_y), S(ibox_w), S(10), (8, 14, 26), clip=clip)
    draw_line(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 20), S(sea_y + 4), S(ibox_x + 120), S(sea_y + 4), 2.5, bytes((22, 38, 66)), clip=clip)
    draw_line(canvas, CANVAS_W, CANVAS_H, S(ibox_x + 160), S(sea_y + 6), S(ibox_x + 275), S(sea_y + 6), 2.5, bytes((22, 38, 66)), clip=clip)


def draw_panel3_illustration(canvas, ibox_x, ibox_y, ibox_w, ibox_h):
    """
    Panel 3 MEXICO (penangkapan kartel):
    - latar oranye senja
    - matahari kuning besar di kiri atas
    - siluet pegunungan gelap di tengah (rapi di dalam kotak)
    - jalan lurus dengan tiga mobil hitam kecil
    - satu bintang lencana kuning besar di kanan sebagai lambang penegak hukum
    """
    clip = (S(ibox_x), S(ibox_y), S(ibox_x + ibox_w), S(ibox_y + ibox_h))

    # Latar oranye senja
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(ibox_y), S(ibox_w), S(ibox_h), (232, 122, 45), clip=clip)

    # Matahari kuning besar di kiri atas
    sun_cx = ibox_x + 48
    sun_cy = ibox_y + 36
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(sun_cx), S(sun_cy), S(19.0), COLOR_YELLOW, clip=clip)

    # Siluet pegunungan gelap di tengah (rapi di dalam batas kotak ibox_w)
    peaks = [
        [(ibox_x, 84), (ibox_x + 38, 50), (ibox_x + 90, 84)],
        [(ibox_x + 65, 84), (ibox_x + 118, 42), (ibox_x + 172, 84)],
        [(ibox_x + 145, 84), (ibox_x + 195, 48), (ibox_x + 245, 84)],
        [(ibox_x + 215, 84), (ibox_x + 258, 54), (ibox_x + ibox_w, 84)],
    ]
    for p in peaks:
        poly_pts = [(S(x), S(ibox_y + y)) for x, y in p]
        fill_polygon(canvas, CANVAS_W, CANVAS_H, poly_pts, COLOR_INK, clip=clip)

    # Bintang lencana kuning besar di kanan sebagai lambang penegak hukum
    badge_cx = ibox_x + 242
    badge_cy = ibox_y + 48
    # Bintang 6 sudut penegak hukum (Sheriff star)
    star_pts = get_star_points(S(badge_cx), S(badge_cy), S(21.0), S(10.5), num_points=6)
    fill_polygon(canvas, CANVAS_W, CANVAS_H, star_pts, COLOR_YELLOW, clip=clip)
    # Lingkaran tengah lencana
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(badge_cx), S(badge_cy), S(7.5), (220, 160, 25), clip=clip)
    fill_circle(canvas, CANVAS_W, CANVAS_H, S(badge_cx), S(badge_cy), S(3.5), COLOR_INK, clip=clip)

    # Jalan lurus di bawah
    road_y = ibox_y + 84
    road_h = 14
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(road_y), S(ibox_w), S(road_h), (38, 40, 44), clip=clip)
    # Garis marka putus-putus putih
    for rx in range(ibox_x + 6, ibox_x + ibox_w - 6, 16):
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(rx), S(road_y + 6), S(8), S(1.5), COLOR_WHITE, clip=clip)

    # Tiga mobil hitam kecil
    car_x_list = [ibox_x + 48, ibox_x + 98, ibox_x + 148]
    for cx in car_x_list:
        # Bodi mobil
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx), S(road_y + 3), S(18), S(5.5), COLOR_INK, clip=clip)
        # Kabin atas
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx + 4), S(road_y - 1), S(10), S(4.5), COLOR_INK, clip=clip)
        # Roda
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(cx + 4.5), S(road_y + 8.5), S(2.0), COLOR_INK, clip=clip)
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(cx + 13.5), S(road_y + 8.5), S(2.0), COLOR_INK, clip=clip)
        # Lampu rotator polisi di atap (merah & biru)
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx + 5.5), S(road_y - 2.5), S(3), S(1.5), COLOR_RED, clip=clip)
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx + 9.5), S(road_y - 2.5), S(3), S(1.5), (40, 120, 240), clip=clip)

# ---------------------------------------------------------------------------
# Main Routine - LANGKAH D: Revisi Keterbacaan dan Jarak
# ---------------------------------------------------------------------------
def main():
    t_start = time.perf_counter()

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    # Allocate cream canvas (4096 x 4096)
    canvas = bytearray(bytes(COLOR_BG) * (CANVAS_W * CANVAS_H))

    # =======================================================================
    # 1. BINGKAI LUAR: margin 16 (1024-space), garis ganda tipis
    # =======================================================================
    stroke_rect(canvas, CANVAS_W, CANVAS_H, S(16), S(16), S(992), S(992), 6, COLOR_INK)
    stroke_rect(canvas, CANVAS_W, CANVAS_H, S(20), S(20), S(984), S(984), 3, COLOR_INK)

    # =======================================================================
    # 2. MASTHEAD (y 28–100): "THE WORLD IN ONE DAY" besar, rata tengah.
    # Garis merah tebal di bawahnya (y ~105).
    # Tanggal (y 114–142): "SUNDAY 22 NOVEMBER 2026" merah, rata tengah.
    # =======================================================================
    draw_text_centered(canvas, "THE WORLD IN ONE DAY", S(50), 22.0, COLOR_INK)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(24), S(105), S(976), S(3), COLOR_RED)
    draw_text_centered(canvas, "SUNDAY 22 NOVEMBER 2026", S(122), 10.5, COLOR_RED)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(24), S(146), S(976), S(1), COLOR_GRAY)

    # =======================================================================
    # 3. 3 PANEL (y 152–378): tiga kolom sama lebar dengan jarak 16 antar kolom (x awal 24)
    # Tiap panel: pita header warna berisi label seksi;
    # kotak ilustrasi flat art;
    # judul 2 baris; ringkasan 2 baris.
    # =======================================================================
    panel_data = [
        {
            "label": "CLIMATE",
            "ribbon_color": COLOR_RED,
            "h1": "COP31 TALKS RUN INTO",
            "h2": "OVERTIME",
            "s1": "FOSSIL-FUEL PHASE-OUT",
            "s2": "STILL DEADLOCKED",
        },
        {
            "label": "MIDDLE EAST",
            "ribbon_color": COLOR_NAVY,
            "h1": "IRAN STRIKES SITE",
            "h2": "IN BAHRAIN",
            "s1": "IRGC CLAIMS MISSILE + DRONE",
            "s2": "ATTACK ON US POSITIONS",
        },
        {
            "label": "MEXICO",
            "ribbon_color": COLOR_DARK_GREEN,
            "h1": "MEXICO CAPTURES",
            "h2": "'EL CHAPO ISIDRO'",
            "s1": "FBI TOP-10 FUGITIVE HELD",
            "s2": "IN SINALOA; 11 KILLED",
        },
    ]

    col_w = 314
    col_gap = 16
    panel_y = 152
    panel_h = 226

    for i, pdata in enumerate(panel_data):
        px = 24 + i * (col_w + col_gap)

        # Panel white card background & border
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(px), S(panel_y), S(col_w), S(panel_h), COLOR_WHITE)
        stroke_rect(canvas, CANVAS_W, CANVAS_H, S(px), S(panel_y), S(col_w), S(panel_h), 3, COLOR_GRAY)

        # Header ribbon
        ribbon_h = 22
        fill_rect(canvas, CANVAS_W, CANVAS_H, S(px), S(panel_y), S(col_w), S(ribbon_h), pdata["ribbon_color"])
        draw_text_in_box(canvas, pdata["label"], S(px), S(panel_y), S(col_w), S(ribbon_h), 6.5, COLOR_WHITE, align="center")

        # Illustration box (106h x 298w)
        ibox_x = px + 8
        ibox_y = 178
        ibox_w = col_w - 16
        ibox_h = 106

        if i == 0:
            draw_panel1_illustration(canvas, ibox_x, ibox_y, ibox_w, ibox_h)
        elif i == 1:
            draw_panel2_illustration(canvas, ibox_x, ibox_y, ibox_w, ibox_h)
        else:
            draw_panel3_illustration(canvas, ibox_x, ibox_y, ibox_w, ibox_h)

        stroke_rect(canvas, CANVAS_W, CANVAS_H, S(ibox_x), S(ibox_y), S(ibox_w), S(ibox_h), 2, COLOR_GRAY)

        # 2-line headline
        tx = px + 10
        draw_text(canvas, pdata["h1"], S(tx), S(293), 7.5, COLOR_INK)
        draw_text(canvas, pdata["h2"], S(tx), S(310), 7.5, COLOR_INK)

        # 2-line summary
        draw_text(canvas, pdata["s1"], S(tx), S(338), 5.5, COLOR_INK)
        draw_text(canvas, pdata["s2"], S(tx), S(354), 5.5, COLOR_INK)

    # =======================================================================
    # 4. STRIP ANGKA (y 390–468): label kecil "BY THE NUMBERS" di kiri atas strip;
    # 4 sel sama lebar, tiap sel angka besar + keterangan 2 baris kecil.
    # =======================================================================
    strip_x = 24
    strip_y = 390
    strip_w = 976
    strip_h = 78

    fill_rect(canvas, CANVAS_W, CANVAS_H, S(strip_x), S(strip_y), S(strip_w), S(strip_h), COLOR_WHITE)
    stroke_rect(canvas, CANVAS_W, CANVAS_H, S(strip_x), S(strip_y), S(strip_w), S(strip_h), 3, COLOR_GRAY)

    # Header label "BY THE NUMBERS"
    draw_text(canvas, "BY THE NUMBERS", S(strip_x + 8), S(394), 5.0, COLOR_RED)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(strip_x), S(406), S(strip_w), S(1), COLOR_GRAY)

    num_items = [
        {"num": "$3.79B", "l1": "GTA 6 FIRST-DAY SALES", "l2": "RECORD"},
        {"num": "11",     "l1": "KILLED IN MEXICO",       "l2": "CAPTURE RAID"},
        {"num": "24",     "l1": "KILLED AS FUNERAL BOAT", "l2": "CAPSIZES IN NIGERIA"},
        {"num": "1,500",  "l1": "STRANDED BY HEAVY SNOW", "l2": "IN FUKUSHIMA, JAPAN"},
    ]

    cell_w = 244
    for i, ndata in enumerate(num_items):
        cx = strip_x + i * cell_w
        if i > 0:
            fill_rect(canvas, CANVAS_W, CANVAS_H, S(cx), S(406), S(1), S(strip_h - 16), COLOR_GRAY)
        tx = cx + 10
        draw_text(canvas, ndata["num"], S(tx), S(412), 11.5, COLOR_RED)
        draw_text(canvas, ndata["l1"], S(tx), S(438), 4.2, COLOR_INK)
        draw_text(canvas, ndata["l2"], S(tx), S(450), 4.2, COLOR_INK)

    # =======================================================================
    # 5. AREA BAWAH (y 482–962): kiri peta, kanan daftar.
    # PETA (x 24–462): judul kecil "WHERE IT HAPPENED";
    # Peta dunia dot-matrix (64x64 grid daratan) + 12 penanda bernomor.
    # Terdistribusi merata sampai dekat kaki.
    # =======================================================================
    map_x = 24
    map_w = 438
    draw_text(canvas, "WHERE IT HAPPENED", S(map_x + 4), S(482), 6.0, COLOR_NAVY)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(map_x), S(496), S(map_w), S(1), COLOR_GRAY)

    list_x = 476
    list_w = 524
    draw_text(canvas, "MORE STORIES", S(list_x + 4), S(482), 6.0, COLOR_NAVY)
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(list_x), S(496), S(list_w), S(1), COLOR_GRAY)

    box_y = 504
    box_h = 458  # 504 to 962, menyisakan 10px elegan ke garis kaki di 972

    # Map Card
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(map_x), S(box_y), S(map_w), S(box_h), COLOR_WHITE)
    stroke_rect(canvas, CANVAS_W, CANVAS_H, S(map_x), S(box_y), S(map_w), S(box_h), 3, COLOR_GRAY)

    grid_cols = 64
    grid_rows = 64
    map_inner_x = map_x + 8
    map_inner_y = box_y + 14
    map_inner_w = map_w - 16   # 422 px
    map_inner_h = box_h - 28   # 430 px

    step_x = map_inner_w / float(grid_cols)
    step_y = map_inner_h / float(grid_rows)
    dot_r = 1.8  # radius titik darat

    num_map_dots = 0
    for r in range(grid_rows):
        lat = 75.0 - (r + 0.5) * (150.0 / float(grid_rows))
        dot_y = map_inner_y + (r + 0.5) * step_y
        for c in range(grid_cols):
            lon = -180.0 + (c + 0.5) * (360.0 / float(grid_cols))
            if is_land(lat, lon):
                dot_x = map_inner_x + (c + 0.5) * step_x
                fill_circle(canvas, CANVAS_W, CANVAS_H, S(dot_x), S(dot_y), S(dot_r), COLOR_SLATE_BLUE)
                num_map_dots += 1

    # 12 Penanda bernomor
    markers = [
        (1, "Antalya", 36.9, 30.7),
        (2, "Bahrain", 26.0, 51.5),
        (3, "Sinaloa", 25.0, -107.5),
        (4, "Finland Gulf", 60.0, 26.0),
        (5, "Crimea", 45.3, 34.5),
        (6, "Denmark", 56.5, 9.5),
        (7, "Saudi Arabia", 20.0, 43.0),
        (8, "Indonesia", -2.0, 118.0),
        (9, "Nigeria", 9.0, 8.0),
        (10, "Fukushima", 37.7, 140.5),
        (11, "Brussels", 50.0, 3.0),
        (12, "Washington", 38.9, -77.0),
    ]

    marker_r = 6.8
    num_markers = len(markers)

    for num, name, m_lat, m_lon in markers:
        m_x = map_inner_x + (m_lon + 180.0) / 360.0 * map_inner_w
        m_y = map_inner_y + (75.0 - m_lat) / 150.0 * map_inner_h

        # Lingkaran merah penanda dengan outline gelap halus
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(m_x), S(m_y), S(marker_r + 0.8), COLOR_INK)
        fill_circle(canvas, CANVAS_W, CANVAS_H, S(m_x), S(m_y), S(marker_r), COLOR_RED)

        # Angka putih rata tengah di dalam penanda
        num_str = str(num)
        if len(num_str) == 1:
            t_scale = 3.2
            thk = 1.8
        else:
            t_scale = 2.4
            thk = 1.4

        tw = measure_text(num_str, t_scale)
        th = t_scale * 6.0
        tx = S(m_x) - tw // 2
        ty = S(m_y) - int(round(th / 2.0))
        draw_text(canvas, num_str, tx, ty, t_scale, COLOR_WHITE, thickness=thk)

    # -----------------------------------------------------------------------
    # DAFTAR (x 476–1000): judul kecil "MORE STORIES";
    # daftar bernomor 4–14 dalam DUA kolom (kolom kiri 4–9, kolom kanan 10–14)
    # terdistribusi simetris dan seimbang sampai dekat kaki (y 962).
    # -----------------------------------------------------------------------
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(list_x), S(box_y), S(list_w), S(box_h), COLOR_WHITE)
    stroke_rect(canvas, CANVAS_W, CANVAS_H, S(list_x), S(box_y), S(list_w), S(box_h), 3, COLOR_GRAY)

    # Garis pemisah vertikal antar kolom (simetris)
    col_split_x = list_x + list_w // 2  # 476 + 262 = 738
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(col_split_x), S(box_y), S(1), S(box_h), COLOR_LIGHT_GRAY)

    left_stories = [
        "4 EU-INDONESIA TRADE DEAL",
        "5 FBI PROBES NCIC HACK",
        "6 DRONE HITS RUSSIAN SHIP SPARTA II",
        '7 ZELENSKY: CRIMEA BRIDGE "FAIR RESPONSE"',
        "8 DENMARK EXPELS RUSSIAN ATTACHE",
        "9 HOUTHIS ATTACK SAUDI ARABIA",
    ]

    right_stories = [
        "10 AMAZON NEARS $7.5B DECART DEAL",
        "11 IBM UNVEILS 520-QUBIT CHIP",
        "12 LEEDS BEAT CHELSEA 4-1",
        "13 CANDY FACTORY FIRE IN INDONESIA",
        "14 EU PLASTIC WASTE BAN (21 NOV)",
    ]

    row_h = box_h // 6  # 76 px
    for r in range(6):
        ry = box_y + r * row_h
        if r > 0:
            fill_rect(canvas, CANVAS_W, CANVAS_H, S(list_x), S(ry), S(list_w), S(1), COLOR_LIGHT_GRAY)
        # Left column item (vertically centered in row)
        draw_text(canvas, left_stories[r], S(list_x + 8), S(ry + 34), 4.8, COLOR_INK)
        # Right column item (sel ke-6 di kanan kosong tetap simetris & seimbang)
        if r < len(right_stories):
            draw_text(canvas, right_stories[r], S(col_split_x + 8), S(ry + 34), 4.8, COLOR_INK)

    # =======================================================================
    # 6. KAKI (y 972–994): garis tipis di 972, lalu "SOURCES: ..." rata tengah di 981
    # Tampil utuh di dalam bingkai (baseline ~988.5, jauh di atas batas 1001/1004).
    # =======================================================================
    fill_rect(canvas, CANVAS_W, CANVAS_H, S(24), S(972), S(976), S(1), COLOR_GRAY)
    draw_text_centered(canvas, "SOURCES: REUTERS, AP, BBC, CNN, WSJ, LE MONDE, UN", S(981), 5.0, COLOR_GRAY)

    # =======================================================================
    # Downscale 4x (4096x4096 -> 1024x1024 box average) and write PNG
    # =======================================================================
    raw_scanlines = downscale_4x(canvas, CANVAS_W, CANVAS_H)
    write_png(1024, 1024, raw_scanlines, out_path)

    t_end = time.perf_counter()
    duration = t_end - t_start
    print(f"Generated {out_path} in {duration:.2f}s")
    print(f"STATS: map_dots={num_map_dots}, markers={num_markers}, duration={duration:.2f}s")


if __name__ == "__main__":
    main()
