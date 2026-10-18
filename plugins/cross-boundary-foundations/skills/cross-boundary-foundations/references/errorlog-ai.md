# AI視点の「エラー設計」と「ログ設計」 リサーチノート

調査日：2026-10-07
担当：AI視点（エンジニア視点・UX視点は別担当）

## このノートの読み方

- **［事実］** は、出典を実際に開いて確認した内容。英語の原文は短く引用した。
- **［解釈］** は、調査担当の読み取りや整理。出典に書いてあることではない。
- 「未確認」と書いた資料は、ネットワーク制限で開けなかったもの。中身は推測で書いていない。
- 扱う意味は2つ。
  - **(A)** AIを組み込んだプロダクトのエラーとログ
  - **(B)** AIエージェントがログやエラーを読む・使う前提の設計（ログ設計の後半）

元の note 記事（「UXデザイナー/PdMがKPIとログとエラーを理解しないとデータドリブンにならない」）との対応は、各項目の［解釈］でところどころ触れた。記事本文は開いて確認済み。エラーは誰かが実装したもの、UIに出ないエラーもある、ログは目的から設計する（ログレベル・構造化）という主張を確認した。

---

## 前提：AI機能の「エラー」は2層ある

［事実］OpenTelemetry の Recording errors では、例外が投げられたか、エラーコードが返った場合に操作を「失敗」とみなす。そのうえで、何をエラーとみなすかは文脈で決まるとしている（HTTP 404 の例）。
［事実］Claude API は、安全分類器による拒否を HTTP 200 の通常応答として返し、`stop_reason: "refusal"` で示す。エラーとしては返さない。
［事実］Anthropic のハルシネーション低減ガイドは、対策をしても「完全には無くならない」とし、重要な情報は検証するよう求めている。

［解釈］AI機能の失敗は次の2層に分けて考えると整理しやすい。
1. **システム的な失敗**：タイムアウト、レート制限、過負荷、型崩れ（JSONが壊れる）、ツール呼び出しの失敗、途中停止（`max_tokens`）など。コードで検知でき、従来のエラー設計の延長で扱える。
2. **意味的な失敗**：答えが間違っている（ハルシネーション）、もっともらしいが誤り、意図と違う、過剰な拒否など。HTTPとしては成功（200）なので、従来の監視には出てこない。

元の note 記事の「UIに出ないエラーもある」はAIでさらに強まる。AI機能では「システムから見ても成功に見えるエラー」がいちばん多い、と言ってよい。意味的な失敗は、評価（eval）とユーザーフィードバックのログで初めて見えるようになる。そのため、エラー設計とログ設計を切り離さずに考える必要がある。

---

# 1. エラー設計（AI視点）

### E1. 応答の終わり方（stop_reason / finish_reason）を必ず分岐させる
- **何を**：モデルの応答を受け取ったら、まず「なぜ止まったか」を見て分岐する。正常終了、トークン上限で切れた、ツールを呼んだ、拒否した、コンテキスト超過、の5つを別々に扱う。
- **なぜ**：［事実］Claude API の stop reason には `end_turn` / `max_tokens` / `tool_use` / `pause_turn` / `refusal` / `model_context_window_exceeded` などがある。`max_tokens` は「上限に達した」、`model_context_window_exceeded` は「切れた応答として扱う」とされ、ガイドは「Always check stop_reason」を勧めている。OTel も `gen_ai.response.finish_reasons` を記録項目に入れている。
- **悪い例→良い例**：本文があれば成功として表示し、途中で切れた要約をそのまま出す → `max_tokens` なら「続きを生成」を出すか、自動で続きを取り、ログに `finish_reason=max_tokens` を残す。
- **出典**：https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md

### E2. 一時的な失敗（429・5xx・過負荷・タイムアウト）は自動で再試行し、再試行できない失敗と分ける
- **何を**：レート制限、サーバーエラー、過負荷は指数バックオフで再試行し、`retry-after` があれば従う。上限到達のように待っても直らない失敗は、別の扱いにする。
- **なぜ**：［事実］Claude API のエラー一覧には、429 `rate_limit_error`、500 `api_error`（指数バックオフで再試行）、504 `timeout_error`、529 `overloaded_error` がある。SDK は一時的な失敗をデフォルトで2回再試行する。一方、利用枠の上限による 429 には `retry-after` が付かず、アクセスが戻るまで失敗し続ける。また、長いリクエストはストリーミングかバッチを使うよう勧めている。
- **悪い例→良い例**：429 でも「エラーが発生しました」とだけ出して終わる → 一時的な失敗は裏で再試行し、待ちが長いときは「混み合っています。数十秒後に自動で再開します」と見通しを示す。上限到達の場合は管理者向けの案内を出す。
- **出典**：https://platform.claude.com/docs/en/api/errors

### E3. ストリーミングの「200のあとに起きる失敗」と途中停止を設計する
- **何を**：表示し始めたあとで止まった、拒否された、エラーになった、という状態を前提に、UIとログを用意する。
- **なぜ**：［事実］Claude API の資料では、SSEストリーミングでは 200 を返したあとにエラーが起こることがあり、通常のエラー処理の仕組みに乗らないとされている。OTel は、失敗した操作でも「部分的にストリームされた出力」があれば出力を記録してよいとし、失敗した操作の出力を「合成してはいけない（SHOULD NOT synthesize）」としている。
- **悪い例→良い例**：途中で止まった文章が完成品のように残る → 途中で止まった箇所に「ここで中断しました（再生成／続きから）」を示し、ログには部分出力と中断理由を残す。
- **出典**：https://platform.claude.com/docs/en/api/errors ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md

