#!/usr/bin/env python3
"""
generate_readup.py - ReadUp パッセージ型問題生成
  Haiku で問題生成 → Sonnet でファクトチェック → reading/staging.json に保存

Usage:
  python3 generate_readup.py              # 全20トピック（約500問）
  python3 generate_readup.py --no-check   # ファクトチェックなし（高速）
  python3 generate_readup.py --resume     # staging.json がある場合は続きから
"""
import argparse, json, os, re, sys, time
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

REPO_ROOT    = Path(__file__).parent
STAGING_JSON = REPO_ROOT / "reading" / "staging.json"

GEN_MODEL   = "claude-haiku-4-5-20251001"
CHECK_MODEL = "claude-sonnet-4-6"
MAX_TOKENS  = 8192

VALID_AXES  = {"main_idea", "vocab_context", "inference", "detail", "tone"}
VALID_DIFFS = {"lv1", "lv2", "lv3", "lv4", "lv5"}

# 20 トピック × 10 パッセージ = 200 パッセージ → 約 500 問
TOPICS = [
    {"id": "daily",   "ja": "日常生活・ルーティン・習慣"},
    {"id": "food",    "ja": "食事・栄養・食文化"},
    {"id": "tech",    "ja": "テクノロジー・AI・デジタル社会"},
    {"id": "env",     "ja": "環境・気候変動・自然エネルギー"},
    {"id": "travel",  "ja": "旅行・観光・異文化体験"},
    {"id": "work",    "ja": "仕事・キャリア・職場環境"},
    {"id": "edu",     "ja": "教育・学習・スキル開発"},
    {"id": "sci",     "ja": "科学・研究・発見・宇宙"},
    {"id": "society", "ja": "社会問題・コミュニティ・ニュース"},
    {"id": "hist",    "ja": "歴史・文化・伝統・遺産"},
    {"id": "arts",    "ja": "芸術・音楽・映画・エンタメ"},
    {"id": "sports",  "ja": "スポーツ・フィットネス・競技"},
    {"id": "psych",   "ja": "心理学・行動・感情・思考"},
    {"id": "biz",     "ja": "ビジネス・経済・起業・お金"},
    {"id": "nature",  "ja": "動物・植物・生態系・自然界"},
    {"id": "health",  "ja": "医療・健康・ウェルネス・予防"},
    {"id": "life",    "ja": "ライフスタイル・趣味・創造性"},
    {"id": "comm",    "ja": "コミュニケーション・言語・SNS"},
    {"id": "urban",   "ja": "都市生活・交通・住まい・建築"},
    {"id": "global",  "ja": "グローバル問題・国際関係・多様性"},
]

# 1 トピックあたりの難易度配分（合計10パッセージ）
DIFF_PER_TOPIC = [("lv1", 2), ("lv2", 3), ("lv3", 3), ("lv4", 1), ("lv5", 1)]
PASSAGES_PER_TOPIC = sum(n for _, n in DIFF_PER_TOPIC)  # 10


# ─── プロンプト ────────────────────────────────────────────────────────────────

