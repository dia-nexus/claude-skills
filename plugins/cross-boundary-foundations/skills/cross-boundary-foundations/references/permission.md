# ② 権限とロールの設計 ― 誰が何を見て、何をできるか（リサーチノート）

調査日：2026-10-07
担当：② 権限とロール

## 表記と調査環境について

- 【確認】：一次資料（公式サイト、または公式が管理する GitHub 上の原文）を実際に開いて中身を確かめたもの。
- 【検索要約のみ】：公式ページ本体は開けず、検索エンジンの要約・抜粋で内容を見たもの。原文で裏を取っていないため、引用や数字は原文で確かめてから使うこと。
- 【未確認】：開けず、要約も得られなかったもの。本文では推測で埋めていない。
- 【解釈】：資料から私が組み立てた見方。出典の主張ではない。

この調査環境では、外向きの通信の多くがプロキシで止められていた。開けなかった主なドメインは owasp.org、cheatsheetseries.owasp.org、genai.owasp.org、research.google、usenix.org、openfga.dev、csrc.nist.gov、nvlpubs.nist.gov、nngroup.com、docs.github.com、slack.com、support.google.com、developers.google.com、modelcontextprotocol.io、rfc-editor.org、datatracker.ietf.org、smashingmagazine.com。
そのため OWASP、OpenFGA、GitHub Docs、MCP 仕様、Microsoft Learn、GOV.UK Design System は、各組織が公式に管理している GitHub リポジトリの原文（raw.githubusercontent.com）で確かめた。公式サイトの表示とは版や言い回しが少しずれている可能性がある。

---

## 0. 定義と範囲

**認証と認可を分ける**
- 認証（Authentication）は「その人が誰か」を確かめること。認可（Authorization）は「その人が、その対象に、その操作をしてよいか」を決めること。【確認】OpenFGA: Authorization Concepts（GitHub原文）
  - 原文：認証は "ensures a user's identity"、認可は "determines if a user can perform a certain action on a particular resource"。
- このノートで扱うのは主に認可である。ただしセッションの失効やトークンの寿命は認可にも響くので、関係する範囲で触れる。

**主なモデル**【確認】OpenFGA: Authorization Concepts
| モデル | 判断のもと | OpenFGA の説明（要旨） |
|---|---|---|
| RBAC（ロールベース） | 編集者・管理者のようなロール | 階層がなく、テナントが1つだけの単純な構成には合う。階層・共有・マルチテナントがあると "breaks down"（破綻する） |
| ABAC（属性ベース） | ユーザー・リソース・リクエストの属性 | 例：「marketing と manager の属性を持つ人はマーケ記事を公開できる」 |
| ReBAC（関係ベース） | ユーザーとオブジェクトの関係、オブジェクト同士の関係 | 例：「親フォルダにアクセスできる人は、その中の文書を見られる」 |
| FGA（細粒度認可） | 個々のリソースと操作の単位 | 「Alice は編集者だ」ではなく「Alice は document-42 を編集できる」 |

- RBAC の標準：Ferraiolo と Kuhn が1992年に提案し、2004年に ANSI/INCITS 359-2004 として標準になった。構成は Core、Hierarchical（ロールの継承）、制約つき（職務分掌 Separation of Duty）。【検索要約のみ】NIST RBAC Library（csrc.nist.gov は開けず）
- ABAC の定義（NIST SP 800-162, 2014）：主体・対象・操作、場合によっては環境条件の属性を、ポリシーやルールや関係と照らして認可を決める方式。【検索要約のみ】NIST SP 800-162（本体PDFは開けず）
- Google Zanzibar（USENIX ATC 2019）：Calendar、Cloud、Drive、Maps、Photos、YouTube など数百のサービスが共通で使う、ACL の保存と評価のための全社システム。規模は数兆件の ACL、毎秒数百万件の認可リクエスト。3年間の本番運用で、95パーセンタイルのレイテンシ 10ms 未満、可用性 99.999% 超。【検索要約のみ】（research.google と usenix.org は開けず。論文本文は未読）
  - OpenFGA は Zanzibar を「object-relation-user のタプルを保存し、そのグラフに対して check と逆引きの問い合わせに答える」システムとして紹介している。【確認】OpenFGA: Authorization Concepts

**このテーマの範囲（【解釈】）**
「誰が（主体：人・グループ・外部ゲスト・サービスアカウント・AIエージェント）」「何を（対象：テナント・ワークスペース・フォルダ・レコード・項目）」「どうできるか（操作：見る・作る・直す・消す・共有する・承認する）」「どんな条件で（プラン・時間・状態・関係）」を決め、それを画面・API・データ・ログに一貫して反映させる設計、と定める。①状態設計（例：承認済みになったら編集不可）や③コード値（ロール名・権限キー）と強くつながっている。

---

## 1. エンジニア視点のベストプラクティス（11）

### E1. デフォルト拒否（deny by default）
- **何をするか**：明示的に許可したものだけを通す。公開リソース以外は、ルールがなければ拒否する。
- **なぜか**：許可漏れは「使えない」という問い合わせで見つかるが、拒否漏れは事故が起きるまで見つからない。OWASP Top 10 2021 の A01 では、テストしたアプリの94%に何らかの不備があった。2025年版でも A01 は1位のまま。【確認】
- **悪い例→良い例**：「管理画面の URL を知らなければ入れない」→「管理系のエンドポイントはすべて、ロールが確認できなければ 403/404 を返す」
- **出典**：OWASP Top 10 2021 A01「How to Prevent」の "Except for public resources, deny by default"（要旨）。2025版 A01 は CWE 40件に対応し、SSRF（CWE-918）もこの分類に含まれる。【確認】
  - https://github.com/OWASP/Top10/blob/master/2021/docs/en/A01_2021-Broken_Access_Control.md
  - https://github.com/OWASP/Top10/blob/master/2025/docs/en/A01_2025-Broken_Access_Control.md
  - OWASP Authorization Cheat Sheet「Deny by Default」【確認】

