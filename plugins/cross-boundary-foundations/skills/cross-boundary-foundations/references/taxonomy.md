# ③ 分類体系とコード値（タクソノミー）リサーチノート

作成日: 2026-10-07 / 調査担当

## 表記のルールと調査の制約

- 【確認】 一次資料（またはその原文を置いた GitHub 等）を実際に開き、本文で確かめた内容。引用は原文の英語をそのまま残す。
- 【未確認】 開けなかった資料。検索結果の要約で存在や書誌だけを知ったものも含む。中身については書かない。
- 【解釈】 確認した資料をもとにした、この調査担当の読み・応用。資料そのものの主張ではない。

**調査環境の制約（重要）**: この環境の通信は、組織のポリシーで接続先が絞られていた。nngroup.com、w3.org、niso.org、iso.org、developers.google.com、arxiv.org、wikipedia.org などは接続を拒否された。そのため次の手段で原文を確かめた。

- GitHub 上の原文（Google AIP、Protocol Buffers 公式ドキュメント、PostgreSQL のドキュメントソース、Unicode CLDR、schema.org、IAB Tech Lab、GOV.UK Design System、18F Methods、dbt ドキュメントなど）
- GitLab 上の GitLab Handbook の原文
- W3C SKOS の各プロパティ定義は、`skos.rdf` から自動生成された RDFLib のソース（コメントに W3C の定義文がそのまま入っている）で確認した。SKOS Reference の本文（整合性条件など）は未確認。
- platform.claude.com（Anthropic の公式ドキュメント）は開けた。

依頼にあった NN/g の記事、Rosenfeld/Morville『Information Architecture』、ANSI/NISO Z39.19、ISO 25964、Google の ML データラベリング資料は、**いずれも本文を確認できていない**。出典一覧で【未確認】として扱う。カードソーティング・ツリーテストの説明は、代わりに 18F（米国政府）と GitLab Handbook の原文で確かめた範囲に限る。

---

## 0. 定義と範囲

**この領域が扱うもの**: 「あるものを、決まった選択肢のどれかに振り分ける」ための値の集合と、その運用のすべて。具体的には次のものを含む。

- 商品カテゴリ、記事のタグ、問い合わせの種類、業種・地域などの選択肢
- ステータスなどのコード値（状態の遷移そのものは①の担当。ここでは「値の集合」としての側面を扱う）
- マスターデータ（都道府県、通貨、部署、商品分類など）
- フォームの選択肢、絞り込み（ファセット）の項目、ナビゲーションの階層
- AI の分類器・LLM に渡すラベルの一覧

**ひとつの分類体系が持つ層**【解釈】（SKOS の語彙を下敷きに整理）

| 層 | 例 | 主に気にする人 |
|---|---|---|
| 識別子（コード） | `JP`、`ORDER_CANCELLED`、`0042` | エンジニア、分析 |
| 表示名（ラベル） | 「日本」「キャンセル済み」 | UX、利用者 |
| 別名・検索語 | 「解約」「取り消し」 | 検索、サポート |
| 定義・範囲の注記・例 | 「含む：〜／含まない：〜」 | 全員、とくにアノテーターと AI |
| 関係 | 親子（階層）、関連、他体系への対応 | IA、データ統合 |
| 寿命 | 追加日、廃止日、後継の値 | エンジニア、分析 |

【確認】W3C SKOS は、この層の多くに名前を付けている。`skos:notation`（コード）、`skos:prefLabel` / `altLabel` / `hiddenLabel`（ラベル）、`skos:definition` / `scopeNote` / `example`（意味）、`skos:broader` / `narrower` / `related`（関係）、`skos:historyNote` / `changeNote`（寿命）、`skos:exactMatch` / `closeMatch` など（他体系への対応）。出典: RDFLib `_SKOS.py`（"Generated from: https://www.w3.org/2009/08/skos-reference/skos.rdf"）。

【確認】SKOS は自らの対象を "thesauri, classification schemes, taxonomies, subject-heading systems" などの構造としている（RDFLib `_SKOS.py` の docstring 冒頭 "An RDF vocabulary for describing the basic structure and content of concept schemes such as thesauri, ..."）。

**範囲の外**: 状態の遷移ルール（①）、誰がどの値を変えられるか（②）、用語そのものの意味の合意（④。ただし定義文は③と強く重なる）。

---

## 1. エンジニア視点（12項目）

### E1. コード値と表示名を分ける

- **何をするか**: データに保存・連携するのは言語に依存しないコード。画面に出す文字列は、コードから引く表示名として別に持つ。
- **なぜか**: 表示名は文言の改善、ブランド変更、翻訳で変わる。コードまで変えるとデータ移行と連携先の改修が発生する。
- **悪い例→良い例**: `status = '発送済み'` を DB に保存し、文言を「出荷済み」に変えた日から集計が二つに割れる → `status = 'SHIPPED'` を保存し、表示名は表示名の表（言語ごと）から引く。
- **根拠**:
  - 【確認】Unicode CLDR の日本語データは、国コードと表示名を分けて持つ（例 `<territory type="JP">日本</territory>`）。コードは共通で、表示名は言語ごとのファイルに入る。
  - 【確認】SKOS は `skos:notation` を "a string of characters such as "T58.5" or "303.4833" used to uniquely identify a concept within the scope of a given concept scheme" と定義し、`skos:prefLabel`（"The preferred lexical label for a resource, in a given language."）と分けている。
  - 【確認】schema.org の README は "the wording/phrasing in definitions is relatively easy to amend, whereas the exact spelling of a type or property ('Person', 'startDate' etc.) is much more disruptive to change." と書く。識別子の綴りを変えるのは、定義文を直すよりずっと影響が大きいという実務上の証言。
