# UX視点の「エラー設計」と「ログ設計」 リサーチノート

調査日：2026-10-07　担当：UX視点
土台：note「UXデザイナー/PdMがKPIとログとエラーを理解しないとデータドリブンにならない」 https://note.com/art_reflection/n/n2458fe47b286 （本文を開いて主張を確認済み）

---

## 0. 読む前に：確認の状況と表記

**調査環境の制約。** この環境のネットワークは、nngroup.com、w3.org、smashingmagazine.com、baymard.com、research.google（HEART論文）、alistapart.com などへの接続が遮断されていた。そこで、公式資料の**原文が GitHub で公開されているもの**（W3C WCAG のソース、GOV.UK Design System、IBM Carbon、MDN、React 公式ドキュメント、Mixpanel・PostHog・Sentry の公式ドキュメント）を開いて確かめた。開けなかった資料は「未確認」と書き、本文の内容に頼らないようにした。

**表記。**
- 【確認】……出典の原文を開いて確かめた事実。引用は英語原文のまま、または忠実な要約。
- 【未確認】……原文を開けなかった。検索結果の抜粋で存在や見出しだけ分かったもの。内容の根拠には使わない。
- 【解釈】……筆者（調査担当）の考え。出典の主張ではない。

**出典どうしで食い違う点があった。** いちばん大きいのは「インラインバリデーションをいつ出すか」。GOV.UK は「欄を離れたときに検証するな、送信時まで待て」、IBM Carbon は「欄を離れたらすぐ検証せよ」と、正反対のことを言っている。A-4 で並べて扱う。

---

## A. エラー設計（UX視点）

元の note 記事の「UXデザイナーは文言だけでなく、どんなときにどんなエラーをどう出すかを設計すべき」を、**①起こさない → ②気づかせる → ③直させる → ④人に渡す**の順に分けた。

### A-1. エラーを「状態の一覧」として棚卸しし、種類ごとに出し方を変える

- **何をするか**：画面ごとに、起こりうる失敗を種類で洗い出す。入力の誤り、資格・権限がない、想定外のシステム障害、計画的な停止、データが空、通信の失敗やタイムアウト、の6つ程度。それぞれ別の見せ方を決める。
- **なぜ**：【確認】GOV.UK は、入力の検証（validation）を「資格や権限の確認に使うな。その場合は資格がないことと次にできることを伝えるページへ案内せよ」としている。さらに 500（想定外の障害）、503（意図した停止）、404 に、それぞれ別のパターンを用意している。【確認】IBM Carbon は空状態を「初回」「ユーザー操作の結果（検索結果0件など）」「エラー管理（権限・システム障害・設定が必要）」に分け、エラー管理のときは「より具体的に詳しく書くほうがよい」としている。
- **悪い例→良い例**：どの失敗にも「エラーが発生しました」→ 権限なしなら「このプロジェクトを見る権限がありません。管理者に申請できます［申請する］」、障害なら「表示できませんでした。入力内容は保存されています」
- 【解釈】元の note 記事の「UIに出ないエラー（ローディングが回り続けるだけ）」は、この一覧に「待ち続けて終わらない」状態が入っていないために生じる。一覧を作る段階で「何秒たったら失敗とみなすか」を決めておけば防げる。
- 出典：https://design-system.service.gov.uk/patterns/validation/ （GitHub 原文 `alphagov/govuk-design-system/src/patterns/validation/index.md` で確認）／ https://carbondesignsystem.com/patterns/empty-states-pattern/ （GitHub 原文 `carbon-design-system/carbon-website` で確認）

### A-2. 予防①：受け入れる形式を広げ、誤りを起こしにくい入力部品を使う

- **何をするか**：郵便番号のスペースや電話番号のハイフンなど、あいまいでない限り多様な書き方を受け入れる。不要な文字は捨てて受け付ける。選べる値が決まっているなら、自由入力より選択式の部品にする。
- **なぜ**：【確認】GOV.UK は「エラーメッセージを出す機会そのものを減らせ」とし、その手段に「問いをよく設計する」「あいまいでない限り様々な形式を受け入れる」を挙げる。スペース、見えない文字、ハイフン、括弧などは「誤って入ると、ユーザーが見つけて直すのが難しい」ので無視せよ、とも書く（コピー＆ペーストや音声入力で混じる例つき）。【確認】Carbon は、選択式など「有効な値しか入らない」部品（bound entry controls）なら検証が要らないとしている。
- 【未確認】Nielsen の10ヒューリスティクス第5項「エラーの予防」。検索結果の抜粋では「良いエラーメッセージより、問題を起こさない注意深い設計のほうがよい」という趣旨が示されていたが、NN/g の原文は開けなかった。
- **悪い例→良い例**：「半角数字7桁で入力してください（ハイフン不可）」→ 「123-4567」「１２３４５６７」「123 4567」をどれも受け付ける
- 出典：GOV.UK validation（上記）／ https://carbondesignsystem.com/patterns/forms-pattern/ （GitHub 原文で確認）／ https://www.nngroup.com/articles/ten-usability-heuristics/ 【未確認】

### A-3. 予防②：取り返しのつかない操作には「取り消し・確認・見直し」のどれかを用意する

