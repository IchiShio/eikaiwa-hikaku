#!/usr/bin/env python3
"""
build_readup.py - reading/staging.json → reading/questions.js に変換して git push

Usage:
  python3 build_readup.py
  python3 build_readup.py --no-push   # git push せずにファイルだけ更新
"""
import argparse, json, os, subprocess, sys
from collections import Counter
from pathlib import Path

REPO_ROOT    = Path(__file__).parent
STAGING_JSON = REPO_ROOT / "reading" / "staging.json"
QUESTIONS_JS = REPO_ROOT / "reading" / "questions.js"


def flatten_questions(passages):
    """パッセージリスト → フラットな問題リスト"""
    questions = []
    for p in passages:
        pid     = p["pid"]
        diff    = p["diff"]
        passage = p["passage"]
        for j, q in enumerate(p.get("questions", []), 1):
            questions.append({
                "id":       f"rp_{pid}_{j}",
                "pid":      pid,
                "diff":     diff,
                "axis":     q["axis"],
                "passage":  passage,
                "question": q["question"],
                "answer":   q["answer"],
                "choices":  q["choices"],
                "expl":     q["expl"],
                "kp":       q.get("kp", []),
            })
    return questions


def js_str(s):
    """Python文字列 → JS文字列リテラル（ダブルクォート）"""
    return json.dumps(s, ensure_ascii=False)


def to_js_obj(q):
    choices = ", ".join(js_str(c) for c in q["choices"])
    kp      = ", ".join(js_str(k) for k in q["kp"])
    return (
        f'  {{ id:{js_str(q["id"])}, pid:{js_str(q["pid"])}, '
        f'diff:"{q["diff"]}", axis:"{q["axis"]}",\n'
        f'    passage:{js_str(q["passage"])},\n'
        f'    question:{js_str(q["question"])},\n'
        f'    answer:{js_str(q["answer"])},\n'
        f'    choices:[{choices}],\n'
        f'    expl:{js_str(q["expl"])},\n'
        f'    kp:[{kp}] }}'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-push", action="store_true", help="git push をスキップ")
    args = parser.parse_args()

    if not STAGING_JSON.exists():
        print(f"ERROR: {STAGING_JSON} not found")
        print("Run: python3 generate_readup.py")
        sys.exit(1)

    passages  = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
    questions = flatten_questions(passages)

    if not questions:
        print("ERROR: No questions in staging.json")
        sys.exit(1)

    # 統計表示
    diff_counts = Counter(q["diff"] for q in questions)
    axis_counts = Counter(q["axis"] for q in questions)
    print(f"Passages  : {len(passages)}")
    print(f"Questions : {len(questions)}")
    print(f"Diff      : {dict(sorted(diff_counts.items()))}")
    print(f"Axis      : {dict(sorted(axis_counts.items()))}")

    # diff 順にソート（lv1 → lv5）
    diff_order = {"lv1": 0, "lv2": 1, "lv3": 2, "lv4": 3, "lv5": 4}
    questions.sort(key=lambda q: (diff_order.get(q["diff"], 9), q["id"]))

    # JS 生成
    header = (
        f"// ReadUp questions.js — v2.0 パッセージ型 ({len(questions)}問)\n"
        "// axis: main_idea / vocab_context / inference / detail / tone\n"
        "const DATA = [\n"
    )

    blocks = []
    current_diff = None
    group = []
    for q in questions:
        if q["diff"] != current_diff:
            if group:
                blocks.append(f"\n  // ── {current_diff} ({len(group)}問) ─────────────────────────\n")
                blocks.extend(group)
            current_diff = q["diff"]
            group = []
        group.append(to_js_obj(q))
    if group:
        blocks.append(f"\n  // ── {current_diff} ({len(group)}問) ─────────────────────────\n")
        blocks.extend(group)

    content = header + ",\n\n".join(b for b in blocks if b.startswith("  {")) + "\n];\n"
    # コメント行を挿入し直す（join がコメントを飛ばすので再構築）
    lines = [header.rstrip("\n")]
    current_diff = None
    diff_group = []
    for q in questions:
        if q["diff"] != current_diff:
            if current_diff is not None and diff_group:
                lines.append(f"\n  // ── {current_diff} ({len(diff_group)}問) ─────────────────────────")
                lines.append(",\n\n".join(diff_group))
            current_diff = q["diff"]
            diff_group = []
        diff_group.append(to_js_obj(q))
    if diff_group:
        lines.append(f"\n  // ── {current_diff} ({len(diff_group)}問) ─────────────────────────")
        lines.append(",\n\n".join(diff_group))

    content = "\n".join(lines) + "\n\n];\n"

    QUESTIONS_JS.write_text(content, encoding="utf-8")
    print(f"\nWritten: {QUESTIONS_JS}")

    if args.no_push:
        print("(--no-push: git push skipped)")
        return

    print("\nCommitting and pushing...")
    os.chdir(REPO_ROOT)
    subprocess.run(["git", "add", "reading/questions.js"], check=True)
    subprocess.run(
        ["git", "commit", "-m",
         f"ReadUp v2.0: パッセージ型問題 {len(questions)}問（{len(passages)}パッセージ）"],
        check=True
    )
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("✅ Pushed to GitHub!")


if __name__ == "__main__":
    main()
