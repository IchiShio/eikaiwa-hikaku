"""
native-real.com 週次アナリティクスレポート生成スクリプト
- GA4 Data API でデータ取得（今週 + 先週比較）
- Claude API で分析・改善提案を生成
- analytics/reports/YYYY-MM-DD.md に保存
"""

import os
import json
from datetime import datetime, timedelta, timezone

import anthropic
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric,
    FilterExpression, Filter,
)
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────
# 設定
# ─────────────────────────────────────────
JST = timezone(timedelta(hours=9))
today = datetime.now(JST)

# 今週（直近7日）
end_date  = (today - timedelta(days=1)).strftime('%Y-%m-%d')
start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')

# 先週（比較用）
prev_end   = (today - timedelta(days=8)).strftime('%Y-%m-%d')
prev_start = (today - timedelta(days=14)).strftime('%Y-%m-%d')

PROPERTY_ID = os.environ['GA4_PROPERTY_ID']

TARGET_EVENTS = [
    'quiz_answer',
    'email_gate_view',
    'email_gate_register',
    'email_gate_skip',
]

# ─────────────────────────────────────────
# GA4 クライアント初期化
# ─────────────────────────────────────────
def get_ga4_client():
    creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/analytics.readonly'],
    )
    return BetaAnalyticsDataClient(credentials=credentials)

ga4 = get_ga4_client()

# ─────────────────────────────────────────
# データ取得ヘルパー
# ─────────────────────────────────────────
def run_report(dimensions, metrics, date_start, date_end, dimension_filter=None):
    req = RunReportRequest(
        property=f'properties/{PROPERTY_ID}',
        date_ranges=[DateRange(start_date=date_start, end_date=date_end)],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
    )
    if dimension_filter:
        req.dimension_filter = dimension_filter
    return ga4.run_report(req)


def get_site_metrics(start, end):
    """サイト全体の基本指標"""
    resp = run_report(
        [],
        ['sessions', 'totalUsers', 'newUsers', 'screenPageViews', 'averageSessionDuration'],
        start, end,
    )
    if not resp.rows:
        return {}
    v = resp.rows[0].metric_values
    return {
        'sessions':        int(v[0].value),
        'users':           int(v[1].value),
        'new_users':       int(v[2].value),
        'page_views':      int(v[3].value),
        'avg_session_sec': float(v[4].value),
    }


def get_listening_metrics(start, end):
    """/listening/ ページの指標"""
    resp = run_report(
        [],
        ['screenPageViews', 'totalUsers', 'averageSessionDuration'],
        start, end,
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name='pagePath',
                string_filter=Filter.StringFilter(
                    value='/listening/',
                    match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                ),
            )
        ),
    )
    if not resp.rows:
        return {'page_views': 0, 'users': 0, 'avg_session_sec': 0}
    v = resp.rows[0].metric_values
    return {
        'page_views':      int(v[0].value),
        'users':           int(v[1].value),
        'avg_session_sec': float(v[2].value),
    }


def get_event_counts(start, end):
    """カスタムイベントの集計"""
    resp = run_report(
        ['eventName'],
        ['eventCount'],
        start, end,
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name='eventName',
                in_list_filter=Filter.InListFilter(values=TARGET_EVENTS),
            )
        ),
    )
    return {
        row.dimension_values[0].value: int(row.metric_values[0].value)
        for row in resp.rows
    }


# ─────────────────────────────────────────
# データ取得
# ─────────────────────────────────────────
print('GA4からデータ取得中...')
site_this  = get_site_metrics(start_date, end_date)
site_prev  = get_site_metrics(prev_start, prev_end)
lst_this   = get_listening_metrics(start_date, end_date)
lst_prev   = get_listening_metrics(prev_start, prev_end)
ev_this    = get_event_counts(start_date, end_date)
ev_prev    = get_event_counts(prev_start, prev_end)

# ─────────────────────────────────────────
# 計算ヘルパー
# ─────────────────────────────────────────
def pct_change(curr, prev):
    if prev == 0:
        return 'N/A'
    c = (curr - prev) / prev * 100
    return f'{"+" if c >= 0 else ""}{c:.1f}%'

def fmt_sec(sec):
    m, s = divmod(int(sec), 60)
    return f'{m}分{s:02d}秒'

def rate(num, denom):
    return f'{num / denom * 100:.1f}%' if denom > 0 else 'N/A'


# ─────────────────────────────────────────
# データサマリー（テーブル形式）
# ─────────────────────────────────────────
gate_view  = ev_this.get('email_gate_view', 0)
gate_reg   = ev_this.get('email_gate_register', 0)
gate_skip  = ev_this.get('email_gate_skip', 0)
quiz_total = ev_this.get('quiz_answer', 0)