### E2. 最小権限
- **何をするか**：仕事に必要な最小限の権限だけを渡す。人にもサービスアカウントにもトークンにも同じ考えを当てはめる。
- **なぜか**：漏れたとき・間違えたときの被害範囲（blast radius）が、持っている権限の大きさで決まるから。
- **悪い例→良い例**：「とりあえず全員 Admin」→「GitHub は5段階のロール（Read / Triage / Write / Maintain / Admin）を用意し、"without giving people more access to the project than they need" と勧めている」
- **出典**：OWASP Authorization Cheat Sheet「Enforce Least Privileges」"assigning users only the minimum privileges necessary to complete their job"【確認】／GitHub Docs: Repository roles for an organization【確認（GitHub原文）】

### E3. すべてのリクエストを、サーバー側で検証する
- **何をするか**：画面でボタンを隠していても、API でも必ず検査する。AJAX、サーバー間通信、バッチなど、リクエストの経路を問わない。
- **なぜか**：クライアント側の制御は書き換えられる。A01 の典型例には、URL やパラメータの改ざん、強制ブラウズ、POST/PUT/DELETE の認可漏れ、JWT の改ざんが並ぶ。【確認】
- **悪い例→良い例**：「フロントで削除ボタンを非表示にしたので OK」→「DELETE /items/:id の中でも所有者かどうかを確かめる」
- **出典**：Cheat Sheet「Validate the Permissions on Every Request」「Verify that Authorization Checks are Performed in the Right Location」（"must be performed server-side, at the gateway, or using serverless function"）【確認】

### E4. 認可ロジックを一か所に集め、使い回す
- **何をするか**：認可の判断を、各所の if 文に散らさない。ポリシーエンジン、ミドルウェア、認可サービスなど一か所に集める。
- **なぜか**：散らばったチェックは漏れる。Cheat Sheet は RBAC の弱点の一つとして "it is easy to miss or improperly perform role checks" を挙げている。
- **悪い例→良い例**：「各コントローラーで `if user.role == 'admin'`」→「`can(user, 'delete', item)` を一つの関数（または OpenFGA のような認可サービス）に集める」
- **出典**：OWASP A01「Implement access control mechanisms once and re-use them throughout the application」（要旨）【確認】

### E5. レコード単位の所有権を守る（IDOR 対策）
- **何をするか**：「このロールは請求書を読める」で止めず、「この請求書は、この人のテナントや所有者に属するか」まで確かめる。
- **なぜか**：ID を推測・列挙するだけで他人のデータに届く欠陥（Insecure Direct Object Reference。CWE では "Authorization Bypass Through User-Controlled Key"）が A01 の代表例だから。
- **悪い例→良い例**：「`/invoices/1043` を `1044` に変えると他社の請求書が出る」→「推測しにくい ID を使い、それに加えて必ず所有権を検査する（ID を隠すことは主対策にならない）」
- **出典**：A01「enforce record ownership」／Cheat Sheet「Ensure Lookup IDs are Not Accessible Even When Guessed」【確認】

### E6. 要件に合うモデルを選ぶ（RBAC だけで押し切らない）
- **何をするか**：単純な社内ツールなら RBAC で足りる。共有・階層・マルチテナント・条件付きの権限があるなら、ABAC や ReBAC を検討する。
- **なぜか**：Cheat Sheet は ABAC/ReBAC を勧める理由として、細かい条件を書ける、ロール爆発（role explosion）が起きにくい、マルチテナントに向く（RBAC は "poorly suited"）、変更しやすい、を挙げている。
- **悪い例→良い例**：「顧客ごとの例外をロールで表して `editor_jp_finance_readonly_v2` が増え続ける」→「ロールは粗く保ち、"所属部署＝対象の部署" のような条件を属性や関係で書く」
- **出典**：Cheat Sheet「Prefer Attribute and Relationship Based Access Control over RBAC」【確認】／OpenFGA Concepts【確認】
- 【解釈】RBAC を捨てるという意味ではない。業務の人が理解できる単位はロールなので、「表に見せるのはロール、内部の判断は関係や属性」という二層にするのが現実的。

### E7. 共有と継承の仕組みを、最初から明示的に設計する
- **何をするか**：フォルダから文書への継承、組織からチームを経てリポジトリへの継承、外部ゲストへの共有を、関係として定義する。
- **なぜか**：Drive のような「親にアクセスできれば子にもアクセスできる」構造は、後から RBAC に足すと破綻しやすい。Zanzibar は、ACL や中身が変わる途中でも利用者の操作の順序（因果順序）を守る一貫性を重視している。【検索要約のみ】
- **悪い例→良い例**：「共有の機能を後付けで個別テーブルに足していき、継承が画面ごとに違う」→「OpenFGA の型定義で `viewer from parent` のように継承を宣言し、タプルとして持つ」
- **出典**：OpenFGA Concepts（ReBAC の定義）【確認】／Zanzibar 論文要旨【検索要約のみ】

### E8. 拒否と例外の扱いを安全側に倒す
- **何をするか**：認可チェックで例外が起きたら拒否する。エラーメッセージで内部構造や対象の存在を漏らさない。
- **なぜか**：「認可サービスがタイムアウトしたので通す」は最悪の失敗の仕方だから。
- **悪い例→良い例**：「権限 API が落ちたら許可」→「落ちたら拒否し、利用者には再試行を案内する」
- **出典**：Cheat Sheet「Exit Safely when Authorization Checks Fail」"Ensure all exception and failed access control checks are handled no matter how unlikely"【確認】
- 補足：GitHub は、権限のない private リポジトリに対して 403 ではなく 404 を返す。"to avoid confirming the existence of private repositories" のためである。【確認（GitHub Docs 原文）】→ この点は UX の「存在を知らない問題」（U6）と正面からぶつかる。

