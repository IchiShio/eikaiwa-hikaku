#!/usr/bin/env python3
"""
generate_200.py - 200問を axis×level 指定で一括生成 → staging.json に保存

5つの axis それぞれに個別のレベル配分を指定して生成し、
全結果を staging.json に書き出す。
"""

import json
import os
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic がインストールされていません")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from lib import parse_response

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "listening" / "questions.js"
STAGING_JSON = REPO_ROOT / "listening" / "staging.json"

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
BATCH_SIZE = 30

# axis ごとの生成計画: (axis, lv1, lv2, lv3, lv4, lv5)
PLAN = [
    ("context",    5,  4,  2,  8,  8),   # 27問
    ("distractor", 8, 10, 15, 15, 12),   # 60問
    ("reduction",  6,  6,  8, 10,  8),   # 38問
    ("speed",      4,  6,  8, 10,  8),   # 36問
    ("vocab",      9, 10,  5, 10,  5),   # 39問
]

AXIS_DESCRIPTIONS = {
    "speed":      'speed    : 発話が速い・詰まった話し方（"Didja hear that?" "Gonna hafta leave." 等）',
    "reduction":  "reduction: gonna/wanna/kinda/dunno/lemme 等の音変化・リンキング・脱落",
    "vocab":      "vocab    : 低頻度語・イディオム・スラング・比喩表現",
    "context":    "context  : 前後の文脈・話者のトーン・感情から正解を推論する必要がある",
    "distractor": "distractor: 誤答が非常に紛らわしく、表面的な理解では正解できない",
}


def load_existing_texts():
    import re
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    texts = re.findall(r'\btext:\s*"((?:[^"\\]|\\.)*)"', content)
    if len(texts) > 3000:
        texts = texts[-3000:]
    return texts


def build_prompt(axis, count, lv1, lv2, lv3, lv4, lv5, existing_texts):
    existing_list = json.dumps(existing_texts, ensure_ascii=False, indent=2)
    axis_desc = AXIS_DESCRIPTIONS[axis]

    return f"""以下のJSON形式でリスニングクイズの問題を{count}問生成してください。

## 難易度の内訳
- lv1（超簡単・日常の短い1文）: {lv1}問
- lv2（簡単）: {lv2}問
- lv3（普通）: {lv3}問
- lv4（難しい）: {lv4}問
- lv5（非常に難しい・速い/崩れた英語）: {lv5}問

## 難易度の微差（axis フィールド）
全ての問題の axis を "{axis}" にすること。
- {axis_desc}

## 出力形式（JSONのみ出力、他の文章は不要）
[
  {{
    "diff": "lv1〜lv5のいずれか",
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
- axis "{axis}" の特性を text と choices の両方に反映させること
- choices は正解が1つ、残り4つは紛らわしい誤答
- **answer は必ず choices[0] と完全に一致させること**（システムが文字列一致で正解判定するため）
- choices[0] に正解を入れる（表示時にJSがシャッフルするためユーザーには先頭に見えない）
- 既存テーマとの重複を避けること（テーマ例: 交通・飲食店・職場・家庭・天気・ショッピング・健康）
- JSON のみ出力（説明文・コードブロック記号不要）

## 既存問題リスト（重複禁止）
以下は既存問題の英文リストです。同じ英文・同じ場面・同じシチュエーションの問題は
絶対に作らないでください（完全一致だけでなく類似した場面も避けること）：

{existing_list}
"""


