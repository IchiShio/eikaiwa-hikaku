// questions.js — 50 questions
const DATA = [
  // ── lv1: meaning ──
  { diff: "lv1", axis: "meaning", word: "grateful", text: "I'm really grateful for your help with the project.", ja: "プロジェクトを手伝ってくれて本当に感謝しています。", answer: "感謝している", choices: ["感謝している","怒っている","退屈している","疲れている"], audio: "audio/q01.mp3", expl: "grateful は「感謝している」という意味。thankful とほぼ同義で、for のあとに感謝の対象がくる。" },
  { diff: "lv1", axis: "meaning", word: "obvious", text: "The answer was so obvious that everyone got it right.", ja: "答えがあまりにも明白だったので全員正解だった。", answer: "明らかな", choices: ["明らかな","難しい","曖昧な","面白い"], audio: "audio/q02.mp3", expl: "obvious は「明らかな、見ればわかる」という意味。clearly visible or understood。" },
  { diff: "lv1", axis: "meaning", word: "hesitate", text: "Don't hesitate to ask if you need anything.", ja: "何か必要なことがあれば遠慮なく聞いてください。", answer: "ためらう", choices: ["ためらう","急ぐ","忘れる","拒否する"], audio: "audio/q03.mp3", expl: "hesitate は「ためらう、躊躇する」という意味。Don't hesitate to 〜 で「遠慮なく〜してください」。" },
  { diff: "lv1", axis: "meaning", word: "curious", text: "She's always been curious about how things work.", ja: "彼女は物事の仕組みにいつも好奇心旺盛だった。", answer: "好奇心のある", choices: ["好奇心のある","怠惰な","慎重な","無関心な"], audio: "audio/q04.mp3", expl: "curious は「好奇心のある、知りたがりの」という意味。curious about 〜 で「〜に興味がある」。" },
  { diff: "lv1", axis: "meaning", word: "afford", text: "I can't afford to buy a new car right now.", ja: "今は新しい車を買う余裕がない。", answer: "〜する余裕がある", choices: ["〜する余裕がある","〜を望む","〜を避ける","〜を楽しむ"], audio: "audio/q05.mp3", expl: "afford は「〜する余裕がある」という意味。can't afford to 〜 で「〜する余裕がない」。金銭的・時間的余裕の両方に使う。" },

  // ── lv1: phrase ──
  { diff: "lv1", axis: "phrase", word: "look forward to", text: "I'm looking forward to the trip next week.", ja: "来週の旅行を楽しみにしています。", answer: "〜を楽しみにする", choices: ["〜を楽しみにする","〜を恐れる","〜を延期する","〜を思い出す"], audio: "audio/q06.mp3", expl: "look forward to 〜 は「〜を楽しみにする」。to のあとは名詞か動名詞（-ing）がくる。" },
  { diff: "lv1", axis: "phrase", word: "figure out", text: "I need to figure out how to fix this.", ja: "これをどう直すか考えないといけない。", answer: "〜を解明する・理解する", choices: ["〜を解明する・理解する","〜を壊す","〜を隠す","〜を無視する"], audio: "audio/q07.mp3", expl: "figure out は「理解する、解明する」という意味の句動詞。問題の解決策を考え出す場面でよく使う。" },

  // ── lv1: context ──
  { diff: "lv1", axis: "context", word: "rough", text: "She's had a rough day at work.", ja: "仕事でつらい一日だった。", answer: "つらい・大変な", choices: ["つらい・大変な","素晴らしい","普通の","短い"], audio: "audio/q08.mp3", expl: "rough は「ざらざらした」が基本の意味だが、ここでは「つらい、大変な」という比喩的な意味で使われている。" },
  { diff: "lv1", axis: "context", word: "pick up", text: "Can you pick up some milk on your way home?", ja: "帰りに牛乳を買ってきてくれる？", answer: "（ついでに）買ってくる", choices: ["（ついでに）買ってくる","持ち上げる","片付ける","捨てる"], audio: "audio/q09.mp3", expl: "pick up は「拾い上げる」が基本だが、この文脈では「ついでに買ってくる」という意味。日常でとてもよく使う。" },

  // ── lv2: meaning ──
  { diff: "lv2", axis: "meaning", word: "reluctant", text: "He was reluctant to share his opinion in the meeting.", ja: "彼は会議で自分の意見を言うのをためらっていた。", answer: "気が進まない", choices: ["気が進まない","熱心な","確信のある","怒った"], audio: "audio/q10.mp3", expl: "reluctant は「気が進まない、渋っている」という意味。reluctant to 〜 で「〜したがらない」。" },
  { diff: "lv2", axis: "meaning", word: "subtle", text: "There's a subtle difference between the two colors.", ja: "その2色には微妙な違いがある。", answer: "微妙な・わずかな", choices: ["微妙な・わずかな","大きな","はっきりした","人工的な"], audio: "audio/q11.mp3", expl: "subtle は「微妙な、かすかな」という意味。目に見えにくい、気づきにくい差異を表す。発音注意：b は発音しない（/sʌtl/）。" },
  { diff: "lv2", axis: "meaning", word: "overwhelm", text: "The amount of homework overwhelmed the students.", ja: "宿題の量が生徒たちを圧倒した。", answer: "圧倒する", choices: ["圧倒する","助ける","退屈させる","刺激する"], audio: "audio/q12.mp3", expl: "overwhelm は「圧倒する、打ちのめす」という意味。処理しきれないほど大量・強烈な状況に使う。" },
  { diff: "lv2", axis: "meaning", word: "inevitable", text: "Change is inevitable in any growing company.", ja: "成長する企業では変化は避けられない。", answer: "避けられない", choices: ["避けられない","望ましい","予想外の","徐々に起こる"], audio: "audio/q13.mp3", expl: "inevitable は「避けられない、必然的な」という意味。It is inevitable that 〜 の形でもよく使う。" },

  // ── lv2: phrase ──
  { diff: "lv2", axis: "phrase", word: "come across", text: "I came across an old photo while cleaning my room.", ja: "部屋を掃除していたら古い写真を見つけた。", answer: "偶然見つける", choices: ["偶然見つける","なくす","探し回る","写真を撮る"], audio: "audio/q14.mp3", expl: "come across は「偶然出くわす、たまたま見つける」という意味。意図せず見つけるニュアンスがポイント。" },
  { diff: "lv2", axis: "phrase", word: "put off", text: "Stop putting off your homework and just do it.", ja: "宿題を先延ばしにするのはやめてやりなさい。", answer: "延期する・先延ばしにする", choices: ["延期する・先延ばしにする","始める","楽しむ","完了する"], audio: "audio/q15.mp3", expl: "put off は「延期する、先延ばしにする」。procrastinate とほぼ同義。put off + 名詞/動名詞。" },
  { diff: "lv2", axis: "phrase", word: "run out of", text: "We've run out of coffee. Can you buy some?", ja: "コーヒーが切れた。買ってきてくれる？", answer: "〜を使い果たす・切らす", choices: ["〜を使い果たす・切らす","〜を注文する","〜を見つける","〜を共有する"], audio: "audio/q16.mp3", expl: "run out of 〜 は「〜がなくなる、使い果たす」。日用品や時間がなくなる場面でよく使う。" },

  // ── lv2: idiom ──
  { diff: "lv2", axis: "idiom", word: "break the ice", text: "He told a joke to break the ice at the party.", ja: "彼はパーティーで場を和ませるためにジョークを言った。", answer: "場の緊張をほぐす", choices: ["場の緊張をほぐす","パーティーを台無しにする","退場する","飲み物を用意する"], audio: "audio/q17.mp3", expl: "break the ice は「場の緊張をほぐす、口火を切る」という意味のイディオム。初対面の緊張を解く場面でよく使う。" },
  { diff: "lv2", axis: "idiom", word: "under the weather", text: "I'm feeling a bit under the weather today.", ja: "今日はちょっと体調が悪い。", answer: "体調が悪い", choices: ["体調が悪い","機嫌が悪い","天気が気になる","憂鬱だ"], audio: "audio/q18.mp3", expl: "under the weather は「体調が悪い」という意味のイディオム。軽い体調不良に使う。天気とは直接関係ない。" },

  // ── lv2: nuance ──
  { diff: "lv2", axis: "nuance", word: "look / see / watch", text: "She watched the sunset from the balcony.", ja: "彼女はバルコニーから夕日を眺めた。", answer: "じっと見る（動くものを注意して）", choices: ["じっと見る（動くものを注意して）","ちらっと見る","たまたま目に入る","じろじろ見る"], audio: "audio/q19.mp3", expl: "watch は「意識して注意深く見る」。特に動きのあるものに使う。see は自然に目に入る、look は視線を向ける。" },
  { diff: "lv2", axis: "nuance", word: "trip / travel / journey", text: "The journey from Tokyo to Osaka takes about two and a half hours by bullet train.", ja: "東京から大阪への旅は新幹線で約2時間半かかる。", answer: "（長距離の）旅・旅程", choices: ["（長距離の）旅・旅程","短い旅行","出張","通勤"], audio: "audio/q20.mp3", expl: "journey は出発地から目的地までの「移動・旅程」を強調。trip は往復を含む旅行、travel は旅行という行為全般。" },

  // ── lv2: context ──
  { diff: "lv2", axis: "context", word: "address", text: "We need to address this issue before the deadline.", ja: "期限前にこの問題に取り組む必要がある。", answer: "（問題に）取り組む・対処する", choices: ["（問題に）取り組む・対処する","住所を書く","演説する","配達する"], audio: "audio/q21.mp3", expl: "address は名詞「住所」が有名だが、動詞で「（問題に）取り組む、対処する」という意味もある。ビジネスでよく使う。" },
  { diff: "lv2", axis: "context", word: "deliver", text: "She delivered an impressive speech at the conference.", ja: "彼女はカンファレンスで印象的なスピーチをした。", answer: "（スピーチを）行う", choices: ["（スピーチを）行う","配達する","書く","中止する"], audio: "audio/q22.mp3", expl: "deliver は「配達する」が基本だが、deliver a speech/presentation で「スピーチ・プレゼンを行う」という意味になる。" },

  // ── lv3: meaning ──
  { diff: "lv3", axis: "meaning", word: "resilient", text: "Children are remarkably resilient and adapt quickly to change.", ja: "子どもは驚くほど回復力があり、変化にすぐ順応する。", answer: "回復力のある・立ち直りが早い", choices: ["回復力のある・立ち直りが早い","傷つきやすい","頑固な","のんびりした"], audio: "audio/q23.mp3", expl: "resilient は「回復力のある、打たれ強い」という意味。困難から立ち直る力を表す。名詞形は resilience。" },
  { diff: "lv3", axis: "meaning", word: "elaborate", text: "Could you elaborate on that point? I didn't quite understand.", ja: "その点をもう少し詳しく説明してもらえますか？よく理解できませんでした。", answer: "詳しく述べる", choices: ["詳しく述べる","要約する","反論する","同意する"], audio: "audio/q24.mp3", expl: "elaborate は動詞で「詳しく述べる」、形容詞で「精巧な、手の込んだ」。elaborate on 〜 で「〜について詳しく説明する」。" },
  { diff: "lv3", axis: "meaning", word: "viable", text: "Solar energy is becoming a more viable option for homeowners.", ja: "太陽光エネルギーは住宅所有者にとってより現実的な選択肢になりつつある。", answer: "実行可能な・現実的な", choices: ["実行可能な・現実的な","安価な","危険な","複雑な"], audio: "audio/q25.mp3", expl: "viable は「実行可能な、成り立つ」という意味。a viable option/alternative などの形でよく使う。" },
  { diff: "lv3", axis: "meaning", word: "comprehensive", text: "The report provides a comprehensive overview of the market.", ja: "そのレポートは市場の包括的な概要を提供している。", answer: "包括的な・全体を網羅した", choices: ["包括的な・全体を網羅した","簡潔な","偏った","古い"], audio: "audio/q26.mp3", expl: "comprehensive は「包括的な、総合的な」。広い範囲をカバーしている様子を表す。" },

  // ── lv3: phrase ──
  { diff: "lv3", axis: "phrase", word: "get away with", text: "He can't get away with breaking the rules every time.", ja: "彼は毎回ルール違反をして罰を逃れるわけにはいかない。", answer: "（罰を受けずに）逃れる", choices: ["（罰を受けずに）逃れる","ルールを守る","逮捕される","謝罪する"], audio: "audio/q27.mp3", expl: "get away with 〜 は「〜をしても罰を受けずに済む、見逃してもらう」。悪いことをしても咎められないニュアンス。" },
  { diff: "lv3", axis: "phrase", word: "turn down", text: "She turned down the job offer because the salary was too low.", ja: "給料が低すぎたので、彼女はその求人を断った。", answer: "断る・拒否する", choices: ["断る・拒否する","受け入れる","検討する","交渉する"], audio: "audio/q28.mp3", expl: "turn down は「断る、拒否する」。decline とほぼ同義。音量を下げるという意味もあるが、文脈で判断。" },

  // ── lv3: idiom ──
  { diff: "lv3", axis: "idiom", word: "hit the nail on the head", text: "You hit the nail on the head — that's exactly the problem.", ja: "まさにその通り——それがまさに問題なんだ。", answer: "的を射たことを言う", choices: ["的を射たことを言う","問題を悪化させる","釘を打つ","間違った指摘をする"], audio: "audio/q29.mp3", expl: "hit the nail on the head は「的を射たことを言う、核心をつく」というイディオム。相手の発言が正確だと認める場面で使う。" },
  { diff: "lv3", axis: "idiom", word: "on the same page", text: "Let's make sure we're all on the same page before we start.", ja: "始める前に全員が同じ認識でいることを確認しよう。", answer: "同じ認識を持っている", choices: ["同じ認識を持っている","同じ本を読んでいる","同じ場所にいる","同じ意見に反対している"], audio: "audio/q30.mp3", expl: "on the same page は「同じ認識を持っている、共通理解がある」。ビジネスミーティングでよく使われるイディオム。" },
  { diff: "lv3", axis: "idiom", word: "a blessing in disguise", text: "Losing that job turned out to be a blessing in disguise.", ja: "その仕事を失ったことが結局は幸運だった。", answer: "不幸に見えて実は幸運なこと", choices: ["不幸に見えて実は幸運なこと","大きな災難","予想通りの結果","単なる偶然"], audio: "audio/q31.mp3", expl: "a blessing in disguise は「不幸に見えて実は幸運なこと」。disguise（変装）に隠れた blessing（恩恵）。" },

  // ── lv3: nuance ──
  { diff: "lv3", axis: "nuance", word: "affect / effect", text: "The new policy will affect thousands of employees.", ja: "新しい方針は何千人もの社員に影響する。", answer: "〜に影響を与える（動詞）", choices: ["〜に影響を与える（動詞）","〜の結果をもたらす","〜を実施する","〜を無効にする"], audio: "audio/q32.mp3", expl: "affect は動詞「影響を与える」、effect は名詞「効果、影響」。affect = 動詞、effect = 名詞と覚えるのが基本。" },
  { diff: "lv3", axis: "nuance", word: "borrow / lend", text: "Can I borrow your charger for a minute?", ja: "充電器をちょっと借りてもいい？", answer: "（自分が）借りる", choices: ["（自分が）借りる","（相手に）貸す","（お金を）返す","（無料で）もらう"], audio: "audio/q33.mp3", expl: "borrow は「借りる」（自分に向かってくる動き）、lend は「貸す」（相手に向かっていく動き）。方向が逆。" },

  // ── lv3: context ──
  { diff: "lv3", axis: "context", word: "sharp", text: "Be there at 9 o'clock sharp.", ja: "9時きっかりにそこにいて。", answer: "きっかり・ちょうど", choices: ["きっかり・ちょうど","鋭い","賢い","厳しい"], audio: "audio/q34.mp3", expl: "sharp は「鋭い」が基本だが、時間の後ろにつくと「きっかり、ちょうど」の意味。at 3 sharp = 3時ちょうど。" },

  // ── lv4: meaning ──
  { diff: "lv4", axis: "meaning", word: "undermine", text: "Constant criticism can undermine a child's confidence.", ja: "絶え間ない批判は子どもの自信を徐々に損ないうる。", answer: "徐々に弱体化させる・損なう", choices: ["徐々に弱体化させる・損なう","強化する","支える","無視する"], audio: "audio/q35.mp3", expl: "undermine は「徐々に弱体化させる、土台を崩す」。under（下から）+ mine（掘る）で、基盤を掘り崩すイメージ。" },
  { diff: "lv4", axis: "meaning", word: "ambiguous", text: "The contract language is deliberately ambiguous.", ja: "契約書の文言は意図的に曖昧にされている。", answer: "曖昧な・多義的な", choices: ["曖昧な・多義的な","明確な","違法な","長い"], audio: "audio/q36.mp3", expl: "ambiguous は「曖昧な、複数の解釈ができる」。vague（漠然とした）と似ているが、ambiguous は「2つ以上の意味に取れる」ニュアンス。" },
  { diff: "lv4", axis: "meaning", word: "paramount", text: "Safety is of paramount importance in this industry.", ja: "この業界では安全が最も重要だ。", answer: "最も重要な・最高の", choices: ["最も重要な・最高の","部分的な","最小限の","標準的な"], audio: "audio/q37.mp3", expl: "paramount は「最も重要な、至上の」。of paramount importance で「最重要」。フォーマルな文脈で使う。" },

  // ── lv4: phrase ──
  { diff: "lv4", axis: "phrase", word: "boil down to", text: "The argument boils down to a matter of trust.", ja: "議論は結局のところ信頼の問題に帰着する。", answer: "結局〜に帰着する", choices: ["結局〜に帰着する","沸騰する","議論が激化する","問題が解決する"], audio: "audio/q38.mp3", expl: "boil down to 〜 は「結局〜に帰着する、要約すると〜になる」。複雑な問題の本質を述べる場面で使う。" },
  { diff: "lv4", axis: "phrase", word: "rule out", text: "The doctor ruled out any serious conditions.", ja: "医師は深刻な疾患の可能性を除外した。", answer: "〜の可能性を排除する", choices: ["〜の可能性を排除する","〜を診断する","〜を治療する","〜を確認する"], audio: "audio/q39.mp3", expl: "rule out は「〜の可能性を排除する、除外する」。医療やビジネスの意思決定場面でよく使う。" },

  // ── lv4: idiom ──
  { diff: "lv4", axis: "idiom", word: "the elephant in the room", text: "We need to talk about the elephant in the room — the budget cuts.", ja: "誰も触れたがらない問題について話す必要がある——予算削減のことだ。", answer: "誰もが気づいているが触れない問題", choices: ["誰もが気づいているが触れない問題","部屋の中の大きな物","重要でない問題","すでに解決した問題"], audio: "audio/q40.mp3", expl: "the elephant in the room は「誰もが気づいているのに誰も触れようとしない問題」。巨大な象が部屋にいるのに無視するイメージ。" },
  { diff: "lv4", axis: "idiom", word: "burn bridges", text: "Don't burn bridges with your old company — you might need their reference.", ja: "前の会社との関係を断ち切るな——推薦状が必要になるかもしれない。", answer: "関係を断ち切る・退路を断つ", choices: ["関係を断ち切る・退路を断つ","新しい関係を築く","妥協する","競争する"], audio: "audio/q41.mp3", expl: "burn bridges は「関係を断ち切る、退路を断つ」。橋を燃やして戻れなくするイメージ。主に否定形で「関係を壊すな」と使う。" },

  // ── lv4: nuance ──
  { diff: "lv4", axis: "nuance", word: "effective / efficient", text: "The new workflow is more efficient — we finish tasks in half the time.", ja: "新しいワークフローの方が効率的だ——半分の時間でタスクが終わる。", answer: "効率的な（無駄なく成果を出す）", choices: ["効率的な（無駄なく成果を出す）","効果的な（望む結果を出す）","経済的な","生産的な"], audio: "audio/q42.mp3", expl: "efficient は「効率的な」（少ないリソースで成果を出す）。effective は「効果的な」（望む結果を実現する）。efficient = HOW（方法）、effective = WHAT（結果）。" },

  // ── lv4: context ──
  { diff: "lv4", axis: "context", word: "critical", text: "The report was critical of the government's response to the crisis.", ja: "その報告書は危機に対する政府の対応に批判的だった。", answer: "批判的な", choices: ["批判的な","重要な","危機的な","分析的な"], audio: "audio/q43.mp3", expl: "critical は「重要な」「危機的な」という意味が有名だが、ここでは「批判的な」。critical of 〜 で「〜に対して批判的」。" },
  { diff: "lv4", axis: "context", word: "sound", text: "That sounds like a sound plan to me.", ja: "それは堅実な計画に思える。", answer: "堅実な・確かな", choices: ["堅実な・確かな","音に関する","大きな","複雑な"], audio: "audio/q44.mp3", expl: "sound は名詞「音」、動詞「〜に聞こえる」の他に、形容詞で「堅実な、確かな」という意味がある。sound advice（確かなアドバイス）。" },

  // ── lv5: meaning ──
  { diff: "lv5", axis: "meaning", word: "exacerbate", text: "The drought exacerbated the already dire food shortage.", ja: "干ばつがすでに深刻な食糧不足をさらに悪化させた。", answer: "悪化させる", choices: ["悪化させる","改善する","引き起こす","予防する"], audio: "audio/q45.mp3", expl: "exacerbate は「（すでに悪い状況を）さらに悪化させる」。worsen/aggravate と同義だが、よりフォーマル。" },
  { diff: "lv5", axis: "meaning", word: "ubiquitous", text: "Smartphones have become ubiquitous in modern life.", ja: "スマートフォンは現代生活でどこにでもある存在になった。", answer: "至る所にある", choices: ["至る所にある","高価な","必要不可欠な","時代遅れの"], audio: "audio/q46.mp3", expl: "ubiquitous は「至る所にある、遍在する」。everywhere と同義だがフォーマルで書き言葉向き。" },

  // ── lv5: phrase ──
  { diff: "lv5", axis: "phrase", word: "get the hang of", text: "It takes a while, but you'll get the hang of it eventually.", ja: "時間はかかるが、そのうちコツをつかめるようになるよ。", answer: "コツをつかむ・要領を得る", choices: ["コツをつかむ・要領を得る","飽きる","失敗する","諦める"], audio: "audio/q47.mp3", expl: "get the hang of 〜 は「〜のコツをつかむ」。新しいスキルや仕事に慣れていく過程で使う。" },

  // ── lv5: idiom ──
  { diff: "lv5", axis: "idiom", word: "cut corners", text: "We can't cut corners on safety — lives are at stake.", ja: "安全面で手を抜くことはできない——人命がかかっている。", answer: "手を抜く・手間を省く", choices: ["手を抜く・手間を省く","経費を削減する","近道をする","安全策を講じる"], audio: "audio/q48.mp3", expl: "cut corners は「手を抜く、近道をして品質を犠牲にする」。角（corner）をカットして最短距離を行くイメージ。否定文で使うことが多い。" },
  { diff: "lv5", axis: "idiom", word: "bite off more than you can chew", text: "I think I bit off more than I could chew with this project.", ja: "このプロジェクトで自分の能力以上のことを引き受けてしまった。", answer: "能力以上のことを引き受ける", choices: ["能力以上のことを引き受ける","とても成功する","簡単にやり遂げる","途中で投げ出す"], audio: "audio/q49.mp3", expl: "bite off more than you can chew は「能力以上のことを引き受ける、無理をする」。噛める以上に口に入れるイメージ。" },

  // ── lv5: nuance ──
  { diff: "lv5", axis: "nuance", word: "assume / presume", text: "I presume you've already read the report?", ja: "すでに報告書を読んだものと推察しますが？", answer: "（確信を持って）推定する", choices: ["（確信を持って）推定する","（根拠なく）思い込む","確認する","疑う"], audio: "audio/q50.mp3", expl: "presume は「（ある程度の根拠・確信を持って）推定する」。assume は「（証拠なしに）思い込む、仮定する」。presume の方がフォーマルで確信度が高い。" },

  // ── lv5: context ──
  { diff: "lv5", axis: "context", word: "exercise", text: "You should exercise caution when investing in volatile markets.", ja: "変動の激しい市場に投資する際は注意を払うべきだ。", answer: "（注意・権利などを）行使する", choices: ["（注意・権利などを）行使する","運動する","練習する","実験する"], audio: "audio/q51.mp3", expl: "exercise は「運動する」以外に「（権利・注意・影響力を）行使する」という意味がある。exercise caution = 注意を払う。フォーマルな表現。" },
  { diff: "lv5", axis: "context", word: "appreciate", text: "Stock prices are expected to appreciate over the next decade.", ja: "株価は今後10年間で値上がりすると予想されている。", answer: "価値が上がる", choices: ["価値が上がる","感謝する","理解する","安定する"], audio: "audio/q52.mp3", expl: "appreciate は「感謝する」が最も一般的だが、金融では「（資産が）価値を上げる」。反意語は depreciate（価値が下がる）。" }
];