- **何をするか**：お金、契約、データの削除・上書きを伴う操作では、(a) あとで取り消せる、(b) 入力の誤りを検査して直す機会がある、(c) 確定前に見直して直せる、の少なくとも1つを満たす。
- **なぜ**：【確認】WCAG 2.x の達成基準 3.3.4 Error Prevention (Legal, Financial, Data)（レベル AA）がこの3択を求めている。原文は "Submissions are reversible." / "Data entered by the user is checked for input errors and the user is provided an opportunity to correct them." / "A mechanism is available for reviewing, confirming, and correcting information before finalizing the submission."。【確認】GOV.UK の「Check answers」パターンは、送信直前に回答を見直すページを置くことで「送信前に誤りに気づいて直す2度目の機会を与え、誤り率を下げる」としている。各項目に「変更」リンクを置き、直したあとは最初からやり直させずに見直しページへ戻すこと、と書く。
- **悪い例→良い例**：「削除」を押すと即座に消える → 消したあと「削除しました［元に戻す］」を数秒表示する、または削除前に対象名を示して確認する
- 【解釈】確認ダイアログを毎回出すと、読まずに押す癖がつく。頻繁な操作は「取り消し」で守り、まれで重い操作だけ「確認」で守る、という使い分けが現実的。これは出典の主張ではない。
- 出典：https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html （GitHub 原文 `w3c/wcag/guidelines/sc/20/error-prevention-legal-financial-data.html` で確認）／ https://design-system.service.gov.uk/patterns/check-answers/ （GitHub 原文で確認）

### A-4. インラインバリデーションのタイミング：流派が分かれていることを知ったうえで決める

- **何をするか**：「いつ赤くするか」「いつ赤を消すか」をプロダクトとして1つに決め、全フォームで揃える。
- **出典ごとの立場**：
  - 【確認】**GOV.UK（送信時派）**："Do not validate when the user moves away from a field." 次へ進もうとした時点（「続ける」「送信」）まで待つ。入力し終わる前の検証は「特に入力が遅いユーザーに問題を起こす」。例外は、リサーチで利点が上回ると示せた場合だけ（文字数カウントで上限超過を知らせる例）。
  - 【確認】**IBM Carbon（離脱時派）**：クライアント側のインライン検証は "should happen as soon as the field loses focus"。
  - 【確認】**MDN（aria-invalid）**：必須欄が空であることを理由に、送信を試みる前から `aria-invalid="true"` を付けるな、としている。
  - 【確認・二次情報】**"reward early, punish late"**：GitHub 上の議論（filament #12164）によれば、「不正な値は、ユーザーが直した瞬間に正常表示へ戻す（reward early）。正常な値は、入力を終えるまで（blur や change まで）赤くしない（punish late）」。この議論は出典として Smashing Magazine の2022年9月の記事を挙げている。
  - 【未確認】Smashing Magazine（Vitaly Friedman, 2022）のインラインバリデーション記事、Baymard Institute のインラインバリデーション記事。どちらも原文を開けなかった。検索抜粋に数値が出ていたが、出典が確かめられないので使わない。
- **共通している点**：どの立場も「入力中に責めない」では一致している。違うのは、最初に赤くするのを「離れたとき」にするか「送信時」にするか。
- **悪い例→良い例**：メールアドレスの1文字目を打った瞬間「メールアドレスの形式が正しくありません」→ 送信時（または離れたとき）に初めて指摘し、指摘したあとは直した瞬間に消す
- 【解釈】行政サービスのように、入力に時間がかかる人や支援技術を使う人の割合が高い文脈では、GOV.UK 寄りが安全。パスワード作成のように条件が多い欄は、条件を先に見せておき、満たしたものから順に印を付ける「前向きな知らせ」が向いている。どちらにするかは推測で決めず、対象ユーザーで確かめる論点。
- 出典：GOV.UK validation（上記）／Carbon forms（上記）／ https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-invalid （GitHub 原文 `mdn/content` で確認）／ https://github.com/filamentphp/filament/discussions/12164 （確認）／Smashing・Baymard【未確認】

### A-5. メッセージの中身：「何が起きたか」と「どう直すか」を、その欄に固有の言葉で書く

- **何をするか**：汎用文を使わず、欄ごと・失敗の種類ごとに文を用意する。ラベルの言葉をそのまま使う。
- **なぜ**：【確認】WCAG 3.3.1 Error Identification（A）："If an input error is automatically detected, the item that is in error is identified and the error is described to the user in text." 【確認】WCAG 3.3.3 Error Suggestion（AA）："If an input error is automatically detected and suggestions for correction are known, then the suggestions are provided to the user, unless it would jeopardize the security or purpose of the content." 【確認】GOV.UK は "Describe what has happened and tell them how to fix it." とし、「An error occurred」「This field is required」のような汎用文を避けるよう求めている。テキスト欄なら、空・長すぎ・短すぎ・使えない文字・形式違いで文を分ける。ラベル「1週間に何時間働きますか」に対して「1週間に働く時間を入力してください」のように、ラベルの言葉を含めると対応が分かりやすい、ともある。
- 【未確認】NN/g のエラーメッセージガイドライン。検索抜粋では「可視性・伝え方・効率の3観点×各4項目＝12項目」という構成が示されていたが、原文は開けなかった。
- **悪い例→良い例**：「入力内容に誤りがあります」→「生年月日の『月』は1〜12で入力してください」
- 【解釈】「なぜ」（原因）はユーザーが直すのに役立つときだけ書けばよい。システム側の原因（タイムアウト等）は、ユーザーが次にとる行動（待つ、再試行する、別手段を使う）が変わる程度にだけ伝える。
- 出典：https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html ／ https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html （いずれも GitHub 原文 `w3c/wcag/guidelines/sc/20/` で確認）／ https://design-system.service.gov.uk/components/error-message/ （GitHub 原文で確認）／ https://www.nngroup.com/articles/error-message-guidelines/ 【未確認】

### A-6. 言い方：責めない、謝りすぎない、専門用語やエラー番号を出さない

