# エラー設計とログ設計：エンジニア視点のベストプラクティス（リサーチノート）

調査日：2026-10-07
土台：note「UXデザイナー/PdMがKPIとログとエラーを理解しないとデータドリブンにならない」（https://note.com/art_reflection/n/n2458fe47b286 ／本文を開いて主張を確認済み）

## このノートの読み方

- **【事実】** は、出典を実際に開いて確認した内容。引用符「」内は原文（英語）からの引用か、その直訳。
- **【解釈】** は調査担当の整理や意見。出典の主張ではない。
- 調査環境のネットワーク制限で、rfc-editor.org / ietf.org / w3.org / opentelemetry.io / sre.google / aws.amazon.com / docs.cloud.google.com / docs.stripe.com などは直接開けなかった。そのため多くは **GitHub 上の公式ソース**（仕様の原稿リポジトリ、公式ドキュメントのソース）で確認した。どこで確認したかは各項目の出典欄に書いた。開けなかった資料は末尾の「未確認の出典」にまとめ、本文の根拠には使っていない。

### 元の note 記事との関係（要約）

記事の主張（エラーは誰かが実装している／UIに出ないエラーもある／ログは全活動の時系列記録／目的から設計／ログレベル／構造化ログ／必要最小限・保持期間／KPIのためにログを事前に仕込む）は、以下の一次資料とおおむね整合する。エンジニア視点で足すべき論点は主に次の3つ。

1. **エラーは「次に誰が何をすべきか」で分類する**（リトライしてよいか、ユーザーが直せるか、運用者が直すか）。
2. **ログは単独では弱い**。相関ID（トレースID）でつなぎ、メトリクス・トレースと役割分担させる。
3. **ログは目的ごとに分ける**（運用ログ／セキュリティ・監査ログ／プロダクト分析イベント）。保持期間・アクセス権・スキーマ管理の要件が違うから。

---

## A. エラー設計（12項目）

### A-1. エラーを「次の行動」で分類する（誰が・何をすれば直るか）

- **何をするか**：エラーごとに「リトライで直る（一時的）」「呼び出し側が入力を直せば直る」「システムの状態を直すまで直らない」「バグ（運用者が直す）」を区別できるように設計する。
- **なぜか**
  - 【事実】gRPC のステータスコード定義は、`FAILED_PRECONDITION`・`ABORTED`・`UNAVAILABLE` の使い分けを「(a) 失敗した呼び出しだけをリトライすればよいなら `UNAVAILABLE`、(b) より上位のレベルでやり直すべきなら `ABORTED`、(c) システムの状態が明示的に直されるまでリトライすべきでないなら `FAILED_PRECONDITION`」と定めている。
  - 【事実】HTTP では、クライアント側の誤りは 4xx、サーバー側で起きた誤りは 5xx を使う（OWASP Error Handling Cheat Sheet）。
  - 【事実】Azure の Retry パターンは、障害が一時的でない・繰り返しても成功しそうにないなら「操作をキャンセルして例外を報告すべき」としている。
  - 【解釈】依頼書にある「ユーザー起因／システム起因／外部依存」「回復可能／不能」「一時的／恒久的」は直交する軸で、一つの表にまとめるより「その結果、誰が何をするか（ユーザーが入力し直す／自動リトライ／待つ／サポートに連絡／開発者が直す）」に落とすと、UX 側の文言設計とも、アラート設計ともつながる。単一の公式分類体系は今回見つけられなかった。
- **悪い例→良い例**：全部 `500 Internal Server Error` で返す → 入力不備は 400 系＋どの項目か、外部APIの一時障害は 503＋`Retry-After`、状態不整合は 409 などに分ける。
- **出典**
  - gRPC Status codes：https://github.com/grpc/grpc/blob/master/doc/statuscodes.md
  - OWASP Error Handling Cheat Sheet（GitHub ソース）：https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Error_Handling_Cheat_Sheet.md
  - Azure Architecture Center, Retry pattern（GitHub ソース）：https://github.com/MicrosoftDocs/architecture-center/blob/main/docs/patterns/retry-content.md

### A-2. 機械が読むエラーコードと、人が読むメッセージを分ける

- **何をするか**：エラーには安定した機械可読の識別子（コード）を持たせ、人向けの文章とは別のフィールドにする。クライアントに文章をパースさせない。
- **なぜか**
  - 【事実】Google の API 設計指針 AIP-193 は、すべてのエラー応答に `ErrorInfo` を含め、`reason`（UPPER_SNAKE_CASE、最大63文字）と `domain` の組を「特定のエラーを機械が識別する方法」とする。可変の値は `metadata` に入れ、「機械がエラーメッセージを解析しなくて済むように」する。ユーザー向けのローカライズ文は `LocalizedMessage` に分ける。
  - 【事実】RFC 9457 の原稿も「利用者は `detail` を解析して情報を取り出すべきでない（SHOULD NOT）。拡張メンバーのほうが適切で誤りにくい」としている。
- **悪い例→良い例**：`"message": "User 123 not found"` をフロントが正規表現で読む → `{"code": "USER_NOT_FOUND", "user_id": "123", "message": "..."}` のようにコードと値を分ける。
- **出典**
  - AIP-193 Errors（GitHub ソース）：https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0193.md
  - RFC 9457 原稿（下の A-3 参照）

### A-3. HTTP API のエラー応答は RFC 9457（Problem Details）の形にそろえる