def build_gen_prompt(topic):
    diff_list = "\n".join(f"  - {d}: {n}パッセージ" for d, n in DIFF_PER_TOPIC)
    return f"""ReadUp英語読解クイズ用のパッセージ型問題を生成してください。

トピック: {topic['ja']}
合計: {PASSAGES_PER_TOPIC}パッセージ（各2〜3問）

難易度配分:
{diff_list}

難易度の目安（Graded Reader語彙コントロール基準）:
- lv1: GR Level 1相当（Oxford 3000上位400語）
       2〜3文・短い単純文（SVO基本）
       不明語があれば文脈から確実に推測可能
       使用可能語彙例: go, get, make, have, see, know, good, big, try, learn
- lv2: GR Level 2相当（Oxford 3000上位700語）
       3〜4文・接続詞・基本的な関係詞OK
       軽い推論が必要な表現を1つまで含む
       使用可能語彙例: provide, require, allow, suggest, improve, increase, system
- lv3: GR Level 3相当（Oxford 3000上位1,000語）
       3〜4文・やや複雑な構造
       文脈から語彙の意味を推測する力が必要
       使用可能語彙例: demonstrate, contribute, significant, various, achieve, process
- lv4: GR Level 4相当（Oxford 3000上位1,400語）
       4〜5文・複文・分詞構文OK
       専門的でない分野での高頻度語まで使用可
       使用可能語彙例: implement, establish, fundamental, perspective, contemporary
- lv5: GR Level 5相当（Oxford 5000上位1,800語）
       5文以上・複雑な構造・受動態・仮定法
       文脈なしでは理解しにくい表現を含む
       使用可能語彙例: scrutinize, nuanced, paradigm, inherently, sustained

重要: 各レベルで指定語彙範囲外の単語を使う場合は、必ず文脈から意味が推測できるように書くこと。

axisの種類（各passageに2〜3種使う）:
- main_idea: パッセージ全体の主旨・テーマを問う
- vocab_context: 文中の語句を文脈から理解する
- inference: 明記されていないことを推論する
- detail: パッセージ中の具体的な情報を問う
- tone: 著者のトーン・態度・目的を問う

制約:
- passageは一般的に知られた事実のみ（架空の統計・数値禁止）
- 設問・選択肢・解説はすべて日本語
- 選択肢は4択（正解1つ＋誤答3つ）
- choicesにanswerを含め、先頭以外の位置に置く（先頭は誤答にする）
- kpはpassageから根拠となる英語フレーズ2〜3個

JSON配列のみ出力（コードブロック・説明文不要）:
[
  {{
    "pid": "{topic['id']}_01",
    "diff": "lv2",
    "passage": "English passage here (3-5 sentences).",
    "questions": [
      {{
        "axis": "main_idea",
        "question": "設問文（日本語）",
        "answer": "正解選択肢（日本語）",
        "choices": ["誤答A", "正解", "誤答B", "誤答C"],
        "expl": "解説。passageの根拠箇所を引用して説明する。",
        "kp": ["key phrase from passage", "another phrase"]
      }}
    ]
  }}
]"""


def build_factcheck_prompt(passages):
    data = json.dumps(passages, ensure_ascii=False, indent=2)
    return f"""以下のReadUp英語読解問題をファクトチェックしてください。

チェック項目:
1. passageの内容が事実として正確か（誤情報・ハルシネーションがないか）
2. answerがpassageの内容から正当化できるか
3. 誤答choicesが明確に誤りか
4. explの解説が正確か

各passageについてok: true/falseを返す。
falseの場合は修正後のpassageとquestionsを返す。

出力形式（JSONのみ、コードブロック不要）:
[
  {{"pid": "daily_01", "ok": true}},
  {{"pid": "daily_02", "ok": false, "passage": "修正後", "questions": [{{...}}]}}
]

対象データ:
{data}"""


# ─── パース ───────────────────────────────────────────────────────────────────

def parse_passages(raw, topic_id):
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # トランケートされた場合のリカバリー
        for end_pattern in ["}\n]", "},\n  {", "  }\n]"]:
            pos = raw.rfind(end_pattern)
            if pos >= 0:
                try:
                    candidate = raw[:pos + len(end_pattern.rstrip(","))] + "\n]"
                    data = json.loads(candidate)
                    print(f"  WARNING: truncated, recovered {len(data)} passages")
                    break
                except json.JSONDecodeError:
                    continue
        else:
            print(f"  ERROR: JSON parse failed (first 200): {raw[:200]}")
            return []

    valid = []
    for idx, p in enumerate(data, 1):
        if not isinstance(p, dict):
            continue
        # pid の正規化
        if not p.get("pid"):
            p["pid"] = f"{topic_id}_{idx:02d}"
        if not p.get("passage") or not p.get("diff"):
            continue
        if p["diff"] not in VALID_DIFFS:
            continue

        qs_valid = []
        for q in p.get("questions", []):
            if not isinstance(q, dict):
                continue
            required = {"axis", "question", "answer", "choices", "expl", "kp"}
            if required - set(q.keys()):
                continue
            if q.get("axis") not in VALID_AXES:
                continue
            if not isinstance(q.get("choices"), list) or len(q["choices"]) != 4:
                continue
            # answerが選択肢に含まれていることを確認
            if q["answer"] not in q["choices"]:
                q["choices"][1] = q["answer"]  # 2番目に挿入
            qs_valid.append(q)

        if qs_valid:
            p["questions"] = qs_valid
            valid.append(p)

    return valid


