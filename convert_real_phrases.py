#!/usr/bin/env python3
"""
native-real の real-phrases Markdown を eikaiwa-hikaku の HTML に変換するスクリプト。
Usage: python3 convert_real_phrases.py
"""
import os
import re
import html as htmllib
from pathlib import Path

SOURCE_DIR = Path("/tmp/native-real/content/real-phrases")
OUTPUT_DIR = Path("/Users/yusuke/projects/claude/eikaiwa-hikaku/real-phrases")
SITE_NAME = "英語学習サービス比較ナビ"
SITE_URL = "https://native-real.com"
GTM_ID = "GTM-PS9R9844"

# ─────────────────── 共通パーツ ───────────────────

NAV_ITEMS = [
    ('/', 'ランキング'),
    ('/articles/', '学習コラム'),
    ('/real-phrases/', 'フレーズ集'),
    ('/listening/', 'リスニングクイズ'),
]

def build_header(active_path='/real-phrases/'):
    nav_links = ''.join(
        f'<a href="{url}"{" class=\"active\"" if url == active_path else ""}>{label}</a>'
        for url, label in NAV_ITEMS
    )
    mobile_links = ''.join(f'<a href="{url}">{label}</a>' for url, label in NAV_ITEMS)
    hamburger = 'document.querySelector(\'.hamburger\').classList.toggle(\'active\');document.querySelector(\'.mobile-nav-overlay\').classList.toggle(\'active\');document.body.style.overflow=document.querySelector(\'.mobile-nav-overlay\').classList.contains(\'active\')?\'hidden\':\'\';'
    mobile_close = 'if(event.target===this||event.target.tagName===\'A\'){this.classList.remove(\'active\');document.querySelector(\'.hamburger\').classList.remove(\'active\');document.body.style.overflow=\'\'}'
    return f'''<header class="site-header">
  <div class="container">
    <a href="/" class="logo">{SITE_NAME}</a>
    <nav>{nav_links}</nav>
    <button class="hamburger" aria-label="メニューを開く" onclick="{hamburger}">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="mobile-nav-overlay" onclick="{mobile_close}">
  {mobile_links}
</div>'''

FOOTER_HTML = '''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>英語学習サービス比較ナビ</h4>
        <p>プロが選ぶオンライン英会話・英語アプリ徹底比較</p>
        <p style="margin-top:12px;">※当サイトはアフィリエイトリンクを含みます。</p>
        <div class="footer-owner">
          <span class="footer-owner-label">運営者</span>
          <a href="https://x.com/ichi_eigo" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>@ichi_eigo</a>
        </div>
      </div>
      <div>
        <h4>サービス一覧</h4>
        <ul>
          <li><a href="/services/dmm-eikaiwa/">DMM英会話</a></li>
          <li><a href="/services/rarejob/">レアジョブ英会話</a></li>
          <li><a href="/services/nativecamp/">ネイティブキャンプ</a></li>
          <li><a href="/services/cambly/">Cambly</a></li>
          <li><a href="/services/bizmates/">Bizmates</a></li>
          <li><a href="/services/progrit/">プログリット</a></li>
          <li><a href="/services/italki/">italki</a></li>
        </ul>
      </div>
      <div>
        <h4>コンテンツ</h4>
        <ul>
          <li><a href="/articles/">学習コラム一覧</a></li>
          <li><a href="/real-phrases/">フレーズ集</a></li>
          <li><a href="/listening/">リスニングクイズ</a></li>
          <li><a href="/">ランキングTOP</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 英語学習サービス比較ナビ. All rights reserved.</p>
    </div>
  </div>
</footer>'''