### E9. 監査ログと検知
- **何をするか**：アクセス制御の失敗を記録し、必要なら管理者に通知する。権限の変更（誰が誰に何を与えたか）も記録する。
- **なぜか**：ログは "one of the most important detective controls"（Cheat Sheet）。A01 も「失敗を記録し、適切に通知する」ことと、自動攻撃へのレート制限を挙げている。
- **悪い例→良い例**：「成功したアクセスしか残らない」→「拒否・権限付与・ロール変更・共有リンク作成を、主体・対象・操作・判断理由・時刻つきで残す」
- **出典**：Cheat Sheet「Implement Appropriate Logging」／A01「Log access control failures, alert admins」【確認】

### E10. 認可をテストで固定する
- **何をするか**：「ロール×操作×対象」の期待値をテストに書き、単体テストと結合テストで回す。
- **なぜか**：認可のバグは機能テストでは見つからない。正常系はどれも通ってしまうから。
- **悪い例→良い例**：「管理者でログインして全画面が動くことだけを確認」→「閲覧者が DELETE すると 403、他テナントの ID は 404、を表形式のテストで網羅する」
- **出典**：Cheat Sheet「Create Unit and Integration Test Cases for Authorization Logic」／A01「include functional access control unit and integration tests」【確認】／OpenFGA モデリング手順の「Test the model」（タプルとアサーションで検証）【確認】

### E11. 権限モデルの変更は「移行」として計画する
- **何をするか**：ロール名やリレーション名の変更・分割は、後方互換 → 新形式の書き込み → 既存データの移行 → 旧定義の削除、という段階を踏む。
- **なぜか**：途中で一瞬でも権限が消えれば業務が止まり、一瞬でも広がれば情報漏えいになる。OpenFGA は "Perform a `write` operation before a `delete` operation to ensure Anne still has access." と書いている。
- **悪い例→良い例**：「マイグレーションで editor を contributor に一括リネーム」→「両方を有効にした期間を設け、データを移してから旧名を消す」
- **出典**：OpenFGA: Migrating Relations【確認（GitHub原文）】
- 【解釈】権限モデルは料金プランや契約にも埋め込まれる（U1）。そのため技術的な移行に加えて、既存顧客の契約上の約束を変えないことも制約に入る。後から変えるのが最も高くつく設計領域の一つ。

---

## 2. ビジネス・UX視点のベストプラクティス（10）

### U1. 権限は料金プランと契約の部品だと認める
- **何をするか**：「どのプランで、どのロールや権限機能が使えるか」を、価格表と同じ表で管理する。
- **なぜか**：実例では、ロールや権限の機能そのものがプランの差になっている。
  - Slack：マルチチャネルゲストとシングルチャネルゲスト、チャネルマネージャーは有料プランのみ。【検索要約のみ】
  - GitHub：カスタムリポジトリロールは GitHub Enterprise Cloud の組織で作れる。【確認（GitHub原文）】
- **悪い例→良い例**：「営業が商談ごとに "この顧客だけ閲覧専用ロールを" と約束し、エンジニアが個別に実装」→「プラン×権限機能の表を一つ持ち、例外は表の更新として扱う」
- **出典**：上記
- 【解釈】権限を「セキュリティの話」としてだけ扱うと、プラン設計と食い違う。

### U2. 組織構造と承認フローを、ロールに写す前に描く
- **何をするか**：役職名ではなく、「誰が何を起案し、誰が承認し、誰が見るだけか」という業務の流れを先に描く。
- **なぜか**：職務分掌（同じ人が起案と承認を兼ねない）は、RBAC の標準にも「制約つき RBAC」として入っている概念で、業務の統制要件そのものだから。【検索要約のみ】
- **悪い例→良い例**：「部長ロール＝何でもできる」→「経費の起案者は自分の申請を承認できない、をルールとして持つ」
- **出典**：NIST RBAC（Separation of Duty）【検索要約のみ】
- 【解釈】①状態設計と重なる。「申請中は申請者が編集できず、差し戻されたらできる」のように、権限は状態によって変わることが多い。

### U3. 「隠す／無効化して理由を示す／申請導線を出す」を使い分ける
- **何をするか**：権限がない操作の見せ方を、次の基準で決める。
  - 存在を知る必要がない、または知られてはいけない → 隠す
  - 存在を知ってほしいが、今は使えない → 無効化し、理由を添える
  - 本人が解決できる → 申請や昇格の導線を出す
- **なぜか**：無効化したボタンは「押せそうなのに反応しない」うえ、何が足りないのかを伝えない。GOV.UK Design System は "Disabled buttons have poor contrast and can confuse some users, so avoid them if possible." と書いている。
- **悪い例→良い例**：「グレーアウトしたボタンだけ」→「"編集には Editor 権限が必要です。オーナー（山田さん）に依頼する" と書き、依頼ボタンを置く」
- **出典**：GOV.UK Design System Button【確認（GitHub原文）】。隠すか無効化するかの経験則（存在を知らせたいなら無効化、今は関係ないなら隠す）は Smashing Magazine "Hidden vs. Disabled In UX"（2024）などにある。【検索要約のみ】NN/g の disabled ボタンに関する記事は【未確認】（nngroup.com が開けず、要約にも NN/g の原文は出てこなかった）