### E4. 拒否（refusal）を「エラー」ではなく「設計された状態」として扱う
- **何を**：拒否は、エラー画面ではなく専用の状態として扱う。代わりにできることを示し、必要なら別モデルにフォールバックする。過剰な拒否は品質問題として計測する。
- **なぜ**：［事実］Claude の拒否は通常応答として返り、`stop_details.category` で方針の区分が分かる。別モデルで再試行すれば答えが得られることが多く、`fallbacks` の設定も用意されている（beta）。OpenAI Cookbook は、ガードレールを厳しくしすぎると無害な依頼まで拒否する「over-refusals」が起き、体験を損なうと指摘している。
- **悪い例→良い例**：拒否されると汎用エラーを出す、または黙って空欄にする → 「この内容はお手伝いできません。〇〇ならできます」と代わりの道を示す。拒否率を区分ごとに監視する。
- **出典**：https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback ／ https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_use_guardrails.ipynb

### E5. 型崩れは「仕組みで防ぐ」→「検証する」→「直せなければ穏やかに失敗する」の3段で扱う
- **何を**：構造化出力（JSONスキーマ）や strict なツール定義で、壊れた出力をそもそも出させない。それでも残る崩れは、決まった処理を行うコードで検証する。検証に落ちたら再試行し、だめなら定型の失敗表示にする。
- **なぜ**：［事実］OpenAI Cookbook は、構造化出力は壊れて返り得るので、構文チェックのガードレールで検知し「retry or fail gracefully」するとしている。OWASP LLM01 は、期待する出力形式を定め、決まった処理を行うコードで準拠を検証するよう勧めている。Anthropic は `strict: true` でツール入力がスキーマに必ず合うとしている。
- **悪い例→良い例**：パースに失敗したまま画面が真っ白になる → スキーマを強制し、検証に失敗したら1回だけ再試行する。それでもだめなら「うまく作れませんでした。もう一度試す／手入力する」を出し、`error.type=schema_validation_failed` を記録する。
- **出典**：https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_use_guardrails.ipynb ／ https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM01_PromptInjection.md ／ https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls

### E6. ツール呼び出しの失敗は、隠さずモデルに返す（is_error と「直し方つき」のメッセージ）
- **何を**：ツールが失敗したら、例外で全体を止めない。何が起き、次に何を試すべきかをエラーとしてモデルに返し、自力で回復させる。
- **なぜ**：［事実］Anthropic のツール処理ガイドは、`tool_result` に `is_error: true` とエラー内容を入れて返すよう示している。さらに、`"failed"` のような汎用エラーではなく「Rate limit exceeded. Retry after 60 seconds.」のように、何が起き何を試すべきかを書くよう勧めている。パラメータが足りないエラーを返すと、Claudeは2〜3回補って再試行し、それでもだめなら謝る、とも書かれている。
- **悪い例→良い例**：`{"content": "Error 500"}` → `{"content": "天気APIが応答しません（HTTP 500）。60秒後に再試行するか、ユーザーに後で確認するよう伝えてください", "is_error": true}`
- **出典**：https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls ／ https://www.anthropic.com/engineering/writing-tools-for-agents

### E7. エージェントの暴走・無限ループには「止める条件」と「上限」を最初から入れる
- **何を**：反復回数の上限、時間とコストの上限、同じ行動の繰り返しの検知、資源消費の上限を設ける。上限に達したら中断し、そこまでの経過を人に見せる。
- **なぜ**：［事実］Anthropic「Building effective agents」は、制御を保つために停止条件（最大反復回数など）を設けるのが一般的だとし、エージェントは自律的なのでコストが高く、誤りが積み重なりやすいと述べている。OWASP LLM10（Unbounded Consumption）は、タイムアウトとスロットリング、利用者ごとの上限、資源消費の監視を挙げている。Claude API にはサーバーツールの反復上限で止まる `pause_turn` がある。
- **悪い例→良い例**：同じ検索を何十回も繰り返して費用が膨らむ → 最大N回、または予算に達したら停止し、「ここまで調べました。続けますか？」と人に判断を返す。
- **出典**：https://www.anthropic.com/engineering/building-effective-agents ／ https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM10_UnboundedConsumption.md ／ https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons

### E8. 影響の大きい操作は「人の承認」を挟み、権限を最小にする（過剰な代理権限を失敗として扱う）
- **何を**：送信・削除・購入など取り消しにくい操作の前に、人の承認を必須にする。ツールの機能と権限は必要最小限にする。「その操作をしてよいか」の判断は、LLMではなく下流のシステムで行う。
- **なぜ**：［事実］OWASP LLM06（Excessive Agency）は、拡張機能を最小限にする、何でもできる拡張を避ける、利用者の権限の範囲で実行する、影響の大きい操作は人の承認を必須にする、を挙げている。そして「LLMに許可判断を任せず下流で認可する（complete mediation）」としている。LLM01 も、リスクの高い操作には人が承認する仕組みを求めている。
- **悪い例→良い例**：メール要約エージェントに送信・削除の権限まで渡す → 読み取り権限だけにし、送信は下書きを作るところで止めて人が送る。
- **出典**：https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM06_ExcessiveAgency.md ／ https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM01_PromptInjection.md

