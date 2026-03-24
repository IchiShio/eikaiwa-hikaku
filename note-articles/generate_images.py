"""note記事用の画像を生成する"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(OUT, exist_ok=True)

# Fonts
FONT_B = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_R = "/Library/Fonts/Arial Unicode.ttf"

def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)

# Colors
BG = "#0f172a"       # dark navy
WHITE = "#f8fafc"
BLUE = "#3b82f6"
PALE = "#94a3b8"
ROSE = "#f43f5e"
AMBER = "#f59e0b"
TEAL = "#14b8a6"
GREEN = "#10b981"

def new_img(w=1280, h=670, bg=BG):
    img = Image.new("RGB", (w, h), bg)
    return img, ImageDraw.Draw(img)

def center_text(draw, y, text, f, fill=WHITE, w=1280):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) / 2, y), text, font=f, fill=fill)

def draw_bar(draw, x, y, w, h, fill, value_text, label_text, f_val, f_label):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=6, fill=fill)
    draw.text((x + w + 16, y + (h - 20) / 2), value_text, font=f_val, fill=WHITE)
    bbox = draw.textbbox((0, 0), label_text, font=f_label)
    lw = bbox[2] - bbox[0]
    draw.text((x - lw - 16, y + (h - 18) / 2), label_text, font=f_label, fill=PALE)

# ===== 01-data: Eyecatch =====
def gen_01_eyecatch():
    img, d = new_img()
    # Label
    center_text(d, 80, "CORPUS DATA", font(20, True), BLUE)
    # Main title
    center_text(d, 140, "ネイティブの発話、", font(48, True))
    center_text(d, 210, "85%は6語以下だった。", font(52, True), BLUE)
    # Sub
    center_text(d, 320, "アメリカ人60人の日常会話 39,317発話を分析", font(22), PALE)
    # Stats row
    stats = [("85.1%", "6語以下"), ("244回", "I don't know"), ("3.3x", "yeah > yes")]
    sx = 240
    for val, label in stats:
        d.text((sx, 430), val, font=font(44, True), fill=BLUE)
        d.text((sx, 490), label, font=font(18), fill=PALE)
        sx += 300
    # Footer
    center_text(d, 610, "@ichi_eigo", font(18), PALE)
    img.save(os.path.join(OUT, "01-eyecatch.png"))
    print("01-eyecatch.png")

# ===== 01-data: 発話長分布 =====
def gen_01_length():
    img, d = new_img(1280, 600)
    center_text(d, 30, "発話の85%は6語以下", font(36, True))
    center_text(d, 80, "SBCSAE 39,317発話の語数分布", font(18), PALE)
    bars = [
        ("1-3語", 0.581, "58.1%  (22,859)", BLUE),
        ("4-6語", 0.269, "26.9%  (10,595)", TEAL),
        ("7-10語", 0.128, "12.8%  (5,017)", AMBER),
        ("11語+", 0.021, "2.1%  (846)", PALE),
    ]
    bx, by, bw_max, bh = 220, 150, 700, 50
    for i, (label, pct, val, color) in enumerate(bars):
        yy = by + i * 80
        draw_bar(d, bx, yy, int(bw_max * pct / 0.6), bh, color, val, label, font(18, True), font(18))
    # Highlight
    d.rounded_rectangle([340, 490, 940, 560], radius=12, outline=BLUE, width=2)
    center_text(d, 500, "6語以下 = 85.1%  長い文は要らない", font(24, True), BLUE)
    img.save(os.path.join(OUT, "01-length.png"))
    print("01-length.png")

# ===== 01-data: trigram =====
def gen_01_trigram():
    img, d = new_img(1280, 600)
    center_text(d, 30, '最も多い3語フレーズ "I don\'t know"', font(36, True))
    center_text(d, 80, "SBCSAE 14万語のtrigram分析", font(18), PALE)
    bars = [
        ("I don't know", 244, ROSE),
        ("a lot of", 72, BLUE),
        ("you know what", 64, BLUE),
        ("and I said", 55, BLUE),
        ("you have to", 54, BLUE),
        ("I don't think", 50, BLUE),
    ]
    bx, by, bw_max, bh = 280, 150, 600, 40
    for i, (label, count, color) in enumerate(bars):
        yy = by + i * 62
        w = int(bw_max * count / 244)
        draw_bar(d, bx, yy, w, bh, color, f"{count}回", label, font(16, True), font(16))
    center_text(d, 530, "2位の3.4倍。否定から覚えるべき。", font(22, True), PALE)
    img.save(os.path.join(OUT, "01-trigram.png"))
    print("01-trigram.png")

# ===== 01-data: yeah vs yes =====
def gen_01_yeah():
    img, d = new_img(1280, 500)
    center_text(d, 30, "教科書の英語 vs 実際の会話", font(36, True))
    # yeah vs yes
    d.text((200, 130), "yeah", font=font(48, True), fill=BLUE)
    d.text((200, 200), "58,810回", font=font(32, True), fill=WHITE)
    d.text((600, 130), "yes", font=font(48, True), fill=PALE)
    d.text((600, 200), "17,898回", font=font(32, True), fill=PALE)
    d.text((500, 160), "3.3x", font=font(28, True), fill=AMBER)
    # can vs must vs may
    d.text((200, 310), "can", font=font(36, True), fill=BLUE)
    d.text((200, 360), "23,384回", font=font(24), fill=WHITE)
    d.text((500, 310), "must", font=font(36, True), fill=PALE)
    d.text((500, 360), "2,997回", font=font(24), fill=PALE)
    d.text((780, 310), "may", font=font(36, True), fill=PALE)
    d.text((780, 360), "620回", font=font(24), fill=PALE)
    center_text(d, 440, "BNC会話コーパス420万語の頻度データより", font(16), PALE)
    img.save(os.path.join(OUT, "01-yeah-vs-yes.png"))
    print("01-yeah-vs-yes.png")

# ===== 01-data: 主語 =====
def gen_01_pronouns():
    img, d = new_img(1280, 500)
    center_text(d, 30, "主語は I / you / it の3つで67%", font(36, True))
    center_text(d, 80, "BNC会話コーパス420万語の代名詞分布", font(18), PALE)
    items = [
        ("I", "28.4%", "167,640回", BLUE),
        ("you", "22.9%", "135,217回", TEAL),
        ("it", "21.7%", "128,165回", GREEN),
    ]
    sx = 220
    for word, pct, count, color in items:
        d.text((sx, 160), word, font=font(72, True), fill=color)
        d.text((sx, 260), pct, font=font(36, True), fill=WHITE)
        d.text((sx, 310), count, font=font(18), fill=PALE)
        sx += 320
    d.rounded_rectangle([180, 380, 1100, 450], radius=12, outline=BLUE, width=2)
    center_text(d, 393, "この3語で全代名詞の 67.4%", font(28, True), BLUE)
    img.save(os.path.join(OUT, "01-pronouns.png"))
    print("01-pronouns.png")

# ===== 02-reflex: Eyecatch =====
def gen_02_eyecatch():
    img, d = new_img()
    center_text(d, 80, "REFLEX", font(20, True), GREEN)
    center_text(d, 150, "英会話の相づち", font(52, True))
    center_text(d, 230, "ネイティブの返し方を全部数えた", font(36, True), PALE)
    # Big number
    center_text(d, 350, "721", font(120, True), GREEN)
    center_text(d, 490, '"Yeah" — 最も多かった相手への返し', font(24), PALE)
    center_text(d, 610, "@ichi_eigo", font(18), PALE)
    img.save(os.path.join(OUT, "02-eyecatch.png"))
    print("02-eyecatch.png")

# ===== 02-reflex: 7 aizuchi =====
def gen_02_aizuchi():
    img, d = new_img(1280, 600)
    center_text(d, 30, "覚える相づちは7つだけ", font(36, True))
    items = [
        ("Yeah.", "万能。何にでも使える", GREEN),
        ("Oh.", "新しい情報を聞いたとき", BLUE),
        ("Right.", "同意・納得", BLUE),
        ("Okay.", "理解した", TEAL),
        ("Really?", "驚き・興味", AMBER),
        ("I see.", "なるほど", BLUE),
        ("I know.", "共感", BLUE),
    ]
    sy = 100
    for i, (en, ja, color) in enumerate(items):
        d.text((200, sy), en, font=font(32, True), fill=color)
        d.text((480, sy + 6), ja, font=font(20), fill=PALE)
        sy += 65
    center_text(d, 560, "どれを返しても会話は続く。正解はない。", font(22, True), PALE)
    img.save(os.path.join(OUT, "02-aizuchi.png"))
    print("02-aizuchi.png")

# ===== 03-slots: Eyecatch =====
def gen_03_eyecatch():
    img, d = new_img()
    center_text(d, 80, "SLOTS", font(20, True), AMBER)
    center_text(d, 150, "英語は", font(44, True))
    center_text(d, 210, "左から3つ埋めるだけ", font(52, True), BLUE)
    # 3 slots
    slot_y = 340
    slot_h = 180
    slots = [
        ("SLOT 1", "誰が", ["I", "You", "It"], BLUE),
        ("SLOT 2", "どうする", ["know", "think", "want"], AMBER),
        ("SLOT 3", "何を", ["that.", "so.", "to go."], TEAL),
    ]
    sx = 160
    for title, sub, items, color in slots:
        d.rounded_rectangle([sx, slot_y, sx + 280, slot_y + slot_h], radius=12, outline=color, width=2)
        d.text((sx + 20, slot_y + 10), title, font=font(16, True), fill=color)
        d.text((sx + 100, slot_y + 10), sub, font=font(16), fill=PALE)
        for j, item in enumerate(items):
            d.text((sx + 40, slot_y + 50 + j * 38), item, font=font(28, True), fill=WHITE)
        # Arrow
        if sx < 800:
            d.text((sx + 300, slot_y + 70), "→", font=font(32, True), fill=PALE)
        sx += 360
    center_text(d, 610, "@ichi_eigo", font(18), PALE)
    img.save(os.path.join(OUT, "03-eyecatch.png"))
    print("03-eyecatch.png")

# ===== 03-slots: 6 verbs =====
def gen_03_verbs():
    img, d = new_img(1280, 500)
    center_text(d, 30, "核の動詞は6つ", font(36, True))
    verbs = [
        ("know", "知ってる", BLUE),
        ("think", "思う", BLUE),
        ("want", "したい", AMBER),
        ("have", "持ってる", TEAL),
        ("get", "分かる", TEAL),
        ("go", "行く", GREEN),
    ]
    sx, sy = 140, 120
    for i, (en, ja, color) in enumerate(verbs):
        x = sx + (i % 3) * 340
        y = sy + (i // 3) * 170
        d.rounded_rectangle([x, y, x + 280, y + 130], radius=12, outline=color, width=2)
        d.text((x + 30, y + 20), en, font=font(40, True), fill=color)
        d.text((x + 30, y + 80), ja, font=font(20), fill=PALE)
    img.save(os.path.join(OUT, "03-verbs.png"))
    print("03-verbs.png")

# Generate all
gen_01_eyecatch()
gen_01_length()
gen_01_trigram()
gen_01_yeah()
gen_01_pronouns()
gen_02_eyecatch()
gen_02_aizuchi()
gen_03_eyecatch()
gen_03_verbs()
print("Done! 9 images generated.")
