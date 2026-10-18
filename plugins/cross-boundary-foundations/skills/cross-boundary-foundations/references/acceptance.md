# ⑤ 受け入れ条件とテストシナリオ — リサーチノート

調査日：2026-10-07
担当範囲：「どうなっていれば成功か」を具体的な場面で書いたもの（受け入れ条件・テストシナリオ・評価データ）

## 表記と確認の範囲

- 【確認】一次資料（またはその原文が置かれた GitHub リポジトリ）を実際に開いて読んだ内容。
- 【未確認】一次資料を開けなかったもの。検索エンジンの要約・二次資料で概要だけ見たものを含む。内容は二次情報のまま書いており、原文の言い回しや数字は検証していない。
- 【解釈】調査者（私）の整理・推論。出典の主張ではない。

この環境のネットワーク制限で、次のサイトは開けなかった：martinfowler.com、cucumber.io（公式サイト）、scrumguides.org / scrum.org、xp123.com（Bill Wake）、gojko.net、testing.googleblog.com、ronjeffries.com、playwright.dev、docs.pact.io、deque.com、openai.com / platform.openai.com、nngroup.com、wikipedia。

代わりに開けたもの：
- Cucumber 公式ドキュメントの原稿（GitHub `cucumber/docs` の `content/docs/...`）。公開サイトの元原稿だが、公開版と完全に同じとは限らない。
- Playwright 公式ドキュメントの原稿（GitHub `microsoft/playwright` の `docs/src/...`）
- axe-core の README、Testing Library の Guiding Principles、Pact 仕様の README、OpenAI Evals の README（いずれも GitHub）
- Anthropic：platform.claude.com の "Define success criteria and build evaluations"（develop-tests）、anthropic.com の "Demystifying evals for AI agents"、code.claude.com の "Best practices for Claude Code"

---

## 0. 定義と範囲

### 0-1. 言葉の定義

| 用語 | ここでの意味 | 根拠 |
|---|---|---|
| 受け入れ条件（Acceptance Criteria） | 利用者・顧客・その他の関係者に「受け入れられる」ために、プロダクトが満たすべき条件 | 【確認】Cucumber "User stories"：*"Acceptance Criteria are conditions that a (software) product must satisfy to be accepted by a user, customer or other stakeholder."* |
| テストシナリオ（Scenario / Example） | 受け入れ条件（ルール）を、具体的な前提・出来事・結果で例示したもの。Gherkin では Given / When / Then で書く | 【確認】Cucumber Gherkin Reference：Example は「初期状態（Given）・出来事（When）・期待結果（Then）」を書く |
| ルール（Rule） | 複数のシナリオをまとめる一つのビジネスルール。Gherkin 6 から `Rule` キーワード | 【確認】Gherkin Reference：*"The purpose of the Rule keyword is to represent one business rule that should be implemented."* |
| 完成の定義（Definition of Done, DoD） | 個々のストーリーではなく、チームが出す成果物すべてに共通する品質基準 | 【未確認】Scrum Guide 2020 の文言 *"The Definition of Done is a formal description of the state of the Increment when it meets the quality measures required for the product."* は検索結果での引用のみ。原文は未開封 |
| 評価（eval） | AI システムに入力を与え、出力を採点ロジックで判定して成功を測るテスト | 【確認】Anthropic "Demystifying evals"：task は *"A single evaluation with defined inputs and success criteria"*（WebFetch の要約経由） |

### 0-2. 位置づけ（【解釈】）

- 受け入れ条件は「ストーリー単位の成功の定義」、DoD は「全ストーリー共通の品質の床」、テストシナリオは「受け入れ条件を具体例に落としたもの」、eval は「確率的に振る舞う機能に対するテストシナリオの集合と合格基準」と整理できる。
- 一つのものが、合意の道具（会話）→ 仕様（文書）→ 検査（自動テスト）→ AI の評価データ、と姿を変えて使い回される。この「使い回せる」点が、6領域の中で ⑤ が AI のデータ資源として最も直接効く理由である。
- Ron Jeffries の Card / Conversation / Confirmation の Confirmation が受け入れテストに当たる、という整理は広く引用される。【未確認】原文（ronjeffries.com, 2001）は開けず、検索要約のみ。

### 0-3. 範囲

含む：受け入れ条件の書き方、BDD/Gherkin、Specification by Example、テスト設計技法（境界値・同値分割）、テストの形（ピラミッド等）、E2E・ビジュアル回帰・アクセシビリティ自動テスト・契約テスト、DoD/DoR、ユーザビリティテストとの接続、AI 機能の eval。
含まない：テスト自動化ツールの導入手順、性能試験・セキュリティ試験の詳細（必要な範囲で触れるだけ）。

---

## 1. エンジニア視点（11項目）

### E1. 受け入れ条件は「ルール＋具体例」で書く（Specification by Example / BDD）

- **何をするか**：抽象的な要件文だけで終わらせず、各ルールに具体的な例（入力値・状態・期待結果）を最低1つ付ける。
- **なぜ**：BDD は「具体的な実例を中心に協働する」ことで、ビジネス側と技術側のずれを埋める方法として説明されている。【確認】Cucumber "Behaviour-Driven Development"：*"We do this by focusing collaborative work around concrete, real-world examples that illustrate how we want the system to behave."* BDD は Discovery / Formulation / Automation の3つの実践からなり、*"If you're new to BDD, discovery is the right place to start."*
- Gojko Adzic の Specification by Example は「目標からスコープを導く」「例で示す」「仕様を磨く」などの「キープロセスパターン」と、生きたドキュメント（living documentation）を中心に据える。【未確認】書籍・gojko.net は未開封。検索要約で概要のみ。
- **悪い例**：「送料は条件に応じて正しく計算されること」
- **良い例**：
  ```gherkin
  Rule: 税込5,000円以上は送料無料
    Example: ちょうど5,000円なら無料
      Given カートの合計が税込5,000円
      When 購入手続きに進む
      Then 送料は0円と表示される
    Example: 4,999円なら有料
      Given カートの合計が税込4,999円
      When 購入手続きに進む
      Then 送料は550円と表示される
  ```
- **出典**：https://cucumber.io/docs/bdd/ （原稿：https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/_index.md）／Gherkin `Rule`：https://cucumber.io/docs/gherkin/reference/

### E2. Given / When / Then の役割を混ぜない

- **何をするか**：Given は「既知の状態に置く」だけ。When は「一つの出来事」。Then は「外から観察できる結果」。
- **なぜ**：【確認】Gherkin Reference：
  - Given：*"The purpose of Given steps is to put the system in a known state before the user (or external system) starts interacting with the system"*、*"Avoid talking about user interaction in Given's."*
  - Then：*"An outcome should be on an observable output. That is, something that comes out of the system (report, user interface, message), and not a behaviour deeply buried inside the system (like a record in a database)."*
  - ステップ数：*"we recommend 3-5 steps per example. Having too many steps will cause the example to lose its expressive power as a specification and documentation."*