### U4. アクセス申請を、作り込んだ導線にする
- **何をするか**：「権限がありません」で終わらせず、誰に、何の権限を、なぜ求めるかを一度で送れるようにする。承認する側は、その文脈の中で処理できるようにする。
- **なぜか**：Google Drive では、権限のないファイルを開くと「アクセスをリクエスト」が出て、オーナーにメールが届く。2023年の更新で、承認者は共有ボタンの通知ドットと共有ダイアログのバナーから、ファイルの中でリクエストを確認・対応できるようになった。【検索要約のみ】
- **悪い例→良い例**：「エラー画面で行き止まり。管理者が誰かも分からない」→「申請先（オーナーか管理者）を明示し、承認者側にも未対応の印を出す」
- **出典**：Google Drive ヘルプ／Workspace Updates ブログ（2023-06）【検索要約のみ】

### U5. 共有と招待は、範囲と結果を見せてから確定させる
- **何をするか**：共有するときは、相手（社内・社外・リンクを知る全員）、付与する操作、継承で何が一緒に見えるようになるか、を確定前に示す。
- **なぜか**：ReBAC の継承（親フォルダの権限が子に及ぶ）は強力だが、利用者には見えにくい。
- **悪い例→良い例**：「フォルダを共有したら、中の人事評価ファイルも見えるようになった」→「"このフォルダには12件のファイルがあり、すべて閲覧可能になります" と事前に示す」
- **出典**：ReBAC の継承の定義 OpenFGA【確認】。UI の提案は【解釈】

### U6. 「見えないから存在を知らない」問題を設計で扱う
- **何をするか**：セキュリティ上、存在を隠す必要があるもの（E8：GitHub の 404）と、知らないせいで機会を失っているもの（使える機能、申請すれば見られる資料）を分ける。
- **なぜか**：存在を隠すのは正しい場面もある。一方で、隠しすぎると「その機能はない」と思われて、上位プランの価値も申請の機会も消える。
- **悪い例→良い例**：「下位ロールには機能のメニューごと出さないので、誰も上位機能を知らない」→「機能の存在は見せ、必要な権限と申請先を示す。機密の対象（個別のリポジトリや文書）だけは存在を隠す」
- **出典**：GitHub REST の 404 方針【確認】。その他は【解釈】

### U7. 管理者のための権限管理画面は「誰が何をできるか」を逆引きできるようにする
- **何をするか**：ロールの一覧だけでなく、「この人は何ができるか（実効権限）」「この資料に誰が触れるか」「なぜそうなっているか（どの継承やグループ経由か）」を答えられるようにする。
- **なぜか**：継承やグループが絡むと、管理者は理由を説明できない。OpenFGA が check に加えて逆引きの問い合わせ（list-objects など）を持つのは、この問いに答えるためでもある。
- **悪い例→良い例**：「ロール定義画面だけがある」→「ユーザー詳細に実効権限と経路（"Team A 経由で Write"）を出す」
- **出典**：OpenFGA Concepts（逆引き）、Search with permissions（list-objects）【確認】。画面の提案は【解釈】

### U8. オーナー・管理者の人数と、時間を限った特権
- **何をするか**：最上位の権限は少人数に絞るが、1人にはしない。強い権限は必要なときだけ、期限つきで、承認を経て有効にする。
- **なぜか**：GitHub は組織オーナーについて "This role should be limited, but to no less than two people" と書いている。Microsoft Entra PIM は、時間を限った割り当て、有効化の承認、理由の記録、アクセスレビュー、監査履歴を提供する。
- **悪い例→良い例**：「創業者1人だけがオーナーで、退職したら誰も設定を変えられない」→「オーナーは2人以上。普段は一般ロールで、特権は申請して時間を限って使う」
- **出典**：GitHub Docs: Roles in an organization【確認（GitHub原文）】／Microsoft Entra PIM「What is PIM」【確認（MicrosoftDocs原文）】

### U9. エンタープライズの要件（SSO・SCIM・カスタムロール）を最初から想定しておく
- **何をするか**：IdP（Okta、Entra ID など）でのユーザーの作成・停止、グループからロールへの対応づけ、ロールのカスタマイズを、エンタープライズ対応の時点で設計する。
- **なぜか**：SCIM（RFC 7644）を使うと、IdP でアプリを割り当てたり外したりするだけでアカウントが自動で作成・停止される。GitHub Enterprise Server では、SCIM を有効にすると、そのユーザーの削除・停止・昇格をサーバー側で直接できなくなり、IdP 側で行うことになる。権限を「誰が管理するか」が顧客の情シスに移る。
- **悪い例→良い例**：「アプリの中でしかロールを変えられない」→「IdP のグループを正とし、アプリはそれに従う。例外の手動付与は記録する」
- **出典**：GitHub Docs: User provisioning with SCIM on GHES【確認（GitHub原文）】。RFC 7644 本体は【未確認】（rfc-editor.org が開けず）

### U10. ロール名を業務の言葉にし、数を絞る
- **何をするか**：ロールは利用者が自分ごととして選べる名前にし、説明文に「推奨される人」を書く。
- **なぜか**：GitHub のロール説明は機能の列挙ではなく、"Recommended for project managers who need to manage the repository without access to sensitive or destructive actions" のように、誰向けかを書いている。
- **悪い例→良い例**：「Role_3（read+comment+export）」→「閲覧者：資料を見てコメントする社外の協力者向け」
- **出典**：GitHub Docs: Repository roles【確認（GitHub原文）】／Slack のロール体系（Primary Owner / Owner / Admin / Member / Guest）【検索要約のみ】
- 【解釈】④用語と概念モデルと直結する。ロール名は用語集に載せるべき語である。

---

## 3. AI視点のベストプラクティス（8）

