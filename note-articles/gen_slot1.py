from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "images")
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_R = "/Library/Fonts/Arial Unicode.ttf"
def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)

BG = "#0f172a"
WHITE = "#f8fafc"
BLUE = "#3b82f6"
PALE = "#94a3b8"
TEAL = "#14b8a6"
GREEN = "#10b981"

def center_text(draw, y, text, f, fill=WHITE, w=1280):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, y), text, font=f, fill=fill)

img = Image.new("RGB", (1280, 500), BG)
d = ImageDraw.Draw(img)

center_text(d, 30, "SLOT 1: 主語は3つでいい", font(36, True))
center_text(d, 80, "この3語で全代名詞の 67.4%", font(20), PALE)

items = [
    ("I", "自分のこと", "28.4%", BLUE),
    ("you", "相手のこと", "22.9%", TEAL),
    ("it", "それ以外", "21.7%", GREEN),
]

sx = 180
for word, ja, pct, color in items:
    # Card
    d.rounded_rectangle([sx, 140, sx + 260, 370], radius=16, outline=color, width=3)
    d.text((sx + 40, 170), word, font=font(72, True), fill=color)
    d.text((sx + 40, 270), pct, font=font(32, True), fill=WHITE)
    d.text((sx + 40, 320), ja, font=font(20), fill=PALE)
    sx += 310

center_text(d, 420, "BNC会話コーパス420万語の代名詞分布", font(16), PALE)

img.save(os.path.join(OUT, "03-slot1.png"))
print("03-slot1.png created")
