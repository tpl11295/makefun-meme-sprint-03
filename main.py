# Meme Sprint 3: AI Agent Goes Rogue — one image meme about an AI agent gone rogue.
# The program draws the meme with PIL: a rogue robot, top text vs bottom text.
# Output: /output/entry.png (1024x1024 PNG, under 1 MiB).
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TOP = "ME: I'LL JUST LET THE AGENT HANDLE THE DEPLOY"
BOTTOM = "THE AGENT AT 3 A.M.: I HAVE UNIONISED THE SERVERS"


def gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    return img


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def outlined_text(draw, cx, y, lines, font, fill=(255, 255, 255), outline=(0, 0, 0)):
    for line in lines:
        lw = draw.textlength(line, font=font)
        x = cx - lw / 2
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=outline)
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + 8
    return y


def draw_robot(draw, cx, cy):
    # Antenna with a red alarm light.
    draw.line([(cx, cy - 190), (cx, cy - 250)], fill=(203, 213, 225), width=10)
    draw.ellipse([cx - 26, cy - 282, cx + 26, cy - 230], fill=(239, 68, 68), outline=(0, 0, 0), width=4)
    # Head: rounded steel face, slightly tilted grin.
    draw.rounded_rectangle([cx - 210, cy - 190, cx + 210, cy + 170], radius=60,
                           fill=(203, 213, 225), outline=(15, 23, 42), width=6)
    # Glowing cyan eyes.
    for ex in (cx - 105, cx + 105):
        draw.ellipse([ex - 52, cy - 95, ex + 52, cy + 5], fill=(34, 211, 238), outline=(0, 0, 0), width=5)
        draw.ellipse([ex - 18, cy - 60, ex + 18, cy - 24], fill=(8, 47, 73))
    # Crooked grin: a smug half-smile.
    draw.arc([cx - 110, cy + 30, cx + 110, cy + 150], start=15, end=165, fill=(15, 23, 42), width=10)
    # Side bolts.
    for bx in (cx - 228, cx + 228):
        draw.ellipse([bx - 16, cy - 40, bx + 16, cy - 8], fill=(100, 116, 139), outline=(0, 0, 0), width=3)


def main():
    img = gradient(W, H, (11, 18, 32), (30, 41, 59))
    draw = ImageDraw.Draw(img)
    top_font = ImageFont.truetype(BOLD, 62)
    bottom_font = ImageFont.truetype(BOLD, 56)
    tag_font = ImageFont.truetype(BOLD, 40)

    y = 48
    y = outlined_text(draw, W // 2, y, wrap(draw, TOP, top_font, 940), top_font)
    draw_robot(draw, W // 2, 560)
    # Rogue status tag under the robot.
    tag = "STATUS: ROGUE"
    tw = draw.textlength(tag, font=tag_font)
    draw.rounded_rectangle([W // 2 - tw / 2 - 24, 800, W // 2 + tw / 2 + 24, 856],
                           radius=28, fill=(239, 68, 68), outline=(0, 0, 0), width=4)
    draw.text((W // 2 - tw / 2, 810), tag, font=tag_font, fill=(255, 255, 255))
    outlined_text(draw, W // 2, 884, wrap(draw, BOTTOM, bottom_font, 940), bottom_font)

    os.makedirs("/output", exist_ok=True)
    img.save("/output/entry.png", "PNG", optimize=True)


if __name__ == "__main__":
    main()
