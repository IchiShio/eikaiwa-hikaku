#!/usr/bin/env python3
"""
generate_grammar.py - Claude API で英文法クイズ問題を生成 → grammar/staging.json に保存

通常モード:
  python3 generate_grammar.py --count 100

axis 指定:
  python3 generate_grammar.py --count 50 --axis-only trap,tense

Batch モード:
  python3 generate_grammar.py --count 100 --batch
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
    pass

from lib import (GRAMMAR_VALID_FIELDS, VALID_AXES_GRAMMAR, VALID_DIFFS,
                 parse_grammar_response)

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "grammar" / "questions.js"
STAGING_JSON = REPO_ROOT / "grammar" / "staging.json"
BATCH_STATE = REPO_ROOT / "grammar" / "batch_state.json"

DEFAULT_MODEL = "claude-sonnet-4-6"
VERIFY_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
BATCH_SIZE = 30
EXCLUDE_LIMIT = 3000

GRAMMAR_BY_LEVEL = {
    "lv1": "be動詞, 一般動詞の現在形, 人称代名詞, 冠詞a/the, 命令文, There is/are, 疑問文(What/Who/Where)",
    "lv2": "過去形, 未来形(will/be going to), 助動詞(can/must/should), 比較級・最上級, 受動態, 現在進行形, 不規則変化, 前置詞の基本",
    "lv3": "現在完了(継続/経験/完了), 関係代名詞(who/which/that), 不定詞・動名詞, 接続詞(although/unless/whether), 間接疑問文, 付加疑問文, 分詞の形容詞用法, due to / in spite of",
    "lv4": "仮定法過去/過去完了, 分詞構文, 倒置(Not only/Hardly/Never), 関係副詞, 使役動詞(make/let/have), 知覚動詞, suggest/insist + 原形, would rather + 過去形",
    "lv5": "仮定法の倒置(Had I/Were it not for), 複合関係詞(whatever/however), 否定の倒置, 同格that, 省略構文, 冠詞の微妙な使い分け, コロケーション(come into effect等), 名詞の可算/不可算",
}

AXIS_DESCRIPTIONS = {
    "form":  "form : 語形変化・活用（三単現-s, 過去形-ed, 品詞変換 -tion/-ly, 不規則変化等）",
    "vocab": "vocab: 語法・コロケーション・前置詞選択（depend on, consist of, refrain from等）",
    "logic": "logic: 文構造の論理（関係詞の先行詞、分詞の修飾先、並列構造、倒置等）",
    "tense": "tense: 時制・相の選択（過去/現在完了/未来/進行形の使い分け、時制マーカーに注目）",
    "trap":  "trap : 紛らわしい選択肢（似た語形、典型的な誤用パターン、日本人が間違えやすい表現）",
}

# diff → tags のデフォルトマッピング
DEFAULT_TAGS_BY_DIFF = {
    "lv1": ["eiken4"],
    "lv2": ["eiken3", "juken"],
    "lv3": ["eikenpre2", "toeic"],
    "lv4": ["eiken2", "toeic"],
    "lv5": ["eikenpre1", "toeic"],
}


def load_existing_stems():
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    stems = re.findall(r'\bstem:\s*"((?:[^"\\]|\\.)*)"', content)
    if len(stems) > EXCLUDE_LIMIT:
        stems = stems[-EXCLUDE_LIMIT:]
    return stems


def build_prompt(count, lv1, lv2, lv3, lv4, lv5, existing_stems, axis_only=None):
    existing_list = json.dumps(existing_stems, ensure_ascii=False, indent=2)

    if axis_only:
        per = count // len(axis_only)
        axis_lines = "\n".join(f"- {AXIS_DESCRIPTIONS[a]}" for a in axis_only)
        axis_instruction = f"各問題に以下の axis のいずれかを割り当て、均等に分散（各約{per}問）：\n{axis_lines}"
    else:
        axis_lines = "\n".join(f"- {d}" for d in AXIS_DESCRIPTIONS.values())
        axis_instruction = f"各問題に以下のいずれかを1つ割り当て、均等に分散（各約{count//5}問）：\n{axis_lines}"

    lv_details = "\n".join(
        f"- lv{i+1}: {[lv1,lv2,lv3,lv4,lv5][i]}問 — 文法範囲: {GRAMMAR_BY_LEVEL[f'lv{i+1}']}"
        for i in range(5)
    )

    return f"""以下のJSON形式で英文法クイズの問題を{count}問生成してください。

