#!/usr/bin/env python3
"""
generate_questions.py - Claude API で問題を自動生成 → staging.json に保存

Usage:
  python3 generate_questions.py --count 100
  python3 generate_questions.py --count 50 --lv1 8 --lv2 12 --lv3 15 --lv4 10 --lv5 5
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic がインストールされていません")
    print("  pip3 install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv がない場合は環境変数から直接読む

QUESTIONS_JS = Path(__file__).parent / "listening" / "questions.js"
STAGING_JSON = Path(__file__).parent / "listening" / "staging.json"

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 8192
BATCH_SIZE = 30  # 1回の API 呼び出しで生成する問題数（8192トークン上限に収まる量）

VALID_FIELDS = {"diff", "text", "ja", "answer", "choices", "expl", "kp"}
VALID_DIFFS = {"lv1", "lv2", "lv3", "lv4", "lv5"}


def load_existing_texts():
    """questions.js から既存の text フィールド一覧を取得"""
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    return re.findall(r'\btext:\s*"((?:[^"\\]|\\.)*)"', content)


def build_prompt(count, lv1, lv2, lv3, lv4, lv5, existing_texts):
    existing_list = json.dumps(existing_texts, ensure_ascii=False, indent=2)
    return f"""以下のJSON形式でリスニングクイズの問題を{count}問生成してください。

## 難易度の内訳
- lv1（超簡単・日常の短い1文）: {lv1}問
- lv2（簡単）: {lv2}問
- lv3（普通）: {lv3}問
- lv4（難しい）: {lv4}問
- lv5（非常に難しい・速い/崩れた英語）: {lv5}問

## 出力形式（JSONのみ出力、他の文章は不要）
[
  {{
    "diff": "lv1〜lv5のいずれか",
    "text": "英語音声スクリプト（ネイティブの自然な発話）",
    "ja": "日本語仮訳（短く自然に）",
    "answer": "何をしている/言っている場面かの日本語説明（15〜25字）",
    "choices": ["正解", "誤答1", "誤答2", "誤答3", "誤答4"],
    "expl": "なぜ正解なのかの日本語解説（1〜2文）",
    "kp": ["聴き取りのカギになるフレーズ1〜2個"]
  }}
]

## 制約
- text はネイティブが実際に使う自然な英語（略語・短縮形OK）
- choices は正解が1つ、残り4つは紛らわしい誤答
- choices の順序はランダムに（正解を先頭にしない）
- 既存テーマとの重複を避けること（テーマ例: 交通・飲食店・職場・家庭・天気・ショッピング・健康）
- JSON のみ出力（説明文・コードブロック記号不要）

## 既存問題リスト（重複禁止）
以下は既存問題の英文リストです。同じ英文・同じ場面・同じシチュエーションの問題は
絶対に作らないでください（完全一致だけでなく類似した場面も避けること）：

{existing_list}
"""


def call_api(client, prompt):
    """Claude API を呼び出して JSON をパース"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()

    # コードブロック除去
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        # 末尾が切れている場合、最後の完全なオブジェクトまでで復元を試みる
        last_obj_end = raw.rfind("},")
        if last_obj_end > 0:
            try:
                questions = json.loads(raw[:last_obj_end + 1] + "\n]")
                print(f"  WARNING: レスポンスが途中で切れたため {len(questions)} 問のみ取得")
                return questions
            except json.JSONDecodeError:
                pass
        raise

    # バリデーション（不正な問題を除去）
    valid = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if VALID_FIELDS - set(q.keys()):
            continue
        if q.get("diff") not in VALID_DIFFS:
            continue
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 5:
            continue
        valid.append(q)

    return valid


def split_levels(total_lv, total_count, batch_count):
    """レベル分布を batch_count 問に按分（合計が batch_count になるよう調整）"""
    total = sum(total_lv)
    if total == 0:
        return [0, 0, batch_count, 0, 0]
    batch = [round(x * batch_count / total) for x in total_lv]
    diff = batch_count - sum(batch)
    # 差分を lv3（インデックス2）に足す
    batch[2] = max(0, batch[2] + diff)
    return batch


def main():
    parser = argparse.ArgumentParser(description="Claude API で問題を生成して staging.json に保存")
    parser.add_argument("--count", type=int, default=100, help="生成問題数（デフォルト: 100）")
    parser.add_argument("--lv1", type=int, default=None)
    parser.add_argument("--lv2", type=int, default=None)
    parser.add_argument("--lv3", type=int, default=None)
    parser.add_argument("--lv4", type=int, default=None)
    parser.add_argument("--lv5", type=int, default=None)
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        print("  .env ファイルに ANTHROPIC_API_KEY=your_key を追加してください")
        sys.exit(1)

    count = args.count
    default_ratios = [0.15, 0.25, 0.30, 0.20, 0.10]

    if any(x is not None for x in [args.lv1, args.lv2, args.lv3, args.lv4, args.lv5]):
        lv = [args.lv1 or 0, args.lv2 or 0, args.lv3 or 0, args.lv4 or 0, args.lv5 or 0]
    else:
        lv = [round(count * r) for r in default_ratios]
        lv[4] = count - sum(lv[:4])  # lv5 に残りを全部

    lv1, lv2, lv3, lv4, lv5 = lv

    print(f"生成設定: {count}問 (lv1:{lv1} lv2:{lv2} lv3:{lv3} lv4:{lv4} lv5:{lv5})")
    print(f"モデル: {MODEL}  バッチサイズ: {BATCH_SIZE}問")

    existing_texts = load_existing_texts()
    print(f"既存問題数: {len(existing_texts)} 問")

    client = anthropic.Anthropic(api_key=api_key)

    all_questions = []
    remaining_lv = list(lv)
    remaining = count
    batch_num = 1
    total_batches = -(-count // BATCH_SIZE)  # 切り上げ除算

    while remaining > 0:
        batch_count = min(remaining, BATCH_SIZE)
        bl = split_levels(remaining_lv, remaining, batch_count)
        bl1, bl2, bl3, bl4, bl5 = bl

        print(f"\n[バッチ {batch_num}/{total_batches}] {batch_count}問 "
              f"(lv1:{bl1} lv2:{bl2} lv3:{bl3} lv4:{bl4} lv5:{bl5}) 生成中...")

        # 既存テキスト + これまで生成した問題の text を除外リストに追加
        exclude_texts = existing_texts + [q["text"] for q in all_questions]
        prompt = build_prompt(batch_count, bl1, bl2, bl3, bl4, bl5, exclude_texts)

        try:
            questions = call_api(client, prompt)
            all_questions.extend(questions)
            print(f"  ✅ {len(questions)}問 取得（累計: {len(all_questions)}問）")
        except Exception as e:
            print(f"  ERROR: バッチ {batch_num} 失敗: {e}", file=sys.stderr)
            if all_questions:
                print(f"  取得済みの {len(all_questions)} 問を staging.json に保存して終了します")
                break
            sys.exit(1)

        # 消費分をレベルカウントから引く
        for i in range(5):
            remaining_lv[i] = max(0, remaining_lv[i] - bl[i])
        remaining -= batch_count
        batch_num += 1

    if not all_questions:
        print("ERROR: 問題を1問も生成できませんでした", file=sys.stderr)
        sys.exit(1)

    STAGING_JSON.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n✅ {len(all_questions)}問 を listening/staging.json に保存しました")
    print("次のステップ:")
    print(f"  cd /Users/yusuke/projects/claude/eikaiwa-hikaku && python3 add_questions.py")


if __name__ == "__main__":
    main()
