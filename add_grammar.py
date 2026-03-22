#!/usr/bin/env python3
"""
add_grammar.py - grammar/staging.json の問題を questions.js に追加

処理フロー:
  1. grammar/staging.json 読み込み・バリデーション
  2. grammar/questions.js から現在の問題数・最大IDを取得
  3. 各問題に id フィールドを付与（g051, g052, ...）
  4. questions.js 末尾の ]; の前に新問題を追記
  5. git add . && git commit && git push
  6. staging.json をクリア
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from lib import GRAMMAR_VALID_FIELDS, VALID_AXES_GRAMMAR, VALID_DIFFS

REPO_ROOT = Path(__file__).parent
QUESTIONS_JS = REPO_ROOT / "grammar" / "questions.js"
STAGING_JSON = REPO_ROOT / "grammar" / "staging.json"


def load_staging():
    if not STAGING_JSON.exists():
        print(f"ERROR: {STAGING_JSON} が見つかりません", file=sys.stderr)
        sys.exit(1)

    content = STAGING_JSON.read_text(encoding="utf-8").strip()
    if not content or content == "[]":
        print("staging.json が空です。generate_grammar.py を先に実行してください。")
        sys.exit(0)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON パースエラー: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("ERROR: staging.json はリスト形式である必要があります", file=sys.stderr)
        sys.exit(1)

    print(f"staging.json から {len(data)} 問を読み込みました")

    errors = []
    auto_fixed = []
    for i, q in enumerate(data):
        missing = GRAMMAR_VALID_FIELDS - set(q.keys())
        if missing:
            errors.append(f"  [{i}] 必須フィールドが不足: {missing}")
        if q.get("diff") not in VALID_DIFFS:
            errors.append(f"  [{i}] diff が不正: {q.get('diff')}")
        if q.get("axis") not in VALID_AXES_GRAMMAR:
            errors.append(f"  [{i}] axis が不正: {q.get('axis')}")
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 5:
            errors.append(f"  [{i}] choices は5要素のリストが必要")
        if not isinstance(q.get("tags"), list):
            errors.append(f"  [{i}] tags はリストが必要")
        if not isinstance(q.get("kp"), list) or len(q["kp"]) == 0:
            errors.append(f"  [{i}] kp は1要素以上のリストが必要")

        # answer === choices[0]
        choices = q.get("choices", [])
        if isinstance(choices, list) and len(choices) > 0:
            if q.get("answer") != choices[0]:
                original = q.get("answer", "")
                if original in choices:
                    idx = choices.index(original)
                    choices[0], choices[idx] = choices[idx], choices[0]
                    q["choices"] = choices
                    auto_fixed.append(f"  [{i}] choices スワップ: [0]<->[{idx}]")
                else:
                    q["answer"] = choices[0]
                    auto_fixed.append(f"  [{i}] answer 自動補正: \"{original}\" -> \"{choices[0]}\"")

    if auto_fixed:
        print("WARNING: answer/choices 自動補正:")
        for msg in auto_fixed:
            print(msg)

    if errors:
        print("ERROR: バリデーションエラー:")
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    return data


def get_max_id(content):
    """questions.js から最大の g*** ID番号を取得"""
    ids = re.findall(r'\bid:\s*"g(\d+)"', content)
    if not ids:
        return 0
    return max(int(x) for x in ids)


def get_existing_count(content):
    count = len(re.findall(r'\bstem:', content))
    print(f"現在の問題数: {count} 問")
    return count


def format_question_js(q):
    def esc(s):
        return (str(s).replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t"))

    choices_str = json.dumps(q["choices"], ensure_ascii=False)
    kp_str = json.dumps(q["kp"], ensure_ascii=False)
    tags_str = json.dumps(q["tags"], ensure_ascii=False)

    return (
        f'  {{ id: "{q["id"]}", diff: "{q["diff"]}", axis: "{esc(q["axis"])}", '
        f'tags: {tags_str}, stem: "{esc(q["stem"])}", ja: "{esc(q["ja"])}", '
        f'answer: "{esc(q["answer"])}", choices: {choices_str}, '
        f'expl: "{esc(q["expl"])}", rule: "{esc(q["rule"])}", kp: {kp_str} }}'
    )


def append_to_questions_js(content, new_questions):
    m = re.search(r'\];\s*$', content)
    if not m:
        print("ERROR: questions.js に ]; が見つかりません", file=sys.stderr)
        sys.exit(1)
    last_bracket_pos = m.start()

    before = content[:last_bracket_pos].rstrip()
    if before and not before.endswith(","):
        before += ","

    new_lines = ",\n".join(format_question_js(q) for q in new_questions)
    new_content = before + "\n" + new_lines + "\n];\n"

    QUESTIONS_JS.write_text(new_content, encoding="utf-8")


def git_commit_push(n_added, total):
    cmds = [
        ["git", "-C", str(REPO_ROOT), "add", "."],
        ["git", "-C", str(REPO_ROOT), "commit", "-m",
         f"Add {n_added} grammar questions (total: {total})"],
        ["git", "-C", str(REPO_ROOT), "push"],
    ]
    for cmd in cmds:
        print(f"$ {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        if result.stdout:
            print(result.stdout.rstrip())


def main():
    staging = load_staging()

    if not QUESTIONS_JS.exists():
        print(f"ERROR: {QUESTIONS_JS} が見つかりません", file=sys.stderr)
        sys.exit(1)

    content = QUESTIONS_JS.read_text(encoding="utf-8")
    existing_count = get_existing_count(content)
    max_id = get_max_id(content)

    # ID付与
    for i, q in enumerate(staging):
        q["id"] = f"g{max_id + i + 1:03d}"

    # questions.js に追記
    print(f"\nquestions.js に {len(staging)} 問を追記中...")
    append_to_questions_js(content, staging)
    total = existing_count + len(staging)
    print(f"追記完了（{existing_count} -> {total} 問）")

    # git commit & push
    print("\ngit commit & push...")
    git_commit_push(len(staging), total)

    # staging クリア
    STAGING_JSON.write_text("[]\n", encoding="utf-8")
    print(f"\n完了！ 問題数: {existing_count} -> {total} 問")


if __name__ == "__main__":
    main()