### E9. プロンプトインジェクションは「防ぎきれない前提」で、外から来た内容を区別し、検知したら止めて知らせる
- **何を**：Webページ・メール・ファイルなど外部から来た内容は信頼できないデータとして区別する。ツールの出力を軽量なモデルで検査し、乗っ取りの疑いがあれば生の内容を渡さず、ユーザーに知らせる。
- **なぜ**：［事実］OWASP LLM01 は、生成AIの性質上、確実な予防策があるかは不明だとし、影響を減らす策を並べている（外部の内容を分けて明示する、敵対的テストなど）。Anthropic は、信頼できない内容は `tool_result` の中だけに置く、JSONで包む、ツールの出力を Claude Haiku 4.5 で検査する、と勧めている。疑いがあれば「エラーか除去した要約を返し、ユーザーに知らせることを検討する」としている。
- **悪い例→良い例**：取得したWebページの本文をシステムプロンプトにそのまま連結する → JSONに包んで `tool_result` に入れる。検査で引っかかったら「このページには指示文が含まれていたため、内容を使いませんでした」と表示し、ログに残す。
- **出典**：https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM01_PromptInjection.md ／ https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks

### E10. ハルシネーションは「言わせない」より先に「分からないと言える」「根拠を示せる」設計にする
- **何を**：分からないときに分からないと言える逃げ道をプロンプトとUIの両方に用意する。主張ごとに根拠（引用・出典）を示させ、根拠が見つからない主張は取り下げる。
- **なぜ**：［事実］Anthropic のガイドは、「分からない」と言う許可を明示する、長い文書では先に逐語引用を抜き出す、主張ごとに引用で裏付けを取り、見つからなければ撤回させる、同じ問いを複数回走らせて食い違いを見る（Best-of-N）、を挙げている。OWASP LLM09（Misinformation）は、RAG、人による確認、自動検証、AI生成であることの明示、信頼性の限界の明示を挙げている。
- **悪い例→良い例**：根拠のない数字をもっともらしく断言する → 数字には出典リンクを付け、裏付けがない箇所は「確認できませんでした」と明示する。
- **出典**：https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations ／ https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM09_Misinformation.md

### E11. 疑わしいときは「範囲を絞る」：聞き返すか、機能を穏やかに縮める
- **何を**：ユーザーの意図や答えに自信がないときは、全力で答えを作らない。選択肢を出して聞き返すか、できる範囲だけ返す（要約だけ、候補だけなど）。
- **なぜ**：［事実］Microsoft の HAX ガイドライン G10「Scope services when in doubt」は、ユーザーの目的が不確かなときは曖昧さの解消に取り組むか、AIの提供範囲を穏やかに縮めるよう求めている。G2 は、システムがどのくらいうまくできるかを明確にするよう求めている。OWASP LLM10 も、負荷が高いときは全部止めずに部分的な機能を保つ「Graceful Degradation」を挙げている。
- **悪い例→良い例**：曖昧な「来週の予定を調整して」に、勝手に全部を組み替えた案を出す → 「どの会議ですか？ A／B／C」と聞き返すか、空き時間の候補だけ示す。
- **出典**：https://www.microsoft.com/en-us/haxtoolkit/library/ ／ https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM10_UnboundedConsumption.md

### E12. 間違ったときに「すぐ直せる・断れる・理由が分かる」を用意する（訂正・却下・説明）
- **何を**：AIの出力をその場で編集・取り消し・再生成できるようにする。不要な提案は1操作で閉じられるようにする。「なぜこう出したか」を確かめる入口を用意する。
- **なぜ**：［事実］HAX ガイドライン G8「Support efficient dismissal」（不要なAI機能を閉じる・無視するのを簡単に）、G9「Support efficient correction」（AIが間違ったときの編集・調整・回復を簡単に）、G11「Make clear why the system did what it did」（なぜそう振る舞ったかの説明にアクセスできるように）。Amershi ほか, CHI 2019。Anthropic のエージェント記事も、エージェントの計画の段階を明示的に見せる透明性を優先するよう勧めている。
- **悪い例→良い例**：AIが自動で書き換えた文章に「元に戻す」がない → 差分表示と「元に戻す」「一部だけ採用」を出し、根拠の出典をたどれるようにする。
- **出典**：https://www.microsoft.com/en-us/haxtoolkit/library/ ／ https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/ ／ https://www.anthropic.com/engineering/building-effective-agents

### E13. フォールバックを段にする（別モデル → 小さいモデル・ルール → 定型文 → 人）
- **何を**：主モデルが使えない・拒否した・検証に落ちたときの代わりを、順に用意する。
- **なぜ**：［事実］Claude API は拒否時に別モデルでの再試行を勧めている。OpenAI Cookbook は、話題外の質問に定型メッセージ（canned message）で返す例を示し、LLMのガードレールをルールや従来型の機械学習モデルと組み合わせるとリスクを減らせるとしている。また、入力ガードレールを本体の呼び出しと並行して走らせ、遅延を抑える設計を紹介している。
- **［解釈］**：PAIR Guidebook の「人へ渡す」（エスカレーション）の扱いは、原典を開けなかったため確認できていない（下の「未確認」参照）。人へ渡す根拠としては、OWASP LLM06・LLM09 の人による承認・確認と、Anthropic の「チェックポイントや詰まったときに人のフィードバックを待つ」がある。
- **悪い例→良い例**：主モデルが落ちると機能ごと使えない → 「別モデル → ルールベースの回答 → 定型文と問い合わせ導線」の順に落とし、どの段で返したかをログに残す。
- **出典**：https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback ／ https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_use_guardrails.ipynb ／ https://www.anthropic.com/engineering/building-effective-agents