BASE_CSS = ''':root{--primary:#2563eb;--primary-light:#3b82f6;--primary-dark:#1d4ed8;--primary-pale:#eff6ff;--accent:#10b981;--accent-dark:#059669;--accent-pale:#ecfdf5;--text:#111827;--text-muted:#6b7280;--bg:#ffffff;--bg-gray:#f9fafb;--border:#e5e7eb;--shadow:0 1px 3px rgba(0,0,0,0.06),0 2px 8px rgba(0,0,0,0.04);--shadow-md:0 4px 16px rgba(0,0,0,0.08),0 8px 24px rgba(0,0,0,0.05);--radius:10px;--radius-lg:14px;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:"Inter","Noto Sans JP",-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic UI",sans-serif;letter-spacing:0.01em;font-size:16px;line-height:1.9;color:var(--text);background:var(--bg);}
a{color:var(--primary);}a:hover{color:var(--primary-light);}
img{max-width:100%;height:auto;}
.container{max-width:1100px;margin:0 auto;padding:0 20px;}
.site-header{background:#ffffff;color:var(--text);padding:14px 0;position:sticky;top:0;z-index:100;box-shadow:0 1px 0 var(--border);}
.site-header .container{display:flex;align-items:center;justify-content:space-between;}
.site-header .logo{font-size:1.0rem;font-weight:700;color:var(--text);text-decoration:none;letter-spacing:0.03em;}
.site-header nav a{color:var(--text-muted);text-decoration:none;margin-left:24px;font-size:0.88rem;border-bottom:2px solid transparent;padding-bottom:2px;transition:color 0.2s,border-color 0.2s;}
.site-header nav a:hover,.site-header nav a.active{color:var(--text);border-color:var(--primary);}
.hamburger{display:none;background:none;border:none;cursor:pointer;padding:4px;width:36px;height:36px;position:relative;z-index:102;}
.hamburger span{display:block;width:22px;height:2px;background:var(--text);margin:5px auto;border-radius:2px;transition:transform 0.3s,opacity 0.3s;}
.hamburger.active span:nth-child(1){transform:translateY(7px) rotate(45deg);}
.hamburger.active span:nth-child(2){opacity:0;}
.hamburger.active span:nth-child(3){transform:translateY(-7px) rotate(-45deg);}
.mobile-nav-overlay{display:none;position:fixed;inset:0;background:rgba(17,24,39,0.95);z-index:101;flex-direction:column;align-items:center;justify-content:center;gap:24px;}
.mobile-nav-overlay.active{display:flex;}
.mobile-nav-overlay a{color:white;text-decoration:none;font-size:1.2rem;font-weight:600;padding:12px 24px;border-radius:var(--radius);transition:background 0.2s;}
.mobile-nav-overlay a:hover{background:rgba(255,255,255,0.1);}
.breadcrumb{padding:12px 0;font-size:0.82rem;color:var(--text-muted);}
.breadcrumb a{color:var(--text-muted);text-decoration:none;}
.breadcrumb a:hover{color:var(--primary);}
.breadcrumb span{margin:0 6px;color:var(--border);}
.article-layout{display:grid;grid-template-columns:1fr 300px;gap:40px;padding:40px 0;}
.article-content{min-width:0;}
.article-content h1{font-size:1.55rem;line-height:1.45;margin-bottom:20px;font-weight:800;}
.article-content h2{font-size:1.25rem;font-weight:700;margin:40px 0 16px;padding:13px 18px;background:var(--bg-gray);border-left:4px solid var(--primary);border-radius:0 var(--radius) var(--radius) 0;color:var(--text);}
.article-content h3{font-size:1.08rem;font-weight:700;margin:28px 0 12px;color:var(--primary);padding-left:12px;border-left:3px solid var(--accent);}
.article-content p{margin-bottom:16px;}
.article-content ul,.article-content ol{margin:16px 0 16px 24px;}
.article-content li{margin-bottom:8px;}
.toc{background:var(--bg-gray);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:0 var(--radius-lg) var(--radius-lg) 0;padding:20px 24px;margin:24px 0 32px;}
.toc h4{font-size:0.95rem;font-weight:700;margin-bottom:12px;color:var(--accent-dark);}
.toc ol{margin-left:20px;}
.toc li{margin-bottom:6px;font-size:0.88rem;}
.toc a{color:var(--text-muted);text-decoration:none;}
.toc a:hover{color:var(--primary);}
.sidebar-widget{background:white;border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;margin-bottom:20px;box-shadow:var(--shadow);}
.sidebar-widget h4{font-size:0.95rem;font-weight:700;margin-bottom:14px;color:var(--text);padding-bottom:10px;border-bottom:2px solid var(--bg-gray);}
.sidebar-service-list{display:flex;flex-direction:column;gap:10px;}
.sidebar-service-item a{font-size:0.88rem;text-decoration:none;color:var(--text);}
.sidebar-service-item a:hover{color:var(--primary);}
.site-footer{background:#2c2520;color:rgba(255,255,255,0.65);padding:48px 0 24px;margin-top:72px;font-size:0.88rem;}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:32px;margin-bottom:32px;}
.site-footer h4{color:rgba(255,255,255,0.9);font-size:0.95rem;margin-bottom:14px;}
.site-footer ul{list-style:none;}
.site-footer li{margin-bottom:9px;}
.site-footer a{color:rgba(255,255,255,0.6);text-decoration:none;transition:color 0.2s;}
.site-footer a:hover{color:#f0a080;}
.footer-bottom{border-top:1px solid rgba(255,255,255,0.1);padding-top:20px;text-align:center;font-size:0.78rem;color:rgba(255,255,255,0.4);}
.footer-owner{margin-top:16px;display:flex;align-items:center;gap:10px;}
.footer-owner-label{font-size:0.78rem;color:rgba(255,255,255,0.4);}
.footer-owner a{color:rgba(255,255,255,0.85);text-decoration:none;font-weight:600;display:inline-flex;align-items:center;gap:6px;transition:color 0.2s;}
.footer-owner a:hover{color:#f0a080;}
.footer-owner svg{width:15px;height:15px;fill:currentColor;}
/* フレーズ集専用スタイル */
.phrase-summary{background:linear-gradient(135deg,var(--accent-pale),#f0fdf4);border:2px solid var(--accent);border-radius:var(--radius-lg);padding:20px 24px;font-size:1.05rem;font-weight:600;margin:16px 0 24px;color:var(--text);}
.scenario-block{background:var(--bg-gray);border-radius:var(--radius-lg);padding:20px 24px;margin:20px 0;border:1px solid var(--border);}
.scenario-title{font-size:0.95rem;font-weight:700;color:var(--text-muted);margin-bottom:14px;padding-left:0;border-left:none;}
.dialogue{margin:0 0 12px;}
.dialogue-line{display:grid;grid-template-columns:28px 1fr;gap:8px;margin-bottom:8px;font-size:0.95rem;}
.speaker{font-weight:700;color:var(--primary);}
.speech{color:var(--text);}
.ja-translation{background:white;border-radius:var(--radius);padding:14px 16px;margin-top:12px;font-size:0.9rem;color:var(--text-muted);border-left:3px solid var(--border);}
.before-after{margin:20px 0;}
.ba-bad{background:#fef2f2;border:1px solid #fecaca;border-radius:var(--radius);padding:14px 18px;margin-bottom:10px;font-size:0.95rem;}
.ba-good{background:var(--accent-pale);border:1px solid #6ee7b7;border-radius:var(--radius);padding:14px 18px;margin-bottom:10px;font-size:0.95rem;}
.ba-note{color:var(--text-muted);font-size:0.9rem;padding-left:8px;border-left:3px solid var(--border);margin:10px 0 20px;}
.diff-block{border-bottom:1px solid var(--border);padding-bottom:20px;margin-bottom:20px;}
.diff-block:last-child{border-bottom:none;}
.diff-title{font-size:1.0rem;font-weight:700;color:var(--text);margin-bottom:8px;padding-left:0;border-left:none;}
.usage-ok{background:var(--accent-pale);border:1px solid #6ee7b7;border-radius:var(--radius);padding:14px 18px;margin-bottom:10px;}
.usage-ng{background:#fef2f2;border:1px solid #fecaca;border-radius:var(--radius);padding:14px 18px;margin-bottom:10px;}
.usage-note{color:var(--text-muted);font-size:0.9rem;padding-left:8px;border-left:3px solid var(--border);margin:10px 0;}
.challenge-box{background:linear-gradient(135deg,#faf5ff,#f3e8ff);border:2px solid #c084fc;border-radius:var(--radius-lg);padding:24px;margin:24px 0;}
.challenge-prompt{font-weight:700;font-size:1.0rem;margin-bottom:12px;}
.challenge-sentence{font-size:1.05rem;color:var(--text);background:white;border-radius:var(--radius);padding:12px 16px;margin-bottom:12px;}
.challenge-hint{font-size:0.9rem;color:var(--text-muted);margin-bottom:12px;}
.challenge-cta a{color:var(--primary);font-size:0.9rem;}
.related-phrases ul{list-style:none;padding:0;margin:0;}
.related-phrases li{padding:8px 0;border-bottom:1px solid var(--border);font-size:0.93rem;}
.related-phrases li:last-child{border-bottom:none;}
@media(max-width:1024px){.article-layout{grid-template-columns:1fr;} .sidebar{display:none;}}
@media(max-width:768px){.site-header nav{display:none;} .hamburger{display:block;} .article-content h1{font-size:1.3rem;} .footer-grid{grid-template-columns:1fr;}}'''