- **何をするか**：`Content-Type: application/problem+json` で、`type`・`title`・`status`・`detail`・`instance` と、必要な拡張メンバーを返す。
- **なぜか（【事実】RFC 9457 の原稿リポジトリで確認）**
  - `type` は問題の種類を表す URI。省略時は `about:blank` とみなす。
  - `title` は「発生ごとに変えるべきでない（SHOULD NOT）。ローカライズは除く」。
  - `detail` は「デバッグ情報ではなく、クライアントが問題を直す手助けに焦点を当てる」。
  - 認識できない拡張メンバーは、クライアントが無視しなければならない（MUST）。
  - 複数の問題が同時にあり型が違う場合は、最も関連が深い・緊急なものを返すことを推奨。
  - この文書は RFC 7807 を廃止（obsoletes）する。
  - 【事実】OWASP Error Handling Cheat Sheet も API のエラー応答の形式として RFC 7807 を推奨している（9457 の前身）。
- **悪い例→良い例**：エンドポイントごとに `{"error": ...}` `{"msg": ...}` `{"errors": [...]}` がばらばら → 全APIで Problem Details に統一し、`type` の URI ごとに意味と対処を文書化する。
- **出典**
  - RFC 9457 の原稿（draft-ietf-httpapi-rfc7807bis、IETF HTTPAPI WG の GitHub）：https://github.com/ietf-wg-httpapi/rfc7807bis/blob/main/draft-ietf-httpapi-rfc7807bis.md
  - 注：確認したのは原稿リポジトリの最新版で、RFC として発行された本文（https://www.rfc-editor.org/rfc/rfc9457）は開けなかった。上の内容が発行版と細部で違う可能性は残る。

### A-4. 利用者に返すエラーは汎用的に、詳細はサーバー側のログへ

- **何をするか**：スタックトレース、フレームワークのバージョン、SQL などを応答に含めない。グローバルなエラーハンドラーで、想定外のエラーは汎用メッセージ＋参照IDだけ返し、詳細はログに書く。
- **なぜか**
  - 【事実】OWASP：「想定外のエラーが起きたら、アプリは汎用的な応答を返し、エラーの詳細はサーバー側に調査用として記録し、ユーザーには返さない」。処理されないエラーは攻撃者の偵察を助ける。
  - 【事実】RFC 9457 原稿のセキュリティの節：スタックダンプのような実装詳細を HTTP 経由で見せないことを推奨。
- **悪い例→良い例**：画面に `NullPointerException at com.example...` → 「問題が発生しました。時間をおいてお試しください（お問い合わせ番号: 4bf92f…）」＋ログに同じIDで詳細。
- **出典**：OWASP Error Handling Cheat Sheet（A-1と同じ）、RFC 9457 原稿（A-3と同じ）

### A-5. 例外は握りつぶさない。直せないなら捕まえない

- **何をするか**：`catch` して何もしない／ログだけ書いて成功扱いにする、をやめる。回復できる層でだけ捕まえ、そうでなければ上へ渡す。再送出するときは元のスタックトレースを保つ。
- **なぜか**
  - 【事実】.NET のベストプラクティス：「コードが例外から回復できないなら、その例外を捕まえない。呼び出し元のより上位で回復できるようにする」。`throw e` で投げ直すとスタックトレースが現在のメソッドから始まり直し、途中の呼び出し履歴が失われる。`catch` 内では引数なしの `throw` を使う。
  - 【事実】OpenTelemetry のエラー記録の規約：同じ例外を複数回記録することは推奨しない（NOT RECOMMENDED）。
  - 【解釈】「握りつぶし」と「各層で毎回ログに書く」は逆方向の失敗。前者は UI に出ないエラーを本当に誰にも見えなくし、後者はアラートとログを水増しする。記録するのは「最終的に処理を決めた層で1回」が目安。
- **悪い例→良い例**：`try { pay() } catch (e) {}` → 回復できない層では捕まえず、境界のハンドラーで1回だけ記録して適切なエラー応答に変換。
- **出典**
  - .NET Best practices for exceptions（GitHub ソース）：https://github.com/dotnet/docs/blob/main/docs/standard/exceptions/best-practices-for-exceptions.md
  - OpenTelemetry Semantic Conventions, Recording errors：https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/recording-errors.md

### A-6. 外部呼び出しには必ずタイムアウト（デッドライン）を設定し、下流へ伝える

- **何をするか**：外部API・DB・他サービスの呼び出しすべてに、現実的なタイムアウトを明示する。自サービスがさらに別サービスを呼ぶときは、元の呼び出しの残り時間を引き継ぐ。
- **なぜか**
  - 【事実】gRPC のガイド：既定ではデッドラインが設定されず、クライアントが事実上永遠に待つ可能性がある。「常に現実的なデッドラインを明示的に設定すべき」。値はネットワーク遅延や処理時間からの見積もりで始め、負荷試験で確かめる。サーバーが別のサーバーを呼ぶ場合、元のクライアントのデッドラインを尊重する（デッドラインの伝播）。
  - 【事実】gRPC の `DEADLINE_EXCEEDED` は「状態を変える操作では、操作が成功していてもこのエラーが返ることがある」。
  - 【解釈】タイムアウトは「失敗」ではなく「結果不明」。決済や送信のような操作では、UI でも「失敗しました」と断定せず、結果を確認できる導線が要る（UX担当への論点）。
- **悪い例→良い例**：外部APIを既定値（無制限）で呼び、ユーザーの画面がスピナーのまま → 例えば2秒で打ち切り、代替表示か再試行を案内。
- **出典**
  - gRPC Deadlines guide（grpc.io の GitHub ソース）：https://github.com/grpc/grpc.io/blob/main/content/en/docs/guides/deadlines.md
  - gRPC Status codes（A-1と同じ）

### A-7. リトライは「一時的なエラー」だけに、指数バックオフ＋ジッター＋上限つきで