### A1. エージェントの権限の過剰を、三つに分けて潰す
- **何をするか**：機能の過剰（不要なツール）、権限の過剰（ツールが持つ権限が広すぎる）、自律の過剰（重い操作を人の確認なしで実行する）を、それぞれ点検する。
- **なぜか**：OWASP LLM06:2025 Excessive Agency は、この三つを根本原因として挙げている。被害は、予想外・曖昧・操作された LLM の出力が、そのまま有害な操作になることで生じる。
- **悪い例→良い例**：「読むだけでよいのに、汎用のシェル実行ツールと DB の管理者接続を渡す」→「SELECT だけの接続で、用途を絞った専用ツールを渡す」
- **出典**：OWASP LLM06:2025 Excessive Agency【確認（GitHub原文）】

### A2. エージェントは「利用者の文脈で」動かす（委任であって、なりすましではない）
- **何をするか**：エージェントの操作は、それを頼んだ利用者の権限の範囲内で行う。全員分の処理を一つの強いシステムアカウントで行わない。
- **なぜか**：LLM06 の対策に "Execute extensions in user's context" がある。危険な例としては、利用者ごとの操作に汎用の高権限アカウントを使うことが挙がっている。
- **悪い例→良い例**：「社内 Bot が管理者トークンで全員のドライブを検索する」→「質問した人の OAuth トークン（またはその人の権限に絞った委任トークン）で検索する」
- **出典**：OWASP LLM06【確認】
- 【未確認】OAuth Token Exchange（RFC 8693）の delegation と impersonation の区別は、datatracker が開けず確認できていない。

### A3. 重い操作には人の承認を挟む
- **何をするか**：削除・送金・外部への送信・権限の付与など影響の大きい操作は、実行前に利用者の承認を取る。
- **なぜか**：LLM06 は "Require user approval" を挙げ、危険な例として「利用者の文書を確認なしに削除する拡張機能」を示している。
- **悪い例→良い例**：「"不要ファイルを整理して" で一括削除」→「削除候補の一覧を見せ、承認を得てから実行する。可逆にできるならゴミ箱に送る」
- **出典**：OWASP LLM06【確認】
- 【解釈】①状態設計の「承認待ち」状態と、U4 の申請導線を、エージェント向けにも作ることになる。

### A4. 完全な仲介：認可は LLM の外で判定する
- **何をするか**：LLM に「権限を守るように」と指示するだけで済ませない。下流の API が、毎回自分で認可を判定する。
- **なぜか**：LLM06 の "Complete mediation"（下流へのリクエストはすべて、セキュリティポリシーに照らして独立に検証する）。プロンプトインジェクションで LLM の判断は覆りうるから。ログ・監視・レート制限は被害を小さくするだけで、防止策としては不十分とも書かれている。
- **悪い例→良い例**：「システムプロンプトに "管理者以外には給与を答えないこと"」→「給与 API が呼び出し元の利用者権限を検査する」
- **出典**：OWASP LLM06【確認】／E3（サーバー側での検証）と同じ原則

### A5. MCP などのツール権限：トークンの宛先とスコープを絞る
- **何をするか**：MCP サーバーは、自分宛てに発行されたトークンだけを受け入れる。上流 API には受け取ったトークンを流用しない。クライアントは必要なスコープだけを求め、足りなくなったら段階的に追加を求める。
- **なぜか**：MCP 仕様（2025-06-18、2025-11-25）は OAuth 2.1 をもとに次を定めている。
  - Resource Indicators（RFC 8707）を必須とする
  - トークンの audience 検証を "MUST" とする
  - "The MCP server MUST NOT pass through the token it received from the MCP client"
  - 2025-11-25 版では、権限不足のときに 403 と `error="insufficient_scope"` で必要なスコープを示し、クライアントが追加の認可を求める、という段階的な昇格（step-up）を記述している
- **悪い例→良い例**：「全部入りのスコープを最初に求め、受け取ったトークンを下流の SaaS にそのまま渡す」→「最小スコープで始め、必要なときに理由つきで追加を求める（利用者には同意画面で見える）」
- **出典**：MCP Specification Authorization 2025-06-18／2025-11-25【確認（GitHub原文）】。Security Best Practices（confused deputy、同意をクライアントごとに取ること）は【検索要約のみ】
- 【解釈】insufficient_scope からの step-up は、U4（申請導線）の機械版といえる。人向けの申請 UI とエージェント向けのスコープ要求は、同じ権限語彙で設計できる。

### A6. 短命で、範囲を絞ったトークンを使う
- **何をするか**：エージェントやスクリプトには、対象リポジトリや資源を絞り、細かい権限と有効期限を持つトークンを発行する。
- **なぜか**：GitHub の fine-grained PAT は、リポジトリ単位で絞れて権限も細かく、有効期限を設定でき、組織が最長期限を強制できる。A01 も「ログアウト後のセッション無効化、JWT は短命に」と書いている。
- **悪い例→良い例**：「期限なしの classic PAT を CI と AI ツールで共有」→「タスク単位で、1リポジトリ・読み取りのみ・7日で切れるトークン」
- **出典**：GitHub Docs: Managing your personal access tokens【確認】／OWASP A01【確認】
- 【未確認】OWASP Top 10 for Agentic Applications 2026 の ASI03 "Identity & Privilege Abuse"（エージェントが利用者の資格情報を受け継ぎ、権限が積み上がり、トークンがタスクより長く生き残る、という問題）は、二次情報の要約でしか見ていない。genai.owasp.org は開けず。

### A7. RAG は「質問者が読めるものだけ」を検索する
- **何をするか**：ベクトル DB や検索インデックスには文書の ACL（グループ ID など）を一緒に持たせ、質問者の権限で絞り込んでから LLM に渡す。
- **なぜか**：OWASP LLM08:2025 は、マルチテナント環境での文脈の漏えいを挙げ、"permission-aware vector and embedding stores" と、データセットの論理的な分割を求めている。LLM02 も最小権限によるデータアクセスの制限を挙げる。
- **実装例**：
  - Azure AI Search の security trimming：`group_ids` フィールドと `search.in()` で、クエリごとに絞り込む（"Document-level authorization is enforced by applying the security filter to every query"）
  - OpenFGA の Search with permissions：検索してから batch-check で落とす／changes API でローカル索引を作る／list-objects で ID を取ってから検索する、の3方式