# ─────────────────── パーサー ───────────────────

def parse_meta(text: str) -> dict:
    meta = {}
    m = re.search(r'## 1\. メタ情報\n(.*?)(?=\n---|\n## 2\.)', text, re.DOTALL)
    if not m:
        return meta
    s = m.group(1)
    for key, pat in [
        ('slug', r'\*\*slug\*\*: (.+)'),
        ('title', r'\*\*title タグ\*\*: "?(.+?)"?\s*$'),
        ('meta_description', r'\*\*meta description\*\*: (.+)'),
        ('h1', r'\*\*H1\*\*: (.+)'),
        ('primary_keyword', r'\*\*primary keyword\*\*: (.+)'),
        ('secondary_keywords', r'\*\*secondary keywords\*\*: (.+)'),
    ]:
        mm = re.search(pat, s, re.MULTILINE)
        if mm:
            meta[key] = mm.group(1).strip().strip('"')
    return meta

def extract_json_ld(text: str) -> str:
    m = re.search(r'## 3\. 構造化データ.*?```json\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip().replace('Native Real', SITE_NAME)
    return ''

def extract_body(text: str) -> str:
    m = re.search(r'## 2\. 本文\n(.*?)(?=\n## 3\.|\Z)', text, re.DOTALL)
    return m.group(1).strip() if m else ''

def parse_body_sections(body: str) -> list:
    """## で区切ってセクションリストを返す [(header, content), ...]"""
    sections = []
    parts = re.split(r'\n## ', body)
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        header = lines[0].strip().lstrip('#').strip()
        content = lines[1].strip() if len(lines) > 1 else ''
        sections.append((header, content))
    return sections

# ─────────────────── セクション変換 ───────────────────

def esc(s: str) -> str:
    return htmllib.escape(s)

def convert_section(header: str, content: str, sec_id: str) -> str:
    h = f'<h2 id="{sec_id}">{esc(header)}</h2>\n'

    if '一言で言うと' in header:
        return h + f'<div class="phrase-summary">{esc(content)}</div>\n'
    elif 'どんな場面で使う' in header:
        return h + convert_paragraphs(content)
    elif 'リアル例文' in header:
        return h + convert_examples(content)
    elif 'Before' in header and 'After' in header:
        return h + convert_before_after(content)
    elif '似た表現' in header:
        return h + convert_differences(content)
    elif '使うときの注意' in header:
        return h + convert_usage_notes(content)
    elif '瞬間英作文' in header:
        return h + convert_challenge(content)
    elif '関連表現' in header:
        return h + convert_related(content)
    else:
        return h + convert_paragraphs(content)

def convert_paragraphs(text: str) -> str:
    parts = []
    buf = []
    for line in text.split('\n'):
        if line.strip():
            buf.append(esc(line.strip()))
        else:
            if buf:
                parts.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
    if buf:
        parts.append('<p>' + ' '.join(buf) + '</p>')
    return '\n'.join(parts) + '\n'

def convert_examples(text: str) -> str:
    """📍 シナリオブロックを変換"""
    parts = []
    # 📍 で分割
    scenarios = re.split(r'(?=📍)', text)
    for sc in scenarios:
        sc = sc.strip()
        if not sc:
            continue
        if sc.startswith('📍'):
            nl = sc.find('\n')
            title = sc[1:nl].strip() if nl > 0 else sc[1:].strip()
            rest = sc[nl:].strip() if nl > 0 else ''

            # --- 区切りで複数のやりとりがある場合も含めて処理
            # （和訳）で分割して英語/日本語を分ける
            en_ja_split = re.split(r'\n\n?（和訳）\n', rest)
            en_block = en_ja_split[0].strip() if en_ja_split else ''
            ja_block = en_ja_split[1].strip() if len(en_ja_split) > 1 else ''

            # 末尾の --- は除去
            en_block = re.sub(r'\n---\s*$', '', en_block).strip()
            ja_block = re.sub(r'\n---\s*$', '', ja_block).strip()

            parts.append('<div class="scenario-block">')
            parts.append(f'<p class="scenario-title">📍 {esc(title)}</p>')
            parts.append('<div class="dialogue">')
            parts.append(render_dialogue(en_block))
            parts.append('</div>')
            if ja_block:
                parts.append('<div class="ja-translation">')
                parts.append(render_dialogue(ja_block))
                parts.append('</div>')
            parts.append('</div>')
        else:
            parts.append(convert_paragraphs(sc))
    return '\n'.join(parts) + '\n'

def render_dialogue(text: str) -> str:
    lines_html = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^([A-Z]): (.+)$', line)
        if m:
            spk = m.group(1)
            speech = m.group(2).strip()
            lines_html.append(
                f'<div class="dialogue-line"><span class="speaker">{esc(spk)}:</span>'
                f' <span class="speech">{esc(speech)}</span></div>'
            )
        else:
            lines_html.append(f'<p>{esc(line)}</p>')
    return '\n'.join(lines_html)

def convert_before_after(text: str) -> str:
    parts = ['<div class="before-after">']
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('❌'):
            parts.append(f'<div class="ba-bad">❌ {esc(line[1:].strip())}</div>')
        elif line.startswith('✅'):
            parts.append(f'<div class="ba-good">✅ {esc(line[1:].strip())}</div>')
        elif line.startswith('→'):
            parts.append(f'<p class="ba-note">{esc(line[1:].strip())}</p>')
        else:
            parts.append(f'<p>{esc(line)}</p>')
    parts.append('</div>')
    return '\n'.join(parts) + '\n'

def convert_differences(text: str) -> str:
    parts = ['<div class="differences">']
    # "XXX" との違い: ... のパターンで分割
    blocks = re.split(r'\n(?="[^"]*?" との違い)', text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        m = re.match(r'"([^"]+)" との違い: (.+)', block, re.DOTALL)
        if m:
            phrase = m.group(1)
            explanation = m.group(2).strip()
            parts.append('<div class="diff-block">')
            parts.append(f'<p class="diff-title">"{esc(phrase)}" との違い</p>')
            parts.append(convert_paragraphs(explanation))
            parts.append('</div>')
        else:
            parts.append(convert_paragraphs(block))
    parts.append('</div>')
    return '\n'.join(parts) + '\n'

def convert_usage_notes(text: str) -> str:
    parts = ['<div class="usage-notes">']
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('🟢'):
            parts.append(f'<div class="usage-ok">🟢 {esc(line[1:].strip())}</div>')
        elif line.startswith('🔴'):
            parts.append(f'<div class="usage-ng">🔴 {esc(line[1:].strip())}</div>')
        elif line.startswith('→'):
            parts.append(f'<p class="usage-note">{esc(line[1:].strip())}</p>')
        else:
            parts.append(f'<p>{esc(line)}</p>')
    parts.append('</div>')
    return '\n'.join(parts) + '\n'

def convert_challenge(text: str) -> str:
    parts = ['<div class="challenge-box">']
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('💬'):
            parts.append(f'<p class="challenge-prompt">💬 {esc(line[1:].strip())}</p>')
        elif line.startswith('「') and line.endswith('」'):
            parts.append(f'<p class="challenge-sentence">{esc(line)}</p>')
        elif line.startswith('→ ヒント'):
            parts.append(f'<p class="challenge-hint">{esc(line[1:].strip())}</p>')
        elif 'もっと練習' in line:
            parts.append('<p class="challenge-cta"><a href="/listening/">→ もっと練習したい？リスニングクイズで毎日トレーニング</a></p>')
        else:
            parts.append(f'<p>{esc(line)}</p>')
    parts.append('</div>')
    return '\n'.join(parts) + '\n'

def convert_related(text: str) -> str:
    parts = ['<div class="related-phrases"><ul>']
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('この表現と') or line.startswith('このカテゴリ'):
            continue  # 見出し行はスキップ
        if line.startswith('-'):
            line = line[1:].strip()
        # /real-phrases/ リンクのみ変換（/blog/ はスキップ）
        m = re.match(r'"?([^"→]+?)"? の意味・使い方 → (/real-phrases/[^\s]+)', line)
        if m:
            phrase_text = m.group(1).strip().strip('"')
            url = m.group(2).rstrip('/') + '/'
            parts.append(f'<li><a href="{url}">{esc(phrase_text)} の意味・使い方</a></li>')
        elif '/blog/' in line:
            pass  # ブログリンクは今回除外
        elif line:
            parts.append(f'<li>{esc(line)}</li>')
    parts.append('</ul></div>')
    return '\n'.join(parts) + '\n'

# ─────────────────── HTML ページ生成 ───────────────────

def generate_page(meta: dict, json_ld: str, body: str) -> str:
    slug = meta.get('slug', '')
    title = meta.get('title', '').replace('- Native Real', f'| {SITE_NAME}')
    if f'| {SITE_NAME}' not in title:
        title = title + f' | {SITE_NAME}'
    desc = meta.get('meta_description', '')
    h1 = meta.get('h1', slug)
    canonical = f'{SITE_URL}/real-phrases/{slug}/'

    # 本文セクション → HTML + TOC
    sections = parse_body_sections(body)
    toc_items = []
    body_html_parts = []
    for i, (header, content) in enumerate(sections, 1):
        sec_id = f'sec-{i}'
        toc_items.append((sec_id, header))
        body_html_parts.append(convert_section(header, content, sec_id))

    # 目次
    toc_html = '<div class="toc"><h4>目次</h4><ol>'
    for sec_id, header in toc_items:
        toc_html += f'<li><a href="#{sec_id}">{esc(header)}</a></li>'
    toc_html += '</ol></div>'

    body_html = '\n'.join(body_html_parts)

    json_ld_tag = f'<script type="application/ld+json">\n{json_ld}\n</script>' if json_ld else ''

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google Tag Manager -->
  <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
  new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
  }})(window,document,'script','dataLayer','{GTM_ID}');</script>
  <!-- End Google Tag Manager -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{esc(h1)}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta name="twitter:card" content="summary">
  {json_ld_tag}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
{BASE_CSS}
  </style>