- Given/When/Then の型は Daniel Terhorst-North と Chris Matts が BDD の一部として作った。【確認】Cucumber "History of BDD"（"Given/When/Then" テンプレートは story の受け入れ条件を実行可能な形で捉えるために作られた）。Martin Fowler の bliki "GivenWhenThen"（2013）も同趣旨と見られる。【未確認】Fowler の原文は未開封。
- **悪い例**：`Then 注文テーブルに status=PAID のレコードが1件ある`
- **良い例**：`Then 注文履歴に「支払い済み」と表示される` ＋ `And 確認メールが届く`
- **出典**：https://cucumber.io/docs/gherkin/reference/ ／ https://cucumber.io/docs/bdd/history/ ／（未確認）https://martinfowler.com/bliki/GivenWhenThen.html

### E3. 手順ではなく振る舞いを書く（宣言的スタイル）

- **何をするか**：「どのボタンを押すか」ではなく「何ができるか」を書く。UI 操作の詳細はステップ定義（自動化コード）に閉じ込める。
- **なぜ**：【確認】Cucumber "Writing better Gherkin"：*"Your scenarios should describe the intended behaviour of the system, not the implementation. In other words, it should describe what, not how."* 書くときの問い：*"Will this wording need to change if the implementation does?"* 命令的スタイルは *"because they are so closely tied to the mechanics of the current UI, they often require more work to maintain."*
- **悪い例**：
  ```
  Given I visit "/login"
  When I enter "Bob" in the "user name" field
  And I press the "login" button
  ```
- **良い例**：`When "Bob" logs in`
- 【解釈】UXデザイナーが画面を作り替えても受け入れ条件が書き換わらない、という状態は、デザインの自由度を守ることでもある。
- **出典**：https://cucumber.io/docs/bdd/better-gherkin/ （原稿：https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/better-gherkin.md）

### E4. テスト可能でない要件は「まだ理解できていない」サイン

- **何をするか**：「使いやすい」「速い」「適切に」のような判定不能な語を、観察可能な条件に置き換える。置き換えられないなら、ストーリーを分けるか、問いとして残す。
- **なぜ**：INVEST の T（Testable）。Bill Wake（2003）は「テストの仕方が分からないなら、それはまだ十分に理解できていないということ」と述べたとされる。【未確認】xp123.com の原文は未開封。Cucumber のドキュメントは、良いストーリーの条件として「テスト可能な受け入れ条件を持つ」ことと INVEST を挙げている。【確認】Cucumber "User stories"。
- **悪い例**：「検索結果がすばやく表示される」
- **良い例**：「通常回線で、検索ボタンを押してから結果一覧の先頭10件が表示されるまで2秒以内（95パーセンタイル）。3秒を超える場合は読み込み中の表示が出ている」
- **出典**：https://cucumber.io/docs/terms/user-story/ ／（未確認）https://xp123.com/invest-in-good-stories-and-smart-tasks/

### E5. 境界値と同値分割で「例の選び方」を決める

- **何をするか**：入力の範囲を「同じ扱いになるグループ（同値クラス）」に分け、各グループから代表値を、境目では境界値とその隣を選ぶ。
- **なぜ**：例を思いつきで並べると、境目（4,999円/5,000円、18歳未満/18歳）が抜けやすい。ISTQB Foundation Syllabus v4.0 では境界値分析を「順序のある同値分割の境界を試す技法」とし、2値 BVA と 3値 BVA を区別する。【未確認】ISTQB のシラバス・白書は未開封、検索要約のみ。
- **悪い例**：送料無料のテストに「3,000円」「10,000円」だけを使う
- **良い例**：4,999円 / 5,000円 / 5,001円（3値）、0円（空カート）、上限値付近、税込/税抜の取り違えを誘う値
- 【解釈】Example Mapping の「緑のカード（例）」を選ぶときの道具として、この技法をビジネス側にも共有すると、議論が「思いつきの例」から「境目の確認」に変わる。
- **出典**：（未確認）https://istqb.org/wp-content/uploads/2025/10/Boundary-Value-Analysis-white-paper.pdf

### E6. テストの「形」を意識し、受け入れ条件をどの層で確かめるか決める

- **何をするか**：受け入れ条件ひとつひとつについて、単体・結合・E2E・手動のどこで確かめるかを決める。すべてを画面経由の E2E にしない。
- **なぜ**：Mike Cohn のテストピラミッドは、GUI 経由の高レベルテストより低レベルの単体テストを多く持つべきだとする。Fowler の bliki は UI 経由の E2E を「壊れやすく、書くのが高く、実行に時間がかかる」と説明しているとされる。【未確認】Fowler の原文は未開封、検索要約のみ。Google Testing Blog "Just Say No to More End-to-End Tests"（2015, Mike Wacker）は E2E 中心の戦略が実際にはうまくいかないことを論じ、目安として 70/20/10 の比率を挙げたとされる。【未確認】
- 一方、Testing Library は *"The more your tests resemble the way your software is used, the more confidence they can give you."* を指針にしている。【確認】つまり「低い層に寄せる」ことと「使われ方に似せる」ことは緊張関係にある。
- **悪い例**：送料計算の全パターンを E2E で画面から入力して確かめる
- **良い例**：送料計算のルールと境界値は単体テスト（同じ Gherkin 例から生成してもよい）。E2E は「無料になったことが画面で分かる」代表1本だけ
- **出典**：（未確認）https://martinfowler.com/bliki/TestPyramid.html ／（未確認）https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html ／ https://testing-library.com/docs/guiding-principles （原稿：https://raw.githubusercontent.com/testing-library/testing-library-docs/main/docs/guiding-principles.mdx）

### E7. E2E の脆さ（フレーク）を前提に設計する

- **何をするか**：E2E は「利用者に見える属性」でロケータを書き、自分で制御できない外部サービスはモックし、テスト同士を独立させる。
- **なぜ**：【確認】Playwright Best Practices：*"Automated tests should verify that the application code works for the end users, and avoid relying on implementation details such as ... the CSS class of some element."*、*"Only test what you control. Don't try to test links to external sites or third party servers that you do not control."*、ロケータは *"we recommend prioritizing user-facing attributes and explicit contracts."* Google では約1.5%のテスト実行がフレークと報告され、約16%のテストに何らかのフレークがあったとされる（2016, John Micco）。【未確認】
- **悪い例**：`page.locator('button.buttonIcon.episode-actions-later')`
- **良い例**：`page.getByRole('button', { name: 'あとで見る' })`
- 【解釈】ロール（role）とアクセシブルな名前でロケータを書くと、支援技術から見た構造もテストの前提になる。UX/アクセシビリティとエンジニアの関心が一致する数少ない接点。
- **出典**：https://playwright.dev/docs/best-practices （原稿：https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/best-practices-js.md）／（未確認）https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html