- **何をするか**：利用者の落ち度を示す言葉、技術用語、ふざけた調子を避け、直し方を淡々と書く。
- **なぜ**：【確認】GOV.UK が避けるよう挙げている語：技術用語（「form post error」「unspecified error」「error 0x0000000643」）、「forbidden」「illegal」「you forgot」「prohibited」、「please」（選択肢があるように聞こえるため）、「sorry」（直す助けにならないため）、「valid / invalid」（何も情報を足さないため）、「oops」などのくだけた言い方。「声に出して読んで、自分が言いそうな文か確かめよ」ともある。
- 【未確認】Nielsen 第9項「ユーザーがエラーを認識・診断・回復できるよう助ける」。検索抜粋では「平易な言葉で（コードを使わず）、問題を正確に示し、解決策を建設的に提案する」という趣旨。原文は開けなかった。
- **悪い例→良い例**：「不正な値です（E-4012）」→「カード番号は16桁で入力してください」
- 【解釈】日本語では「お手数ですが」「恐れ入りますが」を付けるのが慣習になっている。GOV.UK の please / sorry 不要論をそのまま持ち込むかどうかは、日本語の読者で確かめるべき点。GOV.UK 自身も 500 ページの研究課題に「please と sorry を期待するか」を挙げていて、結論は出していない（【確認】）。
- 出典：GOV.UK error message（上記）／GOV.UK problem with the service pages（下記 A-10）

### A-7. 位置と同時性：欄のすぐ近くと、画面上部の要約の両方に、同じ文で出す

- **何をするか**：送信時の誤りは、(1) 画面上部に要約を出してそこにフォーカスを移し、(2) 各項目のリンクから該当欄へ飛べるようにし、(3) 該当欄の近くにも同じ文を出す。
- **なぜ**：【確認】GOV.UK Error summary："Always show an error summary when there is a validation error, even if there's only one." キーボードのフォーカスを要約に移し、各項目を該当欄にリンクし、欄のそばと要約で同じ文を使う（「見た目も音も意味も同じに」「文脈から離れても意味が通るように」）。ページの `<title>` の先頭に「Error: 」を付けて、スクリーンリーダーにすぐ読み上げさせる。【確認】欄の近くには、質問文とヒントのあとに赤い文と赤い枠で示す。
- **悪い例→良い例**：画面最下部の送信ボタン横に「3件のエラーがあります」とだけ出る → 上部に3件の一覧（各項目がリンク）、各欄の下に同じ文
- 【解釈】長いフォームやスマートフォンでは、誤りのある欄が画面外に出やすい。要約からリンクで飛べることが、見つけられないまま離脱することを防ぐ。
- 出典：https://design-system.service.gov.uk/components/error-summary/ ／ error-message（いずれも GitHub 原文で確認）

### A-8. 入力を消さない・二度入力させない

- **何をするか**：誤りがあっても、正しかった欄・誤っていた欄とも入力値を残す。同じ手続きのなかで一度もらった情報を、もう一度打たせない。
- **なぜ**：【確認】GOV.UK："Do not clear any form fields when showing the Error message component. Keep both passing and failing answers." 何が違ったかが見え、直すだけで済み、再入力を避けられるため。【確認】WCAG 2.2 で追加された 3.3.7 Redundant Entry（A）：同じ手続きで再入力が要る情報は、自動で埋めるか選べるようにする（本質的に必要な場合、セキュリティ上必要な場合、情報が古くなった場合は例外）。【確認】GOV.UK の 500 ページのパターンも、障害時に入力済みの情報を一定期間保存し、復旧後に再開できるようにせよとしている。
- **悪い例→良い例**：送信エラーでページが再読込され、全欄が空になる → 入力値が残り、誤った欄だけ印が付く
- 出典：GOV.UK error message ／ https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html （GitHub 原文 `w3c/wcag/guidelines/sc/22/redundant-entry.html` で確認）

### A-9. 支援技術にも同じ情報が届くようにする

- **何をするか**：誤りのある欄には、検証のあとに `aria-invalid="true"` を付ける。エラー文は `aria-describedby`（または `aria-errormessage`）で欄と結び付ける。動的に出すエラーは、最初から DOM にある `role="alert"` などのライブリージョンに入れて読み上げさせる。
- **なぜ**：【確認】W3C 達成方法 ARIA21：`aria-invalid` は検証が行われたあとに付ける。`aria-describedby` でエラー文を欄に関連づける例も示されている。【確認】ARIA19：`role="alert"` またはライブリージョンでエラーを知らせる。要点は "the error container must be present in the DOM on page load for the error message to be spoken by most screen readers"。【確認】WCAG の Status Messages（AA）："status messages can be programmatically determined through role or properties such that they can be presented to the user by assistive technologies without receiving focus."（※番号 4.1.3 は既知の情報。今回開いた原文ファイルには番号の記載がなく、本文では確かめていない）。
- **悪い例→良い例**：赤い枠だけで誤りを示す（色だけ・音声なし）→ 文で示し、欄と結び付け、読み上げられる
- 【解釈】UXデザイナーが担うのは属性の実装ではなく、「どの文が、どの欄に結び付き、いつ読み上げられるか」を仕様に書くこと。A-4 のタイミングの決定がそのまま `aria-invalid` を付ける時点になる。
- 出典：https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA21 ／ https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA19 ／ https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html （いずれも GitHub 原文 `w3c/wcag` で確認）／MDN aria-invalid（確認）

### A-10. システム側の失敗：何が起きたか、入力はどうなったか、ほかに何ができるか

