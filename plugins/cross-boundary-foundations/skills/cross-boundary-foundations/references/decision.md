# ⑥ 設計判断の記録（なぜそうしたか）リサーチノート

調査日: 2026-10-07
対象: アーキテクチャの判断、仕様・デザインの判断、事業上の判断を記録すること。経緯の残し方も含む。

## 表記と調査の制約

- 【確認】 原文（または原文と同じ内容の公式リポジトリ）を実際に開いて、書いてあることを確かめた。
- 【未確認】 原文を開けなかった。検索エンジンの要約だけで知った内容を含む。引用や細部は原文で確かめるまで使わないこと。
- 【解釈】 調査者の解釈・提案。出典が直接言っていることではない。

**この環境のネットワーク制約**: 調査環境の出口プロキシが大半のサイトを遮断していた。開けたのは GitHub の raw ファイル（raw.githubusercontent.com）、code.claude.com、www.anthropic.com だけである。そのため次の資料は**すべて【未確認】**。
Nygard の原文（cognitect.com）、adr.github.io の公開ページ（ただしページのソースは GitHub で確認済み）、Google の design docs 記事（industrialempathy.com）、Martin Fowler の bliki、Thoughtworks Radar、Spotify Engineering、Amazon の株主への手紙、Atlassian の DACI、Bain の RAPID、QOC と IBIS の論文、Jintae Lee (1997)。
これらは検索結果の要約から概要だけ拾い、【未確認】と書いた。公開前に、通信制限のない環境で原文を開いて確かめる必要がある。

---

## 0. 定義と範囲

### 用語

- **Architectural Decision (AD)**: 【確認】adr.github.io（サイトのソース）の定義は "a justified design choice that addresses a functional or non-functional requirement that is architecturally significant"。つまり、アーキテクチャ上重要な機能要件・非機能要件に答える、理由のある設計上の選択。
- **ADR (Architectural Decision Record)**: 【確認】"captures a single AD and its rationale"。判断 1 件と、その理由を記録したもの。
- **Decision log**: 【確認】"The collection of ADRs created and maintained in a project constitute its decision log"。プロジェクトで作り、保守してきた ADR の集まり。
- **"any decision record"**: 【確認】同じページに "ADR usage can be extended to design and other decisions ("any decision record")" とある。設計以外の判断にも使える。MADR は 3.0 のころ名称を "Markdown Any Decision Records" に変えたが、4.0.0 (2024-09) で "Architectural" に戻した。ただし "They can still be used to sustain any decision" と書いており、建築以外の判断に使うことは今も認めている。
- **Design rationale（デザインラショナール）**: HCI・設計学の研究領域。【未確認】源流は Kunz & Rittel (1970) の IBIS（Issue / Position / Argument）と MacLean ら (1991) の QOC（Questions / Options / Criteria）とされる。

### このノートでの範囲【解釈】

「設計判断の記録」を、次の 3 種類の判断について、**何を選び、何を選ばず、なぜそうしたか**を、後から来た人（人間と AI）が読める形で残す実践として扱う。

| 種類 | 例 | 代表的な形式 |
|---|---|---|
| アーキテクチャの判断 | DB の選定、同期か非同期か、モノリスを分割するか | ADR / MADR、RFC、Design Doc |
| 仕様・デザインの判断 | 削除を取り消せるようにするか、開始ボタンの色、エラー表示の位置 | デザインラショナール、デザインシステムの判断ログ、コンポーネントの「Research」欄 |
| 事業上の判断 | 無料プランを残すか、対象市場の優先度 | プロダクトの意思決定ログ、DACI ページ、6-pager 型の文書 |

「議事録」とは違う。議事録は「何が話されたか」を時系列に並べたもの。判断の記録は「何が決まり、何を退け、なぜか」を判断 1 件ごとに独立させたもの。

---

## 1. エンジニア視点（10 項目）

### E1. 判断 1 件につき 1 ファイル。Context / Decision / Status / Consequences の 4 つを最低限そろえる

- **何をするか**: 判断ごとにファイルを 1 つ作る。少なくとも「背景（Context）」「決めたこと（Decision）」「状態（Status）」「結果として起きること（Consequences）」を書く。
- **なぜか**: 【確認】Nygard 型テンプレート（Joel Parker Henderson のリポジトリにある写し）は 4 つの節をそれぞれ次の問いとして定義している。Context "What is the issue that we're seeing that is motivating this decision or change?"、Decision "What is the change that we're proposing and/or doing?"、Consequences "What becomes easier or more difficult to do because of this change?"。良い ADR の条件には "Specific: Each ADR should be about one AD, not multiple ADs" とある。【未確認】Nygard の原文（2011）は、新しく来た人は判断の理由を知らなければ「盲目的に受け入れる」か「盲目的に変える」しかできない、と動機を説明しているとされる（検索要約による）。
- **悪い例**: 「技術選定まとめ.md」に DB、キュー、認証の判断を 1 ファイルで書く。どれか 1 つを変えても、どこを直したかが追えない。
- **良い例**: `0007-use-postgres-for-orders.md` と `0008-use-sqs-for-notifications.md` に分ける。各ファイルの Consequences に「難しくなること」も書く。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record （README と `locales/en/templates/decision-record-template-by-michael-nygard/index.md`）、【未確認】https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html

### E2. 検討して退けた案を、退けた理由と一緒に書く

- **何をするか**: 選んだ案だけでなく、検討した案すべてと、それぞれの長所・短所を書く。
- **なぜか**: 【確認】MADR テンプレートには "Considered Options" と "Pros and Cons of the Options" の節があり、結論は `Chosen option: "...", because {justification}` という形で書く。Rust RFC テンプレートは "What other designs have been considered and what is the rationale for not choosing them?" を問う。Kubernetes KEP テンプレートの "Alternatives" 節は "What other approaches did you consider, and why did you rule them out?" と問う。PEP 1 の "Rejected Ideas" は、退けた案を記録する目的を "preventing people from bringing up the same rejected idea again in subsequent discussions" と説明している（同じ案が議論に何度も戻ってくるのを防ぐ）。
- **悪い例**: 「Redis を採用。」とだけ書く。半年後に「Memcached のほうが軽いのでは」という議論が最初からやり直しになる。
- **良い例**: 「Considered: Redis / Memcached / DB キャッシュ。Memcached はデータ構造が足りずランキング機能を実装できないので退けた。」
- **出典**: https://github.com/adr/madr/blob/main/template/adr-template.md 、https://github.com/rust-lang/rfcs/blob/master/0000-template.md 、https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md 、https://github.com/python/peps/blob/main/peps/pep-0001.rst