# ─── API 呼び出し ─────────────────────────────────────────────────────────────

def generate_topic(client, topic):
    prompt = build_gen_prompt(topic)
    resp = client.messages.create(
        model=GEN_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_passages(resp.content[0].text, topic["id"])


def factcheck_passages(client, passages):
    prompt = build_factcheck_prompt(passages)
    resp = client.messages.create(
        model=CHECK_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())

    try:
        results = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  WARNING: factcheck parse failed, accepting all")
        return passages

    result_map = {r["pid"]: r for r in results if isinstance(r, dict)}
    fixed = []
    for p in passages:
        r = result_map.get(p["pid"])
        if r is None or r.get("ok", True):
            fixed.append(p)
        else:
            # 修正版を適用
            if "passage" in r:
                p["passage"] = r["passage"]
            if "questions" in r:
                p["questions"] = r["questions"]
            fixed.append(p)
            print(f"  FIXED: {p['pid']}")
    return fixed


# ─── メイン ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-check", action="store_true", help="Sonnetファクトチェックをスキップ")
    parser.add_argument("--resume",   action="store_true", help="staging.jsonが存在すれば続きから")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません (.env または環境変数)")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Resume モード: 既存の staging を読み込む
    all_passages = []
    done_topics = set()
    if args.resume and STAGING_JSON.exists():
        try:
            all_passages = json.loads(STAGING_JSON.read_text(encoding="utf-8"))
            # 既に処理済みのトピックIDを抽出
            for p in all_passages:
                tid = p["pid"].split("_")[0]
                done_topics.add(tid)
            print(f"Resume: {len(all_passages)} passages loaded. Done topics: {sorted(done_topics)}")
        except Exception as e:
            print(f"WARNING: Could not load staging ({e}), starting fresh")

    print(f"\n=== ReadUp Generation ===")
    print(f"Gen model  : {GEN_MODEL}")
    print(f"Check model: {CHECK_MODEL}  {'(skipped)' if args.no_check else ''}")
    print(f"Topics     : {len(TOPICS)} × {PASSAGES_PER_TOPIC} = {len(TOPICS)*PASSAGES_PER_TOPIC} passages")
    print()

    for i, topic in enumerate(TOPICS, 1):
        if topic["id"] in done_topics:
            print(f"[{i:02d}/{len(TOPICS)}] {topic['ja']} — SKIP")
            continue

        print(f"[{i:02d}/{len(TOPICS)}] {topic['ja']}")

        # 生成
        try:
            passages = generate_topic(client, topic)
        except Exception as e:
            print(f"  ERROR (gen): {e}")
            time.sleep(3)
            continue

        if not passages:
            print(f"  ERROR: No passages returned")
            continue

        print(f"  Generated: {len(passages)} passages, "
              f"{sum(len(p.get('questions',[])) for p in passages)} questions")

        # ファクトチェック（Sonnet）
        if not args.no_check:
            print(f"  Fact-checking with {CHECK_MODEL}...")
            try:
                passages = factcheck_passages(client, passages)
            except Exception as e:
                print(f"  WARNING: factcheck failed ({e}), accepting all")

        all_passages.extend(passages)

        # 中間保存
        STAGING_JSON.write_text(
            json.dumps(all_passages, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        total_q = sum(len(p.get("questions", [])) for p in all_passages)
        print(f"  Saved. Running total: {len(all_passages)} passages / {total_q} questions")

        time.sleep(0.5)

    # 最終集計
    total_q = sum(len(p.get("questions", [])) for p in all_passages)
    print(f"\n=== Complete ===")
    print(f"Passages  : {len(all_passages)}")
    print(f"Questions : {total_q}")
    print(f"Saved to  : {STAGING_JSON}")
    print(f"\nNext step : python3 build_readup.py")


if __name__ == "__main__":
    main()