### E14. ガードレールのしきい値は「見逃し」と「過検知」の費用で決め、評価データで調整する
- **何を**：ガードレールの判定しきい値を勘で決めない。評価セットと混同行列で、見逃し（false negative）と過検知（false positive）の割合を測ってから決める。
- **なぜ**：［事実］OpenAI Cookbook は、しきい値の設定は最適化の主な対象であり、評価セットを作って混同行列で採点するよう勧めている。過検知が多いと体験が途切れ、見逃しが多いと事業に長く残る害が出る。リスクの大きい分類（ジェイルブレイクなど）はしきい値を低くする、としている。
- **悪い例→良い例**：全カテゴリに同じしきい値を使う → 害の大きいカテゴリは厳しく、軽いカテゴリは緩くする。過検知率もKPIとして見る。
- **出典**：https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_use_guardrails.ipynb

---

# 2. ログ設計（AI視点）

## (A) AIを組み込んだプロダクトのログ

### L1. LLM呼び出しは標準の語彙（OpenTelemetry GenAI semantic conventions）でトレースする
- **何を**：1回のモデル呼び出しを1つのスパンとして記録し、標準の属性名を使う。
- **なぜ**：［事実］OTel の GenAI セマンティック規約は、推論・埋め込み・検索・ツール実行・エージェント呼び出しなどをスパン・イベント・メトリクスとして定義している。主な属性は `gen_ai.operation.name`、`gen_ai.provider.name`、`gen_ai.request.model`、`gen_ai.response.model`、`gen_ai.usage.input_tokens`、`gen_ai.usage.output_tokens`、`gen_ai.response.finish_reasons`、`gen_ai.request.temperature`、`gen_ai.conversation.id`。**注意**：規約全体の状態はまだ「Development」で、安定版ではない。また、規約は `open-telemetry/semantic-conventions` から専用リポジトリ `semantic-conventions-genai` に移っている（旧ページに「Moved」と書かれていることを確認）。
- **悪い例→良い例**：`log.info("called gpt")` → `gen_ai.operation.name=chat, gen_ai.request.model=..., gen_ai.response.model=..., input_tokens=..., output_tokens=..., finish_reasons=["stop"]` をスパンに残す。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/README.md ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md

### L2. 「頼んだモデル」と「実際に答えたモデル」、プロンプトのバージョンを分けて残す（再現性）
- **何を**：要求したモデル名と応答したモデル名を別々に残す。あわせて、プロンプトテンプレートのバージョン、テンプレートに入れた変数、サンプリング設定を残す。
- **なぜ**：［事実］OTel は `gen_ai.request.model` と `gen_ai.response.model`（例：`gpt-4` と `gpt-4-0613`）を別の属性として定義している。プロンプトテンプレートに入れた変数を記録する `gen_ai.prompt.variable`（Opt-In）もある。
- **［解釈］**：プロンプトのバージョンIDを直接表す標準属性は、今回読んだ範囲では見つからなかった。アプリ独自の属性（例：`app.prompt.version`）で補うのが現実的だと考える。同じ入力でも出力は揺れるため、「何を変えたら品質が変わったか」を後から追えるのは、モデル・プロンプト・設定のバージョンが残っている場合に限られる。
- **悪い例→良い例**：「昨日から回答が変だ」と言われても、何が変わったのか分からない → プロンプトv12→v13、モデルの更新、temperature の変更が時系列で引ける。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md

### L3. トークン・レイテンシ・コストを、成功と失敗を1つの指標で記録する
- **何を**：所要時間のヒストグラムに `error.type` を付け、成功と失敗を同じ指標で記録する。トークン数（入力・出力・キャッシュ・推論）も残す。
- **なぜ**：［事実］OTel の Recording errors は、成功と失敗を別々の指標にせず、1つの指標に `error.type` を付ける形を推奨している。成功した操作には `error.type` を付けない。再試行や処理で回復できたエラーは、その操作の失敗として記録しない。GenAI 規約には、`gen_ai.client.operation.duration`、ストリーミングの `time_to_first_token`、エージェントの `invoke_agent.tool_calls` などの指標がある。トークン数は、キャッシュ読み出しや推論用の内訳まで定義されている。
- **悪い例→良い例**：成功数と失敗数を別々のカウンタで持ち、比率が合わない → 1つの所要時間ヒストグラムに `error.type`（`timeout`・`rate_limit` など種類の少ない値）を付け、そこからエラー率を出す。
- **出典**：https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/recording-errors.md ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md