</head>
<body>
  <!-- Google Tag Manager (noscript) -->
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
  height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
  <!-- End Google Tag Manager (noscript) -->
{build_header('/real-phrases/')}
<div class="breadcrumb container">
  <a href="/">ホーム</a><span>›</span>
  <a href="/real-phrases/">フレーズ集</a><span>›</span>
  {esc(h1)}
</div>
<div class="container">
  <div class="article-layout">
    <main class="article-content">
      {toc_html}
      <h1>{esc(h1)}</h1>
      {body_html}
      <div class="disclaimer">
        ※当サイトはアフィリエイトリンクを含みます。サービスの詳細は各社公式サイトでご確認ください。
      </div>
    </main>
    <aside class="sidebar">
      <div class="sidebar-widget">
        <h4>🎧 リスニングで使えるようにしよう</h4>
        <p style="font-size:0.88rem;color:var(--text-muted);margin-bottom:14px;">フレーズを覚えたら、実際の音声で定着させよう。</p>
        <a href="/listening/" style="display:block;background:var(--accent);color:white;text-align:center;padding:10px;border-radius:var(--radius);text-decoration:none;font-weight:700;font-size:0.9rem;">リスニングクイズで練習する →</a>
      </div>
      <div class="sidebar-widget">
        <h4>フレーズ集一覧</h4>
        <p style="font-size:0.88rem;color:var(--text-muted);">100のネイティブ英語フレーズを一覧で確認できます。</p>
        <a href="/real-phrases/" style="display:block;margin-top:12px;color:var(--primary);font-size:0.88rem;text-decoration:none;font-weight:600;">→ フレーズ集トップへ</a>
      </div>
    </aside>
  </div>
