#!/usr/bin/env python3
"""
build_grammar_rules.py - Purdue OWLスクレイピングデータを元に
grammar_rules.json を再構築する
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY required")
    sys.exit(1)

client = anthropic.Anthropic(api_key=api_key)
ROOT = Path(__file__).parent

data = json.loads((ROOT / "grammar/raw_sources/details/purdue_owl_details.json").read_text())
useful = [d for d in data if "error" not in d and len(d.get("content", "")) > 300]
print(f"Useful Purdue OWL pages: {len(useful)}")

mid = len(useful) // 2
batches = [useful[:mid], useful[mid:]]

all_rules = []

for batch_idx, batch in enumerate(batches):
    source_text = ""
    for d in batch:
        source_text += f"\n--- {d['source']}: {d['title']} ---\n"
        source_text += f"URL: {d['url']}\n"
        source_text += d["content"][:2500] + "\n"
        if d.get("examples"):
            source_text += f"Examples: {json.dumps(d['examples'][:5], ensure_ascii=False)}\n"

    prompt = f"""以下はPurdue OWL (Purdue University Online Writing Lab) からスクレイピングした
英文法ページの実際のコンテンツです。このデータに記載がある文法ルールを構造化してください。

## ソースデータ
{source_text}

## 出力形式（JSON配列のみ、説明文は不要）
[
  {{
    "id": "R{batch_idx * 30 + 1:03d}",
    "rule": "日本語ルール名",
    "rule_en": "English Rule Name (from source)",
    "diff": "lv1-lv5",
    "axes": ["form/vocab/logic/tense/trap から1-2個"],
    "tags": ["該当する試験タグ"],
    "cefr": "A1-C1",
    "pattern": "文法パターン（ソースの説明に基づく）",
    "correct_example": "正しい例文（ソースから引用または同パターンの別例）",
    "common_errors": [
      {{"wrong": "典型的間違い", "why": "理由"}},
      {{"wrong": "別の間違い", "why": "理由"}}
    ],
    "key_signal": "正解を選ぶキーワード・判断基準",
    "sources": ["Purdue OWL: ページ名"]
  }}
]

## 制約
- ソースデータに実際に記載がある内容のみをルール化
- 25〜40件を目安
- diff基準: lv1=中学基礎, lv2=中学卒業, lv3=高校基礎/TOEIC400-600, lv4=TOEIC600-800, lv5=TOEIC800+
- axes: form(語形変化), vocab(語法), logic(文構造), tense(時制), trap(引っかけ)
- tags: eiken4, eiken3, eikenpre2, eiken2, eikenpre1, toeic, juken
- JSONのみ出力"""

    print(f"\nBatch {batch_idx + 1}/2 generating...")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw.strip())

    try:
        rules = json.loads(raw)
    except json.JSONDecodeError:
        last = raw.rfind("},")
        if last > 0:
            try:
                rules = json.loads(raw[:last + 1] + "\n]")
                print(f"  WARNING: Truncated, got {len(rules)} rules")
            except json.JSONDecodeError:
                print(f"  ERROR: JSON parse failed completely")
                continue
        else:
            print(f"  ERROR: No valid JSON found")
            continue

    print(f"  Got {len(rules)} rules")
    all_rules.extend(rules)

# Re-number IDs
for i, r in enumerate(all_rules):
    r["id"] = f"R{i + 1:03d}"

# Save
output = ROOT / "grammar" / "grammar_rules.json"
output.write_text(json.dumps(all_rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

from collections import Counter

print(f"\nTotal: {len(all_rules)} rules")
print(f"diff: {dict(Counter(r['diff'] for r in all_rules))}")
axes_count = Counter(a for r in all_rules for a in r.get("axes", []))
print(f"axes: {dict(axes_count)}")
print(f"Saved: {output}")
