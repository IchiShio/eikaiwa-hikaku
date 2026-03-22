#!/usr/bin/env python3
"""Batch 2: Purdue OWL後半のデータからルールを生成してマージ"""

import json
import os
import re
import sys
from pathlib import Path

import anthropic
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
ROOT = Path(__file__).parent

data = json.loads((ROOT / "grammar/raw_sources/details/purdue_owl_details.json").read_text())
useful = [d for d in data if "error" not in d and len(d.get("content", "")) > 300]
batch = useful[len(useful) // 2:]

source_text = ""
for d in batch:
    source_text += f"\n--- Purdue OWL: {d['title']} ---\n"
    source_text += f"URL: {d['url']}\n"
    source_text += d["content"][:2000] + "\n"

prompt = (
    "以下はPurdue OWLからスクレイピングした英文法ページです。\n"
    "このデータに記載がある文法ルールを構造化してJSON配列で出力してください。\n\n"
    "ソースデータ:\n" + source_text + "\n\n"
    "出力形式（JSON配列のみ）:\n"
    '各ルールは以下のフィールドを持つオブジェクト:\n'
    'id, rule(日本語), rule_en, diff(lv1-lv5), axes(配列), tags(配列),\n'
    'cefr, pattern, correct_example, common_errors(配列), key_signal, sources(配列)\n\n'
    'diff基準: lv1=中学基礎, lv2=中学卒業, lv3=高校/TOEIC400-600, lv4=TOEIC600-800, lv5=TOEIC800+\n'
    '25-35件を目安。JSONのみ出力。'
)

print("Generating batch 2...")
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8192,
    messages=[{"role": "user", "content": prompt}],
)
raw = resp.content[0].text.strip()
raw = re.sub(r"^```[a-z]*\n?", "", raw)
raw = re.sub(r"\n?```\s*$", "", raw)

try:
    rules = json.loads(raw)
except json.JSONDecodeError:
    last = raw.rfind("},")
    if last > 0:
        rules = json.loads(raw[:last + 1] + "\n]")
        print(f"  Truncated to {len(rules)} rules")
    else:
        print("ERROR: JSON parse failed")
        print(raw[:300])
        sys.exit(1)

print(f"Got {len(rules)} rules")

# Merge
existing = json.loads((ROOT / "grammar/grammar_rules.json").read_text())
print(f"Existing: {len(existing)} rules")

all_rules = existing + rules
for i, r in enumerate(all_rules):
    r["id"] = f"R{i + 1:03d}"

(ROOT / "grammar/grammar_rules.json").write_text(
    json.dumps(all_rules, ensure_ascii=False, indent=2) + "\n"
)

from collections import Counter
print(f"Total: {len(all_rules)} rules")
print(f"diff: {dict(Counter(r['diff'] for r in all_rules))}")