</div>
{FOOTER_HTML}
</body>
</html>'''

# ─────────────────── インデックスページ生成 ───────────────────

def generate_index(all_meta: list) -> str:
    cards = ''
    for meta in sorted(all_meta, key=lambda m: m.get('slug', '')):
        slug = meta.get('slug', '')
        h1 = meta.get('h1', slug)
        desc = meta.get('meta_description', '')[:80] + '…' if meta.get('meta_description', '') else ''
        keyword = meta.get('primary_keyword', '')
        cards += f'''<a href="/real-phrases/{slug}/" class="phrase-card">
  <div class="phrase-card-keyword">{esc(keyword)}</div>
  <div class="phrase-card-title">{esc(h1)}</div>
  <div class="phrase-card-desc">{esc(desc)}</div>
</a>
'''

    index_css = '''
.phrases-hero{background:var(--bg-gray);border-bottom:1px solid var(--border);padding:52px 0 44px;text-align:center;}
.phrases-hero h1{font-size:1.9rem;font-weight:800;margin-bottom:14px;}
.phrases-hero p{color:var(--text-muted);font-size:1.0rem;max-width:560px;margin:0 auto;}
.phrases-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:40px 0;}
.phrase-card{display:block;background:white;border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px 20px;text-decoration:none;color:var(--text);transition:box-shadow 0.2s,transform 0.15s;box-shadow:var(--shadow);}
.phrase-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
.phrase-card-keyword{font-size:0.78rem;font-weight:700;color:var(--accent-dark);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;}
.phrase-card-title{font-size:0.97rem;font-weight:700;margin-bottom:6px;color:var(--text);}
.phrase-card-desc{font-size:0.82rem;color:var(--text-muted);line-height:1.6;}
@media(max-width:768px){.phrases-grid{grid-template-columns:1fr;}}
@media(min-width:640px) and (max-width:1023px){.phrases-grid{grid-template-columns:repeat(2,1fr);}}
'''
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google Tag Manager -->
  <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
  new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
  }})(window,document,'script','dataLayer','{GTM_ID}');</script>
  <!-- End Google Tag Manager -->
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <title>ネイティブ英語フレーズ集100選 | {SITE_NAME}</title>
  <meta name="description" content="ネイティブが日常・ビジネスで使う英語フレーズ100選。「Heads up」「My bad」「No worries」など、日本の教科書には出てこないリアルな表現を例文・解説付きで紹介。">
  <link rel="canonical" href="{SITE_URL}/real-phrases/">
  <meta property="og:title" content="ネイティブ英語フレーズ集100選">
  <meta property="og:description" content="ネイティブが日常・ビジネスで使う英語フレーズ100選。リアルな例文・類似表現との違いを解説。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/real-phrases/">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta name="twitter:card" content="summary">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
{BASE_CSS}
{index_css}
  </style>
</head>
<body>
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
  height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
{build_header('/real-phrases/')}
<section class="phrases-hero">
  <div class="container">
    <h1>ネイティブ英語フレーズ集</h1>
    <p>日常・ビジネスで使われる100のリアルな英語表現。例文・使い方・類似表現との違いを徹底解説。</p>
  </div>
</section>
<div class="container">
  <div class="phrases-grid">
    {cards}
  </div>
</div>
{FOOTER_HTML}
</body>
</html>'''