### E3. 状態（Status）を持たせる。消さずに「置き換え」でつなぐ

- **何をするか**: proposed / accepted / rejected / deprecated / superseded のような状態を持たせる。古い判断は消さずに、新しい判断へのリンクを付ける。
- **なぜか**: 【確認】MADR の front matter は `status: "{proposed | rejected | accepted | deprecated | … | superseded by ADR-0123}"`。Backstage の ADR 運用は "Records are never deleted but can be marked as superseded by new decisions or deprecated" と定め、置き換えたときは古い ADR の状態を "superseded by ADR-XXXX" にしてリンクを張る。PEP 1 は却下も記録として残す理由を "It is still important to have a record of this fact" と書き、決着したら Status を更新し、決定を告げた投稿へのリンクを Resolution ヘッダーに入れるよう求めている。
- **悪い例**: 方針が変わったので古い ADR を削除する。「前はなぜ違ったのか」が誰にも分からなくなる。
- **良い例**: ADR-0007 の状態を `superseded by ADR-0021` にする。ADR-0021 の Context に「0007 の前提（注文量が月 1 万件）が崩れたため」と書く。
- **出典**: https://github.com/adr/madr/blob/main/template/adr-template.md 、https://github.com/backstage/backstage/blob/master/docs/architecture-decisions/index.md 、https://github.com/python/peps/blob/main/peps/pep-0001.rst

### E4. 不変か、日付つき追記か。チームで先に決めておく

- **何をするか**: 決まった ADR を書き換えない（新しい ADR で置き換える）のか、日付と「決定後に分かったこと」の印を付けて追記してよいのか、運用を先に決める。
- **なぜか**: 【確認】Joel Parker Henderson の README は、良い ADR の条件に "Immutable: Don't alter existing information in an ADR" を挙げている。一方で同じ README の Teamwork advice は "In theory, immutability is ideal. In practice, mutability has worked better for our teams" と書き、日付と「決定後に入った情報」の注記を付けて追記する運用を紹介している。正解は 1 つではない。
- **悪い例**: 誰かが決定理由の一文を黙って書き換える。当時の判断と今の解釈の区別がつかなくなる。
- **良い例**: `> 2026-09-01 追記（決定後の情報）: ベンダーの料金体系が変わり、Consequences のコスト見積もりは無効。再検討は ADR-0030 で。`
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record

### E5. コードの隣（同じリポジトリ）に置き、PR で通す

- **何をするか**: `docs/decisions/NNNN-title-with-dashes.md` のように、コードと同じリポジトリに Markdown で置く。提案は PR として出し、レビューを受ける。
- **なぜか**: 【確認】MADR は `docs/decisions` に置くことと `NNNN-title-with-dashes.md` という命名を勧めている。理由は "to keep them close to the documentation but also separate the decisions from other documentation"。MADR の文書は "It should be as easy as possible to a) write down the decisions and b) to version the decisions" とも書く。Backstage の手順は「テンプレートをコピー → PR を出す → コミュニティの意見を反映 → 番号を振る → マージ」。【未確認】Thoughtworks Radar（Lightweight ADR, Adopt）は、wiki ではなくソース管理に置けばコードと同期した記録になる、と勧めている（検索要約による）。
- **悪い例**: 判断は Confluence に、コードは GitHub に置く。リンクが切れて、誰も見なくなる。
- **良い例**: 実装の PR と同じ PR、または直前の PR で ADR を追加する。PR の説明文から ADR にリンクする。
- **出典**: https://github.com/adr/madr 、https://github.com/backstage/backstage/blob/master/docs/architecture-decisions/index.md 、【未確認】https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records

### E6. 提案の文書（RFC / Design Doc）と、決定の記録（ADR）を分ける

- **何をするか**: 議論中の大きな提案は RFC や Design Doc で揉む。合意した結果は ADR として短く残す。
- **なぜか**: 【確認】GOV.UK Design System の architecture リポジトリは、文書を "Proposals, often referred to as 'requests for comments'" と "Decision Records, which document decisions that have been made, along with any context" の 2 種類に分けている。【未確認】Spotify Engineering (2020) は、影響の大きい変更では RFC で合意を作り、その解を ADR に残す流れを紹介している（検索要約による）。【未確認】Google の design docs（Malte Ubl の記事）は "Goals and non-goals" と "Alternatives considered" を持ち、トレードオフを中心に書く文書とされる。
- **悪い例**: 30 ページの Design Doc を「決定記録」として扱う。何が最終的に決まったのかが文書のどこにも書かれていない。
- **良い例**: Design Doc の末尾に「この提案は ADR-0012 として採択」と書く。ADR-0012 は 1 ページにまとめ、Design Doc へリンクする。
- **出典**: https://github.com/alphagov/govuk-design-system-architecture 、【未確認】https://engineering.atspotify.com/2020/4/when-should-i-write-an-architecture-decision-record 、【未確認】https://www.industrialempathy.com/posts/design-docs-at-google/

### E7. 「目的ではないこと（Non-goals）」を書く

- **何をするか**: 目標と一緒に、「目標にしてもおかしくないが、今回はあえて目標にしないこと」を書く。
- **なぜか**: 【確認】KEP テンプレートは "Non-Goals" を "What is out of scope for this KEP? Listing non-goals helps to focus discussion and make progress" と説明している。【未確認】Google design docs の記事にも同じ趣旨の説明があるとされる（「クラッシュしない」のような目標の否定形ではなく、目標になりえたものを書く）。
- **悪い例**: 目標に「速い検索」とだけ書く。後で「多言語対応は？」と聞かれ、議論が広がる。
- **良い例**: 「Non-goals: 今回は日本語以外の形態素解析に対応しない（理由: 利用者の 98% が日本語。数字の出典はダッシュボード X）」
- **出典**: https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md

### E8. 書く・書かないの基準を、判断の重さで決める

- **何をするか**: どの判断で ADR を書くかを決めておく。小さく、戻せて、一人で閉じる判断は書かない。
- **なぜか**: 【確認】Joel Parker Henderson の README は、書かない理由の例として "decisions that are not about architecture, or are tiny such as minimal-risk or self-contained or single-developer, or are already fully covered elsewhere ... or are temporary such as workarounds or proofs of concepts" を挙げている。書く理由の例は "when we want future developers to understand the 'why'"。【未確認】Spotify の記事は「記録されていない過去の判断を後から書く」ことも勧めているとされる。
- **悪い例**: 変数名の決め方まで ADR にする。誰も読まなくなり、重要な ADR も埋もれる。
- **良い例**: 「外部 API の互換性を壊す」「データモデルを変える」「新しい依存を足す」は必須。それ以外は PR の説明文で足りる。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record