- **悪い例→良い例**：「全社の文書をまとめて埋め込み、回答の時点で "機密は答えないで" と指示」→「検索の段階で権限フィルタをかけ、LLM には権限内の断片しか渡さない」
- **出典**：OWASP LLM08、LLM02【確認】／Azure AI Search security trimming【確認（MicrosoftDocs原文）】／OpenFGA Search with permissions【確認】
- 【解釈】元の文書の権限が変わったとき（退職・異動・共有解除）、インデックスへの反映がどれだけ遅れるかが、そのまま漏えいの時間幅になる。E11 の移行の問題と同じ構造である。

### A8. 権限の判断ログを、AIの監査と学習のためのデータとして残す
- **何をするか**：認可の判断を「主体（人か、どのエージェントか、誰の代理か）・操作・対象・結果・根拠となったルール・承認者」の形で、構造化して残す。
- **なぜか**：
  - E9 の監査ログが、そのままエージェントの行動監査になる。
  - 「誰の代理で動いたか」が残っていないと、事故のとき責任の所在をたどれない。
  - 拒否や申請の記録は、ロール設計の見直し（どの権限がよく申請されるか）の材料になる。
- **悪い例→良い例**：「アクセスログに "bot-service" とだけ残る」→「`actor=agent:support-bot, on_behalf_of=user:123, action=refund, decision=deny, reason=amount>limit` のように残す」
- **出典**：LLM06 のログ・監視（被害を小さくする策として）【確認】／Entra PIM の理由記録と監査履歴【確認】。形式の提案は【解釈】

---

## 4. 越境：それぞれが相手を知るべき理由と、その配慮

### (a) ビジネス・UX がエンジニアリングの権限設計を知るべき理由
1. **後から変えるのが最も高くつく**：権限モデルの変更はデータの移行を伴い、途中で権限が消えたり広がったりする（E11）。「あとで顧客ごとに細かくできますよね」は、設計の初期にしか安く言えない。【解釈】
2. **ボタンを隠すことはセキュリティではない**：UI 制御とサーバー側の認可は別物（E3）。「画面に出さない」は UX の判断であって、守りにはならない。
3. **ロールの例外を一つ足すと、組み合わせが増える**：ロール爆発（E6）。営業の「この顧客だけ」は、テスト（E10）と管理画面（U7）の負担として跳ね返る。
4. **存在を隠すのは意図的な場合がある**：404 で存在を伏せる方針（E8）を知らずに「申請導線を出して」と求めると、漏えいの経路を作りかねない。

### (b) エンジニアがビジネス・UX の観点を知るべき理由と、配慮
1. **権限は売り物であり、契約である**（U1、U9）。ロールの単位はプラン表や契約書に書かれ、顧客の情シスが SCIM で管理する。内部の都合で名前や粒度を変えると、顧客との約束を破る。
2. **拒否は体験の一部である**（U3、U4）。403 を返すだけでは、利用者は行き止まりで困り、問い合わせが増える。拒否のレスポンスに「必要な権限」「申請先」を、機械が読める形で載せる（insufficient_scope と同じ考え方）と、UI が親切に作れる。
3. **管理者もユーザーである**（U7、U8）。実効権限の逆引きや理由の説明ができない設計は、運用の負担を顧客に押しつける。
4. **配慮の具体例**【解釈】：
   - 権限 API に「判定結果」だけでなく「理由」と「解決策のヒント」を返すフィールドを持たせる。
   - ロール名と説明文を、コード値（③）と表示名に分ける。
   - 権限の変更に「この変更で影響を受ける人数」を出すプレビュー API を用意する。

### (c) AI視点：データ資源として、AIエージェントが使う前提として
1. **権限マトリクスは、AIにとって最も参照価値の高い仕様の一つ**【解釈】。「ロール×操作×対象×条件」が機械可読な形（OpenFGA のモデル、ポリシーファイル、表）であれば、AI はテストを生成し（E10）、UI 文言の下書きを作り（U3）、影響範囲を説明できる（U7）。逆に if 文に散らばっていると、AI も人間も全体を把握できない。
2. **エージェントは新しい種類の主体である**。人・グループ・サービスアカウントに加えて「誰かの代理のエージェント」が入る（A2、A8）。ロール設計の表に、エージェントの行を最初から設ける。
3. **RAG によって、権限設計の穴が回答として表に出る**（A7）。以前は誰も開かなかったフォルダでも、AI は見つけて要約する。共有設定の甘さ（U5）が、AI 導入をきっかけに表面化する。【解釈】
4. **人の承認 UI と、エージェントへの権限昇格は同じ設計問題**（A3、A5、U4、U8）。「誰が、何のために、どれだけの時間、どの範囲を」を一つの語彙で扱う。

---

## 5. ゴールの違いと折り合い

### 典型的な対立（表）

