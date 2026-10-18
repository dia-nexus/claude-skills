#!/usr/bin/env python3
"""
insight_digest.py — 気づきの台帳を束ね、持ち帰りの候補を出す

assets/insight-log.md の形（Markdown の表）を、1つ以上の案件ぶん読み、次を出す。

  - タグごとに、いくつの案件で出たか、根拠の数の合計、行のID
  - 持ち帰りの候補：--min-cases 以上の案件で出たタグ、または「製品の欠け」と見立てた行
  - 「未判断」のまま残っている行
  - 点検：タグが空の行、見立てが決まった値でない行、個人情報らしき値（メール、電話番号）を含む行

使い方:
  python3 insight_digest.py 案件A/insight-log.md 案件B/insight-log.md
  python3 insight_digest.py logs/*.md --min-cases 3
  python3 insight_digest.py logs/*.md --json
  python3 insight_digest.py logs/*.md --csv > insights.csv   # Claude Dashboards に添付する表

依存: Python 3.8+ の標準ライブラリだけ。
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict

VERDICTS = ["この顧客だけ", "設定で吸収できる", "業種で共通", "製品の欠け", "未判断"]
REQUIRED = ["ID", "案件", "気づき（観察した事実）", "タグ", "汎用化の見立て"]
PII = [
    ("メールアドレス", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("電話番号", re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")),
]


def read_rows(path):
    """気づきの表（REQUIRED の列をすべて持つ表）の行を返す。"""
    rows, cols = [], None
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if not line.startswith("|"):
                cols = None
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cols is None:
                if all(r in cells for r in REQUIRED):
                    cols = cells
                continue
            if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                continue
            row = dict(zip(cols, cells))
            row["_file"] = path
            rows.append(row)
    return rows


def count_of(text):
    m = re.search(r"\d+", text or "")
    return int(m.group()) if m else 0


def digest(rows, min_cases):
    by_tag = defaultdict(lambda: {"cases": set(), "evidence": 0, "ids": []})
    problems, undecided, product_gaps = [], [], []
    for r in rows:
        rid = r.get("ID", "?")
        tags = [t.strip() for t in re.split(r"[,、]", r.get("タグ", "")) if t.strip()]
        verdict = r.get("汎用化の見立て", "")
        if not tags:
            problems.append(f"{rid}: タグが空です（{r['_file']}）")
        if verdict not in VERDICTS:
            problems.append(f"{rid}: 汎用化の見立て「{verdict}」は決まった値ではありません（{' / '.join(VERDICTS)}）")
        for label, pat in PII:
            for v in r.values():
                if isinstance(v, str) and pat.search(v):
                    problems.append(f"{rid}: {label}らしき値があります。役割名に置き換えてください")
                    break
        if verdict == "未判断":
            undecided.append(rid)
        if verdict == "製品の欠け":
            product_gaps.append(rid)
        for t in tags:
            by_tag[t]["cases"].add(r.get("案件", ""))
            by_tag[t]["evidence"] += count_of(r.get("根拠の数", ""))
            by_tag[t]["ids"].append(rid)

    tags = sorted(
        ({"tag": t, "cases": sorted(v["cases"]), "case_count": len(v["cases"]),
          "evidence": v["evidence"], "ids": v["ids"]} for t, v in by_tag.items()),
        key=lambda x: (-x["case_count"], -x["evidence"], x["tag"]),
    )
    candidates = [t for t in tags if t["case_count"] >= min_cases]
    return {"tags": tags, "candidates": candidates, "product_gaps": product_gaps,
            "undecided": undecided, "problems": problems, "rows": len(rows)}


def main():
    ap = argparse.ArgumentParser(description="気づきの台帳を束ね、持ち帰りの候補を出す")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--min-cases", type=int, default=3, help="候補にする案件の数（既定 3）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--csv", action="store_true", help="タグごとの表を CSV で出す（ダッシュボードに添付する用）")
    a = ap.parse_args()

    rows = []
    for p in a.files:
        try:
            rows.extend(read_rows(p))
        except OSError as e:
            print(f"読めませんでした: {p}（{e}）", file=sys.stderr)
            return 2
    if not rows:
        print("気づきの表が見つかりませんでした。列名（ID、案件、気づき（観察した事実）、タグ、汎用化の見立て）を確かめてください。")
        return 1

    d = digest(rows, a.min_cases)
    if a.csv:
        if d["problems"]:
            for p in d["problems"]:
                print(p, file=sys.stderr)
            print("点検で問題が見つかったので CSV を出しませんでした。直してから添付してください。", file=sys.stderr)
            return 1
        w = csv.writer(sys.stdout)
        w.writerow(["tag", "case_count", "evidence", "candidate", "product_gap_rows", "row_ids"])
        gaps = set(d["product_gaps"])
        for t in d["tags"]:
            w.writerow([t["tag"], t["case_count"], t["evidence"],
                        "yes" if t["case_count"] >= a.min_cases else "no",
                        len([i for i in t["ids"] if i in gaps]), " ".join(t["ids"])])
        return 0
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return 1 if d["problems"] else 0

    print(f"# 台帳のまとめ（{len(a.files)}ファイル、{d['rows']}行）\n")
    print(f"## 持ち帰りの候補（{a.min_cases}案件以上で出たタグ）\n")
    if d["candidates"]:
        for t in d["candidates"]:
            print(f"- {t['tag']}：{t['case_count']}案件、根拠 {t['evidence']}（{', '.join(t['ids'])}）")
    else:
        print("- まだありません")
    print("\n## 「製品の欠け」と見立てた行\n")
    print("- " + (", ".join(d["product_gaps"]) if d["product_gaps"] else "ありません"))
    print("\n## タグごとの数\n")
    print("| タグ | 案件の数 | 根拠の数 | 行 |\n|---|---|---|---|")
    for t in d["tags"]:
        print(f"| {t['tag']} | {t['case_count']} | {t['evidence']} | {', '.join(t['ids'])} |")
    print("\n## 未判断のまま\n")
    print("- " + (", ".join(d["undecided"]) if d["undecided"] else "ありません"))
    print("\n## 点検\n")
    if d["problems"]:
        for p in d["problems"]:
            print(f"- {p}")
    else:
        print("- 問題は見つかりませんでした")
    print("\n点検で分かるのは台帳の形までです。気づきが正しいか、持ち帰ってよいかは人が確かめてください。")
    return 1 if d["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