### E9. 判断が守られているかを、テストやチェックで確かめる

- **何をするか**: 判断の記録に「どう確かめるか」を書く。可能なら CI のチェック（fitness function）にする。
- **なぜか**: 【確認】MADR には "Confirmation" 節があり、"Describe how the implementation / compliance of the ADR can/will be confirmed" と書く。ArchUnit などを例に挙げている。Joel Parker Henderson の README は "A decision record documents the decision, while a fitness function assures the decision" とし、さらに監視対象のパスが変わったのに ADR が追加・更新されていない PR を落とす GitHub Action（ADR Guard）を紹介している。
- **悪い例**: 「UI 層から DB を直接呼ばない」と ADR に書いただけ。半年で破られる。
- **良い例**: ADR の Confirmation に「`ui/` から `db/` への import を禁止する lint ルール `no-ui-db` で確認」と書き、CI で実際に動かす。
- **出典**: https://github.com/adr/madr/blob/main/template/adr-template.md 、https://github.com/joelparkerhenderson/architecture-decision-record

### E10. 1 か月後に振り返り、反対意見も残す

- **何をするか**: 決めたあとに「実際どうだったか」を確かめる日を決める。反対意見は消さずに残す。
- **なぜか**: 【確認】Joel Parker Henderson の README は、Consequences の書き方として "It's typical for teams to review each ADR one month later, to compare the ADR information with what's happened in actual practice" を挙げている。PEP 1 は、提案者の責任を "building consensus within the community and documenting dissenting opinions" と定めている。MADR の "More Information" は "if/when it should be re-visited" を書く場所としている。
- **悪い例**: 反対した人の懸念が記録になく、懸念どおりの障害が起きたときに「誰も予見しなかった」と扱われる。
- **良い例**: 「反対意見: B さん（運用負荷が 2 倍になる懸念）。再検討条件: 夜間のアラート件数が週 5 件を超えたら。見直し日: 11/7。」
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、https://github.com/python/peps/blob/main/peps/pep-0001.rst 、https://github.com/adr/madr/blob/main/template/adr-template.md

---

## 2. ビジネス・UX視点（9 項目）

### B1. デザインの判断にも「何を選び、何を選ばなかったか」を残す（デザインラショナール）

- **何をするか**: 画面やフローの判断を、「問い → 選択肢 → 評価基準 → 評価」の形で残す。
- **なぜか**: 【未確認】MacLean, Young, Bellotti, Moran (1991) の QOC は、デザインを「ありえた別案との関係」で理解する Design Space Analysis の記法とされる（検索要約による）。【確認】MADR も "Decision Drivers"（品質・懸念・制約）と "Considered Options" を持つので、デザインの判断にもそのまま使える。MADR の文書は判断の例に "a decision on features (e.g., infinite undo vs. limited undo)" を挙げている。
- **悪い例**: Figma の最終案だけが残っている。「なぜドロワーではなくタブなのか」に誰も答えられない。
- **良い例**: 「Q: 主要な 4 機能をどう切り替えるか。O: タブ / ドロワー / ボトムナビ。C: 片手操作、発見しやすさ、将来の機能追加。→ ボトムナビ。ドロワーは発見しやすさの基準で負けた（ユーザビリティテストで 5 人中 3 人が見つけられなかった）。」
- **出典**: https://github.com/adr/madr 、【未確認】QOC: MacLean et al., Human-Computer Interaction 6(3-4), 1991（概要は https://acawiki.org/Questions,_Options,_and_Criteria:_Elements_of_Design_Space_Analysis ）

### B2. 判断をリサーチの根拠にリンクする

- **何をするか**: デザインの判断に、根拠になった調査（テスト結果、インタビュー、数値）へのリンクを付ける。
- **なぜか**: 【確認】GOV.UK Design System のコンポーネントページには「Research on this component」欄がある。たとえばボタンのページには "Testing on GOV.UK has shown that using green as the colour of start buttons improved click-through rates" とあり、根拠の議論（backlog の GitHub Issue のコメント）へリンクしている。ページの front matter は `backlogIssueId` で議論の場とつながっている。
- **悪い例**: 「緑のほうが押されるので緑」とだけ書く。誰がいつどう測ったのか分からないので、反論も更新もできない。
- **良い例**: 「開始ボタンは緑。根拠: 2020 年の A/B テスト（Issue #34 のコメント）。再検証の条件: ブランドカラーを変えるとき。」
- **出典**: https://github.com/alphagov/govuk-design-system/blob/main/src/components/button/index.md 、https://github.com/alphagov/govuk-design-system-backlog/issues/34

### B3. デザインシステムでも ADR を使う

- **何をするか**: コンポーネントの API、トークン、廃止の判断をデザインシステムのリポジトリで ADR として残す。
- **なぜか**: 【確認】GitHub の Primer React（デザインシステム）は `contributor-docs/adrs/` に ADR を置いている。ADR-001 (TypeScript) は Status を Approved / Adopted の 2 段階で示し、Consequences には利点だけでなく "New contributors will need some familiarity with TypeScript" という負担も書いている。GOV.UK Design System も提案（RFC）と決定記録を分けて公開している。
- **悪い例**: 非推奨にしたコンポーネントの理由が Slack にしかない。利用者のチームが同じ過ちを繰り返す。
- **良い例**: 「ADR-014: Dropdown を廃止し Select と Menu に分ける。理由: 用途が 2 つ混ざり、アクセシビリティの要件が両立しなかった。移行期限と移行手順は…」
- **出典**: https://github.com/primer/react/blob/main/contributor-docs/adrs/adr-001-typescript.md 、https://github.com/alphagov/govuk-design-system-architecture

### B4. 事業の判断も同じ形で残す（"decisions" と呼ぶ）

- **何をするか**: 料金、対象、優先順位の判断もエンジニアと同じテンプレートで残す。名前は「ADR」より「decisions」が通じやすい。
- **なぜか**: 【確認】Joel Parker Henderson の README は、ディレクトリ名を "decisions" にすると "the team starts putting more information into the directory, such as vendor decisions, planning decisions, scheduling decisions" と報告している。"some developers and some managers dislike the word 'architecture'" とも書く。ただしこれは README 自身が "We hypothesize" と書いているとおり、仮説である。
- **悪い例**: 事業の判断は役員会の資料にだけある。エンジニアは「なぜこの機能が優先なのか」を知らずに作る。
- **良い例**: `decisions/biz-0003-keep-free-tier.md` に「無料プランを残す。理由: 獲得チャネルの 6 割が無料プラン経由（出典: 2026Q2 ファネル分析）。代わりに上限を 3 件に下げる。」
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record

