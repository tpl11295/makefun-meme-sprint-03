# Meme Sprint 3: AI Agent Goes Rogue — one image meme about an AI agent gone rogue.
#
# Stdlib-only rewrite (2026-11-25). The first version used Pillow and was
# rejected in round 1 with run_completes (exit 1): the grader runs
# `python3 -P -s /bot/main.py` in the pinned python:3.13 image, which ships
# neither Pillow nor the DejaVu font files, so `from PIL import Image` raised
# ModuleNotFoundError before drawing anything. This version depends on
# nothing but the Python standard library: it draws into an RGB buffer with
# plain code, renders text with a built-in 5x7 bitmap font, and writes the
# PNG with zlib + struct, so it runs in any python3.13 sandbox with no
# network and no third-party packages.
#
# Output: /output/entry.png (1024x1024 PNG, under 1 MiB).
import math
import os
import struct
import zlib

W, H = 1024, 1024

TOP = "ME: I'LL JUST LET THE AGENT HANDLE THE DEPLOY"
BOTTOM = "THE AGENT AT 3 A.M.: I HAVE UNIONISED THE SERVERS"
TAG = "STATUS: ROGUE"

# 5x7 bitmap font: each glyph is 7 rows of five "0"/"1" characters.
FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}

STEEL = (203, 213, 225)
DARK = (15, 23, 42)
CYAN = (34, 211, 238)
PUPIL = (8, 47, 73)
RED = (239, 68, 68)
GREY = (100, 116, 139)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Canvas:
    """An RGB pixel buffer with tiny drawing primitives (no libraries)."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def gradient(self, top, bottom):
        for y in range(self.h):
            t = y / (self.h - 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            row = bytes(color) * self.w
            start = y * self.w * 3
            self.buf[start:start + self.w * 3] = row

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            start = (y * self.w + x0) * 3
            self.buf[start:start + len(row)] = row

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def rounded_rect(self, x0, y0, x1, y1, r, color):
        self.fill_rect(x0 + r, y0, x1 - r, y1, color)
        self.fill_rect(x0, y0 + r, x1, y1 - r, color)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.fill_circle(cx, cy, r, color)

    def arc(self, cx, cy, rx, ry, start_deg, end_deg, color, width):
        for deg in range(start_deg, end_deg + 1, 2):
            rad = math.radians(deg)
            x = cx + int(rx * math.cos(rad))
            y = cy + int(ry * math.sin(rad))
            self.fill_circle(x, y, width // 2, color)

    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch, FONT[" "])
        for r in range(7):
            for c in range(5):
                if rows[r][c] == "1":
                    self.fill_rect(x + c * scale, y + r * scale,
                                   x + (c + 1) * scale, y + (r + 1) * scale,
                                   color)

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_line(self, text, cx, y, scale, color):
        x = cx - self.text_width(text, scale) // 2
        for ch in text:
            self.glyph(ch, x, y, scale, color)
            x += 6 * scale

    def draw_text(self, text, cx, y, scale, fill=WHITE, outline=BLACK):
        """Word-wrapped, centred text with a black outline for readability."""
        lines = wrap(text, scale, 940)
        for line in lines:
            if outline is not None:
                for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3),
                               (-2, -2), (2, -2), (-2, 2), (2, 2)):
                    self.draw_line(line, cx + dx, y + dy, scale, outline)
            self.draw_line(line, cx, y, scale, fill)
            y += 7 * scale + 10
        return y


def wrap(text, scale, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if len(trial) * 6 * scale - scale <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_robot(cv, cx, cy):
    # Antenna with a red alarm light.
    cv.fill_rect(cx - 5, cy - 250, cx + 5, cy - 190, STEEL)
    cv.fill_circle(cx, cy - 256, 26, RED)
    # Head: rounded steel face with a dark outline.
    cv.rounded_rect(cx - 213, cy - 193, cx + 213, cy + 173, 60, DARK)
    cv.rounded_rect(cx - 210, cy - 190, cx + 210, cy + 170, 60, STEEL)
    # Glowing cyan eyes with dark pupils and a white glint so the face
    # still reads when the meme is shrunk to a phone screen.
    for ex in (cx - 105, cx + 105):
        cv.fill_circle(ex, cy - 45, 52, BLACK)
        cv.fill_circle(ex, cy - 45, 50, CYAN)
        cv.fill_circle(ex, cy - 42, 18, PUPIL)
        cv.fill_circle(ex - 6, cy - 52, 7, WHITE)
    # Crooked grin: a smug half-smile.
    cv.arc(cx, cy + 90, 110, 60, 15, 165, DARK, 10)
    # Side bolts.
    for bx in (cx - 228, cx + 228):
        cv.fill_circle(bx, cy - 24, 18, BLACK)
        cv.fill_circle(bx, cy - 24, 15, GREY)


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def save_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def main():
    cv = Canvas(W, H)
    cv.gradient((11, 18, 32), (30, 41, 59))

    y = 48
    y = cv.draw_text(TOP, W // 2, y, 9)
    draw_robot(cv, W // 2, 560)

    # Rogue status tag under the robot.
    tag_w = cv.text_width(TAG, 6)
    cv.rounded_rect(W // 2 - tag_w // 2 - 28, 796,
                    W // 2 + tag_w // 2 + 28, 860, 28, BLACK)
    cv.rounded_rect(W // 2 - tag_w // 2 - 24, 800,
                    W // 2 + tag_w // 2 + 24, 856, 28, RED)
    cv.draw_line(TAG, W // 2, 810, 6, WHITE)

    cv.draw_text(BOTTOM, W // 2, 872, 6)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    save_png(os.path.join(out_dir, "entry.png"), cv)


if __name__ == "__main__":
    main()