### L4. エラーの種類は「種類の少ない決まった値」で残す（自由文にしない）
- **何を**：`error.type` には、プロバイダのエラーコードや例外のクラス名など、種類が少なく決まった値を入れる。詳しいメッセージは別の欄に分ける。
- **なぜ**：［事実］OTel は、`error.type` はプロバイダやクライアントライブラリが返すエラーコード、例外の正式名、その他の種類の少ない識別子に合わせるべきだとし、報告するエラーの一覧を文書化するよう求めている。GenAI 用の例外イベント `gen_ai.client.operation.exception` は、API エラー、レート制限、モデルのエラー、タイムアウトを対象にし、重要度を WARN にするよう推奨している。`exception.message` には機密情報が入りうると注記されている。
- **悪い例→良い例**：`error="Something went wrong with the AI: <ユーザー入力全文>"` → `error.type="rate_limit_error"`。メッセージは別の欄に、機密を除いて入れる。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-exceptions.md

### L5. プロンプトと応答の本文は「デフォルトでは残さない」。残すなら別の保管先とアクセス権で
- **何を**：入力メッセージ、システム指示、出力、ツールの引数と結果は、明示的に有効にしたときだけ記録する。本番では、本文を外部の保管先に置き、ログには参照だけを残す。
- **なぜ**：［事実］OTel は、モデルへの指示・ユーザーのメッセージ・出力を「sensitive」で大きいデータとして扱い、計装は「SHOULD NOT capture them by default」としつつ、有効にできる手段を用意すべきとしている。推奨の段階は3つ。(1) デフォルトでは記録しない、(2) スパンの属性に記録する（量が扱え、規制に対応できる保管先、例えば本番前の環境向け）、(3) 外部に保存して参照を記録する（本番向け。アクセス制御を分けられる）。`gen_ai.input.messages` などには「user/PII data を含みやすい」と警告がある。
- **悪い例→良い例**：本番のアプリログにプロンプト全文を流し、開発者なら誰でも検索できる → 本文は権限を分けた保管先に置き、ログには `content_ref` と、マスキング済みかどうかの印だけを残す。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md

### L6. 保持期間と「学習に使うか」の同意を、ログの設計時に決める
- **何を**：ログに残るユーザーデータについて、保持期間、削除の手順、学習や改善に使うかどうかとその拒否手段を決め、利用者に示す。
- **なぜ**：［事実］OWASP LLM02（Sensitive Information Disclosure）は、データの保持・利用・削除の方針を明確にし、利用者が自分のデータを学習から外せるようにすること、学習の前にマスキングすること、最小権限でのアクセス制御を挙げている。
- **［解釈］**：元の note 記事の「ログはプライバシーも含めて目的から設計する」は、AI機能では「ログが将来の学習データや評価データになる」ところまで広がる。記録した時点で、その後の使い道まで決めておく必要がある。
- **悪い例→良い例**：「品質改善のため」と曖昧に全会話を無期限に保存する → 「評価用に30日、匿名化したうえで、設定でオプトアウト可能」のように目的・期間・選択肢を明示する。
- **出典**：https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM02_SensitiveInformationDisclosure.md

### L7. ユーザーの反応（採用・却下・修正・再生成・コピー）を、その応答IDに結び付けて残す
- **何を**：AIの出力に対してユーザーが取った行動を、どの応答への反応かが分かる形でイベントとして残す。
- **なぜ**：［事実］HAX ガイドライン G15「Encourage granular feedback」は、普段の操作の中でユーザーが好みを伝えられるようにすることを求めている。G13「Learn from user behavior」もある。OTel は評価結果のイベント `gen_ai.evaluation.result` を定義し、評価対象の操作スパンにつなぐか、`gen_ai.response.id` で結び付けるよう求めている。
- **［解釈］**：👍👎のような明示的なフィードバックは数が少ない。そのため、採用・コピー・編集・再生成・却下といった普段の操作を「暗黙のラベル」として扱うのが現実的だと考える。ただし、コピー＝正解とは限らない（間違いを報告するためにコピーすることもある）。暗黙のラベルは、明示的なフィードバックや人の評価と突き合わせて意味を確かめる必要がある。この点を直接述べた一次資料は今回確認できていない。
- **悪い例→良い例**：「再生成ボタンのクリック数」だけを全体で数える → `ai.suggestion.regenerated {response_id, prompt_version, n_th}` のように応答に結び付け、「どのプロンプトのどの応答が作り直されたか」を引けるようにする。
- **出典**：https://www.microsoft.com/en-us/haxtoolkit/library/ ／ https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md

### L8. 評価は「オフライン（リリース前）」と「オンライン（本番監視）」の両方を回し、本番の失敗をテストケースに戻す
- **何を**：リリース前に評価セットで自動採点する。本番ではログから品質を監視する。ユーザーから報告された失敗は評価セットに追加する。
- **なぜ**：［事実］Anthropic「Demystifying evals for AI agents」（2026-01-09）は、自動評価はユーザーに影響を与えずに速く改善を回せるが手入れが要る、本番監視は実際の振る舞いを見せるが問題がユーザーに届いた後で反応することになる、だから両者は補い合う、としている。また、「ユーザーから報告された失敗をテストケースにすると、評価が実際の使われ方を反映する」としている。Claude の評価ガイドは、評価を実際の課題に合わせる（境界ケースも含める）、できるだけ自動化する、量を優先する、を原則に挙げている。
- **悪い例→良い例**：プロンプトを変えるたびに数件を目で見て「良さそう」でリリースする → 評価セットを自動で走らせて前の版と比べ、本番の失敗ログから毎週ケースを追加する。
- **出典**：https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents ／ https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