### B5. 「なぜこの画面はこうなっているか」に 1 クリックで答えられるようにする

- **何をするか**: 画面やコンポーネントから、それに関わる判断の記録へ直接たどれるようにする（Figma のコメント、ストーリーブックの欄、ページの front matter など）。
- **なぜか**: 【確認】GOV.UK の例では、コンポーネントのページに議論の Issue 番号が紐づいている（B2）。Decision Guardian は、開発者が判断の対象のコードを触ったときに PR 上へ関連する判断の記録を出すツールとして紹介されている（"surfaces the right decision records at the right moment"）。【解釈】記録は書いただけでは読まれない。読まれる場所に出すことがデザインの課題になる。
- **悪い例**: 判断の記録が wiki の 4 階層下にある。新しく来たデザイナーは見つけられず、「古い」と思って作り直す。
- **良い例**: Figma のフレームの説明欄に `Decision: DS-ADR-014` とリンクを置く。
- **出典**: https://github.com/alphagov/govuk-design-system/blob/main/src/components/button/index.md 、https://github.com/joelparkerhenderson/architecture-decision-record

### B6. 後から来た人が意図を壊さないよう、「守るべき意図」と「変えてよい部分」を分ける

- **何をするか**: 判断のうち、どこが本質（理由がある制約）で、どこが偶然（好みや暫定）かを書き分ける。
- **なぜか**: 【未確認】Nygard の原文は、理由を知らない人は盲目的に受け入れるか盲目的に変えるかしかないと述べているとされる。【確認】Joel Parker Henderson の README は、Context に "Explain your organization's situation and business priorities" を書くよう勧めている。【解釈】「変えてよい」ことも書いておけば、後から来た人は過剰に保守的にならずに済む。
- **悪い例**: 「この確認ダイアログは消さないこと」とだけ書く。理由が分からず、全ダイアログが聖域になる。
- **良い例**: 「削除確認は残す（理由: 取り消し機能がなく、誤削除の問い合わせが月 40 件）。文言と配置は自由に変えてよい。取り消し機能ができたら確認は外してよい。」
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、【未確認】Nygard 原文

### B7. 「決めない」ことと「後で決める」ことも記録する

- **何をするか**: 未決の問い、決める期限、決めるのに必要な情報を記録する。
- **なぜか**: 【確認】Rust RFC テンプレートには "Unresolved questions" 節がある。Joel Parker Henderson の README は "Does it have to be made now, or can it wait until more is known?" を問い、"Ideally maintain a decision todo list that complements the product todo list" と勧めている。PEP 1 には "Deferred" という状態がある。
- **悪い例**: 未決事項が会議の口頭の「あとで」で消える。気づけば実装が勝手に決めている。
- **良い例**: 「未決: 退会後のデータ保持期間。期限: ベータ公開の 2 週間前。必要な情報: 法務の見解。決める人: PdM。」
- **出典**: https://github.com/rust-lang/rfcs/blob/master/0000-template.md 、https://github.com/joelparkerhenderson/architecture-decision-record 、https://github.com/python/peps/blob/main/peps/pep-0001.rst

### B8. 判断の時点の数字には日付を付ける

- **何をするか**: コスト、利用率、市場規模など変わる数字には、測った日付と出典を付ける。
- **なぜか**: 【確認】Joel Parker Henderson の README は、良い ADR の条件として "Timestamps: Identify when each item in the ADR is written. This is especially important for aspects that may change over time, such as costs, schedules, scaling" を挙げている。
- **悪い例**: 「利用者の大半がスマホなのでモバイル優先」。3 年後もその前提が正しいのか分からない。
- **良い例**: 「2026-08 時点でセッションの 82% がスマホ（GA4、過去 90 日）。50% を割ったら見直す。」
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record

### B9. 判断の記録は「書かされる事務」にしない

- **何をするか**: 記録の目的（未来の自分たちが速く、迷わず動けること）を先にチームで話し、テンプレートは小さく始める。
- **なぜか**: 【確認】Joel Parker Henderson の README は "decision records are not valuable if they're just an after-the-fact forced paperwork requirement" と書き、"talking together about the 'why', rather than mandating the 'what'" を勧めている。【未確認】デザインラショナール研究では、記録の手間が大きいことが現場で定着しない主因とされてきた（Jintae Lee 1997 などへの言及。検索要約による）。
- **悪い例**: 全項目必須の 12 欄テンプレートを導入する。3 か月で誰も書かなくなる。
- **良い例**: 最初は MADR の minimal 版（必須の節だけ）で始め、困ったときに欄を足す。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、https://github.com/adr/madr （minimal / bare テンプレート）

---

## 3. AI視点（8 項目）

### A1. 理由が書いてあるかどうかで、AI の提案の質が変わる

- **何をするか**: AI にコードやデザインを直させる前に、関連する判断の記録を読ませる。
- **なぜか**: 【確認】Claude Code のベストプラクティスは CLAUDE.md に入れるべきものとして "Architectural decisions specific to your project" を挙げ、入れなくてよいものとして "Anything Claude can figure out by reading code" を挙げている。CLAUDE.md は "persistent context it can't infer from code alone" を与えるものと説明されている。【解釈】「なぜ」はコードから推測できない情報の代表である。理由がなければ、AI はコードの見た目から「冗長だ」「古い」と判断して、意図的な制約を壊す提案をしやすくなる。
- **悪い例**: 「このリトライ処理を整理して」とだけ頼む。AI が、外部 API の制限に合わせてわざと入れた待ち時間を削る。
- **良い例**: 「ADR-0015（外部 API のレート制限で 2 秒待つと決めた）を読んだうえで、このリトライ処理を整理して」と頼む。
- **出典**: https://code.claude.com/docs/en/best-practices

### A2. リポジトリ内の指示ファイル（CLAUDE.md / AGENTS.md）には要点とリンクだけを置き、詳細は判断の記録に置く