- **何をするか**：想定外の障害（500相当）と、意図した停止（503相当）を分ける。どちらも「入力済みの内容がどうなったか」「問い合わせ先」「目的を果たせる別の手段」を示す。
- **なぜ**：【確認】GOV.UK「There is a problem with the service」：想定外の問題はすべて同じページで出す。見出しは「Sorry, there is a problem with the service」、本文は「Try again later.」。手続きの途中なら回答がどうなったかを書き、役に立つなら問い合わせ先を、目的を果たせるなら別サービスへのリンクを置く。「500」「bad request」などの用語、「We are experiencing technical difficulties」、赤い警告文は使わない。"Log all errors and fix them as quickly as possible." 短時間で直らなければサービスを閉じて「Service unavailable」ページに切り替える。【確認】研究は5人で行われ、「いつ使えるようになるか」「どうすれば目的を果たせるか」の2つのニーズが見つかった。ただし想定外の障害では前者には答えられない、と認めている。【確認】「Service unavailable」では、再開の曜日・日付・時刻を書き、「maintenance」「improvements」のようなあいまいな語を避ける。
- **悪い例→良い例**：「500 Internal Server Error」→「申し込みを完了できませんでした。入力内容は30日間保存されています。時間をおいて再度お試しいただくか、お電話（平日9〜17時）でも申し込めます」
- 出典：https://design-system.service.gov.uk/patterns/problem-with-the-service-pages/ ／ https://design-system.service.gov.uk/patterns/service-unavailable-pages/ （いずれも GitHub 原文で確認）

### A-11. 「待ち」を状態として設計し、終わらない待ちをなくす

- **何をするか**：読み込み中の見せ方（スケルトン、インジケーター、進捗バー）を処理の長さで使い分ける。さらに「一定時間で失敗とみなし、再試行や別手段を示す」状態を必ず定義する。
- **なぜ**：【確認】Carbon：ローディングインジケーターは「処理中であること」しか伝えず進み具合は示さない。"If a process will take more than a moment or two to complete, use a progress indicator instead." スケルトンは、タイルやデータ表のような入れ物型の部品に使う。【確認】Mixpanel は、反応のないクリック（dead click）を「対話要素をクリックしたのに、一定時間内に目に見える反応がない」と定義し、既定値を0.5秒としている。
- 【解釈】タイムアウトまでの秒数、オフライン時に何を見せるか（読める・書けない・送信待ちに入る等）、部分的な失敗（10件中2件が保存できなかった）の見せ方については、今回開けた一次資料に具体的な基準がなかった。ここは各プロダクトで決めるしかない。元の note 記事の言う「UIに出ないエラー」はこの層にある。最低限、「何秒で諦めるか」「諦めたら何を出すか」「何件成功・何件失敗かを数えて示すか」の3つを仕様に書くとよい。
- **悪い例→良い例**：保存ボタンを押すとスピナーが回り続ける → 10秒で「保存できませんでした。通信状態を確認して再試行してください［再試行］」、部分的な失敗なら「8件保存、2件は保存できませんでした［2件を表示］」
- 出典：https://carbondesignsystem.com/patterns/loading-pattern/ （GitHub 原文で確認）／ https://docs.mixpanel.com/docs/tracking-methods/autocapture （GitHub 原文 `mixpanel/docs` で確認）／オフライン UX の一次資料は【未確認】（web.dev の該当記事は開けなかった）

### A-12. 楽観的UI：先に成功を見せたなら、失敗時の「巻き戻し」と「知らせ」を両方設計する

- **何をするか**：サーバーの応答を待たずに結果を先に見せる場合、失敗したら表示を元に戻し、戻ったことを利用者に知らせる。
- **なぜ**：【確認】React の `useOptimistic` は、処理が失敗すると表示が自動で元に戻る（"a failure means value hasn't changed, so the UI shows what it showed before the optimistic update"）。一方、エラーを利用者に伝えるのは開発者の責任（"You can catch the error to show a message to the user"）。
- **悪い例→良い例**：「いいね」が付いたように見えたのに、黙って消える → 元に戻したうえで「いいねできませんでした［再試行］」
- 【解釈】仕組みとして自動なのは巻き戻しだけで、知らせは自動ではない。黙って戻ると「押したはずなのに」という不信になる。この「知らせ」はUXデザイナーが仕様に書かないと抜け落ちやすい。
- 出典：https://react.dev/reference/react/useOptimistic （GitHub 原文 `reactjs/react.dev` で確認）

### A-13. エラーから人へ渡す：エラーの記録とサポートの窓口をつなぐ

- **何をするか**：障害画面や問い合わせフォームに、そのエラーの識別子（短い参照番号）を添える。利用者の申告とシステムの記録を突き合わせられるようにする。
- **なぜ**：【確認】Sentry の Crash-Report Modal は、従来の 500 ページを出す場面で、名前・メール・状況の説明を集め、"Sentry pairs the feedback with the original event"。バックエンドで生成したイベントIDを渡して結び付ける。独自のUIからでも `associatedEventId` でフィードバックとエラーを関連づけられる。【確認】GOV.UK の 500 ページも、役に立つなら連絡先を示すよう求めている（A-10）。
- **悪い例→良い例**：「エラーが発生しました。サポートにお問い合わせください」→「申し込みを完了できませんでした（参照番号：K7F2-91）。お問い合わせの際にこの番号をお伝えいただくと、状況をすぐ確認できます」
- 【解釈】ここでエラー設計とログ設計がつながる。参照番号は「エラーコードを見せるな」（A-6）と矛盾しない。原因を説明するためのものではなく、人に渡すための札として出す。
- 出典：https://docs.sentry.io/platforms/javascript/user-feedback/ （GitHub 原文 `getsentry/sentry-docs` で確認）

