# トラッキングプラン：＜プロダクト／機能＞

版：v1（変更したら版を上げ、変更履歴に書く）
承認者（持ち主）：
命名規則：object_action の snake_case（例：signup_form_submitted）。イベント名に ID や数字などの可変値を入れない

## KPI から逆算する

| ユーザーの成功（ゴール） | 必須通過点 | 行動フロー | KPI（計算式） |
|---|---|---|---|
|  |  |  |  |

## イベント

| イベント名 | なぜ取るか（どのKPIのためか） | いつ発火するか（押した時点／成功した時点） | プロパティ（名前：型：例） | 個人情報を含むか・同意が要るか | 持ち主 | 版 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## エラーのイベント

| イベント名 | 発火条件 | プロパティ（error_type、field、recoverable、trace_id など） | 見る指標（発生率・回復率・エラー後の離脱） |
|---|---|---|---|
| form_error_shown |  |  |  |

## AI機能の反応（AI機能があるとき）

| イベント名 | 意味（成功か失敗か、KPIから決める） | 結ぶID（response_id） |
|---|---|---|
| ai_response_accepted |  |  |
| ai_response_edited |  |  |
| ai_response_regenerated |  |  |
| ai_response_rejected |  |  |

## データの質

- 社内・テストのアクセスを除く方法：
- ユーザーIDの統一（ログイン前後）：
- 到着の確認（イベントが届いているかの監視）：

## 回避策と示唆のイベント（持ち帰りのため）

製品が足りていない場所を、利用者の回避策から拾う。KPIのためではなく、気づきの台帳に流すためのイベント。最初から入れておかないと、あとから作れない。

| イベント名 | 何の回避策の痕跡か | プロパティ（名前：型：例） | 台帳のタグ |
|---|---|---|---|
| list_exported | 一覧や絞り込みが足りず、表計算で作業している | screen：string：approval_queue、row_count：int：48 | 回避策, 一覧の不足 |
| other_option_selected | 選択肢が足りない | field：string：expense_category、has_free_text：bool：true | 選択肢の不足, その他の多用 |
| ai_decision_overridden | AIの判定が業務に合っていない | response_id：string、from：string：returned、to：string：approved | AIの誤り |
| permission_exception_requested | 権限の線が業務の実態と合っていない | role：string：member、action：string：edit_after_approval | 権限の不足 |
| free_text_note_added | 決まった項目に入らない情報がある | field：string：return_reason、length_bucket：string：50-200 | 項目の不足 |

自由記述の本文は記録しない。長さの区分と、どの欄かだけを残す。

## 変更履歴

| 日付 | 版 | 変更 | 理由 |
|---|---|---|---|