- **何をするか**: 全セッションで守ってほしい判断の要点だけを指示ファイルに書く。詳細は `docs/decisions/` に置いて参照させる。
- **なぜか**: 【確認】Claude Code の説明では、CLAUDE.md は毎セッションの最初に読み込まれ、目安は "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence"。`@path` で取り込んだファイルも起動時に読み込まれるので、"Imports help you organize a long file but don't reduce its context cost" とある。一部のファイルにしか関係しない指示は `.claude/rules/` の paths 指定や skills に回すよう勧めている。AGENTS.md は "a README for agents: a dedicated, predictable place to provide context and instructions" と説明されている。Claude Code は CLAUDE.md がなければ AGENTS.md を読む（両方読む設定もある）。
- **悪い例**: ADR 40 本をすべて `@docs/decisions/*.md` で CLAUDE.md に取り込む。文脈が膨らみ、肝心の指示が守られにくくなる。
- **良い例**: CLAUDE.md には「決済処理を触るときは `docs/decisions/0011-*.md` を先に読む」と書く。または `.claude/rules/payments.md` を `paths: src/payments/**` で限定して読み込ませる。
- **出典**: https://code.claude.com/docs/en/memory 、https://code.claude.com/docs/en/best-practices 、https://github.com/agentsmd/agents.md

### A3. 指示ファイルは「強制」ではなく「文脈」だと理解し、守らせたい判断は仕組みで止める

- **何をするか**: 必ず守るべき判断は、CLAUDE.md に書くだけでなく、フック、lint、CI で機械的に止める。
- **なぜか**: 【確認】Claude Code の説明は "Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead" と書いている。ベストプラクティスにも "Unlike CLAUDE.md instructions which are advisory, hooks are deterministic" とある。MADR の Confirmation（E9）と同じ考え方である。
- **悪い例**: 「本番 DB に直接書き込まない」と CLAUDE.md に書いただけで安心する。
- **良い例**: CLAUDE.md には理由を 1 行で書く（AI が判断の意図を理解するため）。同時に、フックで該当コマンドを止める（確実に守らせるため）。
- **出典**: https://code.claude.com/docs/en/memory 、https://code.claude.com/docs/en/best-practices

### A4. 指示ファイル自体を判断の記録と同じように扱う（レビューし、古い指示を刈り込む）

- **何をするか**: CLAUDE.md の変更を PR でレビューし、定期的に古い指示や矛盾する指示を消す。消した理由も残す。
- **なぜか**: 【確認】Claude Code の説明は "if two instructions contradict each other, Claude may pick one arbitrarily" と書き、定期的な見直しを勧めている。ベストプラクティスは "Treat CLAUDE.md like code: review it when things go wrong, prune it regularly" と書き、各行について "Would removing this cause Claude to make mistakes?" と問うよう勧めている。CLAUDE.md に書き足すきっかけには "Claude makes the same mistake a second time" などを挙げている。
- **悪い例**: 誰かが CLAUDE.md に「〇〇しない」を足し続ける。互いに矛盾し、どれが新しいのか分からない。
- **良い例**: 指示を足すたびに、元になった指摘や事故へのリンクを HTML コメントで残す。【確認】ブロック単位の HTML コメントは AI の文脈に入る前に除かれる（"stripped before the content is injected into Claude's context"）ので、人間向けの理由を書いてもトークンを使わない。
- **出典**: https://code.claude.com/docs/en/memory 、https://code.claude.com/docs/en/best-practices

### A5. AI に「なぜこうなっているか」を聞くときは、履歴という一次情報を指す

- **何をするか**: 「なぜ」を AI に聞くときは、推測させずに git の履歴、ADR、PR の議論を読ませる。
- **なぜか**: 【確認】Claude Code のベストプラクティスは、「ExecutionFactory の API はなぜ変なのか」と聞くより "look through ExecutionFactory's git history and summarize how its api came to be" と頼むほうが良い、という例を挙げている。コードベースについての質問の例にも "Why does this code call foo() instead of bar() on line 333?" がある。【解釈】判断の記録がなければ、AI の答えは履歴からの推測にとどまる。判断の記録は AI による「なぜ」の回答の精度を直接左右する。
- **悪い例**: 「なぜこうなってる？」とだけ聞き、AI がもっともらしい理由を作って答える。
- **良い例**: 「`docs/decisions/` と、このファイルの git log と、関連 PR の説明を読んで、この設計になった経緯を出典つきで説明して。記録がない部分は『記録なし』と書いて」と頼む。
- **出典**: https://code.claude.com/docs/en/best-practices

### A6. AI に判断の記録の下書きをさせる。ただし Decision と責任者は人間が書く

- **何をするか**: Context、Considered Options、長所と短所の下書きを AI に作らせる。何を選ぶか（Decision）と、誰が決めたかは人間が書く。
- **なぜか**: 【確認】Joel Parker Henderson のリポジトリは、ADR を書くための Claude Code 用スキル（architecture-decision-record-skill）を配布している。このスキルは ADR が必要かどうかの判断、ディレクトリ作成、命名、テンプレート選択、Context / Decision / Consequences の執筆を手伝う。Claude Code のベストプラクティスは、大きな機能では AI にインタビューさせ（"Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs"）、その結果を仕様書に書かせる流れを紹介している。【解釈】AI は網羅的に選択肢を並べるのは得意だが、どれを選ぶかは価値判断であり、責任の所在を記録する意味がなくなるので人間が書く。
- **悪い例**: AI が「推奨: A 案」と書き、そのまま Accepted としてマージされる。誰が決めたのか記録にない。
- **良い例**: AI が下書きした ADR の状態は `proposed` にしておく。`decision-makers:` 欄（MADR）に決めた人を書き、人間が採否を決めてから `accepted` にする。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、https://code.claude.com/docs/en/best-practices 、https://github.com/adr/madr/blob/main/template/adr-template.md

### A7. AI に関わる判断（モデル、プロンプト、評価基準）そのものを記録する

- **何をするか**: どのモデルを使うか、プロンプトをどう変えたか、何で合格とするかを、通常の判断と同じように記録する。プロンプトはコードに埋め込まずファイルで管理し、差分が残るようにする。
- **なぜか**: 【解釈】モデルやプロンプトの変更は、出力の質・コスト・安全性を同時に変える「アーキテクチャ上重要な判断」に当たる（adr.github.io の AD の定義、0 章を参照）。プロンプトの文言は理由が見えにくく、後から来た人が「冗長だ」と消しやすい。プロンプトをコードに埋め込まず、ファイルで管理して変更の理由を残すチームもある。【確認】Joel Parker Henderson の README は、判断の記録と成果物を LLM に照合させる fitness function のプロンプト例を載せている。
- **悪い例**: 「モデルを X から Y に替えた」というコミットメッセージだけが残る。品質が落ちたとき、比較した評価の結果が見つからない。
- **良い例**: `decisions/ai-0004-switch-drafting-model.md` に「比較した候補、評価セット、結果、コスト、戻す条件」を書く。プロンプトの変更 PR からリンクする。
- **出典**: https://adr.github.io/ （ソース: https://github.com/adr/adr.github.io/blob/main/index.md ）、https://github.com/joelparkerhenderson/architecture-decision-record 