## 難易度の内訳
{lv_details}

## 難しさの質（axis フィールド）
{axis_instruction}

## 試験タグ（tags フィールド）
各問題の diff に応じてタグを付与：
- lv1: ["eiken4"]
- lv2: ["eiken3","juken"]
- lv3: ["eikenpre2","toeic"]
- lv4: ["eiken2","toeic"]
- lv5: ["eikenpre1","toeic"]
TOEICに特に頻出の問題は "toeic" を追加してください。

## 出力形式（JSONのみ出力、他の文章は不要）
[
  {{
    "diff": "lv1〜lv5",
    "axis": "form | vocab | logic | tense | trap",
    "tags": ["toeic", "eiken3"],
    "stem": "空欄 ___ を含む英文（例: She ___ to the store yesterday.）",
    "ja": "日本語訳（短く自然に）",
    "answer": "choices[0] と完全に同じ文字列",
    "choices": ["正解", "誤答1", "誤答2", "誤答3", "誤答4"],
    "expl": "なぜ正解なのかの日本語解説（1〜2文）",
    "rule": "文法項目名（例: 現在完了, 仮定法過去完了, look forward to -ing）",
    "kp": ["覚えるべきポイント1〜2個"]
  }}
]

## 制約（厳守）
- stem は空欄 ___ を必ず1つ含む英文
- **正解は必ず1つだけ**に絞れる文脈にすること。曖昧な問題は禁止
  - 時制問題: yesterday/since/by the time 等の時制マーカーを必ず含める
  - will vs be going to: 文脈で1つに絞れるシチュエーションにする
- choices は正解1つ + 紛らわしい誤答4つ（計5つ）
- **answer は必ず choices[0] と完全に一致**（システムが文字列一致で判定）
- choices[0] に正解を入れる（表示時にJSがシャッフル）
- 各 diff の文法範囲を厳守（lv1 で仮定法を出さない等）
- JSON のみ出力

## 既存問題リスト（重複禁止）
{existing_list}
"""


def verify_questions(client, model, questions):
    """二重チェック: 正解が本当に唯一の正解かを検証"""
    if not questions:
        return questions

    batch_text = json.dumps(questions, ensure_ascii=False, indent=2)
    prompt = f"""以下の英文法クイズの問題リストを検証してください。

各問題について以下を確認：
1. answer（正解）は文法的に本当に正しいか？
2. choices の中に answer 以外に正解になりうる選択肢はないか？
3. stem の英文は文法的に自然か？
4. expl の解説は正確か？

問題がある場合は、その問題の index（0始まり）と理由を報告してください。
問題ない場合は "ALL_OK" とだけ返してください。

形式:
FAIL: [index] 理由
FAIL: [index] 理由
...
または
ALL_OK

