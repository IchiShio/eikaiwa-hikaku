#!/usr/bin/env python3
"""lv5 補充生成 → staging.json に追記"""

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

from lib import parse_response

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "listening" / "questions.js"
STAGING_JSON = REPO_ROOT / "listening" / "staging.json"

AXIS_DESCRIPTIONS = {
    "speed":      'speed    : 発話が速い・詰まった話し方（"Didja hear that?" "Gonna hafta leave." 等）',
    "reduction":  "reduction: gonna/wanna/kinda/dunno/lemme 等の音変化・リンキング・脱落",
    "vocab":      "vocab    : 低頻度語・イディオム・スラング・比喩表現",
    "context":    "context  : 前後の文脈・話者のトーン・感情から正解を推論する必要がある",
    "distractor": "distractor: 誤答が非常に紛らわしく、表面的な理解では正解できない",
}

# 不足分（lv5中心）
PLAN = [
    ("distractor", 0, 0, 0, 0, 11),
    ("reduction",  0, 0, 0, 0, 2),
    ("speed",      0, 0, 0, 0, 6),
    ("vocab",      0, 0, 0, 0, 4),
]


def load_existing_texts():
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    texts = re.findall(r'\btext:\s*"((?:[^"\\]|\\.)*)"', content)
    if len(texts) > 3000:
        texts = texts[-3000:]
    return texts


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    # 既存 staging.json を読み込み
    existing_staging = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    print(f"既存 staging: {len(existing_staging)}問")

    existing_texts = load_existing_texts()
    staging_texts = [q["text"] for q in existing_staging]
    exclude = existing_texts + staging_texts

    client = anthropic.Anthropic(api_key=api_key)
    new_questions = []

    for axis, lv1, lv2, lv3, lv4, lv5 in PLAN:
        count = lv1 + lv2 + lv3 + lv4 + lv5
        if count == 0:
            continue
        print(f"\n[{axis}] lv5 {lv5}問 生成中...")

        axis_desc = AXIS_DESCRIPTIONS[axis]
        prompt = f"""以下のJSON形式でリスニングクイズの問題を{count}問生成してください。

## 難易度
全て lv5（非常に難しい・速い/崩れた英語・上級表現）で生成すること。

## axis
全て "{axis}" で生成すること。
- {axis_desc}

## 出力形式（JSONのみ出力）
[
  {{
    "diff": "lv5",
    "axis": "{axis}",
    "text": "英語音声スクリプト（ネイティブの自然な発話）",
    "ja": "日本語仮訳（短く自然に）",
    "answer": "choices[0] と完全に同じ文字列（コピペすること）",
    "choices": ["正解（15〜25字の日本語）", "誤答1", "誤答2", "誤答3", "誤答4"],
    "expl": "なぜ正解なのかの日本語解説（1〜2文）",
    "kp": ["聴き取りのカギになるフレーズ1〜2個"]
  }}
]

## 制約
- text はネイティブが実際に使う自然な英語（略語・短縮形OK）
- lv5 なので ≥27語 or 上級表現・文脈依存の難しい問題にすること
- **answer は必ず choices[0] と完全に一致させること**
- JSON のみ出力

## 既存問題（重複禁止・最新100件）
{json.dumps(exclude[-100:], ensure_ascii=False)}
"""

        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        questions = parse_response(resp.content[0].text)
        for q in questions:
            q["axis"] = axis
            q["diff"] = "lv5"
        new_questions.extend(questions)
        print(f"  ✅ {len(questions)}問 取得")

    # staging.json に追記
    combined = existing_staging + new_questions
    STAGING_JSON.write_text(
        json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n✅ {len(new_questions)}問 追加 → staging.json 合計 {len(combined)}問")


if __name__ == "__main__":
    main()