### A8. AI 自身の作業メモと、チームの判断の記録を区別する

- **何をするか**: AI が自動で残すメモ（auto memory、NOTES.md など）は作業の継続のためのものとして扱う。チームの判断の記録とは置き場所も承認の流れも分ける。
- **なぜか**: 【確認】Claude Code は、人間が書く CLAUDE.md と、Claude が修正や好みから自分で書く auto memory を別の仕組みとして説明している（auto memory は起動時に最初の 200 行または 25KB まで読み込む）。Anthropic の context engineering の記事は、エージェントが文脈の外にメモを残す "structured note-taking" を長時間の作業の技法として紹介している。【解釈】AI のメモは誰の承認も経ていない。これを「決まったこと」として扱うと、承認のない判断が既成事実になる。
- **悪い例**: AI が作業中に「この API は v2 を使う方針」とメモし、それが次のセッションで「決定事項」として扱われる。
- **良い例**: AI のメモに出てきた方針は「提案」として ADR の下書きに起こし、人間の承認を経てから `docs/decisions/` に入れる。
- **出典**: https://code.claude.com/docs/en/memory 、https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

---

## 4. 越境：それぞれが相手を知るべき理由と配慮

### (a) ビジネス・UX がエンジニアの判断の記録を知るべき理由

1. **戻せる判断と戻せない判断が分かる**。【解釈】ADR の Consequences には「何が難しくなるか」が書かれる（E1）。この画面の仕様変更が軽い変更なのか、データモデルの作り直しなのかを見分けられれば、優先順位の議論が現実的になる。
2. **「技術的にできない」の中身を検証できる**。【解釈】退けた案と理由が残っていれば（E2）、「できない」が技術上の制約なのか、時間の制約なのか、当時の前提なのかを確かめられる。前提が変わっていれば再検討を頼める（E3 の superseded）。
3. **事業の前提が、技術の判断の中に埋め込まれている**。【確認】Joel Parker Henderson の README は Context に "your organization's situation and business priorities" を書くよう勧めている。【解釈】つまり ADR を読めば、エンジニアが事業の前提をどう理解したかが分かる。理解がずれていれば、そこを直すのがビジネス側の仕事になる。

**配慮**: ADR の専門用語を全部理解しようとしなくてよい。Context と Consequences の「難しくなること」だけ読めば足りる。【解釈】

### (b) エンジニアがビジネス・UX の観点を知るべき理由と、どう配慮するか

1. **技術の判断の「Decision Drivers」の多くはユーザーと事業から来る**。【確認】MADR の Decision Drivers は "a desired software quality, faced concern, constraint or force" である。【解釈】「速さ」「止まらないこと」の優先度は、本来ユーザー調査や事業の数字で決まる。根拠のない Drivers の上に立つ ADR は脆い。
2. **デザインの判断にも理由がある**。【確認】GOV.UK の「Research on this component」のように、見た目の判断がテストの結果に基づくことがある（B2）。【解釈】実装の都合で余白や順序を「ついでに」変えると、検証済みの意図を壊すことがある。
3. **配慮のしかた**【解釈】:
   - Context を書くとき、ユーザーや事業への影響を 1 行入れる（「この変更で、ユーザーは保存の完了を待つ時間が最大 2 秒増える」）。
   - ADR の通知を、影響を受ける PdM・デザイナーにも送る（MADR の `informed:` 欄を使う）。
   - デザインの判断の記録（Figma のメモ、Research 欄）を、実装前に確認する手順を PR テンプレートに入れる。

### (c) AI 視点：三者にとっての意味

- **ビジネス・UX にとって**: 【解釈】AI に画面やコピーを直させるとき、デザインの理由が書いてなければ、AI は一般的な「ベストプラクティス」に寄せて検証済みの判断を上書きする。デザインラショナールは、人間の後任と同じくらい AI にとっても重要な引き継ぎ資料になる。
- **エンジニアにとって**: 【確認】Claude Code はアーキテクチャの判断を CLAUDE.md に入れることを勧めている（A1）。【解釈】ADR がリポジトリにあれば、AI はそれを読んで判断に沿った変更を提案できる。ADR が「人間の未来の同僚」と「AI」の両方に向けた文書になる。
- **三者共通**: 【解釈】AI が下書きを作れるようになり、記録の手間（B9 の定着しない主因）は下がる。その代わり、「誰が決めたか」と「承認の有無」を記録することの重要さが上がる（A6, A8）。

---

## 5. ゴールの違いと折り合い

### 対立の表

| 対立 | ビジネス側のゴール | エンジニア側のゴール | UX 側のゴール | 解き方（【解釈】、根拠は右の出典） |
|---|---|---|---|---|
| 速さ vs 記録 | 早く決めて早く出したい | 後で困らないよう残したい | 根拠を残したい | 判断の重さで手順を分ける。戻せる判断は軽い記録（PR 説明文）で済ませ、戻せない判断だけ ADR とレビューを通す（E8、【未確認】Amazon の one-way / two-way door） |
| 記録の負担 | 書く時間がもったいない | テンプレートが重い | 調査結果を毎回まとめるのが重い | MADR の minimal 版から始める（B9）。AI に下書きさせ、人間は Decision と責任者だけ書く（A6） |
| 不変 vs 更新 | 状況が変われば方針も変える | 記録は書き換えたくない | 新しい調査結果で更新したい | 「置き換え（superseded）」と「日付つき追記」を使い分ける（E3, E4） |
| 合意 vs 決める人 | 最終的には事業責任者が決めたい | 技術的に正しい案を通したい | ユーザーの声を反映したい | 決める人を 1 人に明示し、反対意見を記録に残す（E10、6 章の DACI / RAPID） |
| 置き場所 | 慣れたツール（Notion、Docs）がよい | リポジトリに置きたい | Figma に置きたい | 正本は 1 か所に決め、他の場所からはリンクで参照する。AI に読ませるならリポジトリが有利（E5, A2） |
| 曖昧さを残すか | 決まっていないことは決まっていないままにしたい | 実装には決定が要る | 検証してから決めたい | 未決事項を、期限と決める人つきで記録する（B7） |

