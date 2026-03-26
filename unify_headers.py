#!/usr/bin/env python3
"""
unify_headers.py - 全ページのヘッダーを新ドロップダウン形式に統一する

デスクトップ: ListenUp / 学ぶ▼ / 読む▼ / ランキング / My Progress (5項目)
モバイル: セクション分けしたフルスクリーンメニュー
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent

# 除外パス（独自UIを持つ or リダイレクトのみ）
EXCLUDE = {
    ROOT / "listening" / "index.html",
    ROOT / "orbit" / "index.html",
}

EXCLUDE_DIRS = {"orbit", ".git"}

# ── ナビゲーション定義 ──

DIRECT_LINKS = [
    ('/', 'ListenUp'),
]

DROPDOWN_LEARN = {
    'label': '学ぶ',
    'items': [
        ('/grammar/', '文法クイズ'),
        ('/words/', 'WordsUp'),
        ('/kioku-shinai/', '記憶しない英単語'),
    ],
}

DROPDOWN_READ = {
    'label': '読む',
    'items': [
        ('/articles/', '学習コラム'),
        ('/real-phrases/', 'フレーズ集'),
        ('/prompts/', 'AIプロンプト'),
    ],
}

DIRECT_LINKS_END = [
    ('/ranking/', 'ランキング'),
    ('/my/', 'My Progress'),
]

# 全リンクのフラットリスト（active判定用）
ALL_LINKS = (
    DIRECT_LINKS
    + DROPDOWN_LEARN['items']
    + DROPDOWN_READ['items']
    + DIRECT_LINKS_END
)

SVG_LOGO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>'

CHEVRON_SVG = '<svg class="dd-chevron" width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 3.5L5 6.5L7.5 3.5"/></svg>'


def detect_active_page(filepath):
    """ファイルパスからアクティブなナビリンクのhrefを判定"""
    rel = filepath.relative_to(ROOT)
    parts = rel.parts
    if len(parts) >= 1:
        section = parts[0]
        for href, label in ALL_LINKS:
            if href.strip('/') == section:
                return href
    return None


def _active(href, active_href):
    return ' class="active"' if href == active_href else ''


def _dropdown_active(items, active_href):
    """ドロップダウン内にactiveがあればTrueを返す"""
    return any(href == active_href for href, _ in items)


def build_header(active_href):
    """新ドロップダウン形式のヘッダーHTMLを生成"""

    # ── デスクトップナビ ──
    nav_parts = []

    # 直リンク（ListenUp）
    for href, label in DIRECT_LINKS:
        nav_parts.append(f'      <a href="{href}"{_active(href, active_href)}>{label}</a>')

    # 学ぶドロップダウン
    learn_active = _dropdown_active(DROPDOWN_LEARN['items'], active_href)
    learn_cls = ' active' if learn_active else ''
    learn_items = '\n'.join(
        f'          <a href="{href}"{_active(href, active_href)}>{label}</a>'
        for href, label in DROPDOWN_LEARN['items']
    )
    nav_parts.append(f'''      <div class="nav-dd">
        <button class="nav-dd-trigger{learn_cls}" type="button">{DROPDOWN_LEARN['label']}{CHEVRON_SVG}</button>
        <div class="nav-dd-menu">
{learn_items}
        </div>
      </div>''')

    # 読むドロップダウン
    read_active = _dropdown_active(DROPDOWN_READ['items'], active_href)
    read_cls = ' active' if read_active else ''
    read_items = '\n'.join(
        f'          <a href="{href}"{_active(href, active_href)}>{label}</a>'
        for href, label in DROPDOWN_READ['items']
    )
    nav_parts.append(f'''      <div class="nav-dd">
        <button class="nav-dd-trigger{read_cls}" type="button">{DROPDOWN_READ['label']}{CHEVRON_SVG}</button>
        <div class="nav-dd-menu">
{read_items}
        </div>
      </div>''')

    # 直リンク後半（ランキング、My Progress）
    for href, label in DIRECT_LINKS_END:
        nav_parts.append(f'      <a href="{href}"{_active(href, active_href)}>{label}</a>')

    nav_html = '\n'.join(nav_parts)

    # ── モバイルナビ ──
    mobile_parts = []
    for href, label in DIRECT_LINKS:
        mobile_parts.append(f'  <a href="{href}"{_active(href, active_href)}>{label}</a>')

    mobile_parts.append('  <div class="mobile-nav-label">学ぶ</div>')
    for href, label in DROPDOWN_LEARN['items']:
        mobile_parts.append(f'  <a href="{href}"{_active(href, active_href)}>{label}</a>')

    mobile_parts.append('  <div class="mobile-nav-label">読む</div>')
    for href, label in DROPDOWN_READ['items']:
        mobile_parts.append(f'  <a href="{href}"{_active(href, active_href)}>{label}</a>')

    mobile_parts.append('  <div class="mobile-nav-label"></div>')
    for href, label in DIRECT_LINKS_END:
        mobile_parts.append(f'  <a href="{href}"{_active(href, active_href)}>{label}</a>')

    mobile_html = '\n'.join(mobile_parts)

    return f'''<header class="site-header" id="siteHeader">
  <div class="site-header-inner">
    <a href="/" class="site-header-logo">{SVG_LOGO}native-real</a>
    <nav class="site-header-nav">
{nav_html}
    </nav>
    <button class="site-hamburger" id="siteHamburger" aria-label="メニューを開く">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="site-mobile-nav" id="siteMobileNav">
{mobile_html}
</div>'''


# ── CSS ──
HEADER_CSS = """/* ── UNIFIED HEADER ── */
    .site-header {
      position: fixed; top: 0; left: 0; right: 0; z-index: 300;
      background: rgba(255,255,255,0.92); backdrop-filter: blur(16px) saturate(180%);
      -webkit-backdrop-filter: blur(16px) saturate(180%);
      border-bottom: 1px solid rgba(0,0,0,0.06); padding: 10px 0;
      transition: padding 0.3s ease, box-shadow 0.3s ease;
    }
    .site-header.scrolled { padding: 6px 0; box-shadow: 0 1px 12px rgba(0,0,0,0.08); }
    .site-header-inner { max-width: 1100px; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; }
    .site-header-logo { font-size: 15px; font-weight: 800; color: #111; text-decoration: none; white-space: nowrap; display: flex; align-items: center; gap: 7px; }
    .site-header-logo svg { width: 18px; height: 18px; color: #F5A623; }
    .site-header-nav { display: flex; align-items: center; gap: 2px; }
    .site-header-nav > a { font-size: 13px; font-weight: 500; color: rgba(0,0,0,0.6); text-decoration: none; padding: 7px 12px; border-radius: 10px; transition: all 0.2s ease; white-space: nowrap; position: relative; }
    .site-header-nav > a:hover { color: #111; background: rgba(0,0,0,0.04); }
    .site-header-nav > a.active { color: #F5A623; font-weight: 700; }
    .site-header-nav > a.active::after { content: ''; position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%); width: 16px; height: 2px; border-radius: 1px; background: #F5A623; }
    /* Dropdown */
    .nav-dd { position: relative; }
    .nav-dd-trigger { font-size: 13px; font-weight: 500; color: rgba(0,0,0,0.6); background: none; border: none; cursor: pointer; padding: 7px 12px; border-radius: 10px; transition: all 0.2s ease; white-space: nowrap; display: flex; align-items: center; gap: 3px; font-family: inherit; }
    .nav-dd-trigger:hover { color: #111; background: rgba(0,0,0,0.04); }
    .nav-dd-trigger.active { color: #F5A623; font-weight: 700; }
    .dd-chevron { transition: transform 0.2s ease; flex-shrink: 0; }
    .nav-dd:hover .dd-chevron, .nav-dd.open .dd-chevron { transform: rotate(180deg); }
    .nav-dd-menu { display: none; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); min-width: 180px; background: #fff; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06); padding: 6px; margin-top: 4px; z-index: 310; }
    .nav-dd:hover .nav-dd-menu, .nav-dd.open .nav-dd-menu { display: block; }
    .nav-dd-menu a { display: block; font-size: 13px; font-weight: 500; color: rgba(0,0,0,0.7); text-decoration: none; padding: 9px 14px; border-radius: 8px; transition: all 0.15s ease; white-space: nowrap; }
    .nav-dd-menu a:hover { color: #111; background: rgba(0,0,0,0.04); }
    .nav-dd-menu a.active { color: #F5A623; font-weight: 700; }
    /* Hamburger */
    .site-hamburger { display: none; background: none; border: none; cursor: pointer; padding: 8px; width: 40px; height: 40px; border-radius: 10px; position: relative; z-index: 302; }
    .site-hamburger span { display: block; width: 18px; height: 2px; background: #111; margin: 4px auto; border-radius: 2px; transition: transform 0.3s, opacity 0.3s; }
    .site-hamburger.active span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
    .site-hamburger.active span:nth-child(2) { opacity: 0; }
    .site-hamburger.active span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }
    /* Mobile nav */
    .site-mobile-nav { display: none; position: fixed; inset: 0; background: rgba(10,10,10,0.96); z-index: 301; backdrop-filter: blur(20px); flex-direction: column; align-items: center; justify-content: center; gap: 4px; opacity: 0; transition: opacity 0.3s; }
    .site-mobile-nav.active { display: flex; opacity: 1; }
    .site-mobile-nav a { color: rgba(255,255,255,0.7); text-decoration: none; font-size: 17px; font-weight: 600; padding: 14px 40px; border-radius: 14px; width: 260px; text-align: center; }
    .site-mobile-nav a:hover { background: rgba(255,255,255,0.08); color: #fff; }
    .site-mobile-nav a.active { color: #F5A623; }
    .mobile-nav-label { color: rgba(255,255,255,0.3); font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; padding: 10px 0 2px; width: 260px; text-align: center; }
    @media (max-width: 768px) { .site-header-nav { display: none; } .site-hamburger { display: block; } }
    /* ── END UNIFIED HEADER ── */"""

HEADER_JS = """
<script>
(function(){
  var b=document.getElementById('siteHamburger'),n=document.getElementById('siteMobileNav');
  if(b&&n){
    b.addEventListener('click',function(){b.classList.toggle('active');n.classList.toggle('active');document.body.style.overflow=n.classList.contains('active')?'hidden':'';});
    n.addEventListener('click',function(e){if(e.target===n||e.target.tagName==='A'){n.classList.remove('active');b.classList.remove('active');document.body.style.overflow='';}});
  }
  var h=document.getElementById('siteHeader');
  if(h){var t=false;window.addEventListener('scroll',function(){if(!t){requestAnimationFrame(function(){h.classList.toggle('scrolled',window.scrollY>40);t=false;});t=true;}});}
  document.querySelectorAll('.nav-dd-trigger').forEach(function(btn){
    btn.addEventListener('click',function(e){
      e.stopPropagation();
      var dd=btn.parentElement;
      document.querySelectorAll('.nav-dd.open').forEach(function(d){if(d!==dd)d.classList.remove('open');});
      dd.classList.toggle('open');
    });
  });
  document.addEventListener('click',function(){document.querySelectorAll('.nav-dd.open').forEach(function(d){d.classList.remove('open');});});
})();
</script>"""


def process_file(filepath):
    """1ファイルのヘッダーを新形式に統一"""
    text = filepath.read_text(encoding='utf-8')

    if '<header class="site-header"' not in text:
        return False

    active = detect_active_page(filepath)
    new_header = build_header(active)

    # 1. ヘッダーHTML置換
    # <header class="site-header"...>...</header> + 直後の <div class="site-mobile-nav"...>...</div>
    old_pattern = re.compile(
        r'<header\s+class="site-header"[^>]*>.*?</header>\s*'
        r'(?:<div\s+class="(?:site-mobile-nav|mobile-nav-overlay)"[^>]*>.*?</div>)?',
        re.DOTALL
    )
    if not old_pattern.search(text):
        return False

    text = old_pattern.sub(new_header, text)

    # 2. 旧ヘッダーCSS削除（/* ── UNIFIED HEADER ── */ があれば先に削除）
    text = re.sub(r'/\* ── UNIFIED HEADER ── \*/.*?/\* ── END UNIFIED HEADER ── \*/', '', text, flags=re.DOTALL)

    # 旧CSS個別ルール削除
    old_css_patterns = [
        r'\.site-header\s*\{[^}]+\}',
        r'\.site-header\.scrolled\s*\{[^}]+\}',
        r'\.site-header-inner\s*\{[^}]+\}',
        r'\.site-header-logo\s*\{[^}]+\}',
        r'\.site-header-logo\s+svg\s*\{[^}]+\}',
        r'\.site-header-nav\s*\{[^}]+\}',
        r'\.site-header-nav\s+a\s*\{[^}]+\}',
        r'\.site-header-nav\s+a:hover\s*\{[^}]+\}',
        r'\.site-header-nav\s+a\.active\s*\{[^}]+\}',
        r'\.site-header-nav\s+a\.active::after\s*\{[^}]+\}',
        r'\.site-hamburger\s*\{[^}]+\}',
        r'\.site-hamburger\.active\s*\{[^}]+\}',
        r'\.site-hamburger\.active\s*span:nth-child\(\d\)\s*\{[^}]+\}',
        r'\.site-hamburger\s+span\s*\{[^}]+\}',
        r'\.site-mobile-nav\s*\{[^}]+\}',
        r'\.site-mobile-nav\.active\s*\{[^}]+\}',
        r'\.site-mobile-nav\s+a\s*\{[^}]+\}',
        r'\.site-mobile-nav\s+a:hover\s*\{[^}]+\}',
        r'\.site-mobile-nav\s+a\.active\s*\{[^}]+\}',
        r'\.mobile-nav-overlay[^{]*\{[^}]+\}',
        r'\.hamburger[^{]*\{[^}]+\}',
        # minified variants
        r'\.site-header\{[^}]+\}',
        r'\.site-header\.scrolled\{[^}]+\}',
        r'\.site-header-inner\{[^}]+\}',
        r'\.site-header-logo\{[^}]+\}',
        r'\.site-header-logo svg\{[^}]+\}',
        r'\.site-header-nav\{[^}]+\}',
        r'\.site-header-nav a\{[^}]+\}',
        r'\.site-header-nav a:hover\{[^}]+\}',
        r'\.site-header-nav a\.active\{[^}]+\}',
        r'\.site-header-nav a\.active::after\{[^}]+\}',
        r'\.site-hamburger\{[^}]+\}',
        r'\.site-hamburger\.active\{[^}]+\}',
        r'\.site-hamburger\.active span:nth-child\(\d\)\{[^}]+\}',
        r'\.site-hamburger span\{[^}]+\}',
        r'\.site-mobile-nav\{[^}]+\}',
        r'\.site-mobile-nav\.active\{[^}]+\}',
        r'\.site-mobile-nav a\{[^}]+\}',
        r'\.site-mobile-nav a:hover\{[^}]+\}',
        r'\.site-mobile-nav a\.active\{[^}]+\}',
    ]
    for pat in old_css_patterns:
        text = re.sub(pat, '', text)

    # 旧 @media ルール（ヘッダー関連）
    text = re.sub(r'@media\s*\(max-width:\s*768px\)\s*\{\s*\.site-header-nav\s*\{[^}]+\}\s*\.site-hamburger\s*\{[^}]+\}\s*\}', '', text)
    text = re.sub(r'@media\(max-width:768px\)\{\.site-header-nav\{[^}]+\}\.site-hamburger\{[^}]+\}\}', '', text)

    # 3. 新CSSを<style>の直後に挿入
    text = text.replace('<style>', f'<style>\n    {HEADER_CSS}\n', 1)

    # 4. 旧ヘッダーJS削除（既存のsiteHamburgerスクリプト）
    text = re.sub(
        r'<script>\s*\(function\(\)\{var b=document\.getElementById\(\'siteHamburger\'\).*?\}\)\(\);\s*</script>',
        '', text, flags=re.DOTALL
    )

    # 5. 新JS追加（</body>の前）
    if HEADER_JS.strip() not in text:
        text = text.replace('</body>', f'{HEADER_JS}\n</body>')

    # 6. 連続空行クリーンアップ
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    filepath.write_text(text, encoding='utf-8')
    return True


def main():
    count = 0
    errors = []
    skipped = []

    for filepath in sorted(ROOT.rglob('index.html')):
        if filepath in EXCLUDE:
            continue
        if any(d in filepath.parts for d in EXCLUDE_DIRS):
            continue
        if '.git' in str(filepath):
            continue

        try:
            if process_file(filepath):
                rel = filepath.relative_to(ROOT)
                print(f"  Updated: {rel}")
                count += 1
            else:
                rel = filepath.relative_to(ROOT)
                skipped.append(str(rel))
        except Exception as e:
            rel = filepath.relative_to(ROOT)
            errors.append(f"{rel}: {e}")
            print(f"  ERROR: {rel} - {e}")

    print(f"\nUpdated: {count} files")
    if skipped:
        print(f"Skipped (no site-header): {len(skipped)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
