#!/usr/bin/env python3
"""
unify_headers.py - 全ページのヘッダーをルート(ListenUp)と統一する

対象: <header class="site-header"> を持つ旧スタイルページ（248ページ）
除外: ルート index.html, grammar/index.html（既に統一済み）,
      listening/（リダイレクト）, orbit/（独自UI）, kioku-shinai/, about/（hd形式）
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent

# 除外パス
EXCLUDE = {
    ROOT / "index.html",
    ROOT / "grammar" / "index.html",
    ROOT / "listening" / "index.html",
    ROOT / "orbit" / "index.html",
}

# 除外ディレクトリ（独自UIを持つ）
EXCLUDE_DIRS = {"kioku-shinai", "about", "orbit", ".git"}

CANONICAL_NAV_LINKS = [
    ('/', 'ListenUp'),
    ('/grammar/', '文法クイズ'),
    ('/kioku-shinai/', '記憶しない英単語'),
    ('/ranking/', 'ランキング'),
    ('/articles/', '学習コラム'),
    ('/real-phrases/', 'フレーズ集'),
    ('/prompts/', 'AIプロンプト'),
    ('/about/', 'About'),
]

SVG_LOGO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>'


def detect_active_page(filepath):
    """ファイルパスからアクティブなナビリンクを判定"""
    rel = filepath.relative_to(ROOT)
    parts = rel.parts
    if len(parts) >= 1:
        section = parts[0]
        for href, label in CANONICAL_NAV_LINKS:
            if href.strip('/') == section:
                return href
    return None


def build_header(active_href):
    """統一ヘッダーHTMLを生成"""
    nav_links = []
    mobile_links = []
    for href, label in CANONICAL_NAV_LINKS:
        cls = ' class="active"' if href == active_href else ''
        nav_links.append(f'        <a href="{href}"{cls}>{label}</a>')
        mobile_links.append(f'  <a href="{href}"{cls}>{label}</a>')

    return f"""<header class="site-header" id="siteHeader">
  <div class="site-header-inner">
    <a href="/" class="site-header-logo">{SVG_LOGO}native-real</a>
    <nav class="site-header-nav">
{chr(10).join(nav_links)}
    </nav>
    <button class="site-hamburger" id="siteHamburger" aria-label="メニューを開く">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="site-mobile-nav" id="siteMobileNav">
{chr(10).join(mobile_links)}
</div>"""


# CSS to inject (replaces old .site-header styles)
HEADER_CSS = """.site-header {
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
    .site-header-nav a { font-size: 13px; font-weight: 500; color: rgba(0,0,0,0.6); text-decoration: none; padding: 7px 12px; border-radius: 10px; transition: all 0.2s ease; white-space: nowrap; position: relative; }
    .site-header-nav a:hover { color: #111; background: rgba(0,0,0,0.04); }
    .site-header-nav a.active { color: #F5A623; font-weight: 700; }
    .site-header-nav a.active::after { content: ''; position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%); width: 16px; height: 2px; border-radius: 1px; background: #F5A623; }
    .site-hamburger { display: none; background: none; border: none; cursor: pointer; padding: 8px; width: 40px; height: 40px; border-radius: 10px; position: relative; z-index: 302; }
    .site-hamburger span { display: block; width: 18px; height: 2px; background: #111; margin: 4px auto; border-radius: 2px; transition: transform 0.3s, opacity 0.3s; }
    .site-hamburger.active span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
    .site-hamburger.active span:nth-child(2) { opacity: 0; }
    .site-hamburger.active span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }
    .site-mobile-nav { display: none; position: fixed; inset: 0; background: rgba(10,10,10,0.96); z-index: 301; backdrop-filter: blur(20px); flex-direction: column; align-items: center; justify-content: center; gap: 6px; opacity: 0; transition: opacity 0.3s; }
    .site-mobile-nav.active { display: flex; opacity: 1; }
    .site-mobile-nav a { color: rgba(255,255,255,0.7); text-decoration: none; font-size: 18px; font-weight: 600; padding: 16px 40px; border-radius: 14px; width: 260px; text-align: center; }
    .site-mobile-nav a:hover { background: rgba(255,255,255,0.08); color: #fff; }
    .site-mobile-nav a.active { color: #F5A623; }
    @media (max-width: 768px) { .site-header-nav { display: none; } .site-hamburger { display: block; } }"""

HEADER_JS = """
<script>
(function(){var b=document.getElementById('siteHamburger'),n=document.getElementById('siteMobileNav');if(!b||!n)return;b.addEventListener('click',function(){b.classList.toggle('active');n.classList.toggle('active');document.body.style.overflow=n.classList.contains('active')?'hidden':'';});n.addEventListener('click',function(e){if(e.target===n||e.target.tagName==='A'){n.classList.remove('active');b.classList.remove('active');document.body.style.overflow='';}});})();
(function(){var h=document.getElementById('siteHeader');if(!h)return;var t=false;window.addEventListener('scroll',function(){if(!t){requestAnimationFrame(function(){h.classList.toggle('scrolled',window.scrollY>40);t=false;});t=true;}});})();
</script>"""


def process_file(filepath):
    """1ファイルのヘッダーを統一"""
    text = filepath.read_text(encoding='utf-8')

    if '<header class="site-header"' not in text:
        return False

    active = detect_active_page(filepath)
    new_header = build_header(active)

    # 1. Replace old header block
    # Pattern: <header class="site-header"...>...</header> + optional mobile-nav-overlay
    old_header_pattern = re.compile(
        r'<header\s+class="site-header"[^>]*>.*?</header>\s*'
        r'(?:<div\s+class="mobile-nav-overlay"[^>]*>.*?</div>)?',
        re.DOTALL
    )
    if not old_header_pattern.search(text):
        return False

    text = old_header_pattern.sub(new_header, text)

    # 2. Replace old header CSS with new (inject into existing <style>)
    # Remove old .site-header, .logo, nav, .hamburger, .mobile-nav-overlay CSS
    old_css_patterns = [
        r'\.site-header\s*\{[^}]+\}',
        r'\.site-header\s+\.container\s*\{[^}]+\}',
        r'\.site-header\s+\.logo\s*\{[^}]+\}',
        r'\.site-header\s+nav\s*\{[^}]+\}',
        r'\.site-header\s+nav\s+a\s*\{[^}]+\}',
        r'\.site-header\s+nav\s+a:hover\s*\{[^}]+\}',
        r'\.site-header\s+nav\s+a\.active\s*\{[^}]+\}',
        r'\.hamburger\s*\{[^}]+\}',
        r'\.hamburger\.active\s*\{[^}]+\}',
        r'\.hamburger\s+span\s*\{[^}]+\}',
        r'\.hamburger\.active\s+span:nth[^}]+\}',
        r'\.mobile-nav-overlay\s*\{[^}]+\}',
        r'\.mobile-nav-overlay\.active\s*\{[^}]+\}',
        r'\.mobile-nav-overlay\s+a\s*\{[^}]+\}',
        r'\.mobile-nav-overlay\s+a:hover\s*\{[^}]+\}',
        r'\.mobile-nav-overlay\s+a\.active\s*\{[^}]+\}',
    ]
    for pat in old_css_patterns:
        text = re.sub(pat, '', text)

    # Inject new CSS after first <style> tag
    text = text.replace('<style>', f'<style>\n    {HEADER_CSS}\n', 1)

    # 3. Add JS before </body>
    if 'siteHamburger' not in text.split('</body>')[0].split('<script')[-1] if '<script' in text else True:
        text = text.replace('</body>', f'{HEADER_JS}\n</body>')

    filepath.write_text(text, encoding='utf-8')
    return True


def main():
    count = 0
    errors = []

    for filepath in ROOT.rglob('index.html'):
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
        except Exception as e:
            rel = filepath.relative_to(ROOT)
            errors.append(f"{rel}: {e}")
            print(f"  ERROR: {rel} - {e}")

    print(f"\nUpdated: {count} files")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