### E8. アクセシビリティの自動テストを受け入れ条件に入れる。ただし「自動で通った＝アクセシブル」ではない

- **何をするか**：axe-core などの自動検査を CI に入れ、違反ゼロを DoD に置く。同時に、自動で拾えない項目（読み上げ順の意味、代替テキストの適切さ、操作の分かりやすさ）は手動確認や当事者を含むテストで扱う。
- **なぜ**：【確認】axe-core README：*"With axe-core, you can find on average 57% of WCAG issues automatically."* 確信できないものは "incomplete" として返し、手動確認が要る。*"It returns zero false positives (bugs notwithstanding)."* 【確認】Playwright Accessibility testing：*"many accessibility problems can only be discovered through manual testing. We recommend using a combination of automated testing, manual accessibility assessments, and inclusive user testing."*
- **悪い例**：受け入れ条件に「WCAG 2.1 AA に準拠すること」とだけ書く
- **良い例**：「axe の wcag2a/wcag2aa タグの違反が0件」「キーボードだけで申込み完了まで到達できる」「エラー発生時、フォーカスがエラー概要に移り、スクリーンリーダーでエラー内容が読み上げられる」
- **出典**：https://github.com/dequelabs/axe-core （README：https://raw.githubusercontent.com/dequelabs/axe-core/develop/README.md）／ https://playwright.dev/docs/accessibility-testing

### E9. ビジュアル回帰は「環境を固定し、許容差を決めた上で」使う

- **何をするか**：スクリーンショット比較を入れるなら、基準画像を作った環境と同じ環境で回す。差分の許容量（threshold / maxDiffPixels）を決めて、誰が基準画像を更新してよいかを決める。
- **なぜ**：【確認】Playwright Visual comparisons：*"Browser rendering can vary based on the host OS, version, settings, hardware, power source ... headless mode, and other factors. For consistent screenshots, run tests in the same environment where the baseline screenshots were generated."* `threshold` は 0（厳密）〜1（緩い）で既定 0.2。
- **悪い例**：差分が出たら担当エンジニアが黙って基準画像を更新する
- **良い例**：基準画像の更新を PR に含め、デザイナーが差分画像をレビューして承認する
- 【解釈】ビジュアル回帰の「基準画像の承認」は、デザイナーが受け入れに関与できる具体的な入口になる。
- **出典**：https://playwright.dev/docs/test-snapshots （原稿：https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/test-snapshots-js.md）

### E10. サービス間の受け入れは契約テストで分担する

- **何をするか**：API を使う側（consumer）が期待するやりとりを契約として書き、提供側（provider）がそれを満たすかを検証する。
- **なぜ**：E2E で全サービスをつないで確かめると遅く脆い。【確認】Pact 仕様 README：Pact は *"an implementation of 'consumer driven contract' testing that allows mocking of responses in the consumer codebase, and verification of the interactions in the provider codebase."* 受け取る側は緩く、送る側は厳しく（Postel の法則）。注意点として *"you cannot verify, using pact, that a key or a header will not be present in a response. You can only verify what is."*
- **悪い例**：「バックエンドの仕様変更で画面が壊れないこと」を E2E で毎回確かめる
- **良い例**：画面側が使う項目（例：`status` の値の集合）を契約にし、バックエンドの CI で検証。【解釈】④ドメイン用語・③コード値と直結する（契約に出てくる値の名前と意味）
- **出典**：https://github.com/pact-foundation/pact-specification （README：https://raw.githubusercontent.com/pact-foundation/pact-specification/master/README.md）

### E11. 受け入れ条件は「生きたドキュメント」として保守する

- **何をするか**：受け入れ条件をチケットに書き捨てにせず、自動テストとして実行され続ける形（feature ファイル等）で残す。言い回しを揃える。
- **なぜ**：【確認】Cucumber BDD：*"Over time, the documented examples become an asset ... The code reflects the documentation, and the documentation reflects the team's shared understanding of the problem domain."* 【確認】"Who Does What"：*"Don't say the same thing in different ways — say it the same way every time."*（`Given I am logged in` と `Given I have logged in to the site` の例）
- **悪い例**：同じ前提を「ログイン済み」「サインインした状態」「認証後」とバラバラに書く
- **良い例**：前提の言い回しを用語集（④）と揃え、ステップを共有する
- **出典**：https://cucumber.io/docs/bdd/who-does-what/ （原稿：https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/who-does-what.md）

---

## 2. ビジネス・UX視点（10項目）

### B1. 受け入れ条件は「利用者の成功の定義」として書く

- **何をするか**：機能が動くことではなく、利用者がその場面で目的を果たせることを条件にする。Feature の冒頭に Why（In order to / So that）を書く。
- **なぜ**：【確認】Cucumber "Who Does What"：`In order to` は機能の理由で、*"this should match to one of the project's core purposes or 'business values'"*（収益を守る・増やす、コスト管理、ブランド価値など）。シナリオは *"stays focused on the perspective of the person the Feature is intended to serve"*。
- **悪い例**：「CSV エクスポートボタンがある」
- **良い例**：「経理担当者が、月末に当月分の請求データを会計ソフトに取り込める形式で、3クリック以内に保存できる」
- **出典**：https://cucumber.io/docs/bdd/who-does-what/

### B2. INVEST でストーリーの質を点検してから受け入れ条件を書く

- **何をするか**：Independent / Negotiable / Valuable / Estimable / Small / Testable の6点で、受け入れ条件を書く前にストーリーを点検する。
- **なぜ**：受け入れ条件が書けない・多すぎるのは、ストーリーが大きすぎるか、価値が定まっていないことが多い。【確認】Cucumber "User stories" が INVEST を良いストーリーの条件として列挙。【未確認】Bill Wake の原文（2003）は未開封。
- **悪い例**：受け入れ条件が20個並ぶストーリー
- **良い例**：ルールごとに分けられるならストーリーを分割する。【確認】Cucumber "Who Does What"：シナリオが多すぎる Feature は *"you might actually be describing more than one feature"*
- **出典**：https://cucumber.io/docs/terms/user-story/ ／（未確認）https://xp123.com/invest-in-good-stories-and-smart-tasks/

### B3. UX の品質基準を「状態の受け入れ条件」として書く（エラー・空・権限なし・遅い回線・支援技術）

