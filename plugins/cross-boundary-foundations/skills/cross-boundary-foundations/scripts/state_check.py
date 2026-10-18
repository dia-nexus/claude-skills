#!/usr/bin/env python3
"""
state_check.py — 状態遷移表を点検する

assets/state-table.md の形（Markdown の表）か CSV を読み、次を拾う。

  - 遷移に出てくるのに、状態の表で定義されていない状態
  - 定義されているのに、どの遷移にも出てこない状態
  - 開始状態から辿り着けない状態（--start で開始状態を指定。既定は最初の状態）
  - 終端でないのに出口がない状態（行き止まり）
  - 終端なのに出口がある状態
  - 処理中の状態に、失敗したときの出口がない（出口が一本だけ）
  - 「誰が」が空の遷移
  - 三層の対応表で、画面ラベルや KPI 段階が空の状態、対応表にない状態
  - 「戻せるか」が「いいえ」の遷移を AI に許している（5章の表があるとき）
  - 状態が多すぎる（--max-states、既定 20。エラーの内訳は分類の表へ回す）
  - 処理中の状態に、結果が分からないとき（タイムアウト・通信断）の出口が書かれていない
  - 三層の対応表で、同じ上流の値（DB や外部 API の値）に複数の状態が重なっている
    （列名に「上流」「DB」などを含む列。--upstream-col で列名の一部を指定できる）

使い方:
  python3 state_check.py state-table.md
  python3 state_check.py state-table.md --start draft --json
  python3 state_check.py transitions.csv          # 列：from,to,操作,誰が（ほかは任意）

依存: Python 3.8+ の標準ライブラリだけ。
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict, deque


def md_tables(text):
    """見出し（## 〜）ごとに表を集める。{見出し: [行dict, ...]}"""
    out, head, rows, cols = {}, "", None, None
    for line in text.splitlines() + [""]:
        if not line.startswith("|") and cols is not None:
            out.setdefault(head, []).extend(rows)
            cols = None
        if line.startswith("#"):
            head = line.lstrip("#").strip()
        if line.startswith("|"):
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            if cols is None:
                cols = cells
                rows = []
            elif re.match(r"^:?-+:?$", cells[0] or "-"):
                continue
            else:
                rows.append(dict(zip(cols, cells)))
    return out


def find(tables, *keys):
    for h, rows in tables.items():
        if any(k in h for k in keys) and rows:
            return rows
    return []


UNKNOWN_WORDS = re.compile(r"(タイムアウト|通信|結果不明|分からない|照会|上限|応答なし|届かない|timeout|network|communication|unknown)", re.I)
UPSTREAM_COLS = ("上流", "DB", "システムの値", "内部の値")
MARK = re.compile(r"【[^】]*】")


def normalize_upstream(v):
    """重なりを比べるための上流の値。印・空白・？を外し、比べられない値は空にする。"""
    v = MARK.sub("", v).replace("`", "")
    v = re.sub(r"[?？]", "", v)
    v = re.sub(r"\s+", "", v)
    if not v or v in ("—", "-", "不明") or v.startswith("（") or v.startswith("("):
        return ""
    return v