### A-14. 空状態：何もないことを、次の一手への案内に変える

- **何をするか**：データが空の画面に、空である理由と次の行動（主ボタン・副リンク）を置く。可能なら前向きな言い方で書く。
- **なぜ**：【確認】Carbon：空状態のタイトルは、可能なら肯定文で書く（「データ資産がありません」より「データ資産を追加して始めましょう」）。本文では、空を埋める次の行動を明確に説明する。空状態は "often treated as an afterthought" とも書いている。検索結果0件なら、検索語や絞り込みを変えればよいと分かるようにする。
- **悪い例→良い例**：「データがありません」→「まだ請求書はありません。最初の請求書を作成すると、ここに一覧で表示されます［請求書を作成］」
- 出典：Carbon empty states（上記）

---

## B. ログ設計（UX・プロダクト分析の視点）

元の note 記事の「KPI設計は何を知りたいかの宣言、ログ設計はそれをどう観測するかの実装」を、公式ガイドと照らし合わせた。主張の骨格は Mixpanel の公式手順とほぼ一致していた（B-1）。

### B-1. KPI → 行動フロー → イベント・プロパティ の順に逆算する

- **何をするか**：最初にKPIを決めて優先順位を付ける。次に、KPIを動かす利用者の行動の流れ（同じ結果に至る別ルートも含む）を書く。最後にその流れをイベント（行動）とプロパティ（その行動の文脈）に分解する。
- **なぜ**：【確認】Mixpanel の公式トラッキングプラン手順は、そのまま "Define and prioritize KPIs" → "Map KPIs to User Flows" → "Translate Flows into Events / Properties" の3段階。さらに "Tracking everything and anything your user can do in your product can lead to unnecessary development effort and unused data." とある。【確認】PostHog も、最初に「成長イベント」（登録・購読・購入など、成功を直接示す行動）を明示的に計測せよとし、自動取得（autocapture）任せで `user_signed_up` を計測し忘れる例を挙げている。
- **悪い例→良い例**：「とりあえず全クリックを取っておく」→「KPI：初回の請求書送付率。必須通過点：取引先登録 → 請求書作成 → 送付。この3つの成功と失敗をイベントにする」
- 【解釈】元の note 記事の「必須通過点」は、Mixpanel の言う "user flows" のなかでも、通らないとKPIに届かない地点のこと。逆算の起点に置くのは、プロダクト側の売上指標ではなく、利用者の成功を表す行動（元の note 記事の例ではお気に入り登録）。ここが「UX視点のログ設計」の要になる。
- 出典：https://docs.mixpanel.com/docs/tracking-best-practices/tracking-plan （GitHub 原文で確認）／ https://posthog.com/docs/product-analytics/best-practices （GitHub 原文 `PostHog/posthog.com` で確認）

### B-2. トラッキングプランを「なぜ」付きの共有文書にする

- **何をするか**：イベント名、発火条件、プロパティ、データ型、目的（どのKPI・どの問いのためか）、個人情報かどうか、担当者を1つの文書にまとめ、変更のたびに更新する。
- **なぜ**：【確認】Mixpanel は、トラッキングプランを「実装の唯一の正解（source of truth）」となる中央の文書とし、KPI、イベント・プロパティ、チーム横断のメモを含む "living and shared document" にせよとしている。プライバシーのガイドでも、イベントとプロパティごとに "definitions, data types, business purposes, and PII flags" を記録せよとある。命名規則もプランに書いておく。
- 【解釈】元の note 記事の「なぜ→何を→どうやって の順でエンジニアに伝える」は、プランの列の並びとして形にできる。「目的（なぜ）」「イベントと発火条件（何を）」の列はUX/PdMが書き、「実装方法（どうやって）」の列はエンジニアが書く、という分担にするとよい。
- **悪い例→良い例**：Slack で「ボタン押されたら取っといて」→ プランに「`invoice_send`／送信APIが成功を返した時点／目的：KPI『初回送付率』の分子／担当：○○」
- 出典：Mixpanel tracking plan ／ https://docs.mixpanel.com/guides/guides-by-workflow/build-tracking-strategy ／ https://docs.mixpanel.com/guides/guides-by-workflow/data-privacy （いずれも GitHub 原文で確認）

### B-3. イベントは少なく保ち、違いはプロパティで表す

- **何をするか**：画面名やボタンIDをイベント名に埋め込まない。固定のイベント名に、可変の値をプロパティとして付ける。
- **なぜ**：【確認】PostHog："Event names and property names should be defined as fixed strings in your code, never generated dynamically." `page_viewed_${pageName}` のような書き方では、何千もの別イベントができて絞り込みも分析もできなくなる。【確認】Mixpanel：プロパティを使えば「バリエーションごとに別イベントを作らずに済む」。データ型（文字列・数値・真偽値）を揃える。アプリのバージョンや端末種別など全イベントに共通する文脈は、自動で付く共通プロパティにする。
- **悪い例→良い例**：`error_email_format`、`error_password_short`… → `form_validation_fail`＋`field: "email"`, `reason: "format"`
- 出典：PostHog best practices ／ Mixpanel build tracking strategy（いずれも確認）

### B-4. 命名規則を1つ決め、全プラットフォームで守る