- **何をするか**：リトライ対象のエラーを限定し、待ち時間を指数的に伸ばし、ランダムな揺らぎ（ジッター）を入れ、最大回数と最大待ち時間を決める。サーバーが `Retry-After` を返したら従う。
- **なぜか**
  - 【事実】AIP-194 は自動リトライしてよいコードを `UNAVAILABLE` だけとし、`INTERNAL`（「通常はバグとして報告すべき」）、`INVALID_ARGUMENT`、`DEADLINE_EXCEEDED` などは自動リトライしないとする。
  - 【事実】gRPC の接続バックオフ仕様：初回1秒、倍率1.6、上限120秒、ジッター0.2 を例示し、同時に始まったバックオフが「分散しなければならない」とする。
  - 【事実】Azure Retry パターン：遅延は段階的または指数的に増やせる。対話的なWebアプリでは少ない回数・短い遅延で失敗させて「後でもう一度お試しください」と出すほうがよく、バッチ処理なら回数を増やして指数的に遅延させる。
  - 【事実】RFC 9110：`Retry-After` は、次のリクエストまでどれだけ待つべきかを示す。503 と一緒に送れば、利用不能が続く見込み時間を示す。
- **悪い例→良い例**：失敗したら即座に無限ループで再送 → 一時エラーのみ、1s・1.6s・2.6s…＋±20%、最大数回で打ち切り。
- **出典**
  - AIP-194 Automatic retry configuration：https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0194.md
  - gRPC Connection Backoff Protocol：https://github.com/grpc/grpc/blob/master/doc/connection-backoff.md
  - Azure Retry pattern（A-1と同じ）
  - RFC 9110（httpwg の GitHub にある rfc9110.xml）：https://github.com/httpwg/http-core/blob/main/rfc9110.xml

### A-8. リトライは1つの層でだけ行う

- **何をするか**：アプリ・SDK・プロキシ・ジョブキューがそれぞれリトライすると回数が掛け算になる。どの層でリトライするか決め、下位層は速く失敗して理由を上へ返す。
- **なぜか**
  - 【事実】Azure Retry パターン：「失敗した操作の全体の文脈が分かる場所でだけリトライを実装する」。リトライ方針を持つタスクが、さらにリトライ方針を持つタスクを呼ぶと長い遅延になる。下位タスクは速く失敗して理由を報告し、上位が自分の方針で扱うほうがよい場合がある。
  - 【解釈】AWS Builders' Library の「Timeouts, retries, and backoff with jitter」もこの増幅の問題を扱っていると広く引用されるが、今回は開けなかったため根拠には使っていない。
- **悪い例→良い例**：フロント3回×BFF3回×SDK3回＝最大27回 → リトライは BFF の1か所、他は0回。
- **出典**：Azure Retry pattern（A-1と同じ）

### A-9. 副作用のある操作は冪等にしてから再試行する（冪等キー）

- **何をするか**：PUT/DELETE は冪等に実装する。POST などの非冪等な操作を再試行するなら、クライアントが一意のキーを付け、サーバーは同じキーの再送を一度だけ処理する。
- **なぜか**
  - 【事実】RFC 9110：同じリクエストを何度送っても、サーバーへの意図した効果が1回と同じなら冪等。PUT、DELETE、安全なメソッドは冪等。クライアントは、非冪等なメソッドを、実際には冪等だと知る手段か、元のリクエストが適用されなかったと検出する手段がない限り、自動で再試行すべきでない（SHOULD NOT）。
  - 【事実】Azure Retry パターン：サービスがリクエストを処理し終えたのに応答を返せなかった場合、再送で2回実行される。クレジットカードの請求のような操作では問題になる。
  - 【事実】IETF の Idempotency-Key ヘッダー（インターネットドラフト、標準化前）：クライアントが生成する一意の値で再送を認識する。元のリクエストが完了する前の再送には 409、同じキーを別の内容で使ったら 422。キーの有効期限はサーバーが定めて文書化すべき（SHOULD）。
- **悪い例→良い例**：「注文する」ボタンの通信がタイムアウト→自動再送で二重注文 → クライアントが `Idempotency-Key: "<UUID>"` を付け、サーバーは同じキーなら前回の結果を返す。
- **出典**
  - RFC 9110 §9.2.2（A-7と同じソース）
  - Azure Retry pattern（A-1と同じ）
  - draft-ietf-httpapi-idempotency-key-header（GitHub）：https://github.com/ietf-wg-httpapi/idempotency/blob/main/draft-ietf-httpapi-idempotency-key-header.md
  - 注：Stripe の冪等キーの公式ドキュメント（https://docs.stripe.com/api/idempotent_requests）はよく参照される実例だが、今回は開けなかった。

### A-10. 失敗し続ける依存先は遮断して速く失敗させ、機能を縮退させる

- **何をするか**：失敗が閾値を超えた依存先にはしばらく呼び出しを送らず即座に失敗させる（サーキットブレーカー）。その間は代替サービスや縮退した機能で応える。
- **なぜか**
  - 【事実】Azure Circuit Breaker パターン：失敗が閾値に達したら、失敗しそうな操作を繰り返さずアクセスを一時的に遮断する。状態は Closed／Open（即座に失敗を返す）／Half-Open（一部だけ試す）。Retry は「いずれ成功する」前提、Circuit Breaker は「失敗しそうな操作をさせない」ためのもので、併用できる。
  - 【事実】Azure Retry パターン：長引く障害なら例外として扱い、代替サービスを呼ぶか、縮退した機能を提供して処理を続ける。
- **悪い例→良い例**：おすすめ API が落ちると商品ページ全体が 500 → おすすめ欄だけ非表示（または人気順の固定リスト）にしてページは出す。
- **出典**
  - Azure Circuit Breaker pattern（GitHub ソース）：https://github.com/MicrosoftDocs/architecture-center/blob/main/docs/patterns/circuit-breaker.md
  - Azure Retry pattern（A-1と同じ）

### A-11. 入力検証はフロントとサーバーの両方で。サーバー側が本番