- **出典**: [CLDR ja.xml](https://github.com/unicode-org/cldr/blob/main/common/main/ja.xml) / [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py) / [schema.org README](https://github.com/schemaorg/schemaorg/blob/main/README.md)

### E2. ID は不変にし、意味を変えず、番号を再利用しない

- **何をするか**: 一度使ったコード・番号は、廃止後も別の意味で使わない。廃止した番号と名前は「予約済み」として残す。
- **なぜか**: 古いデータや古いクライアントは、昔の意味でその番号を読む。再利用すると黙ってデータの意味が変わる。
- **悪い例→良い例**: 問い合わせ種別 `3 = 返品` を廃止し、半年後に `3 = 配送遅延` を割り当てる。過去の `3` が全部「配送遅延」として集計される → `3` は欠番にし、新しい値は `7` などで追加する。
- **根拠**:
  - 【確認】Protocol Buffers の公式ガイドは、enum の値を消したり番号を使い回したりすると "This can cause severe issues if they later load old instances of the same `.proto`, including data corruption, privacy bugs, and so on." と書き、`reserved` で番号を予約するよう求める。
  - 【確認】同じく Best Practices: "When you delete an enum value that's no longer used, reserve its number so that no one accidentally re-uses it in the future." 名前の予約（`reserved FOO, BAR;`）も勧めている。
- **出典**: [proto3 language guide](https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/programming-guides/proto3.md) / [Proto Best Practices](https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/best-practices/dos-donts.md)

### E3. 「未指定」と「不明」と「その他」を別の値として設計する

- **何をするか**: 値が入っていない（未指定）、判断できなかった（不明）、どれにも当てはまらない（その他）を区別する。既定値は意味を持たない「未指定」にする。
- **なぜか**: 既定値に意味のある値（例「一般」）を置くと、入力漏れと本当の「一般」が混ざり、分析で見分けられなくなる。値が増えたとき、古いクライアントは新しい値を既定値として読む。
- **悪い例→良い例**: 種別の既定値を `GENERAL` にする。入力漏れが全部「一般の問い合わせ」に見える → `TYPE_UNSPECIFIED = 0`（使わない値）を既定にし、`OTHER` や `UNKNOWN` は必要なら別の値として定義する。
- **根拠**:
  - 【確認】Google AIP-126: "The first value of the enum **should** be the name of the enum itself followed by the suffix `_UNSPECIFIED`." 例外として "if an enum needs to present an `UNKNOWN`, it is usually clearer and more useful for it to be a zero value rather than having both."
  - 【確認】Proto Best Practices: "When new values are added to an enum, old clients will see the field as unset ... It may be tempting to declare this default as a semantically meaningful value but as a general rule, do not, to aid in the evolution of your protocol as new enum values are added over time."
- **出典**: [AIP-126](https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0126.md) / [Proto Best Practices](https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/best-practices/dos-donts.md)

### E4. 列挙型か、マスターテーブル（または文字列）かは「変更頻度」で決める

- **何をするか**: 年に一度も変わらない値の集合はコード上の列挙型にしてよい。業務側が頻繁に足し引きする集合（商品カテゴリ、問い合わせ種別、タグ）はマスターテーブルや、許可値を文書化した文字列で持つ。
- **なぜか**: 列挙型は読みやすく型で守れるが、変更のたびにリリースと移行が要る。DB によっては値を消せない。
- **悪い例→良い例**: 事業部が月に数回増やすキャンペーン種別を PostgreSQL の ENUM 型にし、不要な値を消せなくなる → `campaign_types` テーブルに `code`, `label`, `is_active`, `sort_order`, `valid_from`, `valid_to` を持たせ、業務側の画面から管理する。
- **根拠**:
  - 【確認】AIP-126: "enums **should** receive new values infrequently. ... a good rule of thumb is no more than once a year. For enums that change frequently, the API **should** use a string and document the format."
  - 【確認】PostgreSQL のドキュメント: "Existing values cannot be removed from an enum type, nor can the sort ordering of such values be changed, short of dropping and re-creating the enum type."
  - 【確認】AIP-126 は「凍結しているか、今後も値を足す予定か」を enum に書くよう求める: "Enums **should** document whether the enum is frozen or they expect to add values in the future."
- **出典**: [AIP-126](https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0126.md) / [PostgreSQL datatype.sgml（Enumerated Types）](https://github.com/postgres/postgres/blob/master/doc/src/sgml/datatype.sgml)

### E5. 外部標準があるなら自作しない

- **何をするか**: 国・通貨・言語・地域・文字種など、広く使われる標準（ISO 3166、ISO 4217、BCP 47 など）があるものは、そのコードをそのまま使う。社内で許す値がその一部でも、標準のコードで持つ。
- **なぜか**: 他のシステムやデータと組み合わせるとき、独自コードは対応表を生み、その対応表が壊れる。
- **悪い例→良い例**: 対応国を `1=日本, 2=アメリカ` と独自採番 → `JP`, `US`（ISO 3166-1 alpha-2）で保存し、扱う国の制限は別の設定で持つ。
- **根拠**:
  - 【確認】AIP-126: "enums **should not** be used when there is a competing, widely-adopted standard representation (such as with language codes or media types)." さらに "This is true even if only a small subset of values are permitted, because using enums in this situation often leads to frustrating lookup tables when trying to use multiple APIs together."
  - 【確認】pycountry は Debian の iso-codes を元に ISO 3166-1/3166-2/3166-3、4217、15924 を提供し、翻訳ファイルも同梱すると README に書く。
- **出典**: [AIP-126](https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0126.md) / [pycountry README](https://github.com/pycountry/pycountry/blob/main/README.rst)

### E6. 廃止は削除ではなく「状態」として持つ

- **何をするか**: 値を廃止するときは、行を消さずに「廃止日」と「後継の値」を記録する。新規入力の選択肢からは外し、過去データの表示・集計では引き続き読めるようにする。
- **なぜか**: 過去の注文・問い合わせ・記事は廃止前の値を持ち続ける。削除すると表示名が引けず、集計が欠ける。
- **悪い例→良い例**: 「店頭受取」をやめた日にマスターから行を削除し、過去注文の画面に空欄が出る → `is_active=false`、`withdrawn_at=2026-04-01`、`superseded_by=PICKUP_LOCKER` を記録し、入力画面だけで非表示にする。
- **根拠**:
  - 【確認】ISO 3166 は削除された国コードを ISO 3166-3 として別に持つ。pycountry の例ではソ連が `alpha_2='SU' ... withdrawal_date='1992-08-30'` として残っている。
  - 【確認】schema.org の語彙データ（`data/schema.ttl`）では、置き換えられた語に `:supersededBy` が付く（例 `:Code` → `:supersededBy :SoftwareSourceCode`）。取得時点で 88 か所あった。
  - 【確認】Protocol Buffers は名前を変えるとき、新しい名前を後ろに追加し古い名前を deprecate してから段階的に外す手順を示す（"Add the new name below the old name and deprecate the old one"）。
  - 【確認】SKOS には `skos:historyNote`（"A note about the past state/use/meaning of a concept."）と `skos:changeNote`（"A note about a modification to a concept."）がある。
- **出典**: [pycountry README](https://github.com/pycountry/pycountry/blob/main/README.rst) / [schema.org data/schema.ttl](https://github.com/schemaorg/schemaorg/blob/main/data/schema.ttl) / [Proto Best Practices](https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/best-practices/dos-donts.md) / [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py)

### E7. 統合・分割・移行は「対応表」をデータとして残す

- **何をするか**: 2つの値を1つに統合する、1つを2つに分ける、別の体系へ移る、といったときは「旧→新」の対応を、完全一致か近似か上位概念かの種類つきで記録する。
- **なぜか**: 分割は機械的に過去データへ当てはめられない（旧値の行がどちらに属するか分からない）。種類を区別しておかないと、「近い」対応を「同じ」として扱い、誤差が積み重なる。
- **悪い例→良い例**: 「配送の問題」を「配送遅延」と「破損」に分割し、過去分を全部「配送遅延」に一括置換 → 対応表に `旧:配送の問題 → 新:配送遅延 (narrowMatch)`、`→ 新:破損 (narrowMatch)` を残す。過去分は旧値のまま保持し、時系列の比較は上位の「配送」で行う。
- **根拠**:
  - 【確認】SKOS: `skos:exactMatch` は "indicating a high degree of confidence that the concepts can be used interchangeably across a wide range of information retrieval applications. skos:exactMatch is a transitive property"。`skos:closeMatch` は "sufficiently similar that they can be used interchangeably in some information retrieval applications. In order to avoid the possibility of "compound errors" when combining mappings across more than two concept schemes, skos:closeMatch is not declared to be a transitive property." ほかに `broadMatch` / `relatedMatch` がある。
  - 【解釈】「近い」対応を推移的に繋ぐと誤差が積み重なる、という SKOS の注意は、社内の分類改訂を何度も重ねるときにもそのまま当てはまる。
- **出典**: [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py)

### E8. 分類体系そのものに版をつけ、壊れる変更と壊れない変更を分ける

- **何をするか**: 分類体系に版番号をつけ、値の追加など既存データを壊さない変更（マイナー）と、階層の組み替えなど旧版と混ぜて使えない変更（メジャー）を区別する。
- **なぜか**: 下流（分析、AI の学習データ、外部連携）は「どの版で付けたラベルか」が分からないと比較できない。
- **悪い例→良い例**: 版の概念がなく、いつの間にか階層が変わっている → `taxonomy_version = 3.1` をラベルと一緒に保存し、3.x と 2.x は混ぜないと決める。
- **根拠**:
  - 【確認】IAB Tech Lab の Taxonomies README: "major version numbers represent breaking changes and minor version numbers represent improvements such as new rows that do not change the taxonomy's hierarchical structure. For example, ... Content Taxonomy 3.0 may not be used alongside earlier versions"。改訂は Taxonomy and Mapping Working Group が提案を受けて検討する。
- **出典**: [IAB Tech Lab Taxonomies README](https://github.com/InteractiveAdvertisingBureau/Taxonomies)

### E9. 多言語は「1コード × 言語ごとの表示名」で持つ

- **何をするか**: 表示名・別名・定義文を言語ごとに持つ。コードは全言語で共通。
- **なぜか**: 言語ごとに別のマスターを作ると、値の追加・廃止が言語間でずれる。
- **悪い例→良い例**: `categories_ja` と `categories_en` を別テーブルで管理し、英語版にだけ新カテゴリがない → `categories(code)` と `category_labels(code, lang, label, definition)` に分ける。翻訳がない言語は既定言語にフォールバックし、翻訳漏れを検出する。
- **根拠**:
  - 【確認】SKOS の `prefLabel` は "in a given language"（言語ごとの優先ラベル）と定義される。
  - 【確認】CLDR は言語ごとのファイル（`common/main/ja.xml` 等）に同じコードの表示名を持つ。
  - 【未確認】SKOS Reference の整合性条件（言語タグごとに prefLabel は1つまで）は本文を開けず未確認。
- **出典**: [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py) / [CLDR ja.xml](https://github.com/unicode-org/cldr/blob/main/common/main/ja.xml)

### E10. 階層（ツリー）とファセット（独立した軸）をデータ構造で区別する

- **何をするか**: 「靴 > スニーカー」のように意味が包含関係にあるものは親子で持つ。「色」「サイズ」「素材」のように互いに独立した軸は、別々の属性（ファセット）として持つ。
- **なぜか**: 独立した軸を1本のツリーに押し込むと「メンズ > 黒 > 26cm > スニーカー」のような組み合わせ爆発と、同じ商品の置き場所が複数できる問題が起きる。
- **悪い例→良い例**: カテゴリツリーに「赤い靴」「青い靴」がある → カテゴリ＝「靴」、色＝独立の属性。
- **根拠**:
  - 【確認】SKOS は階層関係を `skos:broader`（"Relates a concept to a concept that is more general in meaning."）/ `narrower` で表し、意味的に関係はあるが階層でないものを `skos:related`（"associative semantic relationship"）で分ける。
  - 【未確認】ファセット分類の理論的背景（Rosenfeld/Morville、Ranganathan）は本文を確認できていない。
  - 【解釈】ツリーにするかファセットにするかは、ナビゲーション（UX）と分析の両方の都合を見て決める話なので、エンジニア単独で決めないほうがよい（§5 参照）。
- **出典**: [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py)

### E11. 分析の次元として一貫させる（許可値テストと履歴）

- **何をするか**: 分析基盤でも、コード列に「許可された値以外が入っていないか」のテストを置く。分類が付け替わる対象は、いつどの値だったかの履歴を残す。
- **なぜか**: 想定外の値（表記ゆれ、廃止済みの値、テスト用の値）が混ざると、ダッシュボードに説明できない行が出る。上書きだけだと「先月は何件が A だったか」を再現できない。
- **悪い例→良い例**: `status` に `'Shipped'` と `'shipped'` が混在しても誰も気づかない → dbt の `accepted_values` で `['placed','shipped','completed','returned']` 以外を失敗にする。分類の付け替えはスナップショット（SCD Type 2）で `valid_from` / `valid_to` を残す。
- **根拠**:
  - 【確認】dbt の `accepted_values` は "validates that all of the non-`null` values in a column are present in a supplied list of `values`. If any values other than those provided in the list are present, then the data test will fail."（null は対象外なので `not_null` と併用する）。
  - 【確認】dbt のスナップショットは "implement type-2 Slowly Changing Dimensions over mutable source tables" で、`dbt_valid_from` / `dbt_valid_to` 列を持つ。
- **出典**: [dbt data tests](https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/reference/resource-properties/data-tests.md) / [dbt snapshots](https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/docs/build/snapshots.md)

### E12. 知らない値を受け取ったときの振る舞いを決めておく

- **何をするか**: 新しい値を先に追加した側と、まだ知らない側が並存する期間を前提に、知らない値は捨てずに保持し、画面では「その他」等で表示する。
- **なぜか**: 値の追加はリリースのずれを必ず伴う。知らない値で落ちる、または黙って既定値に変換すると、データが失われる。
- **悪い例→良い例**: クライアントが未知の種別を受けたら例外で画面が真っ白 → 未知の値は元のコードのまま保存し、表示は「その他（新しい種別）」にしてログに出す。
- **根拠**:
  - 【確認】proto3 ガイド: "During deserialization, unrecognized enum values will be preserved in the message"。表現は言語により異なる（open enum の言語では整数のまま保持）。
- **出典**: [proto3 language guide](https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/programming-guides/proto3.md)

---

## 2. ビジネス・UX視点（11項目）

### U1. ユーザーの言葉と頭の中の分け方から始める（オープンカードソート）

- **何をするか**: 分類の候補を作る段階で、利用者に項目カードを自由にまとめてもらい、まとまりに名前を付けてもらう。その理由も聞く。
- **なぜか**: 社内の分け方（部署、商品の仕入れ区分、システムの都合）は、利用者が探すときの分け方と一致しないことが多い。
- **悪い例→良い例**: 問い合わせフォームの種別を、社内のサポートチームの担当区分（「EC チーム」「会員基盤チーム」）で並べる → 利用者に「困りごと」のカードを分けてもらい、「注文を変えたい」「届かない」「ログインできない」のような、利用者が自分の状況から選べる言葉に置き換える。
- **根拠**:
  - 【確認】18F Methods の Card sorting: 目的は "To gain insights from users about how to organize content in an intuitive way." オープンカードソートの手順は "Ask users to separate the cards into whatever categories make sense to them." "Ask users to label those categories." "Ask users to tell you why they grouped the cards and labeled the categories as they did." 所要時間は 1 人 15〜30 分、1 人ずつか 2〜3 人のグループで行う。
  - 【未確認】NN/g のカードソーティングの記事（参加人数の推奨など）は本文未確認。
- **出典**: [18F Methods: Card sorting](https://github.com/18F/methods/blob/main/_methods/card-sorting.md)

### U2. 作った分類はクローズドカードソートやツリーテスト、ファーストクリックで検証する

- **何をするか**: 候補の分類ができたら、決めたカテゴリに振り分けてもらう（クローズドカードソート）、または「〇〇を探すならどこ？」と課題を出して正しい場所に辿り着けるかを測る。
- **なぜか**: 作る段階（生成）と確かめる段階（評価）は別の手法が要る。チームの多数決で決めた分類は、利用者が見つけられるかを保証しない。
- **悪い例→良い例**: 会議で決めた分類をそのまま実装 → 課題ベースで「最初にどこを押すか」と成功率を測り、迷いの多い項目の名前や置き場所を直す。
- **根拠**:
  - 【確認】18F: クローズドカードソートは "Ask users to separate the cards into a list of categories you have predefined."
  - 【確認】GitLab Handbook（ナビゲーションの早期検証）: ファーストクリックテストで "Does the hierarchy of your information architecture make sense, why or why not?" などを問う。サンプル数は 30 を目安（詳細は同社のファーストクリックテストのページを参照）。ナビゲーション評価の中心指標に Effectiveness（"A binary measure of a user's ability to find an item when given a task"）と Findability などを置く。
  - 【未確認】NN/g のツリーテストの記事、およびカードソーティングとツリーテストの違いを扱う記事は本文未確認。検索要約では「カードソーティングは IA の案を作るため、ツリーテストは IA の案を評価するため」とされていたが、原文で確かめていない。
- **出典**: [18F Methods: Card sorting](https://github.com/18F/methods/blob/main/_methods/card-sorting.md) / [GitLab Handbook: Testing navigation: early Solution Validation](https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/main/content/handbook/upstream-studios/experience-research/early-solution-validation-process-for-navigation/index.md) / [GitLab Handbook: Evaluating navigation](https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/main/content/handbook/upstream-studios/experience-research/evaluating-navigation/index.md)

### U3. 統制語彙：見せる名前は1つ、探される名前は複数

- **何をするか**: 各値に、画面に出す優先ラベルを1つ決める。同義語・俗称・旧称・よくある誤記は別名として登録し、検索やサジェストで拾う。
- **なぜか**: 選択肢の名前を利用者ごとに変えるとデータが割れる。一方、名前を1つに絞ると、別の言い方で探す人が見つけられない。この両立を語彙の側で受け持つ。
- **悪い例→良い例**: 「解約」で検索すると0件（正式名は「退会」） → 優先ラベル「退会」、別名「解約」「アカウント削除」、検索専用語として誤記「たいかい」を登録する。
- **根拠**:
  - 【確認】SKOS: `altLabel` は "An alternative lexical label for a resource."、`hiddenLabel` は "A lexical label for a resource that should be hidden when generating visual displays of the resource, but should still be accessible to free text search operations."
  - 【未確認】ANSI/NISO Z39.19（単一言語の統制語彙の構築・管理の指針）と ISO 25964（シソーラスと他語彙との相互運用）は本文を確認できていない。書誌のみ検索で確認。
- **出典**: [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py)

### U4. 「その他」「該当なし」「わからない」は、意図して置く

- **何をするか**: どれにも当てはまらない人、判断できない人のための選択肢を、必要なときだけ、最後に、区切って置く。文言は質問を繰り返す形にする。
- **なぜか**: 逃げ道がないと、利用者はいちばん近いもの（あるいは先頭）を選び、分類データが汚れる。逃げ道が目立ちすぎると、考えずにそれを選ぶ。
- **悪い例→良い例**: 単一選択の先頭に「その他」 → 選択肢の最後に区切り線（「または」）を入れ、「どれにも当てはまらない」を置く。複数選択なら「いずれにも行く予定はない」のように質問を繰り返し、他と同時に選べないようにする。
- **根拠**:
  - 【確認】GOV.UK Design System（Checkboxes）: "When 'none' would be a valid answer, give users the option to check a box to say none of the other options apply to them ... Giving users this option also makes sure they do not skip the question by accident." "Show the 'none' option last. Separate it from the other options using a divider. The text is usually the word 'or'." "Write a label that repeats the key part of the question." 排他動作（`exclusive`）も用意されている。
  - 【確認】同（Radios）: "you should include 'None of the above' or 'I do not know' if they are valid options."
  - 【確認】同（Checkboxes）は、より良い質問を立てる、事前の絞り込み質問で対象外の人を外す、ことで 'none' 自体を不要にできる場合があるとも書く。
- **出典**: [GOV.UK Design System: Checkboxes](https://github.com/alphagov/govuk-design-system/blob/main/src/components/checkboxes/index.md) / [GOV.UK Design System: Radios](https://github.com/alphagov/govuk-design-system/blob/main/src/components/radios/index.md)

### U5. 「その他」の割合と中身を定期的に見る

- **何をするか**: 「その他」「該当なし」が選ばれた割合と、自由記述の中身を定期的に読む。一定以上に増えたら、新しい値の候補を出す。
- **なぜか**: 「その他」の比率は、分類体系が現実に合わなくなってきたことを示す最も安い指標になる。
- **悪い例→良い例**: 問い合わせの3割が「その他」なのに、誰も中身を読まない → 月次で「その他」の上位の言い回しを集計し、変更手続き（§6）にかける。
- **根拠**:
  - 【解釈】直接この運用を定めた一次資料は今回確認できていない。ただし次の確認済み資料がこの考えを支える。GoEmotions は、アノテーターが「非常に不明確で付けにくい」と判断した例を `example_very_unclear` として記録している（【確認】）。Claude のチケット分類ガイドは、従来型 ML が曖昧な入力を "defaulting to a catch-all category" しがちだと書く（【確認】）。どちらも「受け皿に落ちたもの」を観測対象にしている。
- **出典**: [GoEmotions README](https://github.com/google-research/google-research/blob/master/goemotions/README.md) / [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

### U6. 単一選択なら相互排他、複数当てはまるなら複数選択（MECE を UI で裏切らない）

- **何をするか**: 1つしか選べない UI にするなら、値どうしが重ならない（相互排他）ように定義する。現実に複数当てはまるなら、複数選択にするか「主たるもの」を選ぶルールを明示する。網羅できない部分は U4 の受け皿で受ける。
- **なぜか**: 重なりのある値を単一選択させると、人によって選ぶ値が変わり、分析も AI の学習データもぶれる。
- **悪い例→良い例**: 「料金について」「解約について」が並び、「解約時の返金」を問い合わせたい人がどちらを選ぶか割れる → 定義書で「解約に伴う返金は『料金』に含む」と決めるか、複数選択にする。
- **根拠**:
  - 【確認】GOV.UK（Radios）: "Do not use the radios component if users might need to select more than one option."
  - 【確認】Claude のチケット分類ガイドは、1件に複数の問題があるとき主たる関心を決めにくいとし、"Clarify the prioritization of intents" を解決策に挙げる。
- **出典**: [GOV.UK Design System: Radios](https://github.com/alphagov/govuk-design-system/blob/main/src/components/radios/index.md) / [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

### U7. 並び順も分類の設計の一部

- **何をするか**: 既定はアルファベット（五十音）順。よく選ばれる順に並べるのは、偏りを生むことを承知のうえで行う。
- **なぜか**: 上にあるものほど選ばれやすく、それが分析上の「人気」に跳ね返る。
- **悪い例→良い例**: 前月の件数順に並べ替え続け、上位がさらに選ばれる → 既定は五十音順。頻度順を採るなら、その判断と見直し時期を定義書に書く。
- **根拠**:
  - 【確認】GOV.UK（Radios）: "Order radio options alphabetically by default." "In some cases, it can be helpful to order them from most-to-least common options ... However you should do this with extreme caution as it can reinforce bias in your service. If in doubt, order alphabetically."
  - 【確認】同: "Do not pre-select radio options"（未回答に気づかない・誤回答の原因になるため）。
- **出典**: [GOV.UK Design System: Radios](https://github.com/alphagov/govuk-design-system/blob/main/src/components/radios/index.md)

### U8. 分類はナビゲーション・検索・分析・組織の担当を一本でつなぐ

- **何をするか**: 1つの分類が、画面の入口、検索の絞り込み、ダッシュボードの切り口、問い合わせの振り分け先（担当チーム）のどれに使われているかを一覧にする。
- **なぜか**: 同じ値の集合がいくつもの役割を兼ねている。どれか1つの都合で変えると、残りが壊れる。
- **悪い例→良い例**: UX 改善で問い合わせ種別を統合したら、担当チームへの自動振り分けとチーム別 KPI が壊れた → 利用者が選ぶ「入口の分類」と、社内の「振り分け先」を別の値として持ち、対応表でつなぐ。
- **根拠**:
  - 【確認】Claude のチケット分類ガイドは、自動化の前に現状の運用を調べるよう求め、"Is ticket routing used to determine which tier of support or product specialist a ticket goes to?" "What criteria are used to determine what SLA/service offering is applied?" を問いとして挙げる。分類の結果が担当・SLA に直結していることを前提にしている。
  - 【確認】GitLab Handbook はナビゲーションの変更で、Findability（"A user's ability to find what requires their attention"）などの指標を全チーム共通で測るとしている。
  - 【解釈】「利用者が選ぶ分類」と「社内で振り分ける分類」を同じ値にする必要はない。分けて対応表を持つと、§5 の対立の多くがほどける。
- **出典**: [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing) / [GitLab Handbook: Evaluating navigation](https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/main/content/handbook/upstream-studios/experience-research/evaluating-navigation/index.md)

### U9. 各値に「定義・範囲の注記・例」を書く

- **何をするか**: 値ごとに、定義（1〜2文）、範囲の注記（含むもの・含まないもの、紛らわしい隣の値との境界）、実例を書く。
- **なぜか**: ラベル名だけでは、入力する人・分析する人・AI がそれぞれ違う意味で使う。
- **悪い例→良い例**: 「請求」というラベル名だけ → 定義「請求額・支払方法・請求書に関する確認」。含む「明細の見方」。含まない「身に覚えのない請求（→『請求の異議』）」。例「先月の請求額の内訳を知りたい」。
- **根拠**:
  - 【確認】SKOS: `skos:definition`（"A statement or formal explanation of the meaning of a concept."）、`skos:scopeNote`（"A note that helps to clarify the meaning and/or the use of a concept."）、`skos:example`（"An example of the use of a concept."）、`skos:editorialNote`（"A note for an editor, translator or maintainer of the vocabulary."）。
  - 【確認】Claude の分類クックブックは、10カテゴリそれぞれに「何を含むか」を複数行で書いた説明を与え、さらに紛らわしい組（"Billing Disputes" と "Billing Inquiries"）の違いを例で示すことを重視している。
- **出典**: [RDFLib _SKOS.py](https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py) / [Claude Cookbook: Classification](https://platform.claude.com/cookbook/capabilities-classification-guide)

### U10. 分類の改訂は「局所的な分かりやすさ」を優先する

- **何をするか**: 全体の理論的な美しさのための大規模な組み替えより、利用者・入力者が困っている具体的な場面の改善を優先する。
- **なぜか**: 大規模な組み替えは移行コストが大きく、過去との比較を壊す。利用者にとっての効果は小さいことが多い。
- **悪い例→良い例**: 「体系として正しくない」ことを理由に全カテゴリを再編 → 迷いの多い数か所の名前と定義を直し、必要な値だけ追加する。
- **根拠**:
  - 【確認】schema.org README: "We are also highly unlikely to take on large-scale reorganizations of Schema.org's terminology if they are motivated solely by considerations of elegance, "proper modeling", ontological purity or conceptual unification." "We prioritize local coherence (having sensible ways to describe many common situations) over global elegance"。新しい語はまず "Pending" 領域に入れてフィードバックを集める。
- **出典**: [schema.org README](https://github.com/schemaorg/schemaorg/blob/main/README.md)

### U11. ファセット分類で「迷わせない」と「細かく絞れる」を両立させる

- **何をするか**: 1本の深いツリーで全部を表そうとせず、浅いカテゴリ＋独立した絞り込み軸（色・価格帯・対象者など）に分ける。
- **なぜか**: 深いツリーは「どの枝に入っているか」を利用者に当てさせることになる。ファセットなら利用者は自分が分かる軸から絞れる。
- **悪い例→良い例**: 「レディース > トップス > 夏 > 半袖 > 白」 → カテゴリは「トップス」までにして、季節・袖丈・色は絞り込みに出す。
- **根拠**:
  - 【未確認】Rosenfeld/Morville『Information Architecture』のファセット分類の議論、NN/g のタクソノミー記事は本文未確認。
  - 【解釈】E10（SKOS の階層関係と関連関係の区別）と同じ考えを UX 側から見たもの。この項は一次資料で確かめられていないため、採用前に IA の文献で確認してほしい。
- **出典**: なし（E10 を参照）

---

## 3. AI視点（9項目）

### A1. ラベル一覧そのものがタスクの定義である

- **何をするか**: 分類器・LLM・判定特化モデルのどれを使う場合でも、最初に作るのはラベルの一覧と定義。モデル選びはその後。
- **なぜか**: モデルはラベルの境界を学ぶ・読むしかない。境界が曖昧ならモデルの精度も上がらない。
- **悪い例→良い例**: 「とりあえず LLM に分類させて」でラベルを即席で並べる → §6 の定義書を作ってから、プロンプトと評価データを作る。
- **根拠**:
  - 【確認】Claude のチケット分類ガイド: "A well-defined list of user intent categories is crucial for accurate support ticket classification with Claude. Claude's ability to route tickets effectively within your system is directly proportional to how well-defined your system's categories are."
- **出典**: [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

### A2. 定義文と例（とくに紛らわしい組の対比）が精度を左右する

- **何をするか**: 各ラベルに説明を付け、典型例と境界例を添える。例が多くて入らない場合は、似た過去事例を検索して都度渡す。
- **なぜか**: ラベル名だけのゼロショットより、説明と例を渡すほうが一貫して精度が上がる。
- **悪い例→良い例**: プロンプトにラベル名を10個並べるだけ → 各ラベルの説明＋似た過去例5件を渡す。
- **根拠**:
  - 【確認】Claude の分類クックブック（保険の問い合わせ10分類）では、正解率が簡単なプロンプトで約70%、類似例の検索（RAG）を加えて94%、さらに考える過程を書かせて97%と示されている（同クックブックの評価値）。
  - 【確認】Claude のチケット分類ガイド: 類似検索で例を選ぶ方法は "has been shown to improve performance from 71% accuracy to 93% accuracy." 暗黙の依頼（「2週間荷物を待っている」＝配送状況の確認）には、実例と「なぜその分類か」の理由を添えるとよいとする。
  - 【解釈】これらの数字は特定のデータセットでの結果。自社のラベルでも同じだけ上がるとは限らない。
- **出典**: [Claude Cookbook: Classification](https://platform.claude.com/cookbook/capabilities-classification-guide) / [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

### A3. 「中立」「判定不能」の出口をラベル設計に入れる

- **何をするか**: 実データにはどれにも当たらないもの、判断できないものが必ずある。ラベル一覧に「該当なし（中立）」を入れ、アノテーションでは「判断できない」を記録できるようにする。
- **なぜか**: 出口がないと、モデルも人も無理にどれかへ押し込み、そのラベルの意味が薄まる。
- **悪い例→良い例**: 感情27種のどれかを必ず付けさせる → 「Neutral」を足し、「非常に不明確」を別フラグで記録する。
- **根拠**:
  - 【確認】GoEmotions は "27 emotion categories or Neutral" でアノテーションし、生データに `example_very_unclear`（"Whether the annotator marked the example as being very unclear or difficult to label (in this case they did not choose any emotion labels)"）を持つ。
  - 【確認】AIP-126 の `UNKNOWN` / `_UNSPECIFIED` の考え方（E3）とも一致する。
- **出典**: [GoEmotions README](https://github.com/google-research/google-research/blob/master/goemotions/README.md) / [AIP-126](https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0126.md)

### A4. ラベルが多いときは階層で判定する

- **何をするか**: ラベルが20を超えるようなら、まず大分類、次に小分類と段階的に判定する。
- **なぜか**: 一度に多数のラベルから選ばせると、必要な例が増えてプロンプトが扱いにくくなる。
- **悪い例→良い例**: 60種の問い合わせ種別を1回で判定 → 「技術」「請求」「一般」で振り分け、それぞれ専用の小分類プロンプトに渡す。
- **根拠**:
  - 【確認】Claude のチケット分類ガイド: "Use a taxonomic hierarchy for cases with 20+ intent categories"。利点は精度と細かさ、欠点は遅延の増加と書く。
  - 【解釈】階層をそのまま判定の段にするには、上位の分類が相互排他であることが前提になる（U6）。
- **出典**: [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

### A5. アノテーションのガイドラインと、人同士の一致率を先に測る

- **何をするか**: 人が付けるラベルにも定義書（§6）を渡し、同じデータを2人以上に付けてもらい、一致率を測る。一致しないラベルは定義を直す。
- **なぜか**: 人同士で一致しないラベルを、モデルに当てさせることはできない。一致率は「定義が通じているか」の指標になる。
- **悪い例→良い例**: 1人が全件ラベル付けし、その結果を正解として学習 → 2人で200件を付けてカッパ係数を見る。低いラベルの組（例：「要望」と「不満」）の境界を定義書で直す。
- **根拠**:
  - 【確認】scikit-learn の `cohen_kappa_score`: "Compute Cohen's kappa: a statistic that measures inter-annotator agreement." 2人のアノテーターの一致度を、偶然の一致を差し引いて表す。
  - 【確認】GoEmotions の学習用データは "examples where there is agreement between at least 2 raters" に絞っている。
  - 【未確認】Google の ML データラベリング資料、Google Cloud のラベラー向け指示書のガイド（ページを取得したが本文が読めなかった）は未確認。
- **出典**: [scikit-learn _classification.py](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/metrics/_classification.py) / [GoEmotions README](https://github.com/google-research/google-research/blob/master/goemotions/README.md)

### A6. ラベルの誤りを機械で探して、人が直す

- **何をするか**: 学習データ・評価データのラベル誤りの候補を自動で洗い出し、人が見直す。混同行列でどのラベル同士が混ざるかを見る。
- **なぜか**: 現実のラベルデータには誤りが含まれる。混ざりやすい組は、分類体系の定義の問題であることが多い。
- **悪い例→良い例**: 評価データを正解と信じ込み、精度が上がらない原因をモデルに求める → ラベル品質の検査で誤り候補を出し、多い組は定義書を直す。
- **根拠**:
  - 【確認】cleanlab README: "cleanlab finds data and label issues in any dataset"。手法は confident learning（JAIR 2021 の論文）。複数アノテーターの合意とアノテーターの質の推定もできるとする。
  - 【確認】Claude の分類クックブックは評価の段で混同行列を描き "show which categories are being confused with each other" とする。
- **出典**: [cleanlab README](https://github.com/cleanlab/cleanlab/blob/master/README.md) / [Claude Cookbook: Classification](https://platform.claude.com/cookbook/capabilities-classification-guide)

### A7. 埋め込みで「候補」を見つけ、名前と採否は人が決める

- **何をするか**: 自由記述や「その他」を埋め込みでクラスタリングし、新しい値の候補を出す。名前付け・統合・採用は人（定義書の管理者）が決める。
- **なぜか**: クラスタは似ている文の集まりであって、業務上意味のある分類とは限らない。外れ値も必ず出る。
- **悪い例→良い例**: クラスタリング結果の自動ラベルをそのままカテゴリにする → 候補として提示し、人が統合・命名し、どのクラスタをどの値に対応させたかを記録する。
- **根拠**:
  - 【確認】BERTopic README: 外れ値を `-1` のトピックに集める（"The `-1` topic refers to all outlier documents and are typically ignored."）。人が付けるラベル（`.set_topic_labels`）、統合（`.merge_topics`）、統合の追跡（`.topic_mapper_`: "tracking topics and their mappings anytime they are merged/reduced"）、既知トピックを与える Guided / Zero-shot の機能を持つ。
  - 【解釈】`-1` の外れ値は U5 の「その他」と同じ役割を持つ。外れ値の量と中身を見ることが、体系の見直しの入口になる。
- **出典**: [BERTopic README](https://github.com/MaartenGr/BERTopic/blob/master/README.md)

### A8. 分類の分布と一貫性の変化（ドリフト）を監視する

- **何をするか**: ラベルごとの件数比、「その他／判定不能」の比率、同じ入力への判定の一貫性を定期的に見る。
- **なぜか**: 商品・顧客・季節が変われば、入力も分類の分布も変わる。分類体系が古くなったのか、モデルがずれたのかを切り分ける必要がある。
- **悪い例→良い例**: 導入時の精度を一度測って終わり → 基準期間と現在の分布の差を毎週測り、標準入力のセットで判定の一貫性を定期的にテストする。
- **根拠**:
  - 【確認】Evidently README: "100+ built-in metrics from data drift detection to LLM judges"。`DataDriftPreset` で "test for shift in column distributions"（例では PSI を指定）。
  - 【確認】Claude のチケット分類ガイドは "Classification consistency" を成功基準に挙げ、"periodically testing the model with a set of standardized inputs and aiming for a consistency rate of 95% or higher." とする。
- **出典**: [Evidently README](https://github.com/evidentlyai/evidently/blob/main/README.md) / [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

### A9. 判定手段は「分類が変わる頻度」と「データの量」で選ぶ

- **何をするか**: ラベル付きデータが少ない、またはカテゴリが今後も変わる場合は LLM の分類（定義と例で動く）を検討する。カテゴリが安定しデータが多く、速度・費用が重要なら、従来型の分類器や判定特化モデルを検討する。
- **なぜか**: 分類体系の変更コストがモデルの種類で大きく違う。従来型 ML はカテゴリの追加・変更のたびに再ラベル付けと再学習が要る。
- **悪い例→良い例**: 月に一度カテゴリが変わる業務に、大量の学習データが要る分類器を作る → 定義書を更新すれば追従できる LLM 方式にし、安定したら軽いモデルへ置き換えを検討する。
- **根拠**:
  - 【確認】Claude のチケット分類ガイド: LLM を選ぶ目安として "Your classification categories are likely to change or evolve over time" を挙げ、"Once a traditional ML approach has been established, changing it is a laborious and data-intensive undertaking." と書く。ラベル付きデータが少ない場合（"just a few dozen labeled examples"）も挙げる。
  - 【未確認】判定特化モデル Jev（Typesafe 社）は、検索結果の要約で「文章を生成せず、選択肢やスコアなどの構造化された判定を返す分類特化モデル」とされていたが、公式サイト・論文はいずれも接続を拒否され、本文を確認できなかった。仕様（出力形式、速度、費用）はここに書かない。
  - 【解釈】どの方式でも、ラベル一覧・定義・例・「判定不能」の出口・評価データは同じものが要る。分類体系をきちんと作っておけば、方式を後から乗り換えられる。
- **出典**: [Claude Docs: Ticket routing](https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing)

---

## 4. 越境：それぞれが相手を知るべき理由と配慮

### 4-a. ビジネス・UX がエンジニアの観点を知るべき理由

| 知っておくこと | 理由 | 根拠 |
|---|---|---|
| 表示名の変更は安いが、コードの変更・削除は高い | 「名前を変えたい」と「分類を変えたい」を分けて頼めば、変更の多くは軽く済む | 【確認】schema.org README（定義文は直しやすく、識別子の綴りは影響が大きい）、E1 |
| 値は「消せない」前提で考える | 過去データは旧値を持ち続ける。廃止＝非表示＋後継の指定 | 【確認】PostgreSQL（enum の値は削除不可）、Protobuf（番号の予約）、ISO 3166-3 |
| 分割は過去に遡れない | 「来月から2つに分ける」と、過去との比較は上位の分類でしかできなくなる | 【解釈】E7 |
| 外部標準があるものは標準に合わせる | 独自の都道府県・国コードは連携先で対応表を生む | 【確認】AIP-126 |
| 分類はダッシュボードと自動振り分けにも使われている | UI の改善が KPI や SLA を壊すことがある | 【確認】Claude ticket routing、【解釈】U8 |

**配慮**【解釈】: 変更を頼むときは「どの値を、表示名だけか意味も変えるか、過去データをどう扱うか」の3点を書いて出す。

### 4-b. エンジニアがビジネス・UX の観点を知るべき理由と配慮

| 知っておくこと | 理由 | 根拠 |
|---|---|---|
| 分類は利用者の「探し方」で決まる | DB の都合や社内組織の区分は、利用者の頭の中の区分と違う | 【確認】18F（カードソーティングの目的） |
| 「その他」は設計対象であり、観測窓 | 逃げ道の有無と置き方でデータの質が変わる | 【確認】GOV.UK Checkboxes/Radios |
| 並び順・既定値は回答を変える | 頻度順は偏りを強め、初期選択は誤回答を生む | 【確認】GOV.UK Radios |
| 単一選択か複数選択かは、現実の重なり方で決める | 型の都合で単一にすると入力がぶれる | 【確認】GOV.UK Radios |
| 改訂は小さく、具体的な困りごとから | 大改修は利用者にとって効果が薄いことが多い | 【確認】schema.org README |

**配慮**【解釈】:
- 表示名・並び順・別名・定義文を、リリースなしに業務側が直せる場所（マスターテーブル＋管理画面、または設定ファイル）に置く。これで「UX の改善」と「コードの変更」が切り離される。
- 「その他」の自由記述と選択率を、最初から集計できるように記録する。
- 値の追加・廃止のときに「過去データの表示はこうなる」を画面例で見せる。

### 4-c. AI の観点（三者が知るべきこと）

| 誰が | 知っておくこと | 根拠 |
|---|---|---|
| ビジネス・UX | AI の精度は分類の定義の明確さに比例する。「AI がうまく分けない」の原因は定義側にあることが多い | 【確認】Claude ticket routing（"directly proportional"） |
| ビジネス・UX | 人同士で一致しないラベルは AI にも当てられない | 【確認】sklearn（kappa）、GoEmotions（2人以上の一致） |
| エンジニア | 定義書・例・版番号をデータとして持てば、プロンプト・評価データ・アノテーション指示書を同じ源から作れる | 【確認】SKOS（definition/scopeNote/example）、【解釈】 |
| エンジニア | 予測ラベルにも分類体系の版を付けて保存する | 【確認】IAB（メジャー版は旧版と混ぜない）、【解釈】 |
| 三者 | 「判定不能」の割合とクラスタの外れ値は、分類体系の見直しの入口 | 【確認】GoEmotions、BERTopic、【解釈】 |

---

## 5. ゴールの違いと折り合い

### 5-1. 典型的な対立

| 立場 | ゴール | 分類への要求 | 放っておくと起きること |
|---|---|---|---|
| 事業・分析 | 細かく把握し、施策の効果を測りたい | 値を増やしたい、細かく分けたい | 選択肢が多すぎて利用者が迷い、入力がぶれ、結局データの質が下がる |
| UX | 迷わせない、早く選べる | 値を減らしたい、利用者の言葉にしたい | 粒度が粗くなり分析できない／社内の振り分けと合わない |
| エンジニア | 変更コストを抑え、データの整合を保ちたい | 値を固定したい、変更は少なく | 現実とずれた分類が固定され「その他」が膨らむ |
| AI | 判定しやすく、評価しやすい | 相互排他で定義が明確、例がある、出口がある | 業務上意味のある区分より、機械的に分けやすい区分が優先される |
| 組織（サポート等） | 担当に正しく振り分けたい | 社内の担当区分で分けたい | 利用者向けの選択肢が社内の組織図になる |

### 5-2. 解き方【解釈】（括弧内は支えになる確認済みの根拠）

1. **「入口の分類」と「内部の分類」を分けて、対応表でつなぐ**
   利用者が選ぶのは少数の、利用者の言葉の選択肢。社内の振り分け・分析には、より細かい内部コードを使う。内部コードは入口の選択＋自由記述＋AI の判定で付ける。UX（少なく）と分析（細かく）の対立がここでほどける。（U8、E7、A9）

2. **細かさは「階層」と「ファセット」で吸収する**
   上位の分類は少なく相互排他に保ち、細かい区分は下位や独立した属性に回す。分析は細かいまま、利用者は上位だけ選べばよい。AI も上位から段階的に判定できる。（E10、A4、Claude ticket routing の階層判定）

3. **変わりやすいものと、変わりにくいものを分ける**
   コードは不変、表示名・定義文・並び順・別名は業務側が直せる場所に置く。エンジニアの変更コストと、UX・事業の改善速度の対立がここでほどける。（E1、E4、schema.org README）

4. **「その他」を許し、測り、見直しの燃料にする**
   全部を最初から網羅しようとせず、受け皿を置いて比率を測り、閾値を超えたら変更手続きにかける。事業の「細かく」と UX の「迷わせない」を、時間をかけて合わせる。（U4、U5、A7）

5. **変更の種類で手続きの重さを変える**
   表示名・定義文の修正は軽く、値の追加は中くらい、統合・分割・階層の組み替えは重く（版を上げ、対応表と過去データの扱いを決める）。（E8、IAB の版の方針、schema.org の Pending 領域）

6. **「AI が判定しやすいか」を、人同士の一致率で測る**
   AI の都合で分類を曲げるのではなく、人が一致して付けられない値は人にとっても分かりにくい、と捉えて直す。AI の要求を利用者・入力者の分かりやすさと同じ方向にそろえる。（A5、A1）

---

## 6. 建設的な議論の進め方

### 6-1. 議論の材料を先に用意する

- **現状の数字**【解釈】: 値ごとの件数、「その他」の比率と中身、入力者による選び方のぶれ（可能なら一致率）、廃止済みの値が残っている件数。
- **使われ方の一覧**【解釈】: その分類がどの画面・検索・ダッシュボード・振り分けルール・AI のプロンプトで使われているか（U8）。
- **利用者の分け方**【確認】: オープン／クローズドカードソートの結果（18F の手順。理由も聞く）。ナビゲーションならファーストクリックや課題の成功率（GitLab Handbook）。

### 6-2. 分類の定義書（ひな形）

【解釈】SKOS の項目（【確認】）を、業務で使える形に置き換えたもの。

| 項目 | 内容 | 対応する SKOS |
|---|---|---|
| コード | 不変の識別子。再利用しない | `notation` |
| 表示名（言語ごと） | 画面に出す名前を1つ | `prefLabel` |
| 別名・検索語 | 同義語、旧称、俗称、誤記 | `altLabel` / `hiddenLabel` |
| 定義 | 1〜2文 | `definition` |
| 含む | 典型例と、迷いやすいが含むもの | `scopeNote` / `example` |
| 含まない | 隣の値との境界と、その行き先 | `scopeNote` |
| 例 | 実データからの例文（AI の例にも使う） | `example` |
| 親／関連 | 上位の値、関連する値 | `broader` / `related` |
| 使われ方 | 画面、分析、振り分け先、AI | （なし） |
| 状態と寿命 | 有効／廃止、開始日、廃止日、後継 | `historyNote` / `changeNote` |
| 変更履歴 | いつ、誰が、なぜ、何を変えたか | `changeNote` / `editorialNote` |
| 版 | 分類体系全体の版番号 | （IAB の版の方針） |

この定義書から、入力画面のヘルプ文、アノテーション指示書、LLM のプロンプト、分析用の許可値テスト（dbt `accepted_values` 等）を生成できるようにしておくと、四者が同じ文書を見て議論できる。【解釈】

### 6-3. 変更の手続き

【解釈】確認済みの事例（IAB の版の方針、schema.org の Pending 領域と Issue 運用、Protobuf の段階的な名前変更）を組み合わせた案。

1. **提案**: 誰でも出せる。「何を・なぜ（データや利用者の声）・影響する使われ方」を書く。schema.org が、PR は具体的な Issue に結びつけるよう求めているのと同じく、具体的な困りごとに紐づける。
2. **種類の判定**:
   - 軽い（表示名・定義文・別名・並び順）→ 管理者の判断で即時反映、変更履歴に残す。
   - 中くらい（値の追加）→ マイナー版。定義書の全項目を埋め、AI の評価データに例を足す。
   - 重い（統合・分割・廃止・階層変更）→ メジャー版。対応表、過去データの扱い、ダッシュボードの切り替え日、AI の再評価を決める。
3. **試行**: 新しい値はまず「試行中」として入れ、一定期間の選択率・一致率・AI の判定精度を見る（schema.org の "Pending" に相当）。
4. **段階的な切り替え**: 新旧を並存させ、古い値は入力から外す→表示は残す→十分な期間の後に後継へ寄せる（Protobuf の名前変更の手順に相当）。
5. **振り返り**: 「その他」比率、一致率、ドリフトの指標を変更の前後で比べる。

### 6-4. 議論の場での約束ごと【解釈】

- 「正しい分類」を争わない。「誰が、何のために、この値を使うか」を先に並べる（schema.org の「局所的な分かりやすさを優先する」方針に近い）。
- 意見が割れた値は、定義書の「含む／含まない」に具体例を1つずつ足して決める。抽象的な定義の言い換えで決着を図らない。
- 決められないときは、カードソートや一致率の小さな測定で決める。測定の方法を先に合意する。
- AI の判定結果は「第4の入力者」として扱い、人との不一致を議論の材料にする。

---

## 出典一覧

### 本文を確認したもの【確認】

| # | 資料 | URL | 確かめた内容 |
|---|---|---|---|
| 1 | Google AIP-126: Enumerations | https://github.com/aip-dev/google.aip.dev/blob/master/aip/general/0126.md （公開版 https://google.aip.dev/126 は接続拒否のため GitHub 原文で確認） | `_UNSPECIFIED`、変更頻度の目安（年1回）、外部標準優先、凍結かどうかの明記 |
| 2 | Protocol Buffers: Proto Best Practices | https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/best-practices/dos-donts.md | 削除値の番号予約、UNSPECIFIED、名前変更の手順 |
| 3 | Protocol Buffers: proto3 Language Guide | https://github.com/protocolbuffers/protocolbuffers.github.io/blob/main/content/programming-guides/proto3.md | 未知の enum 値の保持、Reserved Values |
| 4 | PostgreSQL ドキュメント（Enumerated Types） | https://github.com/postgres/postgres/blob/master/doc/src/sgml/datatype.sgml | enum の値は削除・並べ替え不可 |
| 5 | pycountry README（ISO 3166-3 等） | https://github.com/pycountry/pycountry/blob/main/README.rst | 削除国コードと withdrawal_date、iso-codes 由来 |
| 6 | Unicode CLDR ja.xml | https://github.com/unicode-org/cldr/blob/main/common/main/ja.xml | コードと言語別表示名の分離（`JP`→日本） |
| 7 | W3C SKOS 語彙の定義（RDFLib が skos.rdf から生成） | https://github.com/RDFLib/rdflib/blob/main/rdflib/namespace/_SKOS.py | notation、prefLabel/altLabel/hiddenLabel、definition/scopeNote/example、historyNote/changeNote、broader/related、exactMatch/closeMatch |
| 8 | schema.org README | https://github.com/schemaorg/schemaorg/blob/main/README.md | 局所的な分かりやすさ優先、識別子変更の重さ、Pending 領域 |
| 9 | schema.org data/schema.ttl | https://github.com/schemaorg/schemaorg/blob/main/data/schema.ttl | `:supersededBy` の実例（88か所） |
| 10 | IAB Tech Lab Taxonomies README | https://github.com/InteractiveAdvertisingBureau/Taxonomies | メジャー／マイナー版の方針、作業部会による管理 |
| 11 | dbt: data tests（accepted_values） | https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/reference/resource-properties/data-tests.md | 許可値テスト |
| 12 | dbt: snapshots | https://github.com/dbt-labs/docs.getdbt.com/blob/current/website/docs/docs/build/snapshots.md | SCD Type 2 |
| 13 | 18F Methods: Card sorting | https://github.com/18F/methods/blob/main/_methods/card-sorting.md | オープン／クローズドの手順、目的、所要時間 |
| 14 | GOV.UK Design System: Checkboxes | https://github.com/alphagov/govuk-design-system/blob/main/src/components/checkboxes/index.md | 'none' の置き方、排他動作、エラー文 |
| 15 | GOV.UK Design System: Radios | https://github.com/alphagov/govuk-design-system/blob/main/src/components/radios/index.md | 'None of the above' / 'I do not know'、並び順、初期選択の禁止 |
| 16 | GitLab Handbook: Evaluating navigation | https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/main/content/handbook/upstream-studios/experience-research/evaluating-navigation/index.md | ナビゲーション評価の共通指標（Effectiveness、Findability 等） |
| 17 | GitLab Handbook: Testing navigation: early Solution Validation | https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/main/content/handbook/upstream-studios/experience-research/early-solution-validation-process-for-navigation/index.md | ファーストクリックで IA の階層を確かめる、サンプル数 |
| 18 | Claude Docs: Ticket routing | https://platform.claude.com/docs/en/about-claude/use-case-guides/ticket-routing | カテゴリ定義と精度、LLM と従来 ML の選び方、20以上は階層、一貫性 95%、71%→93% |
| 19 | Claude Cookbook: Classification | https://platform.claude.com/cookbook/capabilities-classification-guide | カテゴリ説明、RAG と思考過程での精度（約70%→94%→97%）、混同行列 |
| 20 | GoEmotions README | https://github.com/google-research/google-research/blob/master/goemotions/README.md | 27感情＋Neutral、example_very_unclear、2人以上一致で学習 |
| 21 | scikit-learn cohen_kappa_score | https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/metrics/_classification.py | アノテーター間一致の指標 |
| 22 | cleanlab README | https://github.com/cleanlab/cleanlab/blob/master/README.md | ラベル誤り検出、confident learning |
| 23 | BERTopic README | https://github.com/MaartenGr/BERTopic/blob/master/README.md | 外れ値 -1、手動ラベル、統合と追跡、Guided/Zero-shot |
| 24 | Evidently README | https://github.com/evidentlyai/evidently/blob/main/README.md | データドリフト検出 |

### 開けなかったもの【未確認】

| 資料 | URL | 状況 |
|---|---|---|
| NN/g: Card Sorting / Tree Testing / Card Sorting vs Tree Testing / Taxonomy 101 | https://www.nngroup.com/articles/card-sorting-definition/ 、https://www.nngroup.com/articles/tree-testing/ 、https://www.nngroup.com/articles/card-sorting-tree-testing-differences/ 、https://www.nngroup.com/articles/taxonomy-101/ | 接続拒否。内容は書いていない |
| Rosenfeld, Morville, Arango『Information Architecture』（O'Reilly） | — | 本文未確認。ファセット分類・統制語彙の章の内容は書いていない |
| ANSI/NISO Z39.19-2005 (R2010) | https://www.niso.org/ （接続拒否） | 検索で書誌（単一言語の統制語彙の構築・表示・保守・管理の指針）のみ確認 |
| ISO 25964-1:2011 / 25964-2 | https://www.iso.org/ （接続拒否） | 検索で書誌のみ確認 |
| W3C SKOS Reference / SKOS Primer 本文 | https://www.w3.org/TR/skos-reference/ | 接続拒否。プロパティ定義は #7 で代替確認。整合性条件は未確認 |
| Google ML のデータラベリング資料（Machine Learning Crash Course 等） | https://developers.google.com/machine-learning | 接続拒否 |
| Google Cloud のラベラー向け指示書ガイド | https://cloud.google.com/ai-platform/data-labeling/docs/instructions | 取得したが本文が読めず |
| Jev（Typesafe 社の判定特化モデル） | 検索結果に出た typesafe.ai、mindstudio.ai 等 | 接続拒否。検索要約のみで、仕様は書いていない |
| GoEmotions 論文（arXiv:2005.00547） | https://arxiv.org/abs/2005.00547 | 接続拒否（README のみ確認） |
| Kimball の Slowly Changing Dimensions 原典 | https://www.kimballgroup.com/ | 接続拒否（dbt ドキュメントで代替） |