- **何をするか**：大文字小文字、区切り、動詞の時制、語順を決めて文書化する。
- **なぜ**：【確認】PostHog は、登録という同じ行動を Web は `Create Account`（登録ボタンを押した時点）、iOS は `user_sign_up`、Android は `create-account`（登録完了時のみ）と別々に記録してしまう例を挙げる。そのうえで、小文字・snake_case・使ってよい動詞の一覧（click, submit, create, view, … fail …）・`category:object_action` 形式（例 `signup_flow:pricing_page_view`）、真偽値は `is_`/`has_` で始める、を提案している。【確認】Mixpanel も「1つ選んで全部で使え」「`SignUp`、`signup_started`、`Signup Started` を混ぜるな」とし、snake_case を推奨している。
- 【確認・注意点】PostHog 自身のドキュメント内でも、別のページでは `[object] [verb]` 形式で過去形（`user signed up`）を勧めていて、規則が1つに揃っていない。正解の形式があるわけではなく、「揃っていること」に価値がある、と読むのが妥当。
- 出典：PostHog best practices ／ PostHog naming tip（`contents/docs/integrate/send-events/_snippets/naming-tip.mdx`）／ Mixpanel build tracking strategy（いずれも確認）

### B-5. 「いつ発火するか」を定義に含める（押した時点か、成功した時点か）

- **何をするか**：同じ名前のイベントでも、「ボタンを押した」「送信した」「サーバーが成功を返した」は別物として定義する。
- **なぜ**：【確認】B-4 の PostHog の例では、Web は「押した時点」、Android は「完了した時点」で記録していて、同じ「登録」の数が食い違う。【確認】PostHog は、正確さが要る数（直近1週間の登録数など）はバックエンドで記録し、画面遷移やクリックのように一部欠けてもよいものはフロントエンドで記録せよとしている。理由は、ブロッカーで送信が止められたり、JavaScript の実行が中断されたりするため。
- 【解釈】エラー設計とつなげると、「押した（`*_submit`）」と「成功した（`*_create` 等）」と「失敗した（`*_fail`）」の3つを取れば、その差から失敗と離脱が見える。押した数と成功した数の差は、UIに出ないエラーを数で拾う最も簡単な方法になる。
- 出典：PostHog best practices（確認）

### B-6. エラーそのものをイベントとして設計する

- **何をするか**：利用者に見せたエラー（入力の誤り、システムの失敗、タイムアウト）を、一定の形式のイベントとして記録する。
- **確認できた範囲**：【確認】PostHog が推奨する動詞の一覧に `fail` が入っている。【確認】Mixpanel は、自由記述の入力値を送るなとしている（意図しない個人情報が入るため）。【確認】Sentry は、エラーごとにイベントIDを持ち、利用者のフィードバックと結び付けられる。
- 【解釈】UX分析用のエラーイベントには、たとえば次のプロパティがあるとよい。`error_kind`（入力／権限／システム／通信／タイムアウト＝A-1 の分類）、`field`（どの欄か。**値そのものは送らない**）、`reason`（形式違い・空など）、`detected_by`（クライアント／サーバー）、`step`（フローのどの段階か）、`shown_as`（欄横・要約・トースト・全画面）、`error_ref`（A-13 の参照番号。エンジニア側のエラー記録と突き合わせる鍵）。エンジニア側のエラーログ（スタックトレース等）とは目的が違う。こちらは「利用者が何を見て、どうしたか」を数えるためのもの。
- **悪い例→良い例**：エラーはサーバーログにしかなく、どの画面で何人が見たか分からない → `form_validation_fail {step: "payment", field: "card_number", reason: "length", detected_by: "client"}`
- 出典：PostHog best practices ／ Mixpanel data privacy ／ Sentry user feedback（いずれも確認）。プロパティ案は解釈。

### B-7. エラーのログをUX指標にする

- **何をするか**：エラーイベントから次のような指標を作る。
  - エラー発生率（その段階に来た人のうち、エラーを見た人の割合）
  - エラー後の離脱率（エラーを見た人のうち、その段階を完了しなかった人の割合）
  - 回復率（エラーを見たあと、同じ段階を完了した人の割合）
  - 回復までの時間・再試行の回数
  - 欄ごとのエラー件数（どの問いの設計が悪いかの手がかり）
- **確認できた範囲**：【確認】Mixpanel のファネルは "identify where your users drop off" のためのもので、間に特定のイベントを挟んだ人を除く「除外ステップ」や、プロパティを固定して段階を追う機能がある。エラーを見た人／見なかった人で比べる形にできる。【未確認】Google の HEART（Rodden, Hutchinson, Fu, CHI 2010）で「タスク成功（Task success）」の指標の例にエラー率が入っていること。検索抜粋では確認できたが、論文の原文は開けなかった。
- 【解釈】エラー発生率だけを追うと「エラーを出さない（検証を緩める）」ことで数字が良くなってしまう。回復率と最終的な完了率を必ず一緒に見る。エラーは、出ること自体が悪いのではなく、出たあとに回復できないことが悪い。
- 出典：https://docs.mixpanel.com/docs/reports/funnels/funnels-overview ／ funnels-advanced（GitHub 原文で確認）／HEART 論文【未確認】

### B-8. 不満の兆候（レイジクリック・デッドクリック）で「出ていないエラー」を拾う

- **何をするか**：同じ場所の連打（レイジクリック）や、押しても反応がないクリック（デッドクリック）を記録し、どの画面・どの要素で多いかを見る。
- **なぜ**：【確認】Mixpanel の定義では、レイジクリックは「同じ場所を短い間に何度もクリックすること。何か起きると期待したのに何も起きないので繰り返し押す、苛立ちの表れ」。既定値は「1秒以内に4回、30ピクセル以内」。デッドクリックは「対話要素をクリックしたが、一定時間内に目に見える反応がない」もので、既定値は0.5秒。どちらも設定で変えられる。【確認】Mixpanel は、セッションリプレイを探す手がかりに「dead clicks / rage clicks といった感情のシグナル」や「KPIの急な増減」を挙げている。
- 【解釈】これらは、元の note 記事の言う「UIに出ないエラー」（反応のないボタン、終わらない読み込み）を、エラーイベントが仕込まれていなくても後から見つける網になる。ただし既定値はあくまで目安で、ダブルクリックが正しい操作の画面では誤検知が出る。
- 出典：https://docs.mixpanel.com/docs/tracking-methods/autocapture ／ https://docs.mixpanel.com/docs/session-replay （GitHub 原文で確認）