- **何をするか**：フロントの検証は即時のフィードバック用。同じ規則をサーバーでも必ず検証する。許可リスト方式（受け付ける形を定義し、それ以外を拒否）で書く。
- **なぜか**
  - 【事実】OWASP Input Validation Cheat Sheet：「クライアント側の検証は迂回できる。即時のフィードバックに使う」「ブラウザが同じ項目を検査していても、サーバーで検証する」。アプリが受け付けるものを定義し、規則外を拒否する。危険な文字列を全部見分けようとしない。
  - 【事実】OWASP Logging Cheat Sheet は、入力検証の失敗（プロトコル違反、不正なパラメータ名や値など）を必ず記録すべきイベントに挙げている。
  - 【解釈】フロントとサーバーで規則がずれると「画面では通ったのに送信でエラー」になる。規則を1か所（スキーマ定義など）から両方に配ると UX と安全性の両方に効く。
- **悪い例→良い例**：フロントで文字数を見ているのでAPIは無検査 → APIでも同じスキーマで検証し、違反は 400＋項目名つきで返す。
- **出典**
  - OWASP Input Validation Cheat Sheet（GitHub ソース）：https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Input_Validation_Cheat_Sheet.md
  - OWASP Logging Cheat Sheet（GitHub ソース）：https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Logging_Cheat_Sheet.md

### A-12. アラートは「原因」ではなく「ユーザーが痛い症状」で鳴らし、SLO とエラー予算で判断する

- **何をするか**：アラートの数を絞り、ユーザーが感じる症状（エラー率、遅延）でページする。下位層の個別エラーごとには鳴らさない。信頼性の目標を SLO として決め、そこから許される失敗量（エラー予算）とその消費速度（バーンレート）で判断する。
- **なぜか**
  - 【事実】Prometheus の Alerting practices：Google の Rob Ewaschuk の考え方に基づき、「アラートは単純に、症状で鳴らし、原因を絞り込めるコンソールを用意し、やることのないページは避ける」。エラー率はユーザーに見えるエラーでページし、それを引き起こす下位のエラーで別途ページする必要はない。ただし、ユーザーに見えなくても人の介入が要るほど深刻なもの（例：大きく損失が出ている）はページを足す。
  - 【事実】Prometheus の Instrumentation practices：失敗のたびにカウンターを増やし、試行の総数も別に持つと失敗率を計算しやすい。
  - 【事実】OpenTelemetry の Observability primer：SLI は「サービスの振る舞いの測定」（ユーザー視点）、SLO は SLI をビジネス価値に結びつけ、信頼性を組織に伝える手段。
  - 【事実】Google の slo-generator（OSS）の README：エラー予算を `EB = 1 - SLI`、バーンレートを `EB / EB_target` と定義し、SLO のアラートにはバーンレートが直接の指標や「SLI > SLO」の閾値より信頼でき安定していると述べる。
  - 【解釈】元の note 記事の「UIに出ないエラーもある（外部APIタイムアウト等）」は、Prometheus の「ユーザーに見えないが深刻な失敗にはページを足す」と対になる。UIに出ないエラーは「ユーザーの症状」に現れるか（遅延・成功率の低下）を見て、現れないなら別途アラートを足すかを決める、という順で考えられる。
  - 【未確認】Google SRE Book「Monitoring Distributed Systems」（4つのゴールデンシグナル：遅延・トラフィック・エラー・飽和、症状と原因の区別）と SRE Workbook「Alerting on SLOs」（マルチウィンドウ・マルチバーンレート）は定番の一次資料だが、今回は開けなかった。具体的な数値（例：1時間で予算の何%）は書かない。
- **悪い例→良い例**：DB接続エラー1件ごと、CPU 80% ごとに夜中に電話 → 「チェックアウトの成功率が SLO を割る速度で落ちている」ときだけページ、ほかはチケット。
- **出典**
  - Prometheus, Alerting：https://github.com/prometheus/docs/blob/main/docs/practices/alerting.md
  - Prometheus, Instrumentation：https://github.com/prometheus/docs/blob/main/docs/practices/instrumentation.md
  - OpenTelemetry Observability primer（opentelemetry.io の GitHub ソース）：https://github.com/open-telemetry/opentelemetry.io/blob/main/content/en/docs/concepts/observability-primer.md
  - google/slo-generator README：https://github.com/google/slo-generator

---

## B. ログ設計（12項目）

### B-1. ログは目的から設計し、目的ごとに分ける（運用・セキュリティ／監査・プロダクト分析）

- **何をするか**：「何のためのログか」を先に決める。少なくとも、運用・障害調査用、セキュリティ・監査用、プロダクト分析用イベントを分けて考え、保存先・保持期間・閲覧権限を変える。
- **なぜか**
  - 【事実】OWASP Logging Cheat Sheet：ログの目的として、セキュリティ事象の検知、業務プロセスの監視（購入の離脱など）、監査証跡（データの追加・変更・削除・エクスポート）などを挙げる。そのうえで「プロセス監視、監査、トランザクションのログは、セキュリティイベントのログとは別の目的で集められることが多く、分けておくべきことが多い」。「意図した目的の知識で、何を・いつ・どれだけ記録するかを決める」。
  - 【事実】同：PCI DSS の監査ログは、取引の元の順序を再構成・検証できる時系列記録を含む、という例を挙げる。
  - 【解釈】分析イベントはスキーマの安定と長期保存が要る。運用ログは量が多く短期保存でよいことが多い。監査ログは改ざん防止と法定保持が要る。1本のログに全部載せると、どの要件も中途半端になる。元の note 記事の「ログは目的から設計する」をこの3分類まで具体化するとエンジニアと話しやすい。
- **悪い例→良い例**：アプリの `console.log` を分析ツールに流してKPIを数える → KPI用イベントは別に定義（B-8）、運用ログは障害調査用、ログイン・権限変更は監査ログに。
- **出典**：OWASP Logging Cheat Sheet（A-11と同じ）

