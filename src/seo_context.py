"""
docs/seo/ ディレクトリから最新のSEOコンテキストを読み込み、
コンテンツ生成時にキーワード戦略を自動反映させる。

使用方法:
    from src.seo_context import SEOContext
    seo = SEOContext()                      # docs/seo/ を自動検出
    injection = seo.get_keyword_injection() # プロンプトに追記する文字列を取得
"""
import re
from pathlib import Path


class SEOContext:
    """docs/seo/ の最新キーワード・戦略ドキュメントを読み込むクラス"""

    def __init__(self, docs_dir: str = "docs/seo") -> None:
        self.docs_dir = Path(docs_dir)
        self.priority_keywords: list[dict] = []
        self.phase2_topics: list[str] = []
        self._loaded = False
        self._load()

    # ------------------------------------------------------------------ #
    # ロード
    # ------------------------------------------------------------------ #

    def _load(self) -> None:
        """最新の keyword-research-*.md と strategy-*.md を読み込む"""
        if not self.docs_dir.exists():
            return

        # 最新の keyword-research ファイル（ファイル名降順でソート）
        kw_files = sorted(
            self.docs_dir.glob("keyword-research-*.md"), key=lambda p: p.name, reverse=True
        )
        if kw_files:
            self._parse_keywords(kw_files[0].read_text(encoding="utf-8"))

        # 最新の strategy ファイル
        strat_files = sorted(
            self.docs_dir.glob("strategy-*.md"), key=lambda p: p.name, reverse=True
        )
        if strat_files:
            self._parse_strategy(strat_files[0].read_text(encoding="utf-8"))

        self._loaded = bool(self.priority_keywords or self.phase2_topics)

    def _parse_keywords(self, content: str) -> None:
        """優先度S / A のキーワードを抽出してリストに格納"""
        # 「キーワード名」Vol 数字 / KD 数字 の形式
        kw_pattern = re.compile(r'「(.+?)」.*?Vol ([\d,]+) / KD (\d+)')

        for priority_label, section_re in [
            ("S", r"### 優先度S.*?(?=###|\Z)"),
            ("A", r"### 優先度A.*?(?=###|\Z)"),
        ]:
            section = re.search(section_re, content, re.DOTALL)
            if section:
                for m in kw_pattern.finditer(section.group()):
                    self.priority_keywords.append({
                        "keyword": m.group(1),
                        "volume": int(m.group(2).replace(",", "")),
                        "kd": int(m.group(3)),
                        "priority": priority_label,
                    })

    def _parse_strategy(self, content: str) -> None:
        """Phase 2 の優先コンテンツリストを抽出"""
        phase2 = re.search(r"## Phase 2.*?(?=## Phase 3|\Z)", content, re.DOTALL)
        if not phase2:
            return
        # 箇条書き行「数字. 〜」を取得
        for m in re.finditer(r"^\d+\.\s+(.+)", phase2.group(), re.MULTILINE):
            self.phase2_topics.append(m.group(1).strip())

    # ------------------------------------------------------------------ #
    # プロンプト注入
    # ------------------------------------------------------------------ #

    def get_keyword_injection(self, article_type: str = "how_to") -> str:
        """プロンプトに追記するSEOキーワード指示文を生成する。

        Args:
            article_type: "how_to" または "service_review"
        Returns:
            プロンプトに append する文字列。SEOドキュメントが存在しない場合は空文字。
        """
        if not self.priority_keywords:
            return ""

        s_kws = [k["keyword"] for k in self.priority_keywords if k["priority"] == "S"]
        a_kws = [k["keyword"] for k in self.priority_keywords if k["priority"] == "A"]

        lines = [
            "",
            "---",
            "## SEOキーワード指示（docs/seo/ から自動注入）",
            "以下のキーワードを記事内に**自然に**含めてください（詰め込みや不自然な使用はNG）:",
        ]

        if s_kws:
            kw_list = "・".join(s_kws[:3])
            lines.append(f"- 最優先（必ず1回以上使用）: {kw_list}")

        if a_kws:
            kw_list = "・".join(a_kws[:3])
            lines.append(f"- 優先（自然に含める）: {kw_list}")

        if article_type == "how_to" and self.phase2_topics:
            lines.append("")
            lines.append("現在の重点コンテンツ戦略（Phase 2）:")
            for topic in self.phase2_topics[:4]:
                lines.append(f"  - {topic}")

        lines += [
            "",
            "※ キーワードは読者にとって有益な文脈でのみ使用。SEO目的の無理な挿入は不要。",
            "---",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # ユーティリティ
    # ------------------------------------------------------------------ #

    def is_loaded(self) -> bool:
        return self._loaded

    def summary(self) -> str:
        """ロード状態のサマリーを返す（ログ用）"""
        s_count = sum(1 for k in self.priority_keywords if k["priority"] == "S")
        a_count = sum(1 for k in self.priority_keywords if k["priority"] == "A")
        return (
            f"優先度S: {s_count}件, 優先度A: {a_count}件, Phase2トピック: {len(self.phase2_topics)}件"
        )