| # | 対立 | 営業・顧客・ビジネスの言い分 | エンジニアの言い分 | UX の言い分 | 解き方（【解釈】） |
|---|---|---|---|---|---|
| 1 | 粒度 | 顧客ごとに細かく柔軟に（カスタムロール） | ロールが増えるとテストと移行が破綻する（E6、E11） | 選択肢が多いと管理者が迷う | **二層構造**：表には少数の既定ロール。カスタムは上位プランで「既定ロールをもとに権限を足し引きする」形に限る（GitHub のカスタムロールが Enterprise 限定なのと同じ構図、U1）。内部は属性や関係で表す |
| 2 | 見せ方 | 上位機能を見せて売りたい | 存在を伏せたい（E8） | 行き止まりを作りたくない | **対象ごとに分ける**（U6）：機能の存在は見せる。個別の機密オブジェクトは隠す。どちらにするかを権限マトリクスの列として明記する |
| 3 | 速さ vs 安全 | 招待や共有を簡単にして広めたい | デフォルト拒否、最小権限（E1、E2） | 摩擦を減らしたい | **既定値を安全に、昇格を簡単に**：最初は狭い権限で招待し、申請と承認を1クリックにする（U4）。共有は確定前に範囲を見せる（U5） |
| 4 | 管理の主導権 | 顧客の情シスに任せたい（SSO/SCIM） | アプリ内の権限と IdP の正がずれる | 二重管理は混乱する | **正（source of truth）を一つに決める**（U9）。IdP 連携時はアプリ内の変更を制限し、例外は記録する |
| 5 | AI の便利さ | エージェントに何でもやらせたい | 権限の過剰（A1） | 毎回の確認はうっとうしい | **影響度で段階を分ける**：読み取りは自動、可逆な変更は事後報告、不可逆・外部送信は事前承認（A3）。スコープは段階的に増やす（A5） |
| 6 | 特権 | 社長や担当者が全部できないと困る | 特権の常時付与は危険 | 権限申請の手間 | **時間を限った特権**（U8、PIM）と、オーナー2人以上 |
| 7 | 監査 | ログは要らない、コストだ | 検知と追跡に必須（E9） | 管理画面で履歴を見たい | **監査ログを顧客向けの機能にする**：エンタープライズ向けの価値として売り、同時に AI の監査にも使う（A8） |

### 解き方の原則【解釈】
- **対立を「誰が正しいか」ではなく「どの層で解くか」に置き換える**。粒度は内部のモデル、見せ方は UI、管理の主導権は運用、と層を分けると、同時に満たせることが多い。
- **既定値は安全側、例外は記録して可逆に**。営業の例外要求は否定せず、「期限つき・記録つき・プラン表に載る」形でだけ受ける。
- **判断の記録を残す**（⑥設計判断の記録へ）。「なぜ RBAC にしたか」「なぜここは 404 か」を残しておかないと、同じ対立が繰り返される。

---

## 6. 建設的な議論の進め方

### 6-1. 「ロール」という言葉から始めない
OpenFGA のモデリング手順は、最初に機能の権限要件を平易な言葉で書かせ、"Avoid using the word 'roles', as this ties you to an RBAC way of thinking" と注意している。書式は "A user {user} can perform action {action} to/on/in {object types} ... IF {conditions}"。【確認】
- 例："A user can share a document with another user or an organization as either editor or viewer if..."
- 【解釈】この書式は、ビジネス・UX・エンジニアが同じ紙に書ける。「〜できる、もし〜なら」の文を集めると、そのまま受け入れ条件（⑤）とテスト（E10）になる。

### 6-2. 進め方（OpenFGA の手順を、三者の会議用に組み替えたもの）
OpenFGA の手順：最も重要な機能を選ぶ → オブジェクトの種類を挙げる → リレーションを挙げる → 定義する → テストする → 繰り返す。【確認】
1. **最も重要な一機能を選ぶ**（全体を一度に決めない）。
2. **ペルソナ×操作の表を作る**（UX が主導）。行は実在の人（社内の一般社員、承認者、経理、外部の協力者、情シス、AIエージェント）、列は操作。
3. **「できる、もし〜なら」の文に直す**（三者で）。条件の欄に、状態（①）・所属・関係・プランが入る。
4. **権限マトリクスに落とす**（エンジニアが主導）。ロール×操作×対象に加えて、「拒否時の見せ方（隠す／理由つきで無効化／申請）」「申請先」「監査対象かどうか」「エージェントに許すか（自動／要承認／不可）」の列を足す。
5. **境界のシナリオで試す**：退職、異動、共有の解除、プランのダウングレード、テナントをまたぐリンク、エージェントが代理で動く場合。
6. **テストとアサーションに変換する**（E10）。マトリクスはテストの元データにする。
7. **繰り返す**。次の機能に移る。

### 6-3. 使える道具
| 道具 | 誰が主に読むか | 何を決めるか | 注意 |
|---|---|---|---|
| 権限マトリクス（ロール×操作×対象＋条件） | 全員 | 誰が何をできるか | 「拒否時の見せ方」「エージェント可否」の列を足す【解釈】 |
| ペルソナ×操作の表 | UX、ビジネス | 実在の人の仕事に必要な操作 | ロール名を先に決めない |
| RACI（実行・説明責任・相談・報告） | ビジネス | 承認フローと責任 | RACI は責任の表であって、システムの権限と一致するとは限らない。A（説明責任）と承認権限の対応を確かめる【解釈】 |
| ロールのユースケース記述 | 全員 | "Recommended for …" の形で、誰向けのロールかを書く（U10、GitHub の書き方） | |
| 平易な文の要件（"can … if …"） | 全員→エンジニア | モデルの元 | OpenFGA の手順【確認】 |
| 境界シナリオ集 | 全員 | 退職・異動・ダウングレード・代理 | ⑤受け入れ条件と共有する |
| 設計判断の記録 | 将来の全員と AI | なぜそのモデルか、なぜ隠すのか | ⑥と接続 |

### 6-4. 会議で使える問い【解釈】
- 「その人は、権限がないと分かったとき、次に何をすればいいですか」（U3、U4）
- 「その例外は、プラン表のどこに書かれますか」（U1）
- 「退職した翌日、その人が作った共有リンクはどうなりますか」（U9、A7）
- 「エージェントがこの操作をするとき、誰の権限で、誰の承認で動きますか」（A2、A3）
- 「この権限を後から分割するとしたら、移行に何が要りますか」（E11）