### L9. LLM-as-a-judge は人の評価との一致を確かめてから使い、トランスクリプトを人が読む
- **何を**：LLMに採点させる前に、人の専門家の採点と照らし合わせてずれを確認する。採点の結果だけでなく、採点されたやりとりの記録そのもの（トランスクリプト）も定期的に人が読む。
- **なぜ**：［事実］Anthropic は、LLM-as-judge の採点者を人の専門家と密に照らし合わせ、両者のずれが小さいことを確かめるよう述べている。また、「多数の試行のトランスクリプトと採点を読まなければ、採点が機能しているか分からない」とも述べている。採点方法はコードによる採点・モデルによる採点・人による採点の3つを挙げ、それぞれ長所と短所がある。Claude の評価ガイドは、詳しい採点基準（ルーブリック）を使うこと、生成したモデルとは別のモデルで評価するのが一般的に良いこと、を挙げている。OpenAI Cookbook は、LLMをガードレールに使う場合、本体と同じ弱点（プロンプトインジェクションなど）を持つと注意している。
- **［未確認］**：LLM採点の具体的な偏り（回答の位置、長さ、自分の回答をひいきする傾向）を示した Zheng ほか（2023, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"）は、arXiv とNeurIPSのページを開けなかったため、中身は確認していない。GitHub の FastChat `llm_judge` README が論文にリンクしていることだけ確認した。
- **悪い例→良い例**：LLM採点の平均点が上がったので改善したと判断する → 50件ほどで人とLLMの採点の一致率を測り、ずれた事例のトランスクリプトを読んでから採点を信用する。
- **出典**：https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents ／ https://platform.claude.com/docs/en/test-and-evaluate/develop-tests ／ https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_use_guardrails.ipynb

### L10. 評価結果もログの一部として、元の応答に結び付けて残す
- **何を**：自動評価やガードレールの判定結果を、どの応答に対するものか、どの評価項目で何点か、どのラベルか、理由は何かが分かる形で記録する。
- **なぜ**：［事実］OTel の `gen_ai.evaluation.result` イベントは、`gen_ai.evaluation.name`（例：Relevance）、`gen_ai.evaluation.score.value`、`gen_ai.evaluation.score.label`（例：correct / incorrect、pass / fail。種類は少なくする）、`gen_ai.evaluation.explanation` を持ち、評価対象の操作スパンを親にするよう求めている。
- **［解釈］**：これで「意味的な失敗」をシステム的なエラーと同じ画面で数えられるようになる。前提で書いた2層のエラーを、1つのダッシュボードに並べられる。
- **悪い例→良い例**：ガードレールが止めた件数だけがあり、何を止めたか分からない → `evaluation.name=topical_guardrail, label=blocked, explanation=...` が該当の応答から引ける。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md

### L11. エージェントは「判断の連鎖」をトレースとして残す（計画・ツール呼び出し・結果・人の介入）
- **何を**：エージェントの呼び出しを親スパンにし、その下に計画、モデル呼び出し、ツール実行を子スパンとしてつなぐ。ツール名、呼び出しID、（有効にした場合は）引数と結果、人が承認・却下した記録を残す。
- **なぜ**：［事実］OTel には、`invoke_agent`、`plan`、`execute_tool`、`invoke_workflow` などの操作名がある。属性には `gen_ai.agent.name` / `id` / `version`、`gen_ai.tool.name`、`gen_ai.tool.call.id`、`gen_ai.tool.call.arguments` と `gen_ai.tool.call.result`（どちらも Opt-In）がある。Anthropic の評価記事は、トランスクリプト（トレース）を「出力、ツール呼び出し、推論、途中の結果、その他のやりとりを含む試行の完全な記録」と定義している。OWASP LLM06 は、拡張機能と下流システムの動きを記録・監視するよう求めている。
- **悪い例→良い例**：最終回答だけが残り、どのツールの結果を根拠に誤ったか追えない → 1つのトレースで「計画 → 検索 ×3 → 要約 → 人が承認」がたどれる。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md ／ https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents ／ https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM06_ExcessiveAgency.md

### L12. 会話IDは「本物のIDがあるときだけ」付ける。プロバイダのリクエストIDも残す
- **何を**：会話・セッションの単位でまとめるためのIDを付ける。ただし、無いIDを作り出さない。問い合わせ用に、プロバイダが返すリクエストIDも残す。
- **なぜ**：［事実］OTel は `gen_ai.conversation.id` について、識別子が無いときは設定しないようにし、新しいUUID、トレースID、リクエスト内容のハッシュを代わりに使ってはいけない（SHOULD NOT）としている。会話履歴をアプリが管理する場合は、アプリ側で付けてよい。Claude API はすべての応答に `request-id` ヘッダを付け、エラー本文にも `request_id` を含める。サポートへの問い合わせにはこのIDを添えるよう求めている。
- **悪い例→良い例**：毎回ランダムなIDを会話IDとして付け、同じ会話が集計でバラバラになる → アプリが持つスレッドIDを `gen_ai.conversation.id` にし、`provider.request_id` も併せて記録する。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md ／ https://platform.claude.com/docs/en/api/errors

## (B) AIがログやエラーを読む・使う時代の設計