### 解き方の原則【解釈】

1. **判断の重さで手順を分ける**。戻せない・影響が広い判断だけ重い手順にする。【未確認】Bezos の 2015 年の株主への手紙は、取り返しのつかない判断（Type 1、one-way door）は慎重に、戻せる判断（Type 2、two-way door）は判断力のある個人や小さなグループで素早く決めるべきとし、大きな組織は Type 2 にまで重い手順を使いがちだと指摘しているとされる（検索要約による）。【確認】Joel Parker Henderson の README の例にも "70% estimates are good enough for easily-reversable easily-isolatable decisions" という原則の例がある。
2. **記録を軽くする**。テンプレートの必須欄を減らし、AI に下書きさせる。
3. **記録の目的を共有する**。「事務」ではなく「未来の自分たちと AI への引き継ぎ」として位置づける（B9）。
4. **数字には日付と見直し条件を付ける**。「いつまで正しいか」を書くと、変えるときの対立が減る（B8, E10）。

---

## 6. 建設的な議論の進め方

### D1. 決める人を 1 人に明示する（DACI / RAPID）

- **何をするか**: 判断ごとに、進行役、決める人、意見を出す人、知らされる人を最初に決めて記録に書く。
- **なぜか**: 【未確認】Atlassian の DACI は Driver（進行役）、Approver（決める 1 人）、Contributors（声はあるが票はない）、Informed（決定後に知らされる）を定義しているとされる（検索要約による）。【未確認】Bain の RAPID は Recommend / Agree / Perform / Input / Decide の 5 つの役割を置き、決める人を 1 人にすること（"who has the D"）を重視するとされる（HBR 2006、Rogers & Blenko。検索要約による）。【確認】MADR の front matter には `decision-makers`、`consulted`（双方向のやりとり）、`informed`（一方向の通知）の欄があり、DACI と同じ考え方を記録の形式に持っている。
- **悪い例**: 全員の合意を待つうちに 3 週間経つ。最後は声の大きい人の案になり、記録にはその経緯が残らない。
- **良い例**: `decision-makers: PdM（田中）` / `consulted: テックリード、デザイナー` / `informed: CS` と書いてから議論を始める。
- **出典**: https://github.com/adr/madr/blob/main/template/adr-template.md 、【未確認】https://www.atlassian.com/team-playbook/plays/daci 、【未確認】https://www.bain.com/insights/who-has-the-d

### D2. 戻せるかどうかで、議論の重さを変える（one-way / two-way door）

- **何をするか**: 議論の最初に「この判断は戻せるか」を確かめ、戻せるなら短い期限で決める。
- **なぜか**: 【未確認】Amazon の 2015 年の株主への手紙（Type 1 / Type 2）。2016 年の手紙では、欲しい情報の 70% ほどで決めるべきだという主張があるとされる（検索要約による）。【確認】Joel Parker Henderson の README の原則例（5 章を参照）。
- **悪い例**: ボタンの文言にも、DB の分割と同じ数の承認者を立てる。
- **良い例**: 記録の冒頭に `reversibility: two-way（フィーチャーフラグで戻せる）` と書き、期限 2 日で決める。
- **出典**: 【未確認】https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders （2015 年の手紙も同サイト）、https://github.com/joelparkerhenderson/architecture-decision-record

### D3. 反対しても、決まったら全力で実行する（Disagree and commit）。反対意見は記録に残す

- **何をするか**: 合意がなくても決める人が決め、反対した人も実行に協力する。反対の内容と再検討の条件は記録に残す。
- **なぜか**: 【未確認】Bezos の 2016 年の手紙は "disagree and commit" を紹介しており、決める側が自分の反対意見を表明したうえでチームの案に乗る例も挙げているとされる（検索要約による）。【確認】PEP 1 は提案者の責任に "documenting dissenting opinions" を含めている（E10）。【解釈】反対意見の記録は、後で前提が崩れたとき「誰が正しかったか」ではなく「どの条件で見直すか」の議論に使う。
- **悪い例**: 反対した人が実装中に別案を勝手に混ぜる。または、反対意見が議事録から消される。
- **良い例**: 「反対: Cさん（理由…）。再検討の条件: 解約率が 2 か月連続で 3% を超えたら。Cさんは実装に合意。」
- **出典**: https://github.com/python/peps/blob/main/peps/pep-0001.rst 、【未確認】Amazon 2016 年の株主への手紙

### D4. 提案は期限つきで公開し、意見を求める（RFC）

- **何をするか**: 決める前に提案を公開し、期限を切ってコメントを集める。コメントへの対応も記録に残す。
- **なぜか**: 【確認】Joel Parker Henderson の README の例は「調査と評価を終え、提案を関係者に公開して 1 週間のコメント期間を設け、すべてのコメントに対応してから投票する」という流れを示している。Backstage は PR でコミュニティの意見を反映してからマージする。GOV.UK Design System は提案（RFC）を公開リポジトリで議論している。
- **悪い例**: 決まってから「共有」として ADR を流す。反対が出ても覆せず、不満が残る。
- **良い例**: 状態を `proposed` で PR を出し、「コメント期限 10/14、決める人 X」と書く。期限後に `accepted` か `rejected` にする。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、https://github.com/backstage/backstage/blob/master/docs/architecture-decisions/index.md 、https://github.com/alphagov/govuk-design-system-architecture

### D5. 記録そのものをレビューする（次の段階へ進む基準を持つ）

- **何をするか**: 判断の記録をレビューするとき、結論の良し悪しだけでなく記録の質を見る。
- **なぜか**: 【確認】Joel Parker Henderson の README は、次の段階へ進む基準として "Is the problem clearly articulated? Have the alternatives been considered? Are trade-offs well-enough understood and documented? Is all relevant context in place? Are all relevant stakeholders involved? Has all feedback been incorporated?" を挙げている。【未確認】MADR のページには、Olaf Zimmermann の「ADR のレビューのしかた」の記事へのリンクがある（記事自体は未確認）。
- **悪い例**: 「LGTM」だけで承認する。選択肢が 1 つしかない ADR が通る。
- **良い例**: レビューの観点を PR テンプレートに入れる。（1）問いが明確か（2）別案が 2 つ以上あるか（3）短所も書かれているか（4）ユーザーと事業への影響が書かれているか（5）決める人が書かれているか。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、https://github.com/adr/madr

### D6. 議論の場では「論点 → 立場 → 論拠」を見える形にする