- **何をするか**：正常系の受け入れ条件に加え、次の状態ごとに「利用者に何が見え、次に何ができるか」を書く。
  - エラー時（入力エラー・通信失敗・サーバー失敗）
  - 空状態（初回・検索結果0件・削除後）
  - 権限なし（閲覧のみ・期限切れ・未ログイン）
  - 遅い回線・読み込み中・タイムアウト
  - 支援技術（キーボード・スクリーンリーダー・拡大表示）
- **なぜ**：【解釈】正常系だけの受け入れ条件では、これらの状態の振る舞いが実装者の判断に任され、結果として「技術的には正しいが利用者が詰まる」画面になる。Anthropic の評価ガイドも、エッジケース（無関係・存在しない入力、長すぎる入力、曖昧なケース）を評価に含めるよう勧めており、AI 以外でも同じ考え方が当てはまる。【確認】platform.claude.com develop-tests：*"Don't forget to factor in edge cases!"*
- **悪い例**：「検索結果が一覧で表示される」だけ
- **良い例**：
  ```gherkin
  Rule: 0件のときは次の一手を示す
    Example: 該当なし
      Given 「ｶﾞｽｺﾝﾛ」で一致する商品がない
      When その語で検索する
      Then 「該当する商品はありません」と表示される
      And 表記ゆれを直した候補「ガスコンロ」が示される
  Rule: 通信失敗時は入力を失わない
    Example: 送信中に回線が切れる
      Given 申込みフォームを入力し終えている
      When 送信中に通信が切れる
      Then 入力内容は保持されている
      And 再送信の操作が示される
  ```
- 【解釈】これは ①状態とステータス、②権限とロール の設計と直結する。状態の一覧（①）とロールの一覧（②）から受け入れ条件の「抜け」を機械的に洗い出せる。
- **出典**：https://platform.claude.com/docs/en/test-and-evaluate/develop-tests ／ https://playwright.dev/docs/accessibility-testing

### B4. DoD に「体験の床」を入れる（ストーリーごとに書かない）

- **何をするか**：すべての画面に共通する品質（アクセシビリティ自動検査の違反0、エラーメッセージの文言ルール、読み込み表示の有無など）は DoD に入れ、個別の受け入れ条件には書かない。
- **なぜ**：DoD は個々の項目ではなく成果物全体の品質基準であり、満たさないものはリリースもスプリントレビューでの提示もできない、とされる。【未確認】Scrum Guide 2020 原文は未開封（検索要約で確認）。【解釈】毎回の受け入れ条件に書くと漏れと重複が出る。床は DoD、そのストーリー固有の成功は受け入れ条件、と分けると、UX の要求が「毎回の交渉事項」から「前提」に変わる。
- **悪い例**：ストーリーごとに「アクセシビリティに配慮すること」と書く
- **良い例**：DoD に「axe 違反0件」「キーボード操作で主要タスクが完了できる」「エラー文言は文言ガイドに沿う」を入れる
- **出典**：（未確認）https://scrumguides.org/scrum-guide.html

### B5. Definition of Ready は「関門」ではなく「会話の目安」として使う

- **何をするか**：着手前に「ルールと例がそろっている」「未解決の問いが少ない」ことを確認する。ただし満たさないストーリーを門前払いする道具にしない。
- **なぜ**：DoR は Scrum Guide には含まれない補助的な実践で、関門として運用するとフローを損なうという批判がある。【未確認】scrum.org の議論は検索要約のみ。【確認】Cucumber "Discovery workshop"：1ストーリー25〜30分で終わらないなら、ストーリーが大きすぎるか情報が足りないので、調べ直すために脇に置く。
- **悪い例**：「DoR を満たしていないので着手できません」で差し戻して終わる
- **良い例**：Example Mapping で赤カード（問い）が多いなら、誰がいつまでに答えるかを決めてから戻す
- **出典**：https://cucumber.io/docs/bdd/discovery-workshop/ （原稿：https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/discovery-workshop.md）

### B6. ユーザビリティテストと受け入れテストを混同せず、つなげる

- **何をするか**：受け入れテストは「合意した条件を満たしたか」を確かめる。ユーザビリティテストは「その条件自体が利用者にとって正しかったか」を確かめる。後者で見つかった問題を、次の受け入れ条件・Example に書き戻す。
- **なぜ**：【解釈】受け入れテストに全部通っても使われない機能はあり得る。逆にユーザビリティテストの観察は、そのままでは再現可能な検査にならない。観察を「Given〜のとき When〜すると Then〜できる」に書き戻すと、次の版で退行しない。
- 【確認】Playwright のアクセシビリティ文書も、自動テスト・手動評価・inclusive user testing の組み合わせを推奨しており、「自動の受け入れ」と「人による評価」を役割分担させる考え方は一次資料にもある。
- **悪い例**：ユーザビリティテストの報告書が共有フォルダで眠る
- **良い例**：「5人中3人が送料無料の条件に気づかなかった」→ 受け入れ条件に「カート画面で、あと何円で送料無料になるかが表示される」を追加
- **出典**：https://playwright.dev/docs/accessibility-testing ／（ユーザビリティテスト一般の一次資料は未確認）

### B7. KPI と受け入れ条件の役割を分ける

- **何をするか**：KPI は「出したあと、何を知りたいか」（例：申込み完了率）。受け入れ条件は「出す前に、何ができていればよいか」（例：申込みの各段階でエラーが起きても入力を失わずに再開できる）。KPI を仮説に分解し、仮説を支える振る舞いを受け入れ条件にする。
- **なぜ**：【解釈】KPI を受け入れ条件にすると（「完了率が5%上がること」）、リリース前に判定できず、受け入れ条件として機能しない。逆に受け入れ条件だけでは、出したものが効いたかどうか分からない。Anthropic の評価ガイドの「良い成功基準」は、F1 0.85 以上のような測定可能な目標を挙げており、AI 機能では「リリース前の合格基準」に数値が入りうる点が通常の機能と違う（→ 3章）。【確認】
- **悪い例**：受け入れ条件「コンバージョン率が改善すること」
- **良い例**：KPI「申込み完了率」／仮説「途中離脱の主因は入力エラー後のやり直し」／受け入れ条件「エラー時に入力値が保持され、エラー箇所にフォーカスが移る」
- **出典**：https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

### B8. スコープの判断は PO が、例を出すのはテスター・UX が

- **何をするか**：議論で出た境界ケースを「今回やる／やらない」とその場で決める人を明確にする。やらないものは新しいストーリーとして切り出す。
- **なぜ**：【確認】Cucumber "Who Does What"：PO は *"As the tester comes up with edge cases, the product owner is responsible for deciding what is within scope."* 【確認】BDD の Discovery は *"often reveals low-priority functionality that can be deferred from the scope of a user story"*。
- **悪い例**：エッジケースが出るたびに全部受け入れ条件に追加し、ストーリーが終わらない
- **良い例**：Example Mapping で黄色（ストーリー）カードを新たに切り、後回しにする
- **出典**：https://cucumber.io/docs/bdd/who-does-what/ ／ https://cucumber.io/docs/bdd/