### B-9. ファネルとリテンションを、必須通過点に合わせて組む

- **何をするか**：B-1 の必須通過点をそのままファネルの段階にし、成功体験のあとに戻ってくるかをリテンションで見る。
- **なぜ**：【確認】Mixpanel のファネルは、一連のイベントの間の転換を一定期間内で計算し、どこで離脱したか、どの層がよく転換するかを見るためのもの。リテンションは「どれだけの期間、利用者が戻ってきて価値を得続けているか」を見るためのもの（例：「登録後7日で、メッセージを送り続けている利用者の割合」）。
- 【解釈】リテンションの「戻ってきた」を、単なるログインではなく必須通過点（価値を得た行動）で定義すると、UX視点の指標になる。
- 出典：Mixpanel funnels overview ／ https://docs.mixpanel.com/docs/reports/retention （GitHub 原文で確認）

### B-10. HEART と Goals–Signals–Metrics で、UXの目標から指標を選ぶ【原典未確認】

- **何をするか**：Happiness（満足）、Engagement（関与）、Adoption（採用）、Retention（継続）、Task success（タスク成功）の5つの観点ごとに、目標（Goals）→ その兆し（Signals）→ 測り方（Metrics）の順で決める。
- **確認状況**：【未確認】原典は Rodden, Hutchinson, Fu "Measuring the User Experience on a Large Scale: User-Centered Metrics for Web Applications"（CHI 2010）。research.google / research.google.com / ACM はいずれも開けなかった。上の5観点と GSM の流れは、複数の検索抜粋で一致していたという程度の確認にとどまる。原典の定義や注意書き（全観点を使う必要があるか等）は書かない。
- 【解釈】GSM の「Goal → Signal → Metric」は、元の note 記事の「KPI設計＝宣言、ログ設計＝観測の実装」と同じ方向の逆算になっている。資料に載せる前に、原典PDFを人の手で開いて確かめてほしい。
- 出典：https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/ 【未確認】

### B-11. 定量から定性へ：ログで「誰に話を聞くか」を決める

- **何をするか**：ログで見つけた層（エラーのあと離脱した人、レイジクリックが多い人、回復した人）からインタビューやユーザビリティテストの対象を選ぶ。その前にセッションリプレイや、エラーに紐づいたフィードバックで当たりを付ける。
- **確認できた範囲**：【確認】Mixpanel は、リプレイを探す切り口として「注目すべき利用者（ヘビーユーザー、購入者）」「KPIの急な増減」「デッドクリック・レイジクリックが起きた回」を挙げている。【確認】Sentry は、エラーに対する利用者の申告をそのエラーのイベントと結び付ける（A-13）。
- 【解釈】元の note 記事の「ログ設計はリサーチの調査観点を決めるのと同じ」は、逆向きにも成り立つ。ログで「どこで」「何人が」は分かるが「なぜ」は分からない。だから「なぜ」を聞く相手をログで選ぶ。この募集には、連絡に使うことへの同意（B-12）が前提になる。
- 出典：Mixpanel session replay ／ Sentry user feedback（いずれも確認）

### B-12. プライバシー：集めるのは目的に要るものだけ、同意の前には送らない

- **何をするか**：KPIに要らないデータは取らない。メールアドレスなどではなく内部IDで人を識別する。自由記述の入力値は送らない。リプレイでは入力欄を隠す。分析用クッキーは同意を得てから使う。見られる人を役割で絞る。
- **なぜ**：【確認】Mixpanel のプライバシーガイドは4原則を挙げる。データ最小化（KPIと判断に役立たないなら集めない）、既定で仮名化（`user_id` などの内部IDを使う）、目的との整合（"Data collected without a specific purpose is almost always a liability."）、責任の共有。さらに、政府ID・カード情報・認証情報は「送るな」、メールアドレスや電話番号は識別子に使うな、未確認の自由記述は送るな、リプレイの入力欄は隠せ、本番と検証環境を分けよ、閲覧権限は最小にせよ、としている。【確認】GOV.UK のクッキーバナーは、利用者が受け入れていない限り、必須でないクッキー（HTML5 の local storage や service worker も含む）を設定しない、としている。
- 【未確認】日本の個人情報保護法、電気通信事業法の外部送信規律（2023年施行）が分析ツールにどう適用されるか。今回は一次資料を開いていない。法務の確認が要る論点として挙げるにとどめる。
- **悪い例→良い例**：エラー時に入力値ごと送る（`value: "taro@example.com"`）→ 欄名と理由だけ送る（`field: "email", reason: "format"`）
- 出典：Mixpanel data privacy（確認）／ https://design-system.service.gov.uk/components/cookie-banner/ （GitHub 原文で確認）

### B-13. データの質を守る：社内利用の除外、IDの統一、イベントの版管理、到着の遅れ