def col(row, *names):
    for n in names:
        for k, v in row.items():
            if k.lower() == n.lower() or n in k:
                return v.strip()
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--start", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-states", type=int, default=20, help="これを超えたら状態の切り方を見直すよう知らせる")
    ap.add_argument("--upstream-col", default="", help="上流の値の列名に含まれる文字（既定：上流／DB／システムの値／内部の値）")
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read()

    if a.file.endswith(".csv"):
        trans = list(csv.DictReader(text.splitlines()))
        states_rows, layer_rows, ai_rows = [], [], []
    else:
        t = md_tables(text)
        states_rows = find(t, "状態（内部）", "1. 状態")
        trans = find(t, "2. 遷移") or [r for h, rs in t.items() if h.endswith("遷移") and "AI" not in h for r in rs]
        layer_rows = find(t, "三層")
        ai_rows = find(t, "AI に許す")

    issues = defaultdict(list)
    kinds = {col(r, "状態ID", "state"): col(r, "種類", "kind") for r in states_rows}
    kinds.pop("", None)
    edges = defaultdict(list)
    seen = set()
    for i, r in enumerate(trans, 1):
        f, to = col(r, "from"), col(r, "to")
        if not f or not to:
            issues["from / to が空の遷移"].append(f"{i}行目")
            continue
        edges[f].append((to, r))
        seen.update([f, to])
        if not col(r, "誰が", "actor") or col(r, "誰が", "actor") in ("-", "—"):
            issues["「誰が」が空の遷移"].append(f"{f} → {to}")

    defined = set(kinds)
    if defined:
        for s in sorted(seen - defined):
            issues["遷移にあるが、状態の表で定義されていない"].append(s)
        for s in sorted(defined - seen):
            issues["定義されているが、どの遷移にも出てこない"].append(s)

    n_states = len(defined or seen)
    if n_states > a.max_states:
        issues[f"状態が多すぎる（{a.max_states} 個超。画面の出し分けに要る単位にまとめ、エラーの内訳は分類の表へ回す）"].append(f"{n_states} 個")

    order = list(kinds) or [col(r, "from") for r in trans]
    start = a.start or (order[0] if order else "")
    if start:
        reach, q = {start}, deque([start])
        while q:
            for to, _ in edges[q.popleft()]:
                if to not in reach:
                    reach.add(to)
                    q.append(to)
        for s in sorted((defined or seen) - reach):
            issues[f"開始状態（{start}）から辿り着けない"].append(s)

    for s in sorted(defined or seen):
        k = kinds.get(s, "")
        out = edges.get(s, [])
        if "終端" in k and out:
            issues["終端なのに出口がある"].append(f"{s} → {', '.join(t for t, _ in out)}")
        if "終端" not in k and not out and (k or not defined):
            issues["終端でないのに出口がない（行き止まり）"].append(s)
        if "処理中" in k and len(out) < 2:
            issues["処理中なのに失敗したときの出口がない"].append(s)
        if "処理中" in k and out and not any(
            UNKNOWN_WORDS.search(" ".join([col(r, "条件"), col(r, "操作"), t])) for t, r in out
        ):
            issues["処理中なのに、結果が分からないとき（タイムアウト・通信断・通知が来ない）の出口が書かれていない"].append(s)

    if layer_rows:
        mapped = set()
        upstream = defaultdict(list)
        up_words = (a.upstream_col,) if a.upstream_col else UPSTREAM_COLS
        up_key = next((k for k in layer_rows[0] if any(w in k for w in up_words)), None)
        for r in layer_rows:
            s = col(r, "状態ID", "state")
            mapped.add(s)
            for k, v in r.items():
                if k != next(iter(r)) and v in ("", "?", "？"):
                    issues["三層の対応に空欄がある（見えないなら「（見えない）」、数えないなら「—」と書く）"].append(f"{s}：{k}")
            if up_key:
                v = normalize_upstream(r.get(up_key, ""))
                if v:
                    upstream[v].append(s)
        for s in sorted(defined - mapped):
            issues["三層の対応表にない状態"].append(s)
        for v, ss in upstream.items():
            if len(ss) > 1:
                issues["同じ上流の値に複数の状態が重なっている（上流の値だけでは画面を決められない。理由コードか画面向けの結果コードが要る）"].append(f"{v}：{', '.join(ss)}")

    irrev = {(col(r, "from"), col(r, "to")) for r in trans if col(r, "戻せるか").startswith("いいえ")}
    for r in ai_rows:
        m = re.findall(r"[A-Za-z_][\w]*", col(r, "遷移"))
        allow = col(r, "AI に許すか", "AI")
        if len(m) >= 2 and allow.startswith("許す"):
            for to in m[1:]:
                if (m[0], to) in irrev and not col(r, "人の承認").startswith("要"):
                    issues["戻せない遷移を、人の承認なしに AI に許している"].append(f"{m[0]} → {to}")

    if a.json:
        print(json.dumps({"states": sorted(defined or seen), "issues": issues}, ensure_ascii=False, indent=2))
        return 1 if issues else 0
    print(f"# 状態遷移表の点検：{a.file}（状態 {len(defined or seen)}、遷移 {len(trans)}）\n")
    if not issues:
        print("問題は見つかりませんでした。")
        return 0
    for k, v in issues.items():
        print(f"## {k}（{len(v)}件）")
        for x in v:
            print(f"- {x}")
        print()
    print("直し方は SKILL.md の「1. 状態とステータス」と references/state.md の E1・U6・A2 を参照。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