### B-2. ログ・メトリクス・トレースを使い分ける

- **何をするか**：「どれくらい起きているか」はメトリクス、「この1リクエストがどこを通ってどこで遅れたか」はトレース、「その時点で何が起きたかの詳細」はログ、と役割を分ける。ログを書く箇所には対応するカウンターも置く。
- **なぜか**
  - 【事実】OpenTelemetry の Observability primer：ログは「サービスなどが出すタイムスタンプ付きのメッセージ」だが、どこから来たかの文脈を持たないことが多く、ログだけではコードの実行経路を追うには足りない。スパンやトレースと相関させると有用性が大きく上がる。トレースは1リクエストが複数サービスを通る経路を記録する。
  - 【事実】Prometheus の Instrumentation practices：「ログのコード1行ごとに、増えるカウンターも持つべき」。気になるログを見つけたとき、どれくらいの頻度で、いつから起きているかを見られるように。
- **悪い例→良い例**：エラー率をログの行数を grep して数える → `http_requests_total{code="5xx"}` のようなメトリクスで率を見て、詳細はトレースID経由でログを引く。
- **出典**：OpenTelemetry Observability primer（A-12と同じ）、Prometheus Instrumentation（A-12と同じ）

### B-3. ログレベルの意味をチームで定義し、運用ルールも決める

- **何をするか**：TRACE/DEBUG/INFO/WARN/ERROR/FATAL の意味を文章で定義する。本番の既定レベル、レベル変更の手順も決める。
- **なぜか**
  - 【事実】OpenTelemetry Logs Data Model は重大度を数値で正規化している：TRACE 1–4（細かいデバッグ、通常は既定で無効）、DEBUG 5–8、INFO 9–12（「イベントが起きたことを示す」）、WARN 13–16（「エラーではないが情報より重要そう」）、ERROR 17–20（「何かがうまくいかなかった」）、FATAL 21–24（「アプリやシステムのクラッシュのような致命的エラー」）。
  - 【事実】OWASP Logging Cheat Sheet：ログレベルを変えられるようにするなら、既定レベルは業務上必要な詳細を満たすこと、変更は承認済みの仕組みか変更管理に従うこと、ログレベルを定期的に検証することを求める。
  - 【事実】Azure Retry パターン：リトライして最終的に成功した失敗でアラートを鳴らさないよう、途中の失敗は情報（informational）として記録し、最後の試行の失敗だけを実際のエラーとして記録するのがよい。
  - 【解釈】「ERROR は誰かが対応すべきもの」「WARN は自動で回復したが傾向を見たいもの」のように、**レベルを“誰が何をするか”に結びつける**と、ERROR の乱発（狼少年化）を防げる。元の note 記事の ERROR/WARN/INFO の説明に、この運用ルールを足すとよい。
- **悪い例→良い例**：リトライ1回目の失敗も ERROR → 途中は INFO/WARN、最終失敗だけ ERROR。
- **出典**
  - OpenTelemetry Logs Data Model（GitHub ソース）：https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md
  - OWASP Logging Cheat Sheet（A-11と同じ）、Azure Retry pattern（A-1と同じ）

### B-4. 構造化ログ（JSON など）で、共通フィールドを決める

- **何をするか**：自由文ではなく、キーと値の構造で出す。時刻・重大度・イベント名・サービス名とバージョン・トレースID・本文・属性など、全サービス共通のフィールドを決める。
- **なぜか**
  - 【事実】OpenTelemetry Logs Data Model のフィールド：Timestamp、ObservedTimestamp、TraceId、SpanId、TraceFlags、SeverityText、SeverityNumber、Body、Resource（ログの発生元）、InstrumentationScope、Attributes、EventName。
  - 【事実】OWASP Logging Cheat Sheet：各イベントに「いつ・どこで・誰が・何を」を記録する（時刻、アプリ名とバージョン、エントリポイントURL、送信元、ユーザー、イベント種別、重大度、結果など）。
  - 【事実】OWASP Logging Vocabulary Cheat Sheet：時刻は UTC オフセットつきの ISO 8601 で記録する。中核フィールドは datetime、appid、event、level、description。
- **悪い例→良い例**：`"2026/10/7 user taro failed login"` → `{"timestamp":"2026-10-07T01:02:03Z","severity":"WARN","event":"authn_login_fail","service":"auth","version":"1.4.2","trace_id":"4bf9…","user_id":"u_123"}`
- **出典**
  - OpenTelemetry Logs Data Model（B-3と同じ）
  - OWASP Logging Cheat Sheet（A-11と同じ）
  - OWASP Logging Vocabulary Cheat Sheet（GitHub ソース）：https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Logging_Vocabulary_Cheat_Sheet.md

### B-5. 相関ID（トレースID）を W3C Trace Context で全サービスに通す

- **何をするか**：リクエストの入口でトレースIDを発行（または受け取り）し、`traceparent` ヘッダーで下流へ伝え、全ログに trace_id / span_id を入れる。ユーザーに見せるエラー画面の参照IDにも使える。
- **なぜか**
  - 【事実】W3C Trace Context：`traceparent` は version・trace-id（16バイト＝16進32文字）・parent-id（8バイト＝16進16文字）・trace-flags の4つをハイフンでつなぐ。例 `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`。全ゼロの trace-id は無効で、不正な場合はヘッダー全体を無視しなければならない（MUST）。`tracestate` はベンダー固有の追跡情報を運ぶ。
  - 【事実】OpenTelemetry Logs Data Model の TraceId / SpanId は W3C Trace Context の定義に従う。
  - 【事実】OWASP Logging Cheat Sheet は「インタラクション識別子」（1回のユーザー操作に関わるイベントすべてをつなぐ方法）を記録項目に挙げる。
