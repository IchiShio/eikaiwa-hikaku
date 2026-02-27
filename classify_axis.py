#!/usr/bin/env python3
"""
classify_axis.py - 既存問題に axis フィールドを一括付与

axis の定義:
  speed      : 発話が速い・詰まった話し方（"Didja hear that?" 等）
  reduction  : gonna/wanna/kinda/dunno/lemme 等の音変化・リンキング・脱落
  vocab      : 低頻度語・イディオム・スラング・比喩表現
  context    : 前後の文脈・話者のトーン・感情から正解を推論する必要がある
  distractor : 誤答が非常に紛らわしく、表面的な理解では正解できない

使い方:
  python3 classify_axis.py            # 全問を分類（Haiku 使用、~100円/460問）
  python3 classify_axis.py --dry-run  # 最初の30問だけ試す（本番変更なし）
  python3 classify_axis.py --model claude-sonnet-4-6  # モデル指定
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

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "listening" / "questions.js"
AXIS_CACHE = REPO_ROOT / "listening" / "axis_cache.json"  # 途中経過保存

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # 分類タスクは Haiku で十分
BATCH_SIZE = 30
VALID_AXES = {"speed", "reduction", "vocab", "context", "distractor"}


def load_questions_raw():
    """questions.js から各行を読み込む（1行 = 1問）"""
    content = QUESTIONS_JS.read_text(encoding="utf-8")
    lines = content.split("\n")
    return lines


def parse_question_from_line(line):
    """1行から text, diff を抽出して返す"""
    text_m = re.search(r'\btext:\s*"((?:[^"\\]|\\.)*)"', line)
    diff_m = re.search(r'\bdiff:\s*"(lv[1-5])"', line)
    if not text_m or not diff_m:
        return None
    return {
        "text": text_m.group(1).replace('\\"', '"').replace("\\\\", "\\"),
        "diff": diff_m.group(1),
    }


def load_cache():
    """axis_cache.json から既存の分類結果を読み込む"""
    if AXIS_CACHE.exists():
        return json.loads(AXIS_CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    AXIS_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def build_classify_prompt(questions):
    """分類プロンプトを構築"""
    items = []
    for i, q in enumerate(questions):
        items.append(f'{i+1}. [{q["diff"]}] {q["text"]}')
    items_str = "\n".join(items)

    return f"""以下の英語リスニングクイズの問題文を、指定の axis に分類してください。

## axis の定義
- speed      : 発話スピードが速い、詰まった話し方（"Didja hear that?" "Gonna hafta leave." "Whadya think?" 等）
- reduction  : gonna/wanna/kinda/dunno/lemme/sorta/hafta 等の音変化・リンキング・音の脱落が含まれる
- vocab      : 低頻度語・イディオム・スラング・比喩表現（"pull it off", "break a leg", "hit the sack" 等）が含まれる
- context    : 前後の文脈・話者のトーン・感情・状況から正解を推論する必要がある（語句自体は平易でも文脈依存）
- distractor : 誤答が非常に紛らわしく、表面的な語句理解だけでは正解できない（"just discovered" vs "first time visiting" 等）

## 分類ルール
- 最も特徴的な1つの axis を選ぶ
- speed と reduction は音声特徴が中心。vocab はテキストに稀語・イディオムがある場合
- context は「語句は分かるが何を言いたいかが文脈依存」な場合
- distractor は「語句も文脈も理解できるが選択肢で迷いやすい」場合

## 出力形式（JSON配列のみ、他の文章は不要）
[
  {{"id": 1, "axis": "vocab"}},
  {{"id": 2, "axis": "context"}},
  ...
]

## 分類対象（{len(questions)}問）
{items_str}
"""


def classify_batch(client, model, questions):
    """1バッチを分類してaxisのリストを返す"""
    prompt = build_classify_prompt(questions)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())

    results = json.loads(raw)
    axis_map = {}
    for item in results:
        axis_map[item["id"]] = item["axis"]
    return axis_map


def inject_axis_into_js(lines, text_to_axis):
    """questions.js の各行に axis フィールドを注入"""
    new_lines = []
    injected = 0
    skipped = 0
    for line in lines:
        if 'axis:' in line:
            new_lines.append(line)
            skipped += 1
            continue
        text_m = re.search(r'\btext:\s*"((?:[^"\\]|\\.)*)"', line)
        if not text_m:
            new_lines.append(line)
            continue
        text = text_m.group(1).replace('\\"', '"').replace("\\\\", "\\")
        if text in text_to_axis:
            axis = text_to_axis[text]
            # diff: "lv3", の直後に axis: "xxx", を挿入
            new_line = re.sub(
                r'(\bdiff:\s*"lv[1-5]")',
                rf'\1, axis: "{axis}"',
                line,
                count=1,
            )
            new_lines.append(new_line)
            injected += 1
        else:
            new_lines.append(line)
    return new_lines, injected, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="最初のバッチのみ実行・ファイル非更新")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    lines = load_questions_raw()
    cache = load_cache()

    # axis 未付与の問題を収集
    todo = []
    for line in lines:
        if 'axis:' in line:
            continue
        q = parse_question_from_line(line)
        if q and q["text"] not in cache:
            todo.append(q)

    print(f"分類対象: {len(todo)}問（キャッシュ済み: {len(cache)}問）")

    if args.dry_run:
        todo = todo[:BATCH_SIZE]
        print(f"--dry-run: 最初の {len(todo)} 問のみ処理します")

    # バッチ処理
    total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_i in range(total_batches):
        batch = todo[batch_i * BATCH_SIZE:(batch_i + 1) * BATCH_SIZE]
        print(f"バッチ {batch_i+1}/{total_batches}（{len(batch)}問）...", end=" ", flush=True)

        try:
            axis_map = classify_batch(client, args.model, batch)
            for idx, q in enumerate(batch):
                axis = axis_map.get(idx + 1)
                if axis in VALID_AXES:
                    cache[q["text"]] = axis
                else:
                    print(f"\n  WARNING: 無効なaxis '{axis}' → vocab にフォールバック")
                    cache[q["text"]] = "vocab"
            save_cache(cache)
            print(f"OK（キャッシュ保存済み）")
        except Exception as e:
            print(f"\nERROR: {e}")
            print("  途中まで axis_cache.json に保存済み。再実行すると続きから処理されます")
            break

    # questions.js に反映
    if not args.dry_run:
        lines_updated, injected, skipped = inject_axis_into_js(lines, cache)
        QUESTIONS_JS.write_text("\n".join(lines_updated), encoding="utf-8")
        print(f"\n✅ questions.js 更新完了: {injected}問にaxis付与（既存スキップ: {skipped}問）")
    else:
        print(f"\n[dry-run] questions.js は変更しませんでした")
        print(f"  分類結果（サンプル）:")
        for q in todo[:5]:
            axis = cache.get(q["text"], "未分類")
            print(f"  [{q['diff']}] [{axis}] {q['text'][:60]}")

    # 統計表示
    if cache:
        from collections import Counter
        counter = Counter(cache.values())
        print(f"\n分類分布（キャッシュ計 {len(cache)}問）:")
        for axis in ["speed", "reduction", "vocab", "context", "distractor"]:
            print(f"  {axis:12s}: {counter.get(axis, 0)}問")


if __name__ == "__main__":
    main()