問題リスト:
{batch_text}"""

    try:
        resp = client.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        result = resp.content[0].text.strip()

        if "ALL_OK" in result:
            print(f"  検証: ALL OK ({len(questions)}問)")
            return questions

        # FAIL行を解析して該当問題を除外
        fail_indices = set()
        for line in result.split("\n"):
            m = re.match(r'FAIL:\s*\[(\d+)\]', line)
            if m:
                fail_indices.add(int(m.group(1)))

        if fail_indices:
            print(f"  検証: {len(fail_indices)}問を除外 (indices: {sorted(fail_indices)})")
            for idx in sorted(fail_indices):
                if idx < len(questions):
                    print(f"    [{idx}] {questions[idx].get('stem', '')[:50]}...")
            questions = [q for i, q in enumerate(questions) if i not in fail_indices]

        return questions
    except Exception as e:
        print(f"  WARNING: 検証スキップ ({e})")
        return questions


def split_levels(total_lv, remaining, batch_count):
    total = sum(total_lv)
    if total == 0:
        return [0, 0, batch_count, 0, 0]
    batch = [round(x * batch_count / total) for x in total_lv]
    diff = batch_count - sum(batch)
    batch[2] = max(0, batch[2] + diff)
    return batch


def run_normal(client, model, count, lv, existing_stems, axis_only=None):
    all_questions = []
    remaining_lv = list(lv)
    remaining = count
    batch_num = 1
    total_batches = -(-count // BATCH_SIZE)

    while remaining > 0:
        batch_count = min(remaining, BATCH_SIZE)
        bl = split_levels(remaining_lv, remaining, batch_count)
        bl1, bl2, bl3, bl4, bl5 = bl

        print(f"\n[{batch_num}/{total_batches}] {batch_count}問 "
              f"(lv1:{bl1} lv2:{bl2} lv3:{bl3} lv4:{bl4} lv5:{bl5}) 生成中...")

        exclude = existing_stems + [q["stem"] for q in all_questions]
        prompt = build_prompt(batch_count, bl1, bl2, bl3, bl4, bl5, exclude, axis_only=axis_only)

        try:
            resp = client.messages.create(
                model=model, max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            questions = parse_grammar_response(resp.content[0].text)
            print(f"  生成: {len(questions)}問")

            # 二重検証
            questions = verify_questions(client, VERIFY_MODEL, questions)

            all_questions.extend(questions)
            print(f"  累計: {len(all_questions)}問")
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            if all_questions:
                print(f"  取得済みの {len(all_questions)} 問を保存して終了します")
                break
            sys.exit(1)

        for i in range(5):
            remaining_lv[i] = max(0, remaining_lv[i] - bl[i])
        remaining -= batch_count
        batch_num += 1

    return all_questions


def main():
    parser = argparse.ArgumentParser(description="Claude API で英文法問題を生成して grammar/staging.json に保存")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--lv1", type=int, default=None)
    parser.add_argument("--lv2", type=int, default=None)
    parser.add_argument("--lv3", type=int, default=None)
    parser.add_argument("--lv4", type=int, default=None)
    parser.add_argument("--lv5", type=int, default=None)
    parser.add_argument("--batch", action="store_true", help="Batch API を使用（24時間以内・50%%オフ）")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--axis-only", default=None, help="生成する axis をカンマ区切り（例: form,tense）")
    parser.add_argument("--no-verify", action="store_true", help="二重検証をスキップ")
    args = parser.parse_args()

    axis_only = None
    if args.axis_only:
        axis_only = [a.strip() for a in args.axis_only.split(",")]
        invalid = [a for a in axis_only if a not in VALID_AXES_GRAMMAR]
        if invalid:
            print(f"ERROR: 無効な axis: {invalid}")
            print(f"  有効な値: {sorted(VALID_AXES_GRAMMAR)}")
            sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        print("  .env ファイルに ANTHROPIC_API_KEY=your_key を追加してください")
        sys.exit(1)

    count = args.count
    default_ratios = [0.25, 0.30, 0.25, 0.15, 0.05]
    if any(x is not None for x in [args.lv1, args.lv2, args.lv3, args.lv4, args.lv5]):
        lv = [args.lv1 or 0, args.lv2 or 0, args.lv3 or 0, args.lv4 or 0, args.lv5 or 0]
    else:
        lv = [round(count * r) for r in default_ratios]
        lv[4] = count - sum(lv[:4])

    print(f"生成設定: {count}問 (lv1:{lv[0]} lv2:{lv[1]} lv3:{lv[2]} lv4:{lv[3]} lv5:{lv[4]})")
    print(f"モデル: {args.model}  検証: {'OFF' if args.no_verify else 'ON'}")
    if axis_only:
        print(f"axis 指定: {axis_only}")

    existing_stems = load_existing_stems()
    print(f"既存問題数: {len(existing_stems)} 問")

    client = anthropic.Anthropic(api_key=api_key)

    if args.batch:
        print("ERROR: Batch モードは未実装です（通常モードを使用してください）")
        sys.exit(1)

    all_questions = run_normal(client, args.model, count, lv, existing_stems, axis_only=axis_only)
    if not all_questions:
        print("ERROR: 問題を1問も生成できませんでした", file=sys.stderr)
        sys.exit(1)

    STAGING_JSON.parent.mkdir(parents=True, exist_ok=True)
    STAGING_JSON.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(all_questions)}問 を grammar/staging.json に保存しました")
    print("次のステップ:")
    print("  cd /Users/yusuke/projects/claude/native-real && python3 add_grammar.py")


if __name__ == "__main__":
    main()