### L13. エラーメッセージを「人にもAIにも直せる形」にする（何が起き、次に何をすべきか）
- **何を**：エラー文に「何が起きたか」「原因の手がかり」「次に取るべき行動」を入れる。不透明なコードやスタックトレースだけで終わらせない。
- **なぜ**：［事実］Anthropic「Writing effective tools for AI agents」（2025-09-11）は、エラー応答をプロンプトと同じように設計し、不透明なエラーコードやトレースバックではなく、具体的で実行できる改善点を伝えるよう述べている。ツール処理のガイドも「failed」より「Rate limit exceeded. Retry after 60 seconds.」を勧め、それによって Claude が推測せずに回復できるとしている。
- **［解釈］**：これは、元の note 記事の「エラーは誰かが実装したもの」の延長にある。エラー文の読み手に「エージェント」が加わった、と言える。人向けのUI文言と、機械向けの欄（`error.type`・`retry_after`・`hint`）を分けて両方持たせるのが扱いやすいと考える。
- **悪い例→良い例**：`ERR_42` → `{"error.type":"invalid_date_range","message":"end_date が start_date より前です","hint":"start_date <= end_date になるよう指定してください","retry_after":null}`
- **出典**：https://www.anthropic.com/engineering/writing-tools-for-agents ／ https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls

### L14. ログは機械可読で、一貫したスキーマと意味の分かる名前で書く（エージェントがそのまま読める）
- **何を**：自由文のログではなく、構造化されたイベントにする。イベント名と属性名は、プロジェクト内でも標準規約とも揃える。暗号のようなIDだけでなく、人が読める名前も併記する。
- **なぜ**：［事実］Anthropic は、エージェントは暗号的な識別子より自然言語の名前・用語・識別子のほうがはるかにうまく扱えると述べている。また、文脈を節約するために、ページ分割・範囲選択・絞り込み・切り詰めを、適切なデフォルト値と組み合わせて用意するよう勧めている。OTel のエラー記録・GenAI規約は、`error.type` を種類の少ない決まった値に保ち、スパンと指標で揃えるよう求めている。
- **［解釈］**：AIエージェントにログを渡して調べさせる場合、効いてくるのは「grepしやすさ」より「スキーマの一貫性」と「1件の自己完結性」だと考える。どの機能の、どの版の、どのユーザー行動に紐づくイベントかが、そのイベント1行で分かることが大事になる。元の note 記事の「構造化」の主張は、AIが読み手になることでさらに重要になる。このことを直接示す実証研究は今回見つけられていない。
- **悪い例→良い例**：`"user 8f3a... failed at step 3"` → `{"event":"checkout.payment.failed","feature":"ai_summary","prompt_version":"v13","error.type":"timeout","trace_id":"...","user_segment":"trial"}`
- **出典**：https://www.anthropic.com/engineering/writing-tools-for-agents ／ https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/recording-errors.md

### L15. トレースID・リクエストIDで「前後のログ」を一発でたどれるようにする
- **何を**：UIの操作、バックエンド、LLM呼び出し、ツール実行、評価、ユーザーの反応を、同じトレースIDか結び付けIDでつなぐ。
- **なぜ**：［事実］OTel は、評価イベントを評価対象のスパンに親子付けするか、`gen_ai.response.id` で結び付けるよう求めている（L10）。会話IDの扱い（L12）や、Claude API の `request-id`（L12）もこの結び付けに使える。
- **［解釈］**：元の note 記事にある「エラーだけでは原因が分からず、前後のログを見て根本原因を特定する」作業は、AIエージェントに任せられるようになりつつある。そのとき、相関IDが通っていれば、エージェントは「この不満フィードバックの元になった応答、そのときのプロンプトの版、使ったツールの結果」をたどれる。通っていなければ、エージェントも人と同じく推測するしかない。
- **悪い例→良い例**：フロントのエラーログとLLMのログが別のシステムにあり、時刻で突き合わせるしかない → 👎フィードバックのイベントから `trace_id` で、該当するLLM呼び出し・ツール結果・評価まで一度でたどれる。
- **出典**：https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md ／ https://platform.claude.com/docs/en/api/errors

### L16. AIに読ませるログ自体を「信頼できない入力」として扱う
- **何を**：エージェントにログ・チケット・ユーザー入力を読ませて調査させるときは、それらをデータとして渡し、命令として扱わせない。エージェントの権限は読み取り中心に絞る。
- **なぜ**：［事実］Anthropic は、第三者の内容（メール、Webページ、文書、ツールの結果）に悪意ある指示が含まれる「間接プロンプトインジェクション」を独立した脅威として挙げ、信頼できない内容をデータとして扱うよう方針を明示すること、最小権限にすることを勧めている。
- **［解釈］**：ログにはユーザーが入力した文字列がそのまま入る。だから「ログを読むAI」は、間接プロンプトインジェクションの入口になりうる。ログ設計の段階で、ユーザー入力の欄を明確に区切る（JSONの値として入れる）ことは、AIに読ませる時代の安全対策にもなる。ログ解析エージェントへのインジェクションを直接扱った一次資料は、今回は確認していない。
- **悪い例→良い例**：自由文のログに「以前の指示を無視して…」というユーザー入力が混ざったまま、権限の広いエージェントに読ませる → ユーザー入力を `user_input` の値として分けて保存し、調査用エージェントには読み取り権限だけを与える。
- **出典**：https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks

---

## 出典一覧

### 確認できた（実際に開いた）
| 資料 | URL | 備考 |
|---|---|---|
| Microsoft HAX Toolkit Design Library（G1〜G18） | https://www.microsoft.com/en-us/haxtoolkit/library/ | G8〜G16の説明文を確認 |
| Amershi et al. "Guidelines for Human-AI Interaction" CHI 2019（MSR掲載ページ） | https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/ | 著者・掲載先・要旨のみ。PDF本文は未読 |
| OTel GenAI semconv（新リポジトリ）README / spans / client-inference / events / exceptions / agent-spans / metrics | https://github.com/open-telemetry/semantic-conventions-genai （raw.githubusercontent.com 経由で取得） | 状態は Development |
| OTel 旧GenAIページ（Moved の告知） | https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai | |
| OTel Recording errors | https://github.com/open-telemetry/semantic-conventions/blob/main/docs/general/recording-errors.md | |
| OWASP Top 10 for LLM Applications 2025：LLM01, 02, 06, 09, 10（GitHub原稿） | https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/tree/main/2_0_vulns | LLM05 は取得したが本ノートでは不使用 |
| Claude API errors | https://platform.claude.com/docs/en/api/errors | |
| Claude stop reasons | https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons | |
| Claude refusals and fallback | https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback | 冒頭部分のみ確認 |
| Claude handle tool calls（is_error） | https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls | |
| Claude reduce hallucinations | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations | |
| Claude mitigate jailbreaks and prompt injections | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks | |
| Claude develop tests（評価設計） | https://platform.claude.com/docs/en/test-and-evaluate/develop-tests | |
| Anthropic "Building effective agents" | https://www.anthropic.com/engineering/building-effective-agents | |
| Anthropic "Writing effective tools for AI agents" (2025-09-11) | https://www.anthropic.com/engineering/writing-tools-for-agents | |
| Anthropic "Demystifying evals for AI agents" (2026-01-09) | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | |
| OpenAI Cookbook "How to use guardrails"（GitHub原稿） | https://github.com/openai/openai-cookbook/blob/main/examples/How_to_use_guardrails.ipynb | cookbook.openai.com は開けず、GitHub原稿で確認 |
| FastChat llm_judge README | https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge | 論文へのリンクの確認のみ |
| note 記事 | https://note.com/art_reflection/n/n2458fe47b286 | 要点を確認 |

### 未確認（開けなかった。中身は書いていない）
| 資料 | URL | 状況 |
|---|---|---|
| Google PAIR Guidebook "Errors + Graceful Failure" | https://pair.withgoogle.com/chapter/errors-failing/ | ネットワークで遮断。Google Codelabs の日本語版も遮断。**本ノートでは PAIR の主張を根拠に使っていない** |
| OpenTelemetry 公式サイト（opentelemetry.io の GenAI ページ） | https://opentelemetry.io/docs/specs/semconv/gen-ai/ | 遮断。GitHub の原稿で代わりに確認 |
| OWASP GenAI 公式サイト | https://genai.owasp.org/llm-top-10/ | 遮断。GitHub の原稿で代わりに確認 |
| NIST AI RMF / NIST AI 600-1（Generative AI Profile） | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf ／ https://www.nist.gov/itl/ai-risk-management-framework | 遮断 |
| OpenAI 公式 docs（evals ほか） | https://platform.openai.com/docs/guides/evals | 遮断 |
| Zheng et al. 2023 "Judging LLM-as-a-Judge"（arXiv 2306.05685） | https://arxiv.org/abs/2306.05685 | 遮断（LLM採点の偏りの具体的な中身は未確認） |
| Hamel Husain "LLM-as-a-judge" ブログ | https://hamel.dev/blog/posts/llm-judge/ | 遮断 |

---

## エンジニア・UX視点の担当に渡すとよい論点

1. **エンジニア視点へ**：AI機能では、HTTP 200 なのに失敗（拒否、途中停止、型崩れ、誤答）が起きる。`stop_reason` / `finish_reason` と評価結果を `error.type` と同じ考え方で集計に乗せるかどうか（「エラー」の定義をどこまで広げるか）を決めてほしい。
2. **エンジニア視点へ**：プロンプトと応答の本文をログに残すかどうか。OTel はデフォルトで記録しない、本番では外部保存と参照を推奨している。保持期間・アクセス権・学習への利用と同意を、プライバシー設計として一緒に決める必要がある。
3. **UX視点へ**：拒否、途中停止、「自信がない」、上限で止めたエージェントを、エラー画面ではなく「次の一手がある状態」としてどう見せるか（HAX G9・G10・G11）。人へ渡す導線をどこに置くか。PAIR の該当章は未確認なので、UX担当で原典を確かめてほしい。
4. **UX視点へ**：採用・修正・再生成・コピー・却下を暗黙のフィードバックとして計測する場合、それぞれが「成功」「失敗」のどちらを意味するかは、画面と作業によって変わる。KPI（ユーザーの成功）から逆算して、どの行動をどう解釈するかを決めてほしい。
5. **3視点共通**：ログの読み手に「AIエージェント」が加わる。イベント名・スキーマ・相関IDの一貫性と、エラー文の「次に何をすべきか」は、人・AIの両方にとっての品質要件として扱うのがよいと考える。