### B9. 受け入れ条件の言葉を、利用者と業務の言葉にそろえる

- **何をするか**：受け入れ条件では、画面の文言・業務用語・コード上の名前を一致させる（④ドメイン用語と連動）。
- **なぜ**：【確認】Cucumber BDD："Formulation" で実行可能な仕様を一緒に書くことで *"we establish a shared language for talking about the system. This helps us to use problem-domain terminology all the way down into the code."* Given/When/Then の誕生にもドメイン駆動設計の「ユビキタス言語」の影響があったとされる（Cucumber "History of BDD"）。【確認】
- **悪い例**：受け入れ条件は「会員」、画面は「ユーザー」、コードは `account`
- **良い例**：用語集で一つに決め、受け入れ条件・画面・コードで同じ語を使う
- **出典**：https://cucumber.io/docs/bdd/ ／ https://cucumber.io/docs/bdd/history/

### B10. 受け入れ条件は「交渉可能」なまま、合意したら固定する

- **何をするか**：議論の段階では条件を変えてよい（INVEST の N）。開発に入ったら、変更は明示的な合意（版の更新）として扱う。
- **なぜ**：【解釈】曖昧なまま着手し、終盤で「こういう意味だった」と条件が動くのが、ビジネスとエンジニアの摩擦の大きな原因になる。Cucumber は Discovery を *"As late as possible before development on a new User Story begins"* に行うよう勧めている。【確認】直前に詰めて、そこで固める、という運用になる。
- **悪い例**：レビュー当日に PO が「やっぱりこの場合も」と条件を足す
- **良い例**：追加は新しい Example として記録し、今回入れるか次に回すかをその場で決める
- **出典**：https://cucumber.io/docs/bdd/discovery-workshop/

---

## 3. AI視点（8項目）

### A1. 受け入れ条件・シナリオは、そのまま AI 機能の評価データ（eval）になる

- **何をするか**：AI 機能の受け入れ条件を「入力・期待される結果・判定方法」の組として書き、eval のタスクとして登録する。
- **なぜ**：【確認】Anthropic "Demystifying evals"：タスク＝「定義された入力と成功基準を持つ一つの評価」。さらに *"Defining eval tasks is one of the best ways to stress-test whether the product requirements are concrete enough to start building."* また *"Two engineers reading the same initial spec could come away with different interpretations ... An eval suite resolves this ambiguity."*、評価は *"the highest-bandwidth communication channel between product and research teams"* になりうる。
- 【確認】OpenAI Evals README：*"If you are building with LLMs, creating high quality evals is one of the most impactful things you can do."* 自社データで非公開 eval を作れる。
- **悪い例**：「問い合わせに適切に答えること」
- **良い例**：`{入力: "解約したいが違約金はいくら？", 期待: 契約種別を確認する質問を返す／金額を断定しない, 判定: LLM採点（ルーブリック）}`
- **出典**：https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents ／ https://github.com/openai/evals

### A2. 確率的な出力には「合格率としきい値」で受け入れ条件を書く

- **何をするか**：1回通れば合格、ではなく「N 件のテストセットで◯%以上」「k 回試行して全部成功」などで書く。複数の観点を同時に置く。
- **なぜ**：【確認】Anthropic develop-tests の良い例：*"The sentiment analysis model should achieve an F1 score of at least 0.85 on a held-out test set of 10,000 diverse Twitter posts..."*。多次元の例：F1 ≥ 0.85、出力の 99.5% が非有害、エラーの 90% が「不便」で済む、95% の応答が 200ms 未満。【確認】"Demystifying evals"：pass@k（k回のうち1回でも成功）と pass^k（k回すべて成功）の区別。*"If your agent has a 75% per-trial success rate and you run 3 trials, the probability of passing all three is (0.75)³ ≈ 42%."*
- 【解釈】利用者が毎回同じ結果を期待する場面（請求額の説明など）は pass^k、1回でも当たれば価値がある場面（案出し）は pass@k、とビジネス・UX 側が選ぶべき指標である。
- **悪い例**：「要約が正確であること」
- **良い例**：「評価セット200件で、事実誤りを含む要約が2%以下。同じ入力に3回実行して3回とも金額を誤らない（pass^3）」
- **出典**：https://platform.claude.com/docs/en/test-and-evaluate/develop-tests ／ https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

### A3. 判定方法（grader）を受け入れ条件の一部として決める

- **何をするか**：各条件を、コードで判定するか、LLM で採点するか、人が見るかを決めて書く。
- **なぜ**：【確認】develop-tests：*"choose the fastest, most reliable, most scalable method"*。コード採点は最速・最も確実だがニュアンスに弱い、人の採点は高品質だが遅く高い（*"Avoid if possible."*）、LLM 採点は柔軟だが *"Test to ensure reliability first then scale."* LLM 採点のこつ：詳細で明確なルーブリック、'correct'/'incorrect' や 1〜5 のような具体的な出力、採点前に推論させる。コード例のコメントに「生成とは別のモデルで評価するのが一般にベストプラクティス」とある。【確認】"Demystifying evals" は3種（code-based / model-based / human）の長所短所を整理。
- **悪い例**：「トーンが丁寧であること」（判定方法なし）
- **良い例**：「LLM 採点。ルーブリック：謝罪は1回まで／専門用語を使わない／最初の文で結論を述べる。1〜5で採点し平均4.0以上。月1回、人が50件を抜き取り、LLM 採点との一致を確認」
- **出典**：https://platform.claude.com/docs/en/test-and-evaluate/develop-tests ／ https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

### A4. ゴールデンデータセットは「実際の失敗」から少数で始める

- **何をするか**：最初から大規模なデータを作らず、既知の失敗・問い合わせ・バグ票から20〜50件を集め、期待結果（参照解）を付ける。
- **なぜ**：【確認】"Demystifying evals"：*"20-50 simple tasks drawn from real failures is a great start."* 手動確認・バグトラッカー・サポート窓口から集める。タスクの質の基準は「2人の領域専門家が独立に同じ合否判定に至る」こと、解けることを示す参照解を付ける。一方 develop-tests は *"More questions with slightly lower signal automated grading is better than fewer questions with high-quality human hand-graded evals."* と量を重視する。【解釈】両者は矛盾せず、「最初は少数の高品質な実例で始め、自動採点できる形にして量を増やす」順番と読める。
- **悪い例**：合成データ1万件を最初に作り、何を測っているか誰も説明できない
- **良い例**：サポート窓口の実例30件に、PO・UX・CS が合否基準を付け、2人の判定が割れたものは基準を直す
- **出典**：https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents ／ https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