- **何をするか**: 議論中に、問い（何を決めるか）、選択肢、それぞれの賛否の論拠を、その場で構造化して書く。
- **なぜか**: 【未確認】IBIS（Kunz & Rittel 1970）は Issue / Position / Argument で議論を構造化し、複数の利害関係者がいる複雑な問題を扱うための手法とされる。【確認】Joel Parker Henderson の README は判断の技法の例として "dialogue mapping" を挙げている（IBIS を使った会議の進め方）。
- **悪い例**: 議論が「A がいい」「いや B だ」の往復になり、何について対立しているのか分からないまま終わる。
- **良い例**: ホワイトボードに「問い: 退会時にデータをすぐ消すか」「選択肢: 即時 / 30 日後 / 選ばせる」「論拠: 法務（+）、CS 負荷（−）…」と書く。そのまま MADR の Pros and Cons に転記する。
- **出典**: https://github.com/joelparkerhenderson/architecture-decision-record 、【未確認】https://en.wikipedia.org/wiki/Issue-based_information_system

---

## 出典一覧

### 【確認】実際に開いて内容を確かめたもの

| # | 資料 | URL | 確認方法 |
|---|---|---|---|
| 1 | adr.github.io（定義、decision log、"any decision record"） | https://github.com/adr/adr.github.io/blob/main/index.md | サイトのソース（GitHub raw）。公開ページ https://adr.github.io/ は遮断されて開けず |
| 2 | MADR テンプレート（4.x、status、decision-makers / consulted / informed、Considered Options、Confirmation） | https://github.com/adr/madr/blob/main/template/adr-template.md | GitHub raw |
| 3 | MADR README・文書（docs/decisions、命名、minimal / bare、名称の変遷） | https://github.com/adr/madr （README、develop ブランチの docs/index.md） | GitHub raw |
| 4 | Joel Parker Henderson "Architecture decision record"（良い ADR の条件、チーム運用、fitness function、Claude Code スキル、Nygard 型テンプレートの写し） | https://github.com/joelparkerhenderson/architecture-decision-record | GitHub raw（README、テンプレート） |
| 5 | adr-tools の ADR 0001（Nygard 型の実例） | https://github.com/npryce/adr-tools/blob/master/doc/adr/0001-record-architecture-decisions.md | GitHub raw |
| 6 | Rust RFC テンプレート | https://github.com/rust-lang/rfcs/blob/master/0000-template.md | GitHub raw |
| 7 | PEP 1（Rationale、Rejected Ideas、反対意見の記録、状態） | https://github.com/python/peps/blob/main/peps/pep-0001.rst | GitHub raw |
| 8 | Kubernetes KEP テンプレート（Non-Goals、Alternatives、Drawbacks） | https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/README.md | GitHub raw |
| 9 | Primer React ADR-001（デザインシステムの ADR） | https://github.com/primer/react/blob/main/contributor-docs/adrs/adr-001-typescript.md | GitHub raw |
| 10 | Backstage ADR 運用 | https://github.com/backstage/backstage/blob/master/docs/architecture-decisions/index.md | GitHub raw |
| 11 | GOV.UK Design System Architecture（Proposals と Decision Records） | https://github.com/alphagov/govuk-design-system-architecture | GitHub raw（README） |
| 12 | GOV.UK Design System ボタンのページ（Research on this component） | https://github.com/alphagov/govuk-design-system/blob/main/src/components/button/index.md | GitHub raw。リンク先の Issue #34 は未確認 |
| 13 | Claude Code "How Claude remembers your project"（CLAUDE.md、AGENTS.md、rules、auto memory） | https://code.claude.com/docs/en/memory | 直接取得 |
| 14 | Claude Code "Best practices" | https://code.claude.com/docs/en/best-practices | 直接取得 |
| 15 | Anthropic "Effective context engineering for AI agents"（2025-09-29） | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | 直接取得 |
| 16 | AGENTS.md | https://github.com/agentsmd/agents.md （公開サイト https://agents.md/ は遮断） | GitHub raw（README） |
| 17 | あるリポジトリの CLAUDE.md（プロンプトをファイルで管理する例） | （非公開） | ローカル |

### 【未確認】開けなかった。検索結果の要約だけで概要を知ったもの

| 資料 | URL | 状態 |
|---|---|---|
| Michael Nygard "Documenting Architecture Decisions" (2011) | https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html | 遮断。テンプレートの節構成は資料 4・5 の写しで確認。動機の文（盲目的に受け入れる / 変える）は未確認 |
| Martin Fowler "Architecture Decision Record" | https://martinfowler.com/bliki/ArchitectureDecisionRecord.html | 遮断 |
| Malte Ubl "Design Docs at Google" | https://www.industrialempathy.com/posts/design-docs-at-google/ | 遮断。Goals and non-goals、Alternatives considered は検索要約のみ |
| Thoughtworks Radar "Lightweight Architecture Decision Records" | https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records | 遮断 |
| Spotify Engineering "When Should I Write an Architecture Decision Record" (2020) | https://engineering.atspotify.com/2020/4/when-should-i-write-an-architecture-decision-record | 遮断（Backstage の文書がリンクしていることは確認） |
| Amazon 2015 年・2016 年の株主への手紙（Type 1/2、one-way / two-way door、disagree and commit、70%） | https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders ほか | 遮断。一次資料の文言は要確認 |
| Atlassian Team Playbook "DACI" | https://www.atlassian.com/team-playbook/plays/daci | 遮断。検索要約にあった「McKinsey の調査で成功率 25% 向上」は出典不明なので使わない |
| Bain "RAPID"、Rogers & Blenko "Who Has the D?" (HBR, 2006) | https://www.bain.com/insights/who-has-the-d | 遮断 |
| MacLean et al. "Questions, Options, and Criteria" (HCI, 1991) | （論文） | 未入手 |
| Kunz & Rittel "Issues as Elements of Information Systems" (1970) / IBIS | https://en.wikipedia.org/wiki/Issue-based_information_system | 遮断 |
| Jintae Lee "Design Rationale Systems: Understanding the Issues" (IEEE Expert, 1997) | （論文） | 未入手 |
| Olaf Zimmermann "How to review ADRs — and how not to" | https://medium.com/olzzio/how-to-review-architectural-decision-records-adrs-and-how-not-to-2707652db196 | MADR のページにリンクがあることだけ確認 |
| Azure Well-Architected "Architecture decision record"、AWS Prescriptive Guidance "ADR" | adr.github.io からのリンク | 遮断 |
