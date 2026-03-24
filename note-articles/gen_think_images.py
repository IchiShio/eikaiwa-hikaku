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
ROSE = "#f43f5e"
AMBER = "#f59e0b"
TEAL = "#14b8a6"
GREEN = "#10b981"

def center_text(draw, y, text, f, fill=WHITE, w=1280):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, y), text, font=f, fill=fill)

# ===== Eyecatch =====
def gen_eyecatch():
    img = Image.new("RGB", (1280, 670), BG)
    d = ImageDraw.Draw(img)
    center_text(d, 60, "THINK", font(20, True), ROSE)
    center_text(d, 120, "主語+動詞を", font(44, True))
    center_text(d, 180, "0.5秒で出す", font(56, True), ROSE)
    # SVO boxes
    boxes = [
        ("I", BLUE), ("think...", AMBER), ("it's good.", TEAL)
    ]
    bx = 240
    for word, color in boxes:
        d.rounded_rectangle([bx, 300, bx + 220, 390], radius=12, outline=color, width=3)
        d.text((bx + 30, 320), word, font=font(36, True), fill=color)
        if bx < 700:
            d.text((bx + 240, 325), "→", font=font(28, True), fill=PALE)
        bx += 280
    center_text(d, 430, "SVO思考トレーニング30題", font(28, True), PALE)
    center_text(d, 490, "Stivers et al. (2009): ターン交替の最頻値 0〜200ms", font(16), PALE)
    center_text(d, 520, "Jefferson (1989): 沈黙の標準最大値 約1秒", font(16), PALE)
    center_text(d, 550, "DeKeyser: 宣言的知識 → 手続き的知識 → 自動化", font(16), PALE)
    center_text(d, 610, "@ichi_eigo", font(18), PALE)
    img.save(os.path.join(OUT, "04-eyecatch.png"))
    print("04-eyecatch.png")

# ===== Turn-taking timing =====
def gen_timing():
    img = Image.new("RGB", (1280, 500), BG)
    d = ImageDraw.Draw(img)
    center_text(d, 30, "会話のターン交替タイミング", font(36, True))
    center_text(d, 80, "Stivers et al. (2009) — 10言語の日常会話を分析", font(18), PALE)
    # Timeline
    ty = 200
    d.line([(200, ty), (1080, ty)], fill=PALE, width=2)
    # Markers
    marks = [
        (200, "0ms", "話し終わり", PALE),
        (460, "200ms", "最頻値", ROSE),
        (720, "500ms", "", PALE),
        (900, "1秒", "標準最大値\n(Jefferson 1989)", AMBER),
    ]
    for x, label, desc, color in marks:
        d.line([(x, ty - 15), (x, ty + 15)], fill=color, width=3)
        d.text((x - 20, ty + 25), label, font=font(20, True), fill=color)
        if desc:
            for i, line in enumerate(desc.split('\n')):
                d.text((x - 40, ty + 55 + i * 22), line, font=font(14), fill=PALE)
    # Highlight zone
    d.rounded_rectangle([200, ty - 40, 460, ty - 20], radius=4, fill=ROSE)
    center_text(d, ty - 42, "ほとんどの応答はここ", font(14, True), WHITE, w=660)
    center_text(d, 400, "完璧な文を組み立てる時間はない → 主語+動詞を先に出す", font(22, True), WHITE)
    img.save(os.path.join(OUT, "04-timing.png"))
    print("04-timing.png")

# ===== Skill Acquisition =====
def gen_skill():
    img = Image.new("RGB", (1280, 400), BG)
    d = ImageDraw.Draw(img)
    center_text(d, 30, "スキル習得の3段階（DeKeyser）", font(36, True))
    # 3 stages
    stages = [
        ("知っている", "宣言的知識", "SVOの語順を\n理解している", BLUE),
        ("できる", "手続き的知識", "日本語→英語の\n主語+動詞が言える", AMBER),
        ("自動化", "反射で出る", "考えずに\n口から出る", GREEN),
    ]
    sx = 140
    for title, sub, desc, color in stages:
        d.rounded_rectangle([sx, 100, sx + 300, 320], radius=16, outline=color, width=3)
        d.text((sx + 30, 115), title, font=font(28, True), fill=color)
        d.text((sx + 30, 155), sub, font=font(16), fill=PALE)
        for i, line in enumerate(desc.split('\n')):
            d.text((sx + 30, 200 + i * 30), line, font=font(18), fill=WHITE)
        if sx < 800:
            d.text((sx + 320, 180), "→", font=font(36, True), fill=PALE)
        sx += 380
    center_text(d, 350, "声に出す反復練習が自動化への唯一の道", font(18, True), PALE)
    img.save(os.path.join(OUT, "04-skill.png"))
    print("04-skill.png")

# ===== 6 patterns =====
def gen_patterns():
    img = Image.new("RGB", (1280, 450), BG)
    d = ImageDraw.Draw(img)
    center_text(d, 30, "30題で使う6パターン", font(36, True))
    patterns = [
        ("I think...", "意見を言う", BLUE),
        ("I don't know...", "分からないと言う", ROSE),
        ("I want...", "したいと言う", AMBER),
        ("I have to...", "しなきゃと言う", TEAL),
        ("I don't think...", "否定する", BLUE),
        ("Do you...?", "聞き返す", GREEN),
    ]
    sx, sy = 140, 100
    for i, (en, ja, color) in enumerate(patterns):
        x = sx + (i % 3) * 340
        y = sy + (i // 3) * 150
        d.rounded_rectangle([x, y, x + 290, y + 110], radius=12, outline=color, width=2)
        d.text((x + 20, y + 15), en, font=font(24, True), fill=color)
        d.text((x + 20, y + 55), ja, font=font(18), fill=PALE)
    img.save(os.path.join(OUT, "04-patterns.png"))
    print("04-patterns.png")

gen_eyecatch()
gen_timing()
gen_skill()
gen_patterns()
print("Done! 4 images for think article.")
