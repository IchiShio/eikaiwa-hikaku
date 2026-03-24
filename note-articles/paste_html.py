"""Copy HTML to macOS clipboard as rich text for pasting into note.com editor"""
import subprocess, sys, tempfile, os

def copy_html_to_clipboard(html_content):
    """Convert HTML to RTF and copy to clipboard"""
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
        f.write(f'<html><body>{html_content}</body></html>')
        tmp_html = f.name

    tmp_rtf = tmp_html.replace('.html', '.rtf')
    subprocess.run(['textutil', '-convert', 'rtf', '-output', tmp_rtf, tmp_html], check=True)

    # Use osascript to set clipboard from RTF file
    script = f'''
    set rtfFile to POSIX file "{tmp_rtf}"
    set rtfData to read rtfFile
    set the clipboard to rtfData
    '''
    subprocess.run(['osascript', '-e', script], check=True)

    os.unlink(tmp_html)
    os.unlink(tmp_rtf)

def article_01():
    return """
<p>英語を何年も勉強してきたのに、いざ会話になると口から出てこない。</p>

<p>「文法は分かるのに話せない」<br>「相手が何か言ったのに、何も返せなかった」</p>

<p>もしこの感覚に覚えがあるなら、それは英語力の問題ではなく、「教科書の英語」と「実際の会話」のギャップが原因かもしれません。</p>

<p>私は、実際のアメリカ人の日常会話データを分析しました。</p>

<p>使ったのは2つのコーパスです。</p>

<p>→ <b>SBCSAE</b>（UC Santa Barbara公開）: アメリカ人60人の日常会話、39,317発話、約14万語<br>
→ <b>BNC会話セクション</b>: イギリス英語の日常会話約420万語から抽出された頻度リスト</p>

<p>この記事では、そこから見えてきた「英語の会話の本当の姿」を、数字で示します。</p>

<hr>

<h2>発話の85%は6語以下</h2>

<p>39,317発話の語数を全て数えました。</p>

<p>→ 1-3語: <b>58.1%</b>（22,859発話）<br>
→ 4-6語: <b>26.9%</b>（10,595発話）<br>
→ 7-10語: 12.8%（5,017発話）<br>
→ 11語以上: 2.1%（846発話）</p>

<p><b>6語以下の発話が全体の85.1%。</b></p>

<p>つまり、ネイティブ同士の会話は「短い」のです。長い文を組み立てる必要はありません。短い文をポンポン返していくのが、会話の現実です。</p>

<hr>

<h2>最も多いフレーズは "I don't know"</h2>

<p>14万語の会話データから、3語の連鎖（trigram）を全て抽出しました。</p>

<p>最も多かったのは <b>"I don't know"（244回）</b>。2位の3.4倍です。</p>

<p>→ 1位: <b>I don't know — 244回</b><br>
→ 2位: a lot of — 72回<br>
→ 3位: you know what — 64回<br>
→ 4位: and I said — 55回<br>
→ 5位: you have to — 54回<br>
→ 6位: I don't think — 50回</p>

<p>教科書では肯定文から教えますが、実際の会話では「分からない」「そうは思わない」という<b>否定の表現が圧倒的に多い</b>のです。</p>

<hr>

<h2>"I don't" の後に来る動詞は3つで69%</h2>

<p>"I don't" の後に続く動詞を全453件調べました。</p>

<p>→ <b>know — 53.9%</b>（244回）<br>
→ <b>think — 11.0%</b>（50回）<br>
→ <b>wanna/want — 6.4%</b>（計29回）<br>
→ have — 4.2%（19回）<br>
→ care — 3.1%（14回）<br>
→ like — 2.9%（13回）</p>

<p>上位3語（know, think, want）だけで<b>69.1%</b>。</p>

<p>「分からない」と言えることは、会話の生存スキルです。分からないのに黙るより、"I don't know" と言える方がずっと会話は続きます。</p>

<hr>

<h2>教科書の英語と、実際の会話の違い</h2>

<p>420万語の会話コーパスから抽出された頻度データで比べました。</p>

<p><b>yeah vs yes:</b><br>
→ yeah: 58,810回<br>
→ yes: 17,898回<br>
→ <b>yeahはyesの3.3倍</b>。会話での「はい」のデフォルトはyeahです。</p>

<p><b>否定形:</b><br>
→ 縮約形（don't, can't等）: <b>78.3%</b><br>
→ フルフォーム（do not等）: 21.7%<br>
→ 否定の約8割は縮約形。"do not" より "don't" が標準です。</p>

<p><b>助動詞:</b><br>
→ can: <b>23,384回</b><br>
→ must: 2,997回（canの1/8）<br>
→ may: 620回（canの1/38）<br>
→ 教科書で時間をかけて習う must / may より、canの方がはるかに実用的です。</p>

<hr>

<h2>主語は I, you, it の3語で67%</h2>

<p>420万語の会話コーパスから抽出された頻度データで、代名詞の分布を調べました。</p>

<p>→ <b>I — 167,640回（28.4%）</b><br>
→ <b>you — 135,217回（22.9%）</b><br>
→ <b>it — 128,165回（21.7%）</b><br>
→ he — 48,322回（8.2%）<br>
→ they — 43,977回（7.5%）<br>
→ she — 33,763回（5.7%）<br>
→ we — 33,166回（5.6%）</p>

<p><b>I + you + it だけで全代名詞の67.4%。</b></p>

<p>会話では「自分のこと」「相手のこと」「それ以外のこと」の3つしか話題になりません。主語選びに迷う必要はありません。</p>

<hr>

<h2>会話は「発言」と「相づち」の繰り返し</h2>

<p>言語学の研究でも、この構造は確認されています。</p>

<p>Stolcke et al. (2000) は、アメリカ英語の電話会話2,400件を分析し、<b>発話の49%がStatement（発言）</b>で、<b>Statementの後にBackchannel（相づち）が続く確率は26%</b>であったと報告しています。</p>

<p>つまり英語の会話は「質問に答える」場ではなく、<b>「発言して、相づちをもらって、また発言する」の繰り返し</b>です。</p>

<p>私たちのSBCSAE分析でも、相手の発言の後に来る最も多い1語は "yeah"（721回）であり、"why"（16回）のような聞き返しはほとんど発生していません。</p>

<hr>

<h2>まとめ: データが示す「英語の会話の本当の姿」</h2>

<p>→ 発話の<b>85%は6語以下</b>。長い文は要らない<br>
→ 最頻フレーズは <b>"I don't know"</b>。否定から覚えるべき<br>
→ <b>yeahはyesの3.3倍</b>。教科書の英語は会話の英語ではない<br>
→ 主語は<b>I/you/itで67%</b>。3つで十分<br>
→ 会話は<b>発言+相づちの繰り返し</b></p>

<p>次の記事では、このデータに基づいて「まず何を返せばいいか」を解説します。</p>

<hr>

<h3>データの出典</h3>

<p><b>SBCSAE</b>（Santa Barbara Corpus of Spoken American English）<br>
UC Santa Barbara 言語学部公開。アメリカ人60人の日常会話録音の書き起こし。60会話・約14万語。CC BY-ND 3.0ライセンス。n-gram分析、発話長分析、文頭パターン分析は筆者が独自に実行。</p>

<p><b>BNC Demographic 頻度リスト</b><br>
British National Corpus 日常会話セクション（約420万語）から抽出された単語×品詞×出現回数の頻度リスト。Adam Kilgarriff 公開。</p>

<p><b>Stolcke, A. et al. (2000)</b><br>
"Dialogue act modeling for automatic tagging and recognition of conversational speech." Computational Linguistics, 26(3), 339-373.</p>
"""

if __name__ == '__main__':
    article = sys.argv[1] if len(sys.argv) > 1 else '01'
    if article == '01':
        copy_html_to_clipboard(article_01())
    print(f"Article {article} copied to clipboard as rich text")