- **悪い例→良い例**：サービスごとに独自の request_id を発行し、つなげられない → 入口で `traceparent` を作り、全サービスがそれを引き継いでログに出す。
- **出典**
  - W3C Trace Context（w3c/trace-context の GitHub ソース）：https://github.com/w3c/trace-context/blob/main/spec/20-http_request_header_format.md
  - OpenTelemetry Logs Data Model（B-3と同じ）、OWASP Logging Cheat Sheet（A-11と同じ）

### B-6. エラーは「1回だけ・同じ分類で」記録し、ログ・メトリクス・トレースで値をそろえる

- **何をするか**：失敗した操作には低カーディナリティのエラー種別（`error.type`）を付け、スパン・メトリクス・ログで同じ値を使う。成功には付けない。
- **なぜか**
  - 【事実】OpenTelemetry Recording errors：操作が失敗したらスパンのステータスを Error にし、`error.type` を設定する。所要時間のメトリクスにも `error.type` を含めるべき（SHOULD）で、成功した操作には含めない。1つの操作のスパンと対応メトリクスは同じ `error.type` を持つべき。同じ例外を複数回記録すること、ライブラリ内で処理済みの例外を記録することは推奨しない。
- **悪い例→良い例**：ログには `"Timeout!"`、メトリクスには `err=1`、トレースには何もなし → 3つとも `error.type="timeout"`。
- **出典**：OpenTelemetry Recording errors（A-5と同じ）

### B-7. イベント名は固定の語彙にし、可変の値は属性へ。名前がスキーマの契約になる

- **何をするか**：イベント名に ID や日付を埋め込まない。イベント名ごとに属性の定義（スキーマ）を決め、命名規則（大文字小文字、区切り）を統一する。
- **なぜか**
  - 【事実】OpenTelemetry の Events 規約：イベントは「イベントの構造を一意に識別する」名前を持たなければならない（MUST）。イベント名に動的な値を含めてはならない（MUST NOT）。識別子や発生ごとに変わる値は属性に入れる。あるイベント名で検索したら、対応する規約に従ったイベントが返るべき（＝名前がスキーマの契約になる）。
  - 【事実】OWASP Logging Vocabulary：`authn_login_fail:joebob1` のような「カテゴリ_イベント:パラメータ」形式の共通語彙で、監視・アラートをその語でキーにできるようにする。
  - 【事実】Segment のトラッキングプラン：イベント名は Object + Action（例 `Blog Post Read`）、イベント名は Title Case・プロパティ名は snake_case を推奨。動的なイベント名（`User Signed Up (11-01-2019)`）や、バリエーションごとに別イベントを作ること、動的なプロパティキー（`feature_1`, `feature_2`）を避ける。
- **悪い例→良い例**：`Business Tier Workspace Created` → `Workspace Created` ＋ `account_tier: "business"`。
- **出典**
  - OpenTelemetry Semantic Conventions, Events：https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/events.md
  - OWASP Logging Vocabulary Cheat Sheet（B-4と同じ）
  - Segment Docs, Tracking plan best practices（GitHub ソース）：https://github.com/segmentio/segment-docs/blob/develop/src/protocols/tracking-plan/best-practices.md

### B-8. プロダクト分析用イベントはトラッキングプランとして事前に定義し、変更を管理する

- **何をするか**：KPI からさかのぼって必要なイベントとプロパティを一覧（トラッキングプラン）にし、実装前に合意する。意味が変わる変更はイベント名かスキーマのバージョンを分け、変更履歴を残す。
- **なぜか**
  - 【事実】Segment：命名規則を決めたら守ること（「Pick a convention and stick to it」）、バリエーションはプロパティで表すことを推奨（B-7）。
  - 【事実】OpenTelemetry：イベント名がその構造を一意に識別する（B-7）。
  - 【解釈】スキーマのバージョン管理について、今回開けた資料には決まった方式（例：`schema_version` フィールド）を推奨する記述はなかった。実務では「属性の追加は互換、意味の変更や削除は新しいイベント名かバージョン」とする運用が多いと理解しているが、これは調査担当の解釈。元の note 記事の「KPIを測るにはログを事前に仕込む必要がある」は、エンジニア側では「トラッキングプランがレビュー対象の仕様書になる」ことに当たる。
- **悪い例→良い例**：リリース後に「アクティベーション率が見たい」と言われ、該当イベントがない → 企画段階で KPI→イベント→プロパティの表を作り、PR レビューで照合。
- **出典**：Segment（B-7と同じ）、OpenTelemetry Events（B-7と同じ）

### B-9. 記録してはいけないもの・マスクすべきものを決め、ログ注入を防ぐ

- **何をするか**：パスワード・トークン・セッションID・接続文字列・鍵・カード情報は記録しない。健康情報や公的IDなどの機微な個人情報は、削除・マスク・ハッシュ化・暗号化する。外から来た値は改行や区切り文字を無害化してから書く。
- **なぜか**
  - 【事実】OWASP Logging Cheat Sheet：「法的に認められていない限りデータを記録しない」。直接記録しないもの：ソースコード、セッションID、アクセストークン、認証パスワード、DB接続文字列、暗号鍵などの主要な秘密情報、銀行口座やカード会員データ。機微な個人情報、ファイルパス、内部ネットワーク名、本人特定が不要な個人データは、削除・マスク・サニタイズ・ハッシュ化・暗号化する。ログ注入を防ぐため、CR・LF・区切り文字をサニタイズする。
  - 【事実】同：信頼境界の外から来たイベントデータは欠落・改ざん・偽造・リプレイの可能性があり、信頼できないデータとして扱う。
