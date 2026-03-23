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
import random
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
RULES_JSON = REPO_ROOT / "grammar" / "grammar_rules.json"

DEFAULT_MODEL = "claude-sonnet-4-6"
VERIFY_MODEL = "claude-opus-4-6"
MAX_TOKENS = 8192
BATCH_SIZE = 30
EXCLUDE_LIMIT = 3000


def load_rules():
    """grammar_rules.json を読み込む"""
    if not RULES_JSON.exists():
        print(f"ERROR: {RULES_JSON} が見つかりません", file=sys.stderr)
        sys.exit(1)
    return json.loads(RULES_JSON.read_text(encoding="utf-8"))


def load_existing_stems():
    if not QUESTIONS_JS.exists():
        return []
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    stems = re.findall(r'\bstem:\s*"((?:[^"\\]|\\.)*)"', content)
    if len(stems) > EXCLUDE_LIMIT:
        stems = stems[-EXCLUDE_LIMIT:]
    return stems


def select_rules_for_batch(all_rules, count, lv_counts, axis_only=None):
    """バッチに使うルールをランダムに選択"""
    lv_names = ['lv1', 'lv2', 'lv3', 'lv4', 'lv5']
    selected = []

    for i, lv in enumerate(lv_names):
        n = lv_counts[i]
        if n == 0:
            continue
        candidates = [r for r in all_rules if r['diff'] == lv]
        if axis_only:
            candidates = [r for r in candidates if any(a in axis_only for a in r['axes'])]
        if not candidates:
            candidates = [r for r in all_rules if r['diff'] == lv]
        # ルール数よりcount が多い場合は繰り返し選択
        for _ in range(n):
            selected.append(random.choice(candidates))

    return selected


def format_rules_for_prompt(rules):
    """ルールをプロンプト用テキストに変換"""
    lines = []
    for r in rules:
        errors_parts = []
        for e in r.get("common_errors", []):
            if isinstance(e, dict):
                errors_parts.append(f'"{e["wrong"]}" ({e["why"]})')
            else:
                errors_parts.append(f'"{e}"')
        errors_text = "; ".join(errors_parts)
        lines.append(
            f'- [{r["id"]}] {r["rule"]} ({r["rule_en"]})\n'
            f'  diff: {r["diff"]}, axes: {r["axes"]}, tags: {r["tags"]}\n'
            f'  pattern: {r["pattern"]}\n'
            f'  example: {r["correct_example"]}\n'
            f'  common errors: {errors_text}\n'
            f'  key signal: {r["key_signal"]}'
        )
    return "\n".join(lines)


def build_prompt(count, lv1, lv2, lv3, lv4, lv5, existing_stems, axis_only=None, rules=None):
    existing_list = json.dumps(existing_stems[-500:] if len(existing_stems) > 500 else existing_stems,
                               ensure_ascii=False, indent=2)

    # ルールDBからバッチ用ルールを選択
    all_rules = rules or load_rules()
    selected = select_rules_for_batch(all_rules, count, [lv1, lv2, lv3, lv4, lv5], axis_only)
    rules_text = format_rules_for_prompt(selected)

    return f"""以下の文法ルールDBに基づいて、英文法クイズの問題を{count}問生成してください。

## 文法ルールDB（これらのパターンに基づいて類似問題を作成すること）
{rules_text}

## 生成ルール
- 各ルールの pattern に従った正解を作成
- 各ルールの common_errors を参考に紛らわしい誤答を作成
- correct_example とは異なる英文で出題すること（類似パターンの別の文を作る）
- key_signal を活用して、正解が1つに絞れる文脈を作ること

## 難易度の内訳
- lv1: {lv1}問 / lv2: {lv2}問 / lv3: {lv3}問 / lv4: {lv4}問 / lv5: {lv5}問

## 出力形式（JSONのみ出力、他の文章は不要）
[
  {{
    "diff": "lv1〜lv5",
    "axis": "form | vocab | logic | tense | trap",
    "tags": ["toeic", "eiken3"],
    "stem": "空欄 ___ を含む英文",
    "ja": "日本語訳",
    "answer": "choices[0] と完全に同じ文字列",
    "choices": ["正解", "誤答1", "誤答2", "誤答3", "誤答4"],
    "expl": "なぜ正解なのかの日本語解説（1〜2文）",
    "rule": "文法項目名（ルールDBのruleフィールドと同じ値を使うこと）",
    "kp": ["覚えるべきポイント1〜2個"]
  }}
]

## 制約（厳守）
- stem は空欄 ___ を必ず1つ含む
- **正解は必ず1つだけ**に絞れる文脈にすること
- choices は正解1つ + 紛らわしい誤答4つ（計5つ）
- **answer は必ず choices[0] と完全に一致**
- choices[0] に正解を入れる（JSがシャッフルして表示）
- JSON のみ出力

## 既存問題（重複禁止）
{existing_list}
"""


def verify_questions(client, model, questions):
    """二重チェック: 正解が本当に唯一の正解かを検証（Opusモデル推奨）"""
    if not questions:
        return questions

    batch_text = json.dumps(questions, ensure_ascii=False, indent=2)
    prompt = f"""あなたは英文法問題の品質検査官です。以下の問題リストを1問ずつ厳密に検証してください。

## 最重要チェック: 複数正解の検出

各問題について「answer 以外の choices に文法的に正解になりうるものがないか」を最優先で確認してください。
以下は特に注意すべき複数正解パターンです：

### よくある複数正解パターン（必ずチェック）
- need + -ing と need + to be pp（例: need repairing = need to be repaired）
- suggest/recommend/insist + that S + 原形 と should + 原形（両方正しい）
- used to と would（過去の習慣を表す場合、両方正しいことがある）
- Not only + does/can/will（助動詞の選択で複数正解になりうる）
- while / whereas / although（対比・譲歩で互換性がある場合）
- who / that（関係代名詞で人に対して両方使える）
- which / that（制限用法で物に対して両方使える）
- so ... that / such ... that（構文の入れ替えで両方正解になる場合）
- 前置詞の微妙な違い（in/at/on で文脈次第で複数正解）
- 能動態と受動態が両方成立する文（make/have/get + O + pp/原形）

### その他のチェック項目
1. answer は文法的に本当に正しいか？
2. stem の英文は自然で文法的に正確か？
3. expl の解説は正確か？
4. 難易度(diff)と実際の問題の難しさが合っているか？

## 判定ルール
- 「唯一の正解」と確信できる場合のみ PASS
- 「別の選択肢も正解になりうる」と少しでも疑われる場合は FAIL
- 疑わしきは FAIL（false negative より false positive を優先）

問題がある場合は、その問題の index（0始まり）と理由を報告してください。
問題ない場合は "ALL_OK" とだけ返してください。

形式:
FAIL: [index] 理由（どの選択肢がなぜ正解になりうるか具体的に）
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
    all_rules = load_rules()
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
        prompt = build_prompt(batch_count, bl1, bl2, bl3, bl4, bl5, exclude,
                             axis_only=axis_only, rules=all_rules)

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