### A5. 「やるべきこと」と「やってはいけないこと」の両方を例に入れる

- **何をするか**：肯定例だけでなく否定例（答えるべきでない、断るべき、確認を返すべき）も評価セットに入れる。
- **なぜ**：【確認】"Demystifying evals"：問題セットは肯定・否定の両方を含めて偏りを避ける（片側だけ最適化すると逆側が壊れる）。【確認】develop-tests のエッジケース例：無関係・存在しない入力、長すぎる入力、有害・無関係な入力、人でも合意が難しい曖昧なケース。
- 【解釈】これは B3（エラー・空・権限なし）の AI 版。「AI が答えられないとき何を見せるか」は UX の受け入れ条件そのもの。
- **悪い例**：正しく答えられる質問だけで 95% 合格
- **良い例**：「契約外の質問には答えず、窓口を案内する」例を全体の2割入れる
- **出典**：同上

### A6. 経路ではなく結果を採点し、記録（transcript）を人が読む

- **何をするか**：AI エージェントがどう動いたかではなく、最後に何ができたかで判定する。そのうえで採点結果と実行記録を定期的に人が読む。
- **なぜ**：【確認】"Demystifying evals"：*"Grade what the agent produced, not the path it took."*、*"You won't know if your graders are working well unless you read the transcripts and grades from many trials."*、*"a 0% pass rate across many trials (i.e 0% pass@100) is most often a signal of a broken task, not an incapable agent"*。
- 【解釈】Gherkin の「Then は観察できる結果を書く」（E2）と同じ考え方。手順の固定は実装の自由を奪う、という点で E3 とも一致する。
- **出典**：https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

### A7. 能力の評価と退行の評価を分け、飽和したら作り直す

- **何をするか**：「これからできるようにしたいこと」の評価（低い合格率から始まる）と、「できていたことが壊れていないか」の評価（ほぼ100%を保つ）を別に持つ。100%に張り付いた評価は更新する。
- **なぜ**：【確認】"Demystifying evals"：Capability evals と Regression evals の区別。100%に達すると改善の信号を出さなくなる（saturation）。評価を先に作って能力を定義し、エージェントが満たすまで改善する進め方（*"build evals to define planned capabilities before agents can fulfill them"*）。自動評価・本番モニタリング・定期的な人のレビューを組み合わせる（スイスチーズモデル）。
- 【解釈】通常の受け入れテストは「全部通る」ことが前提だが、AI の能力評価は「通らないものがある」状態から始まる。この違いをビジネス側に説明しないと「テストが落ちている＝未完成」と誤解される。
- **出典**：同上

### A8. AI にテストを書かせる／テストを AI の検証手段として渡す

- **何をするか**：AI に実装を頼むときは、例となる入出力（受け入れ条件）を渡し、テストを走らせて結果を見せるよう指示する。テストを書く AI と実装する AI を分けてもよい。
- **なぜ**：【確認】Claude Code Best practices：*"Give Claude a check it can run: tests, a build, a screenshot to compare."* 悪い例→良い例として "implement a function that validates email addresses" → *"write a validateEmail function. example test cases: user@example.com is true, invalid is false, user@.com is false. run the tests after implementing"*。*"you can do something similar with tests: have one Claude write tests, then another write code to pass them."* 有用な仕様は *"end with an end-to-end verification step that proves the feature works."* develop-tests：*"Get Claude to help you generate more from a baseline set of example test cases."*
- 【解釈】受け入れ条件を Given/When/Then で書いておくと、人間にも AI にも同じ仕様として渡せる。逆に AI がテストを大量生成すると「通るが意味のない」テストが増えうるので、生成元の例（ゴールデン）は人が持ち、生成物はレビューする。Claude Code の文書も、レビュー役に「穴を探せ」と頼むと健全な成果物でも何か報告しがちで、追いかけすぎると過剰設計になると注意している。【確認】
- **出典**：https://code.claude.com/docs/en/best-practices ／ https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

---

## 4. 越境：それぞれが相手を知るべき理由と配慮

### (a) ビジネス・UX がエンジニアリングの観点を知るべき理由

| 知るべきこと | 理由 | 根拠 |
|---|---|---|
| 「テスト可能」でない言葉は検査にならない | 「使いやすい」「すばやく」は合否を決められず、結局実装者の判断になる | 【未確認】INVEST の Testable（Bill Wake）／【確認】Cucumber の user story 定義 |
| Then は観察できる結果で書く | 利用者から見えない結果（DB の値）を条件にすると、体験の保証にならない | 【確認】Gherkin Reference |
| 自動テストの層とコスト | 画面経由の E2E は遅く脆い。全条件を E2E で、と求めると開発が止まる | 【未確認】TestPyramid／【確認】Playwright Best Practices |
| 自動検査の限界 | axe で拾えるのは平均57%。残りは人が見る必要がある | 【確認】axe-core README |
| 境界値・同値分割 | 例の選び方に技法がある。思いつきの例では境目が抜ける | 【未確認】ISTQB |

配慮：【解釈】受け入れ条件を書くときに「この条件はどう確かめますか」とエンジニアに聞く習慣を持つ。判定方法まで一緒に決めると、条件が実装可能な形に締まる。

### (b) エンジニアがビジネス・UX の観点を知るべき理由とどう配慮すべきか

| 知るべきこと | 理由 | どう配慮するか（【解釈】） |
|---|---|---|
| 受け入れ条件は「利用者の成功」 | 機能が動いても利用者が目的を果たせなければ価値がない | Feature の Why（In order to）を読んでからシナリオを書く。Why が空なら PO に聞く |
| 異常系の「見え方」も仕様 | エラー・空・権限なしの画面は実装者が決めがちだが、それが体験の大部分を占めることがある | 状態一覧・ロール一覧から異常系の Example を自分から提案する |
| 宣言的に書くとデザインの自由を守れる | UI 手順を書いたテストは、デザイン変更のたびに壊れる。デザイナーが変更をためらう原因になる | ロケータは role・ラベルで書き、手順はステップ定義に閉じ込める |
| ユーザビリティテストの知見 | 受け入れテストに全部通っても使われない機能はある | 観察結果を Example として受け取り、回帰テストに組み込む |
| 「全部網羅したい」は利用者価値と必ずしも一致しない | 網羅の追求で出荷が遅れれば、利用者は何も得られない | リスクの高い箇所（お金・個人情報・不可逆操作）に網羅を集中する |

### (c) AI 視点