---

## 出典一覧

### 【確認】（一次資料。公式の GitHub 原文を含む）
1. OWASP Top 10 2021 A01 Broken Access Control（GitHub 原文）
   https://github.com/OWASP/Top10/blob/master/2021/docs/en/A01_2021-Broken_Access_Control.md （公式表示：https://owasp.org/Top10/A01_2021-Broken_Access_Control/ は開けず）
2. OWASP Top 10 2025 A01 Broken Access Control（GitHub 原文）
   https://github.com/OWASP/Top10/blob/master/2025/docs/en/A01_2025-Broken_Access_Control.md
3. OWASP Authorization Cheat Sheet（GitHub 原文）
   https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Authorization_Cheat_Sheet.md （公式表示：https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html は開けず）
4. OWASP Top 10 for LLM 2025: LLM06 Excessive Agency（GitHub 原文）
   https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM06_ExcessiveAgency.md （公式表示：https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ は開けず）
5. OWASP LLM08:2025 Vector and Embedding Weaknesses（GitHub 原文）
   https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM08_VectorAndEmbeddingWeaknesses.md
6. OWASP LLM02:2025 Sensitive Information Disclosure（GitHub 原文）
   https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM02_SensitiveInformationDisclosure.md
7. OpenFGA: Authorization Concepts（GitHub 原文）
   https://github.com/openfga/openfga.dev/blob/main/docs/content/authorization-concepts.mdx
8. OpenFGA: Modeling – Getting Started（GitHub 原文）
   https://github.com/openfga/openfga.dev/blob/main/docs/content/modeling/getting-started.mdx
9. OpenFGA: Migrating Relations（GitHub 原文）
   https://github.com/openfga/openfga.dev/blob/main/docs/content/modeling/migrating/migrating-relations.mdx
10. OpenFGA: Search with Permissions（GitHub 原文）
    https://github.com/openfga/openfga.dev/blob/main/docs/content/interacting/search-with-permissions.mdx
11. GitHub Docs: Repository roles for an organization（GitHub 原文）
    https://github.com/github/docs/blob/main/content/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization.md
12. GitHub Docs: Roles in an organization（GitHub 原文）
    https://github.com/github/docs/blob/main/content/organizations/managing-peoples-access-to-your-organization-with-roles/roles-in-an-organization.md
13. GitHub Docs: Troubleshooting the REST API（404 と 403 の方針）
    https://github.com/github/docs/blob/main/content/rest/using-the-rest-api/troubleshooting-the-rest-api.md
14. GitHub Docs: Managing your personal access tokens
    https://github.com/github/docs/blob/main/content/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens.md
15. GitHub Docs: User provisioning with SCIM on GHES
    https://github.com/github/docs/blob/main/content/admin/managing-iam/provisioning-user-accounts-with-scim/user-provisioning-with-scim-on-ghes.md
16. MCP Specification 2025-06-18: Authorization（GitHub 原文）
    https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-06-18/basic/authorization.mdx
17. MCP Specification 2025-11-25: Authorization（GitHub 原文）
    https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/authorization.mdx
18. Microsoft Entra Privileged Identity Management（MicrosoftDocs 原文）
    https://github.com/MicrosoftDocs/entra-docs/blob/main/docs/id-governance/privileged-identity-management/pim-configure.md
19. Azure AI Search: Security trimming（MicrosoftDocs 原文）
    https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/search/search-security-trimming-for-azure-search.md
20. GOV.UK Design System: Button（disabled ボタンの指針。GitHub 原文）
    https://github.com/alphagov/govuk-design-system/blob/main/src/components/button/index.md

### 【検索要約のみ】（本体は開けず、検索の要約・抜粋で内容を見たもの。使う前に原文で確かめること）
21. Pang et al., "Zanzibar: Google's Consistent, Global Authorization System", USENIX ATC 2019
    https://www.usenix.org/conference/atc19/presentation/pang ／ https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/
22. NIST SP 800-162 Guide to ABAC Definition and Considerations（2014）
    https://csrc.nist.gov/pubs/sp/800/162/final
23. NIST RBAC Library（ANSI/INCITS 359-2004、職務分掌）
    https://csrc.nist.gov/projects/role-based-access-control/rbac-library
24. Slack: Types of roles in Slack
    https://slack.com/help/articles/360018112273
25. Google Drive ヘルプ（アクセスのリクエスト）／Workspace Updates（2023-06 アクセスリクエストへの対応）
    https://support.google.com/drive/answer/53355 ／ https://workspaceupdates.googleblog.com/2023/06/respond-to-access-requests-for-google-workspace-files-efficiently.html
26. Smashing Magazine "Hidden vs. Disabled In UX"（2024-05）
    https://smashingmagazine.com/2024/05/hidden-vs-disabled-ux/
27. MCP Security Best Practices（confused deputy、トークンのパススルー）
    https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
28. OWASP Top 10 for Agentic Applications 2026（ASI02、ASI03。二次情報の要約のみ）
    https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

### 【未確認】（開けず、要約からも原文の内容を得られなかったもの）
- NN/g（Nielsen Norman Group）の、無効化したボタンや権限エラーの表示に関する記事（nngroup.com が開けず、Jakob Nielsen の Substack も開けなかった）
- RFC 7644（SCIM）本体、RFC 8693（OAuth Token Exchange：delegation と impersonation の区別）本体
- Google Workspace 管理者ロールの公式ヘルプ（support.google.com/a/answer/2405986）、Drive API のロール定義（developers.google.com）
- OpenFGA 公式サイトの表示版（openfga.dev。内容は GitHub 原文で代わりに確認した）