# ─────────────────── メイン処理 ───────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_files = sorted(SOURCE_DIR.glob('*.md'))
    print(f"変換対象: {len(md_files)} ファイル")

    all_meta = []
    errors = []

    for md_path in md_files:
        try:
            text = md_path.read_text(encoding='utf-8')
            meta = parse_meta(text)
            slug = meta.get('slug')
            if not slug:
                print(f"  [SKIP] slug なし: {md_path.name}")
                continue

            json_ld = extract_json_ld(text)
            body = extract_body(text)
            html_content = generate_page(meta, json_ld, body)

            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'index.html').write_text(html_content, encoding='utf-8')
            all_meta.append(meta)
            print(f"  ✅ {slug}/index.html")
        except Exception as e:
            errors.append((md_path.name, str(e)))
            print(f"  ❌ {md_path.name}: {e}")

    # インデックスページ
    index_html = generate_index(all_meta)
    (OUTPUT_DIR / 'index.html').write_text(index_html, encoding='utf-8')
    print(f"\n✅ インデックスページ: real-phrases/index.html")
    print(f"✅ 完了: {len(all_meta)} ページ生成")
    if errors:
        print(f"❌ エラー {len(errors)} 件:")
        for name, err in errors:
            print(f"  {name}: {err}")

if __name__ == '__main__':
    main()
