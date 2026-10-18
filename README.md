# claude-skills

dia-nexus が作った Claude のスキルの一覧です。スキルごとにリポジトリを分けていて、中身と説明はそれぞれのリポジトリにあります。

| スキル | 中身 |
|---|---|
| [cross-boundary-foundations](https://github.com/dia-nexus/cross-boundary-foundations) | 事業、UX、システムのあいだで誰も決めていない決めごと（KPI、用語、状態、権限、コード値、エラーとログ、受け入れ条件、判断の記録、ダッシュボード）を仮決めし、表にして渡す。FDE、UXエンジニア、PdM 向け |

## 入れ方

### Claude Code

Claude Code の中で、次の2行を順に打ちます。`<スキル名>` は上の表の名前に置き換えます。

```
/plugin marketplace add dia-nexus/claude-skills
/plugin install <スキル名>@dia-nexus-skills
```

1行目は最初の1回だけで、2つ目からのスキルは2行目だけで入ります。2行目を打つと確認の画面が開くので、そこでインストールを選びます。

新しい版が出たら、`/plugin marketplace update dia-nexus-skills` で取り込めます。

### Claude のアプリ（claude.ai、デスクトップ）

アプリに上げる用の zip は、スキルごとのリポジトリの `dist/` にあります。入れ方は、それぞれの README に書いてあります。