def generate_for_axis(client, model, axis, lv1, lv2, lv3, lv4, lv5, existing_texts, all_generated):
    count = lv1 + lv2 + lv3 + lv4 + lv5
    questions = []
    remaining = count
    remaining_lv = [lv1, lv2, lv3, lv4, lv5]
    batch_num = 1
    total_batches = -(-count // BATCH_SIZE)

    while remaining > 0:
        batch_count = min(remaining, BATCH_SIZE)
        # 各レベルのバッチ配分
        total_rem = sum(remaining_lv)
        if total_rem == 0:
            bl = [0, 0, batch_count, 0, 0]
        else:
            bl = [round(x * batch_count / total_rem) for x in remaining_lv]
            diff = batch_count - sum(bl)
            # 差分を最大のレベルに加算
            max_idx = bl.index(max(bl))
            bl[max_idx] += diff

        print(f"  [{batch_num}/{total_batches}] {batch_count}問 "
              f"(lv1:{bl[0]} lv2:{bl[1]} lv3:{bl[2]} lv4:{bl[3]} lv5:{bl[4]}) 生成中...")

        exclude = existing_texts + [q["text"] for q in all_generated] + [q["text"] for q in questions]
        prompt = build_prompt(axis, batch_count, bl[0], bl[1], bl[2], bl[3], bl[4], exclude)

        try:
            resp = client.messages.create(
                model=model, max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            batch_questions = parse_response(resp.content[0].text)
            # axis を強制設定
            for q in batch_questions:
                q["axis"] = axis
            questions.extend(batch_questions)
            print(f"    ✅ {len(batch_questions)}問 取得（axis累計: {len(questions)}問）")
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            if questions:
                print(f"    取得済みの {len(questions)} 問を使います")
                break
            raise

        for i in range(5):
            remaining_lv[i] = max(0, remaining_lv[i] - bl[i])
        remaining -= batch_count
        batch_num += 1

    return questions


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    model = DEFAULT_MODEL
    total_planned = sum(lv1 + lv2 + lv3 + lv4 + lv5 for _, lv1, lv2, lv3, lv4, lv5 in PLAN)
    print(f"=== 200問一括生成 ===")
    print(f"モデル: {model}")
    print(f"計画: {total_planned}問（5 axis）")
    print()

    for axis, lv1, lv2, lv3, lv4, lv5 in PLAN:
        total = lv1 + lv2 + lv3 + lv4 + lv5
        print(f"  {axis:12s}: {total}問 (lv1:{lv1} lv2:{lv2} lv3:{lv3} lv4:{lv4} lv5:{lv5})")
    print()

    existing_texts = load_existing_texts()
    print(f"既存問題数: {len(existing_texts)} 問\n")

    client = anthropic.Anthropic(api_key=api_key)

    all_questions = []
    for axis, lv1, lv2, lv3, lv4, lv5 in PLAN:
        total = lv1 + lv2 + lv3 + lv4 + lv5
        print(f"\n{'='*50}")
        print(f"[{axis}] {total}問 生成開始")
        print(f"{'='*50}")

        questions = generate_for_axis(client, model, axis, lv1, lv2, lv3, lv4, lv5, existing_texts, all_questions)
        all_questions.extend(questions)
        print(f"[{axis}] 完了: {len(questions)}問（全体累計: {len(all_questions)}問）")

    # staging.json に保存
    STAGING_JSON.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 集計
    print(f"\n{'='*50}")
    print(f"✅ 全 {len(all_questions)}問 を staging.json に保存しました")
    print(f"{'='*50}")

    # axis × diff クロス集計
    from collections import Counter
    cross = Counter()
    for q in all_questions:
        cross[(q.get("axis", "?"), q.get("diff", "?"))] += 1

    axes = ["context", "distractor", "reduction", "speed", "vocab"]
    diffs = ["lv1", "lv2", "lv3", "lv4", "lv5"]
    print(f"\n{'':12s} {'lv1':>5s} {'lv2':>5s} {'lv3':>5s} {'lv4':>5s} {'lv5':>5s} {'合計':>6s}")
    for a in axes:
        counts = [cross[(a, d)] for d in diffs]
        total = sum(counts)
        print(f"{a:12s} {counts[0]:5d} {counts[1]:5d} {counts[2]:5d} {counts[3]:5d} {counts[4]:5d} {total:6d}")
    grand = sum(cross.values())
    print(f"{'合計':12s} {sum(cross[(a,'lv1')] for a in axes):5d} "
          f"{sum(cross[(a,'lv2')] for a in axes):5d} "
          f"{sum(cross[(a,'lv3')] for a in axes):5d} "
          f"{sum(cross[(a,'lv4')] for a in axes):5d} "
          f"{sum(cross[(a,'lv5')] for a in axes):5d} {grand:6d}")

    print(f"\n次のステップ:")
    print(f"  cd /Users/yusuke/projects/claude/native-real && python3 add_questions.py")


if __name__ == "__main__":
    main()