- **悪い例→良い例**：`{"email":"taro@example.com","password":"..."}` をリクエストごと記録 → パスワードは記録しない、メールは必要ならハッシュ、`user_id` で足りるならそれだけ。
- **出典**：OWASP Logging Cheat Sheet（A-11と同じ）

### B-10. 保持期間は「短すぎず長すぎず」決め、ログ自体を守る

- **何をするか**：ログの種類ごとに保持期間を決め、期限が来たら確実に消す。ログは改ざん検知、書き込み専用の権限、安全な転送で守る。
- **なぜか**
  - 【事実】OWASP Logging Cheat Sheet：ログ、一時的なデバッグログ、バックアップ・コピー・抽出物は、必要な保持期間より前に消してはならず、それを超えて保持してもならない。保存時は改ざん検知を組み込み、できるだけ早く読み取り専用媒体にコピーする。信頼できないネットワークでは安全な転送プロトコルを使う。DBに書くならログ書き込み専用の制限されたアカウントを使う。スタックトレースやリクエスト・レスポンスの本文のような拡張情報は、別のファイルやテーブルに分けることを検討する。
  - 【解釈】「消し忘れたデバッグログ」と「分析基盤にコピーされたログ」が保持期間の抜け穴になりやすい。元の note 記事の「適切な期間だけ保持する」は、コピー先まで含めて期限を決める、まで書くと実装に落ちる。
- **悪い例→良い例**：全ログ無期限保存、開発者全員が本番ログを閲覧可 → 運用ログ30日、監査ログは法定期間、閲覧は役割ごと（日数は例。実際は法務・要件で決める）。
- **出典**：OWASP Logging Cheat Sheet（A-11と同じ）

### B-11. セキュリティ・監査イベントは漏れなく記録する

- **何をするか**：認証の成功と失敗、認可の失敗、セッション管理の失敗、入力検証の失敗、高リスク機能の利用（ユーザー管理、機微データへのアクセス）、同意（オプトイン）、疑わしい業務ロジックの動き、を必ず記録する。
- **なぜか**
  - 【事実】OWASP Logging Cheat Sheet は上記を常に記録すべきイベントとして挙げる。社内システム・信頼された第三者・検索ロボット・監視・ペンテスターなど「既知の」相手のイベントも除外しない（分類フラグを付けるのは可）。
  - 【事実】OWASP Logging Vocabulary は、侵害の発見までの平均時間が約200日のままだという状況を動機に、共通語彙（AUTHN、AUTHZ、EXCESS、INPUT、MALICIOUS、SYS、USER など）でのログを提案する。
- **悪い例→良い例**：ログイン成功だけ記録 → 失敗・権限エラー・管理者操作も、共通のイベント名（`authn_login_fail` など）で記録。
- **出典**：OWASP Logging Cheat Sheet（A-11と同じ）、OWASP Logging Vocabulary（B-4と同じ）

### B-12. 量とコストを設計する：サンプリングとカーディナリティ

- **何をするか**：トレースはサンプリングで量を絞る（同じトレースの中で判断がぶれないようにする）。メトリクスのラベルに user_id のような値を入れない。高カーディナリティの分析はログや分析基盤側で行う。
- **なぜか**
  - 【事実】OpenTelemetry Trace SDK 仕様：サンプリングはバックエンドへ送るトレースの数を減らしてオーバーヘッドを抑える。AlwaysOn、AlwaysOff、TraceIdRatioBased（トレースIDに基づく決定的な判断）、ParentBased（親の判断に従う）などがあり、sampled フラグは子スパンへ伝播する。
  - 【事実】Prometheus Instrumentation practices：ラベルの組み合わせごとに時系列が増え、RAM・CPU・ディスク・ネットワークのコストがかかる。メトリクスのカーディナリティは10未満を目安とし、100を超えうるなら次元を減らすか、汎用の処理システムに分析を移すことを検討する。
  - 【解釈】ERROR のログやエラーになったトレースは、サンプリングで落とさない（全量残す）設計にすることが多いが、OTel の仕様本文でそう推奨されている箇所は今回確認していない（いわゆるテールサンプリングは Collector 側の機能）。
- **悪い例→良い例**：`requests_total{user_id="..."}` → ユーザー別の分析はイベントログで、メトリクスは `route` と `status_class` 程度。
- **出典**
  - OpenTelemetry Trace SDK（GitHub ソース）：https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/trace/sdk.md
  - Prometheus Instrumentation（A-12と同じ）

### （補足）B-13. アプリはログを標準出力にイベントの流れとして出し、ルーティングと保存は基盤に任せる

- 【事実】The Twelve-Factor App：ログは「実行中のすべてのプロセスとバッキングサービスの出力から集めた、時系列のイベントの流れ」。各プロセスはイベントの流れをバッファせず `stdout` に書く。アプリは出力の行き先や保存を気にせず、ログファイルを書いたり管理したりしない。
- 【解釈】元の note 記事の「ログはシステムの全活動の時系列記録」はこの定義とほぼ一致する。アプリ側でファイル管理を持たないことで、保持期間やマスキングを基盤側で一元管理しやすくなる。
- 出典：The Twelve-Factor App, Logs（GitHub ソース）：https://github.com/heroku/12factor/blob/master/content/en/logs.md

---

## C. UX・AI 視点の担当に渡すとよい論点