- **何をするか**：社内・テスト利用を除外する。端末をまたいでも同じ人が同じIDになるようにする。フローを作り直したらイベントに版を付ける。イベントの到着順に頼った分析をしない。
- **なぜ**：【確認】PostHog：利用者の少ないアプリは自分たちの利用で数字が膨らむので、社内利用を除外せよ。Web で `"user-456"`、モバイルで `"USER-456"` のように形式が違うと別人として扱われる。ログイン前後のIDを結び付けないと、ログイン前の行動が切れる。フローを作り直したら `registration_v2:...` のように版を分けて新旧を比べられるようにする。モバイルのイベントは数時間から数日遅れて届くことがあるので、時間の分析は記録時刻で行う。
- 【解釈】UXデザイナーにとって特に大事なのは版管理。デザインを変えた前後を比べるのがUX改善の基本だが、イベントの意味が黙って変わると、前後の比較が成り立たなくなる。
- 出典：PostHog best practices（確認）

### B-14. ダッシュボードとアラートは「誰が、いつ見て、何をするか」まで決める

- **何をするか**：指標ごとに、見る人・見る頻度・異常時の行動を決める。エラーの急増（システム側）はエンジニアに即時のアラートで、エラー後の離脱率や回復率（体験側）はUX/PdMが週次で、のように分ける。
- **確認できた範囲**：【確認】GOV.UK は 500 ページのパターンで "Log all errors and fix them as quickly as possible." としている。【確認】Mixpanel は、役割に応じて見えるデータを絞る（Data Views、最小権限、定期的な権限の見直し）よう勧め、例としてサポートには個人情報込みの「利用者の履歴」、戦略チームには匿名化した「傾向」を挙げている。
- 【解釈】ダッシュボードの設計方法そのものについては、今回開けた一次資料にまとまった指針はなかった。誰も見ない指標は取る意味が薄い。B-2 のトラッキングプランに「この指標を見る人」の列を足すのが手軽な方法。
- 出典：GOV.UK problem with the service pages ／ Mixpanel data privacy（いずれも確認）

---

## C. エンジニア・AI視点の担当に渡すとよい論点

1. **エラーの参照番号（A-13・B-6）を、UI・分析イベント・サーバーのエラーログ・サポート窓口で共通の鍵にできるか。** 誰が採番し、どこまで伝播させるか（エンジニア視点）。
2. **タイムアウトと部分的な失敗の定義（A-11）。** 何秒で失敗とみなすか、再試行は自動か手動か、冪等性をどう保つか。UXは「何を見せるか」までしか決められない（エンジニア視点）。
3. **バリデーションのタイミングの決定（A-4）と、クライアント／サーバー両方での検証。** GOV.UK は、クライアント側の検証は迂回されたり読み込みに失敗したりするので、サーバー側でも必ず検証せよとしている【確認】。2か所の文言をどう一致させるか（エンジニア視点）。
4. **AIが生成するエラーメッセージや、AI機能自体の失敗（応答なし・途中で止まる・もっともらしい誤り）。** これを A-1 の分類にどう足すか。人の入力ミスと違って「エラーだと検知できない失敗」がある点を、ログ（B-6）でどう拾うか（AI視点）。
5. **分析ログを AI に読ませる場合のプライバシーの線引き（B-12）。** 自由記述やリプレイを渡してよい範囲と、仮名化の方法（AI視点）。

---

## 付録：出典の確認状況一覧

### 原文を開いて確認できたもの
| 出典 | 確認方法 |
|---|---|
| note 記事 https://note.com/art_reflection/n/n2458fe47b286 | 直接開いた |
| GOV.UK Design System：Error message／Error summary／Recover from validation errors／Check answers／There is a problem with the service／Service unavailable／Cookie banner | GitHub `alphagov/govuk-design-system` の原文 |
| W3C WCAG 2.x 達成基準 3.3.1／3.3.3／3.3.4／3.3.7 Redundant Entry／Status Messages の本文、Understanding 3.3.1・3.3.3 の意図 | GitHub `w3c/wcag` の原文 |
| W3C 達成方法 ARIA21（aria-invalid）／ARIA19（role=alert・ライブリージョン） | GitHub `w3c/wcag` の原文 |
| MDN aria-invalid | GitHub `mdn/content` の原文 |
| IBM Carbon：Empty states／Loading／Forms | GitHub `carbon-design-system/carbon-website` の原文 |
| React `useOptimistic` | GitHub `reactjs/react.dev` の原文 |
| Mixpanel：Tracking Plan／Build Tracking Strategy／Data Privacy & PII／Autocapture（rage・dead click）／Session Replay／Heatmaps／Funnels／Retention | GitHub `mixpanel/docs` の原文 |
| PostHog：Product analytics best practices／naming tip | GitHub `PostHog/posthog.com` の原文 |
| Sentry：User Feedback（Crash-Report Modal, associatedEventId） | GitHub `getsentry/sentry-docs` の原文 |
| "reward early, punish late" の説明（filament discussions #12164） | github.com を直接開いた（二次情報） |

### 開けなかったもの（未確認。内容の根拠には使っていない）
- Nielsen Norman Group：10 Usability Heuristics、Error-Message Guidelines、Error messages scoring rubric（ネットワークで遮断。検索抜粋で見出しのみ）
- Google HEART 論文（Rodden, Hutchinson, Fu, CHI 2010。research.google / research.google.com / ACM すべて遮断）
- Smashing Magazine のインラインバリデーション記事（2022, Vitaly Friedman）
- Baymard Institute のインラインバリデーション記事（検索抜粋に数値があったが、出典を確かめられないため不使用）
- Luke Wroblewski "Inline Validation in Web Forms"（A List Apart）
- W3C WAI Forms Tutorial（Notifications）、web.dev のオフライン UX ガイド
- Amplitude 公式のトラッキングプランガイド（今回は開いていない。Mixpanel・PostHog で代替）
- 日本の個人情報保護法・電気通信事業法の外部送信規律に関する一次資料