data_summary = f"""
### サイト全体

| 指標 | 今週 | 先週 | 前週比 |
|---|---|---|---|
| セッション | {site_this.get('sessions', 0):,} | {site_prev.get('sessions', 0):,} | {pct_change(site_this.get('sessions', 0), site_prev.get('sessions', 0))} |
| ユーザー | {site_this.get('users', 0):,} | {site_prev.get('users', 0):,} | {pct_change(site_this.get('users', 0), site_prev.get('users', 0))} |
| 新規ユーザー | {site_this.get('new_users', 0):,} | {site_prev.get('new_users', 0):,} | {pct_change(site_this.get('new_users', 0), site_prev.get('new_users', 0))} |
| ページビュー | {site_this.get('page_views', 0):,} | {site_prev.get('page_views', 0):,} | {pct_change(site_this.get('page_views', 0), site_prev.get('page_views', 0))} |
| 平均セッション時間 | {fmt_sec(site_this.get('avg_session_sec', 0))} | {fmt_sec(site_prev.get('avg_session_sec', 0))} | - |

### /listening/ ページ

| 指標 | 今週 | 先週 | 前週比 |
|---|---|---|---|
| ページビュー | {lst_this.get('page_views', 0):,} | {lst_prev.get('page_views', 0):,} | {pct_change(lst_this.get('page_views', 0), lst_prev.get('page_views', 0))} |
| ユーザー | {lst_this.get('users', 0):,} | {lst_prev.get('users', 0):,} | {pct_change(lst_this.get('users', 0), lst_prev.get('users', 0))} |
| 平均滞在時間 | {fmt_sec(lst_this.get('avg_session_sec', 0))} | {fmt_sec(lst_prev.get('avg_session_sec', 0))} | - |

### クイズ・メールゲート ファネル

| 指標 | 今週 | 先週 | 前週比 |
|---|---|---|---|
| クイズ回答数 | {quiz_total:,} | {ev_prev.get('quiz_answer', 0):,} | {pct_change(quiz_total, ev_prev.get('quiz_answer', 0))} |
| ゲート表示回数 | {gate_view:,} | {ev_prev.get('email_gate_view', 0):,} | {pct_change(gate_view, ev_prev.get('email_gate_view', 0))} |
| メール登録完了 | {gate_reg:,} | {ev_prev.get('email_gate_register', 0):,} | {pct_change(gate_reg, ev_prev.get('email_gate_register', 0))} |
| スキップ | {gate_skip:,} | {ev_prev.get('email_gate_skip', 0):,} | {pct_change(gate_skip, ev_prev.get('email_gate_skip', 0))} |
| **登録率**（表示→登録） | **{rate(gate_reg, gate_view)}** | {rate(ev_prev.get('email_gate_register', 0), ev_prev.get('email_gate_view', 0))} | - |
| スキップ率 | {rate(gate_skip, gate_view)} | {rate(ev_prev.get('email_gate_skip', 0), ev_prev.get('email_gate_view', 0))} | - |
"""

# ─────────────────────────────────────────
# Claude 分析
# ─────────────────────────────────────────
print('Claude で分析中...')
claude = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

message = claude.messages.create(
    model='claude-haiku-4-5-20251001',
    max_tokens=1500,
    messages=[{
        'role': 'user',
        'content': f"""あなたは英語学習サービスのグロースアナリストです。
native-real.com（英語リスニングクイズ「ListenUp」）の週次データを分析し、日本語でレポートを作成してください。

サービス概要：
- 455問の英語リスニングクイズ（無料）
- 5問後にメールゲート表示（Beehiiv登録）
- 登録後は1日15問まで無料
- 収益化：英会話サービスのアフィリエイト（メインサイト native-real.com）

{data_summary}

以下の形式で Markdown レポートを出力してください（見出しレベルは ## から）：

## 今週のサマリー
（2〜3行で全体の状況を簡潔に）

## トレンド分析
（前週比で注目すべき変化をポジティブ/ネガティブ両面から）

## ファネル考察
（クイズ→ゲート表示→登録率→スキップ率の評価と仮説）

## 改善アクション提案（優先度順）
（具体的で実行可能な提案を3〜5項目、各項目に「優先度：高/中/低」を付ける）

## 来週の注目KPI
（来週特に追うべき指標1〜2つとその理由）
""",
    }],
)
analysis = message.content[0].text

# ─────────────────────────────────────────
# レポート組み立て・保存
# ─────────────────────────────────────────
report = f"""# native-real.com 週次分析レポート

**期間**: {start_date} 〜 {end_date}
**生成日時**: {today.strftime('%Y-%m-%d %H:%M')} JST
**自動生成**: GitHub Actions + Claude Haiku

---

## 生データ
{data_summary}

---

{analysis}
"""

os.makedirs('analytics/reports', exist_ok=True)
report_path = f"analytics/reports/{today.strftime('%Y-%m-%d')}.md"
latest_path = 'analytics/reports/latest.md'

with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)
with open(latest_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f'レポート保存完了: {report_path}')