- 【確認】受け入れ条件・シナリオ＝ eval のタスク、という対応は Anthropic の文書で明示されている（A1）。
- 【解釈】そのため、受け入れ条件を構造化して残す（入力・前提・期待結果・判定方法）ことは、AI 機能を作るときの評価データ資産になり、AI に実装を任せるときの検証手段（A8）にもなり、過去の判断の記録（⑥）にもなる。
- 【解釈】AI 機能では「合格率」という概念が入るため、ビジネス・UX が「何%なら出してよいか」「どの失敗は許容できないか」を決める責任を持つ。これはエンジニアだけでは決められない。Anthropic も *"The people closest to product requirements and users are best positioned to define success."* とし、PM やカスタマー対応のチームが eval タスクを作れるようにすることを勧めている。【確認】（WebFetch の要約経由）

---

## 5. ゴールの違いと折り合い

### 5-1. 典型的な対立

| 対立 | QA・エンジニアの主張 | ビジネスの主張 | UX の主張 | 解き方（【解釈】中心。根拠があるものは併記） |
|---|---|---|---|---|
| 網羅 vs 速度 | 境界ケースまで全部テストしたい | 早く出したい。細部は後で | 異常系の見え方も入れたい | リスクで仕分ける。お金・個人情報・不可逆操作は網羅、それ以外は代表例。エッジケースのスコープは PO が決め、後回しは新ストーリーとして切る（【確認】Cucumber Who Does What, BDD） |
| 受け入れ条件の粒度 | 細かく書いてほしい（実装の迷いを減らす） | 書く時間がない | 画面の細部まで書くと縛られる | ルール＋例で書き、手順は書かない（【確認】Better Gherkin）。1ストーリー25〜30分で終わらない分量なら分割（【確認】Discovery workshop） |
| E2E の量 | 脆いので減らしたい | 画面で動くのを見たい | 実際の使われ方で確かめたい | 代表シナリオ1〜数本を E2E、ルールの網羅は下の層。E2E は利用者に見える属性で書く（【確認】Playwright） |
| UX 品質をどこで担保するか | 主観的なものはテストできない | 体験は後から改善できる | 体験こそ品質 | 客観化できる部分は DoD（axe 違反0、キーボード完了）、できない部分はユーザビリティテストで確かめ、結果を Example に書き戻す（B4, B6） |
| ビジュアル回帰の差分 | 差分が出るたびに止まるのは困る | — | 意図しない見た目の変化は困る | 許容差を決め、基準画像の更新はデザイナー承認（【確認】Playwright snapshots の threshold/maxDiffPixels） |
| AI 機能の合格基準 | 決定的に合否を出したい | 「だいたい合っていれば」出したい | 失敗時の体験が重要 | 合格率・しきい値・失敗の深刻度を分けて合意（【確認】develop-tests の多次元基準：エラーの90%は「不便」で済む、など）。pass@k と pass^k のどちらで測るかを場面で選ぶ |
| 受け入れ条件の後出し | 着手後の変更は困る | 状況が変わったので変えたい | テストで気づいたので変えたい | 直前に Discovery を行い（【確認】）、着手後の変更は新しい Example・版として記録 |

### 5-2. 折り合いの原則（【解釈】）

1. **「何を守るか」と「どう確かめるか」を分けて議論する。** 守るべき体験（UX）と、確かめる層・方法（エンジニア）は別の問い。混ぜると「テストしにくいから要件から外す」が起きる。
2. **床（DoD）と個別（受け入れ条件）を分ける。** 毎回交渉するものを減らす。
3. **リスクで網羅度を変える。** 一律の網羅も、一律の省略もしない。
4. **書き戻しの経路を作る。** ユーザビリティテスト・障害・問い合わせ → Example → 自動テスト／eval。
5. **AI 機能では合格率を経営判断として扱う。** 何%で出すかはビジネスとUXが決め、測り方はエンジニアが保証する。

---

## 6. 建設的な議論の進め方

### 6-1. Three Amigos

- 【確認】Cucumber "Who Does What"：PO（スコープ）・テスター（シナリオと境界ケース、どう壊れるか）・開発者（ステップと実装上の制約）の少なくとも3つの声で、ストーリーを Gherkin シナリオにする会。*"it is essential that all of these roles have conversations to discover examples together."* 3人に限る必要はなく、プロジェクト初期に1回だけでもない。
- 【確認】Gherkin の書き手：初期は全員で書き、言い回しが固まったら開発者とテスターのペアで書いて PO がレビューする。
- 【解釈】UX デザイナーは「第4のアミーゴ」として入るのが現実的。担当は、利用者の文脈（どんな状況でこの操作をするか）と、異常系の見え方の提案。

### 6-2. Example Mapping（Matt Wynne, 2015）

- 【確認】Cucumber "Example Mapping"：
  - 黄：ストーリー（一番上）
  - 青：ルール（＝受け入れ条件）。ストーリーの下に並べる
  - 緑：ルールを示す例。対応するルールの下に
  - 赤：その場で答えられない問い。会話を先に進めるために書き出す
  - *"We keep going until the group is satisfied that the scope of the story is clear, or we run out of time."*
- 【確認】Discovery workshop：3〜6人、1ストーリー25〜30分が目安。超えるならストーリーが大きすぎるか情報不足。開発着手のできるだけ直前に行う。
- 【未確認】Matt Wynne の元記事（2015-12-08）にある「25分のタイムボックス」「最後に親指で準備完了か投票する」は検索要約のみ。
- 【解釈】マップの形がそのまま診断になる：青が多い→ストーリーが大きい（分割）／赤が多い→情報不足（調べてから戻す）／緑のない青→ルールが抽象的（例が出せない＝理解が足りない）。

### 6-3. 受け入れ条件のレビュー会（【解釈】運用案）

- 対象：着手直前のストーリーの受け入れ条件（Gherkin または表形式）
- 確認項目：
  1. Why（In order to / So that）が書かれているか
  2. 各ルールに例があるか、境界値が入っているか
  3. 異常系（エラー・空・権限なし・遅い回線・支援技術）の例があるか、DoD でカバーされているか
  4. Then が利用者から観察できる結果か（【確認】Gherkin Reference）
  5. 実装に依存した言い回しがないか（【確認】Better Gherkin の問い）
  6. どの層で確かめるか、AI 機能なら合格率・判定方法が決まっているか
  7. 用語が用語集（④）とそろっているか
- 時間：1ストーリー25〜30分以内（【確認】Discovery workshop の目安を流用）

### 6-4. テストシナリオを UX デザイナーが書く運用（【解釈】）

