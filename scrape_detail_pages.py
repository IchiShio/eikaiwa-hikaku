#!/usr/bin/env python3
"""
scrape_detail_pages.py - Purdue OWL & Cambridge の個別文法ページを取得
各ページの解説・例文・ルールを取得して grammar/raw_sources/details/ に保存
"""

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = Path(__file__).parent / "grammar" / "raw_sources" / "details"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}


def fetch(url, timeout=20):
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extract_text_content(soup):
    """メインコンテンツからテキスト・例文を抽出"""
    # Remove nav, footer, sidebar
    for tag in soup.select("nav, footer, .sidebar, .breadcrumb, .related, script, style"):
        tag.decompose()

    main = (soup.find("main") or soup.find("article") or
            soup.find("div", class_="content") or soup.find("div", id="content") or
            soup.find("div", class_="post-body") or soup.find("body"))
    if not main:
        return ""
    return main.get_text(separator="\n", strip=True)


def scrape_purdue_owl():
    """Purdue OWL の全文法ページを取得"""
    print("=" * 50)
    print("Purdue OWL - Individual Pages")
    print("=" * 50)

    urls_file = Path(__file__).parent / "grammar" / "raw_sources" / "purdue_owl.json"
    urls = json.loads(urls_file.read_text())

    results = []
    for i, item in enumerate(urls):
        url = item["url"]
        title = item["title"]
        slug = url.rstrip("/").split("/")[-1].replace(".html", "")

        print(f"  [{i+1}/{len(urls)}] {title}...")
        try:
            soup = fetch(url)
            content = extract_text_content(soup)

            # Extract examples (often in <em>, <blockquote>, or specific patterns)
            examples = []
            for em in soup.select("em, .example, blockquote"):
                text = em.get_text(strip=True)
                if 5 < len(text) < 200:
                    examples.append(text)

            result = {
                "source": "Purdue OWL",
                "title": title,
                "url": url,
                "content": content[:5000],
                "examples": examples[:20],
            }
            results.append(result)
            print(f"    OK: {len(content)} chars, {len(examples)} examples")
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"source": "Purdue OWL", "title": title, "url": url, "error": str(e)})

        time.sleep(1.5)

    out = OUTPUT_DIR / "purdue_owl_details.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"\nSaved: {out} ({len(results)} pages)")
    return results


def scrape_cambridge():
    """Cambridge Dictionary Grammar の個別ページを取得"""
    print("\n" + "=" * 50)
    print("Cambridge Grammar - Individual Pages")
    print("=" * 50)

    urls_file = Path(__file__).parent / "grammar" / "raw_sources" / "cambridge.json"
    urls = json.loads(urls_file.read_text())

    # Filter to actual grammar topic pages (not language selector etc)
    grammar_urls = [u for u in urls if "/grammar/british-grammar/" in u.get("url", "")
                    and len(u.get("title", "")) > 3
                    and u.get("title", "") not in ("Grammar", "British Grammar")]

    results = []
    for i, item in enumerate(grammar_urls):
        url = item["url"]
        title = item["title"]

        print(f"  [{i+1}/{len(grammar_urls)}] {title}...")
        try:
            soup = fetch(url)
            content = extract_text_content(soup)

            examples = []
            for em in soup.select("em, .example, .eg, blockquote, .dexamp"):
                text = em.get_text(strip=True)
                if 5 < len(text) < 200:
                    examples.append(text)

            result = {
                "source": "Cambridge Grammar",
                "title": title,
                "url": url,
                "content": content[:5000],
                "examples": examples[:20],
            }
            results.append(result)
            print(f"    OK: {len(content)} chars, {len(examples)} examples")
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"source": "Cambridge Grammar", "title": title, "url": url, "error": str(e)})

        time.sleep(2)

    out = OUTPUT_DIR / "cambridge_details.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"\nSaved: {out} ({len(results)} pages)")
    return results


def scrape_british_council():
    """British Council LearnEnglish の文法ページを取得"""
    print("\n" + "=" * 50)
    print("British Council - Grammar Pages")
    print("=" * 50)

    # British Council grammar categories
    bc_urls = [
        ("A1-A2 Grammar", "https://learnenglish.britishcouncil.org/grammar/a1-a2-grammar"),
        ("B1-B2 Grammar", "https://learnenglish.britishcouncil.org/grammar/b1-b2-grammar"),
        ("C1-C2 Grammar", "https://learnenglish.britishcouncil.org/grammar/c1-c2-grammar"),
    ]

    results = []
    for title, url in bc_urls:
        print(f"  {title}...")
        try:
            soup = fetch(url, timeout=30)
            content = extract_text_content(soup)

            # Find sub-topic links
            sub_links = []
            for a in soup.select("a[href*='/grammar/']"):
                href = a.get("href", "")
                text = a.get_text(strip=True)
                if text and len(text) > 3 and href != url:
                    full = href if href.startswith("http") else f"https://learnenglish.britishcouncil.org{href}"
                    sub_links.append({"title": text, "url": full})

            result = {
                "source": "British Council",
                "title": title,
                "url": url,
                "content": content[:3000],
                "sub_topics": sub_links[:30],
            }
            results.append(result)
            print(f"    OK: {len(content)} chars, {len(sub_links)} sub-topics")
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"source": "British Council", "title": title, "url": url, "error": str(e)})

        time.sleep(2)

    # Scrape individual sub-topic pages (first 20 per level)
    all_sub = []
    for r in results:
        for sub in r.get("sub_topics", [])[:20]:
            all_sub.append(sub)

    print(f"\n  Fetching {len(all_sub)} sub-topic pages...")
    for i, sub in enumerate(all_sub):
        print(f"  [{i+1}/{len(all_sub)}] {sub['title']}...")
        try:
            soup = fetch(sub["url"], timeout=20)
            content = extract_text_content(soup)
            examples = []
            for em in soup.select("em, .example, blockquote"):
                text = em.get_text(strip=True)
                if 5 < len(text) < 200:
                    examples.append(text)

            results.append({
                "source": "British Council",
                "title": sub["title"],
                "url": sub["url"],
                "content": content[:4000],
                "examples": examples[:15],
            })
            print(f"    OK: {len(content)} chars")
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(1.5)

    out = OUTPUT_DIR / "british_council_details.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"\nSaved: {out} ({len(results)} pages)")
    return results


if __name__ == "__main__":
    scrape_purdue_owl()
    scrape_cambridge()
    scrape_british_council()
    print("\nDone!")