- **タイムアウトは「失敗」ではなく「結果不明」**（gRPC の DEADLINE_EXCEEDED、RFC 9110 の再試行の条件）。決済・送信の UI で「失敗しました」と断定せず、二重実行を防ぐ導線（冪等キーと対になる「処理中」「結果を確認」表示）をどう出すか。
- **エラー分類の軸（自動リトライ／ユーザーが直せる／待つ／サポートへ）を、UI の文言・行動の選択肢と1対1で対応させられるか**。`type` や `reason` のコードごとに UX 文言を管理する運用を提案できる。
- **ユーザーに見せる参照ID＝トレースID** にすれば、問い合わせから該当ログへ一直線に行ける。表示の仕方とプライバシー上の扱いは UX 側で決めたい。
- **AI 視点**：LLM 呼び出しは「一時的エラー（レート制限・過負荷）」「入力起因（長すぎる・ポリシー拒否）」「出力の品質不良（エラーではないが失敗）」が混ざる。最後の種類はステータスコードに出ないため、評価ログ・ユーザーのフィードバックイベントとして別に設計が要る。また、プロンプトや応答をログに残すときの PII マスキングと保持期間は、OWASP の基準をそのまま当てはめてよいか検討が要る。
- **プロダクト分析イベントの命名とスキーマ管理**（B-7, B-8）は PdM が持ち主になるのが自然。トラッキングプランを誰が承認し、どこで変更履歴を管理するか。

---

## 出典一覧

### 確認できた出典（実際に開いて内容を確認）

| 資料 | 確認した場所 |
|---|---|
| note「UXデザイナー/PdMがKPIとログとエラーを理解しないと…」 | https://note.com/art_reflection/n/n2458fe47b286 |
| RFC 9457 Problem Details（原稿） | https://github.com/ietf-wg-httpapi/rfc7807bis （draft-ietf-httpapi-rfc7807bis.md） |
| RFC 9110 HTTP Semantics（§9.2.2 冪等、Retry-After） | https://github.com/httpwg/http-core （rfc9110.xml） |
| IETF Idempotency-Key ヘッダー（インターネットドラフト） | https://github.com/ietf-wg-httpapi/idempotency |
| W3C Trace Context（traceparent の形式） | https://github.com/w3c/trace-context/blob/main/spec/20-http_request_header_format.md |
| OpenTelemetry Logs Data Model | https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md |
| OpenTelemetry Trace SDK（サンプリング） | https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/trace/sdk.md |
| OpenTelemetry Semantic Conventions: Recording errors | https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/recording-errors.md |
| OpenTelemetry Semantic Conventions: Events | https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/events.md |
| OpenTelemetry Observability primer | https://github.com/open-telemetry/opentelemetry.io/blob/main/content/en/docs/concepts/observability-primer.md |
| OWASP Logging Cheat Sheet | https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Logging_Cheat_Sheet.md |
| OWASP Logging Vocabulary Cheat Sheet | https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Logging_Vocabulary_Cheat_Sheet.md |
| OWASP Error Handling Cheat Sheet | https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Error_Handling_Cheat_Sheet.md |
| OWASP Input Validation Cheat Sheet | https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Input_Validation_Cheat_Sheet.md |
| Google AIP-193 Errors | https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0193.md |
| Google AIP-194 Automatic retry configuration | https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0194.md |
| gRPC Status codes | https://github.com/grpc/grpc/blob/master/doc/statuscodes.md |
| gRPC Connection Backoff Protocol | https://github.com/grpc/grpc/blob/master/doc/connection-backoff.md |
| gRPC Deadlines guide | https://github.com/grpc/grpc.io/blob/main/content/en/docs/guides/deadlines.md |
| Azure Architecture Center: Retry pattern | https://github.com/MicrosoftDocs/architecture-center/blob/main/docs/patterns/retry-content.md |
| Azure Architecture Center: Circuit Breaker pattern | https://github.com/MicrosoftDocs/architecture-center/blob/main/docs/patterns/circuit-breaker.md |
| .NET Best practices for exceptions | https://github.com/dotnet/docs/blob/main/docs/standard/exceptions/best-practices-for-exceptions.md |
| Prometheus: Alerting practices | https://github.com/prometheus/docs/blob/main/docs/practices/alerting.md |
| Prometheus: Instrumentation practices | https://github.com/prometheus/docs/blob/main/docs/practices/instrumentation.md |
| google/slo-generator README（エラー予算・バーンレートの定義） | https://github.com/google/slo-generator |
| Segment: Tracking plan best practices | https://github.com/segmentio/segment-docs/blob/develop/src/protocols/tracking-plan/best-practices.md |
| The Twelve-Factor App: Logs | https://github.com/heroku/12factor/blob/master/content/en/logs.md |

注：GitHub 上のソースは公式リポジトリだが、公開サイトの最新版や発行済み RFC 本文と細部が違う可能性がある。資料に使う前に、公開版の URL（下表）で一度照合することを勧める。

### 確認できなかった出典（ネットワーク制限で開けず。本文の根拠には使っていない）

| 資料 | URL | 備考 |
|---|---|---|
| RFC 9457（発行版） | https://www.rfc-editor.org/rfc/rfc9457 | 原稿で代替確認 |
| W3C Trace Context（公開版） | https://www.w3.org/TR/trace-context/ | GitHub ソースで代替確認 |
| OpenTelemetry 公式サイト | https://opentelemetry.io/docs/ | GitHub ソースで代替確認 |
| OWASP Cheat Sheet Series（公開サイト） | https://cheatsheetseries.owasp.org/ | GitHub ソースで代替確認 |
| Google SRE Book「Monitoring Distributed Systems」 | https://sre.google/sre-book/monitoring-distributed-systems/ | 4つのゴールデンシグナル等。内容は未確認 |
| Google SRE Workbook「Alerting on SLOs」 | https://sre.google/workbook/alerting-on-slos/ | バーンレートの具体値は未確認 |
| AWS Builders' Library「Timeouts, retries, and backoff with jitter」 | https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/ | 未確認 |
| AWS Well-Architected（Reliability, retries） | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html | 未確認 |
| Google Cloud Logging「Structured logging」 | https://cloud.google.com/logging/docs/structured-logging | 未確認 |
| Stripe「Idempotent requests」 | https://docs.stripe.com/api/idempotent_requests | 未確認 |
