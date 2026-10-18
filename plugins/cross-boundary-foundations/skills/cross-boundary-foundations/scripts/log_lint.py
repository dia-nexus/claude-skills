#!/usr/bin/env python3
"""
log_lint.py — ログ・イベントのサンプルを点検する

JSONL（1行に1つのJSON）のログやプロダクト分析イベントを読み、
設計の決めごとから外れている行を拾う。直すべき場所が分かるよう、行番号と理由を出す。

点検すること:
  - 必須フィールドの欠け（既定：timestamp, event。--require で変更）
  - イベント名の命名規則（既定：snake_case の object_action。--name-re で変更）
  - イベント名に混じった可変値（数字の連なり、UUID、メールなど）→ 属性に移すべき
  - ログレベルの値（--levels で許す値を指定。既定：TRACE DEBUG INFO WARN ERROR FATAL）
  - エラーなのに種別がない（level が ERROR 以上、または event に error/failed を含むのに error.type がない）
  - 個人情報らしき値（メールアドレス、日本の電話番号、カード番号らしき数字、パスワード・トークンらしきキー）
  - トレースIDの欠け（--trace-key があるとき）
  - トラッキングプランとの突き合わせ（--plan に Markdown か CSV。プランにないイベント、プランにあって一度も来ないイベント）
  - 記録してはいけない結果が、イベント名や画面名（screen_name、page_path、page_title など）から漏れていないか
    （--sensitive。既定の語：reject 否決 謝絶 denied declined approved 承認 審査結果 ng_limit。--sensitive-words で変更）

使い方:
  python3 log_lint.py events.jsonl
  python3 log_lint.py logs.jsonl --require timestamp,level,event,service,trace_id --trace-key trace_id
  python3 log_lint.py events.jsonl --plan tracking-plan.md --json

依存: Python 3.8+ の標準ライブラリだけ。
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict

DEF_LEVELS = ["TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL"]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_JP = re.compile(r"(?<!\d)0\d{1,4}-?\d{1,4}-?\d{3,4}(?!\d)")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
SECRET_KEYS = re.compile(r"(pass(word)?|passwd|secret|token|api[_-]?key|authorization|cookie|session)", re.I)
DEF_SENSITIVE = "reject,否決,謝絶,denied,declined,approved,承認,審査結果,ng_limit"
SCREEN_KEYS = re.compile(r"(screen|page|path|title|url|route)", re.I)
ALLOWED_ID_KEYS = re.compile(r"(trace_id|span_id|request_id|response_id|.*_pseudo_id|.*_id_hash)$", re.I)


def luhn(s):
    d = [int(c) for c in re.sub(r"\D", "", s)]
    if not 13 <= len(d) <= 19:
        return False
    tot = 0
    for i, x in enumerate(reversed(d)):
        if i % 2:
            x *= 2
            if x > 9:
                x -= 9
        tot += x
    return tot % 10 == 0


def get(d, path):
    cur = d
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def walk(d, prefix=""):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from walk(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            yield from walk(v, f"{prefix}[{i}]")
    else:
        yield prefix, d


def load_plan(path):
    names = set()
    text = open(path, encoding="utf-8").read()
    if path.endswith(".csv"):
        for row in csv.DictReader(text.splitlines()):
            n = row.get("event") or row.get("イベント名") or ""
            if n.strip():
                names.add(n.strip())
    else:
        # 見出し行の1列目が「イベント名」か event の表だけを読む（KPI表などを拾わない）
        in_event_table = False
        for line in text.splitlines():
            if not line.startswith("|"):
                in_event_table = False
                continue
            if re.match(r"^\|\s*:?-", line):
                continue
            cell = line.split("|")[1].strip().strip("`")
            if cell in ("イベント名", "event", "Event", "event_name"):
                in_event_table = True
                continue
            if in_event_table and re.match(r"^[a-z][a-z0-9_]*$", cell):
                names.add(cell)
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--require", default="timestamp,event", help="必須フィールド（ドット区切りで入れ子も可）")
    ap.add_argument("--event-key", default="event")
    ap.add_argument("--level-key", default="level")
    ap.add_argument("--levels", default=" ".join(DEF_LEVELS))
    ap.add_argument("--name-re", default=r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$", help="イベント名の規則（既定：snake_case で2語以上）")
    ap.add_argument("--trace-key", default="", help="トレースIDのキー。指定するとERROR以上の行で欠けを拾う")
    ap.add_argument("--plan", default="", help="トラッキングプラン（.md の表 か .csv）")
    ap.add_argument("--json", action="store_true", help="結果を JSON で出す")
    ap.add_argument("--sensitive", action="store_true", help="イベント名・画面名に結果を表す語が入っていないかを点検する")
    ap.add_argument("--sensitive-words", default=DEF_SENSITIVE, help="結果を表す語（カンマ区切り）")
    ap.add_argument("--max", type=int, default=20, help="種類ごとに表示する行の上限")
    a = ap.parse_args()

    req = [x.strip() for x in a.require.split(",") if x.strip()]
    levels = set(x.upper() for x in a.levels.split())
    name_re = re.compile(a.name_re)
    sens = [w.strip().lower() for w in a.sensitive_words.split(",") if w.strip()] if a.sensitive else []
    issues = defaultdict(list)
    events = Counter()
    n = 0
    for ln, line in enumerate(open(a.file, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        n += 1
        try:
            d = json.loads(line)
        except json.JSONDecodeError as e:
            issues["JSONとして読めない"].append((ln, str(e)))
            continue
        for r in req:
            if get(d, r) in (None, ""):
                issues["必須フィールドの欠け"].append((ln, r))
        ev = get(d, a.event_key)
        if isinstance(ev, str):
            events[ev] += 1
            if UUID.search(ev) or EMAIL.search(ev) or re.search(r"\d{3,}", ev):
                issues["イベント名に可変値（IDや数字）が混じっている → 属性へ"].append((ln, ev))
            elif not name_re.match(ev):
                issues["イベント名が命名規則に合わない"].append((ln, ev))
        if sens:
            hits = [(a.event_key, ev)] if isinstance(ev, str) else []
            hits += [(p, v) for p, v in walk(d) if isinstance(v, str) and SCREEN_KEYS.search(p.split(".")[-1])]
            for p, v in hits:
                if any(w in v.lower() for w in sens):
                    issues["結果を表す語がイベント名・画面名に入っている（自動計測で記録してはいけない結果が漏れる）"].append((ln, f"{p}={v}"))
        lv = get(d, a.level_key)
        if lv is not None and str(lv).upper() not in levels:
            issues["ログレベルの値が決めごとにない"].append((ln, str(lv)))
        is_err = (lv is not None and str(lv).upper() in {"ERROR", "FATAL", "CRITICAL"}) or (isinstance(ev, str) and re.search(r"(error|fail|exception)", ev))
        if is_err and not (get(d, "error.type") or get(d, "error_type") or get(d, "properties.error_type") or get(d, "error.code")):
            issues["エラーなのに種別がない（error.type / error.code / error_type / properties.error_type のどれか）"].append((ln, ev or str(lv)))
        if is_err and a.trace_key and not get(d, a.trace_key):
            issues["エラーなのにトレースIDがない"].append((ln, ev or str(lv)))
        for path, v in walk(d):
            key = path.split(".")[-1]
            if SECRET_KEYS.search(key) and v not in (None, "", False):
                issues["秘密情報らしきキーに値がある"].append((ln, path))
            if isinstance(v, str):
                if EMAIL.search(v):
                    issues["メールアドレスらしき値"].append((ln, path))
                if not ALLOWED_ID_KEYS.search(key) and PHONE_JP.search(v):
                    issues["電話番号らしき値"].append((ln, path))
                for m in CARD.finditer(v):
                    if luhn(m.group(0)):
                        issues["カード番号らしき値"].append((ln, path))
            elif isinstance(v, int) and len(str(v)) >= 13 and luhn(str(v)):
                issues["カード番号らしき値"].append((ln, path))

    plan_diff = {}
    if a.plan:
        plan = load_plan(a.plan)
        plan_diff = {"プランにないイベント": sorted(set(events) - plan), "プランにあるが来ていないイベント": sorted(plan - set(events))}

    if a.json:
        print(json.dumps({"lines": n, "events": dict(events), "issues": {k: v for k, v in issues.items()}, "plan": plan_diff}, ensure_ascii=False, indent=2))
        return 1 if issues or any(plan_diff.values()) else 0

    print(f"# ログ・イベントの点検：{a.file}（{n}行、イベント{len(events)}種類）\n")
    if not issues and not any(plan_diff.values()):
        print("問題は見つかりませんでした。")
        return 0
    for k, v in sorted(issues.items(), key=lambda x: -len(x[1])):
        print(f"## {k}（{len(v)}件）")
        for ln, what in v[:a.max]:
            print(f"- {ln}行目：{what}")
        if len(v) > a.max:
            print(f"- ほか {len(v) - a.max} 件")
        print()
    for k, v in plan_diff.items():
        if v:
            print(f"## {k}（{len(v)}件）")
            for e in v[:a.max]:
                print(f"- {e}")
            print()
    print("直し方は references/errorlog-guide.md の「3. ログを設計する」と references/errorlog-engineering.md の B-4・B-7・B-9 を参照。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