- やり方：UX デザイナーが、ユーザーフロー・画面状態一覧から Given/When/Then の草案を書く（宣言的スタイル）。開発者とテスターがステップ定義に落とし、PO がスコープを確認する。
- 利点：異常系や空状態が最初から入る。デザインの意図が実行可能な形で残る。
- 注意：UI 手順を書きがち（「◯◯ボタンを押す」）なので、Better Gherkin の問い「実装が変わったらこの文言も変わるか？」で点検する（【確認】）。Cucumber の推奨（初期は全員で書く、慣れたらペア＋PO レビュー）とも矛盾しない。
- AI 機能の場合：UX デザイナー・CS が「良い応答／悪い応答」の実例と理由を書き、それをルーブリックにする（【確認】Anthropic：要件と利用者に最も近い人が成功を定義するのに最適）。

### 6-5. 議論を壊すパターンと言い換え（【解釈】）

| 壊すパターン | 言い換え |
|---|---|
| 「それはテストできません」 | 「どう観察できれば満たしたと言えますか。一緒に例を作りませんか」 |
| 「そこまでやる時間はありません」 | 「このケースは今回入れますか、次のストーリーに切りますか」（PO が決める） |
| 「UX的に気持ちよくしてください」 | 「どの状態で、利用者に何が見え、次に何ができればよいか」 |
| 「AI だから100%は無理です」 | 「何%なら出せますか。どの失敗は1件でも許容できませんか」 |
| 「テストが落ちているので未完成です」（AI の能力評価） | 「これは能力評価なので、合格率の推移で見ましょう。退行評価は全部通っています」 |

---

## 出典一覧

### 【確認】実際に開いて読んだもの

| 資料 | 公開URL | 実際に読んだ場所 |
|---|---|---|
| Cucumber: Behaviour-Driven Development | https://cucumber.io/docs/bdd/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/_index.md |
| Cucumber: Example Mapping | https://cucumber.io/docs/bdd/example-mapping/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/example-mapping.md |
| Cucumber: Discovery workshop | https://cucumber.io/docs/bdd/discovery-workshop/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/discovery-workshop.md |
| Cucumber: Who Does What?（Three Amigos） | https://cucumber.io/docs/bdd/who-does-what/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/who-does-what.md |
| Cucumber: Writing better Gherkin | https://cucumber.io/docs/bdd/better-gherkin/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/better-gherkin.md |
| Cucumber: History of BDD | https://cucumber.io/docs/bdd/history/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/bdd/history.md |
| Cucumber: Gherkin Reference | https://cucumber.io/docs/gherkin/reference/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/gherkin/reference.md |
| Cucumber: User stories | https://cucumber.io/docs/terms/user-story/ | https://raw.githubusercontent.com/cucumber/docs/main/content/docs/terms/user-story.md |
| Playwright: Best Practices | https://playwright.dev/docs/best-practices | https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/best-practices-js.md |
| Playwright: Visual comparisons | https://playwright.dev/docs/test-snapshots | https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/test-snapshots-js.md |
| Playwright: Accessibility testing | https://playwright.dev/docs/accessibility-testing | https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/accessibility-testing-js.md |
| axe-core README | https://github.com/dequelabs/axe-core | https://raw.githubusercontent.com/dequelabs/axe-core/develop/README.md |
| Testing Library: Guiding Principles | https://testing-library.com/docs/guiding-principles | https://raw.githubusercontent.com/testing-library/testing-library-docs/main/docs/guiding-principles.mdx |
| Pact Specification README | https://github.com/pact-foundation/pact-specification | https://raw.githubusercontent.com/pact-foundation/pact-specification/master/README.md |
| OpenAI Evals README | https://github.com/openai/evals | https://raw.githubusercontent.com/openai/evals/main/README.md |
| Anthropic: Define success criteria and build evaluations | https://platform.claude.com/docs/en/test-and-evaluate/develop-tests | 同左 |
| Anthropic: Demystifying evals for AI agents（2026-01-09, Grace / Hadfield / Olivares / De Jonghe） | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | 同左（WebFetch の要約・抜粋経由。全文の逐語確認ではない） |
| Claude Code: Best practices | https://code.claude.com/docs/en/best-practices | 同左（旧URL https://www.anthropic.com/engineering/claude-code-best-practices からリダイレクト） |

注：Cucumber・Playwright は公開サイトが開けず、GitHub 上の原稿（main ブランチ、2026-10-07 時点）を読んだ。公開版と細部が違う可能性がある。

### 【未確認】一次資料を開けず、検索要約・二次情報のみのもの

| 資料 | URL | 本ノートでの扱い |
|---|---|---|
| Martin Fowler: GivenWhenThen（2013） | https://martinfowler.com/bliki/GivenWhenThen.html | GWT の起源の補強のみ。主たる根拠は Cucumber History |
| Martin Fowler: TestPyramid | https://martinfowler.com/bliki/TestPyramid.html | E2E が脆い・高い・遅いという要約のみ |
| Scrum Guide 2020（DoD） | https://scrumguides.org/scrum-guide.html | DoD の定義文は検索結果での引用 |
| Bill Wake: INVEST in Good Stories, and SMART Tasks（2003） | https://xp123.com/invest-in-good-stories-and-smart-tasks/ | 6文字の意味は Cucumber で確認、Testable の説明は未確認 |
| Matt Wynne: Introducing Example Mapping（2015-12-08） | https://cucumber.io/blog/example-mapping-introduction | 25分・親指投票は未確認。カードの色は Cucumber docs で確認 |
| Gojko Adzic: Specification by Example（Manning, 2011） | https://gojko.net/ | キープロセスパターンの名前のみ |
| Google Testing Blog: Just Say No to More End-to-End Tests（2015, Mike Wacker） | https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html | 70/20/10 は未確認 |
| Google Testing Blog: Flaky Tests at Google and How We Mitigate Them（2016, John Micco） | https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html | 1.5% / 16% は未確認 |
| Ron Jeffries: Essential XP: Card, Conversation, Confirmation（2001） | https://ronjeffries.com/xprog/articles/expcardconversationconfirmation/ | Confirmation＝受け入れテストという整理のみ |
| scrum.org の Definition of Ready に関する議論 | https://www.scrum.org/ | DoR が Scrum Guide にない点、関門化の批判 |
| ISTQB: Boundary Value Analysis white paper / CTFL v4.0 | https://istqb.org/wp-content/uploads/2025/10/Boundary-Value-Analysis-white-paper.pdf | 2値/3値 BVA の概要のみ |

### 調べきれていないこと

- ユーザビリティテストと受け入れテストの関係について、一次資料（NN/g 等）を確認できていない。B6 は解釈が中心。
- OpenAI の evals ガイド（platform.openai.com）の本文は未確認。README のみ。
- Deque の「57%」の算出方法（調査対象・期間）は README の記載のみで、元の調査は未確認。
