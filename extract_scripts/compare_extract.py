# -*- coding: utf-8 -*-
"""Compare new honor extract against reference directory."""
import csv
import json
import os
import sys

REF = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extract", "20260705_230658")

# Row-count → canonical filename (from reference after CSV label fixes)
LINEUP_BY_ROWS = [
    (391, "最佳阵容1阵"),
    (389, "最佳阵容2阵"),
    (386, "最佳阵容1阵"),
    (384, "最佳阵容2阵"),
    (180, "最佳阵容3阵"),
    (175, "最佳阵容3阵"),
    (285, "最佳防守阵容2阵"),
    (284, "最佳防守阵容1阵"),
    (280, "最佳防守阵容1阵"),
    (279, "最佳防守阵容2阵"),
    (313, "新秀最佳阵容1阵"),
    (308, "新秀最佳阵容1阵"),
    (177, "新秀最佳阵容2阵"),
    (173, "新秀最佳阵容2阵"),
]

AWARD_BY_ROWS = {
    69: "常规赛MVP",
    68: "常规赛MVP",
    78: "总决赛历史",
    77: "总决赛历史",
    42: None,  # DPOY or 第六人 — disambiguate by content
    41: None,
    75: "最佳新秀",
    74: "最佳新秀",
    76: "得分王",
    75: "得分王",
    74: "助攻王",
    73: "篮板王",
    72: "上场时间王",
    51: None,  # 抢断王 or 盖帽王
    50: None,
    39: "进步最快球员",
    37: "进步最快球员",
    62: "最佳教练",
    61: "最佳教练",
}


def read_csv_info(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    return headers, rows


def hdr(path):
    return read_csv_info(path)[0]


def row_count(path):
    return len(read_csv_info(path)[1])


def guess_award_41(rows):
    text = str(rows[:5])
    if "Giannis" in text or "Kawhi" in text or "Duncan" in text:
        return "最佳防守球员"
    if "Edwards" in text or "Conley" in text:
        return "最佳第六人"
    return "进步最快球员"


def guess_51(rows, headers):
    if not rows:
        return "抢断王"
    try:
        val = float(rows[0][-1])
        return "盖帽王" if val >= 2.0 else "抢断王"
    except ValueError:
        return "抢断王"


def map_lineup(rows):
    for threshold, name in LINEUP_BY_ROWS:
        if rows == threshold:
            return name
    return None


def map_table(name, rows, headers, data_rows):
    if name not in ("Table1", "Table3", "Table8", "Table15", "Table18", "Table20") and not name.startswith("最佳阵容"):
        return name.replace(".csv", "") if name.endswith(".csv") else name

    if "位置" in headers:
        mapped = map_lineup(rows)
        if mapped:
            return mapped
        return name

    if rows in AWARD_BY_ROWS:
        mapped = AWARD_BY_ROWS[rows]
        if mapped:
            return mapped
        if rows in (41, 42):
            return guess_award_41(data_rows)
        if rows in (50, 51):
            return guess_51(data_rows, headers)

    if name == "Table15" or (rows in (41, 42) and "Giannis" in str(data_rows[:3])):
        return "最佳防守球员"
    if name == "Table18" or rows == 39:
        return "进步最快球员"
    if name == "Table20" or rows in (68, 69):
        return "常规赛MVP"
    if name == "Table3" or rows in (74, 75):
        return "最佳新秀"
    if name == "Table8" or rows in (61, 62):
        return "最佳教练"
    if name == "Table1":
        return guess_award_41(data_rows)

    return name


def main():
    new_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if not new_dir:
        print("Usage: compare_extract.py <new_extract_dir>")
        sys.exit(1)

    ref_files = sorted(f for f in os.listdir(REF) if f.endswith(".csv"))
    expected = {f: {"headers": hdr(os.path.join(REF, f)), "rows": row_count(os.path.join(REF, f))} for f in ref_files}

    print(f"Reference: {REF}")
    print(f"New:       {new_dir}\n")

    # Map new files from all_data.json
    ad_path = os.path.join(new_dir, "all_data.json")
    with open(ad_path, encoding="utf-8") as f:
        tables = json.load(f)["tables"]

    mapped = {}
    for t in tables:
        canonical = map_table(t.get("name", ""), t["rows"], t["headers"], t["data"])
        mapped[canonical] = t

    print("=== FIELD CHECK (headers) ===")
    ok = mismatch = missing = 0
    for fname in ref_files:
        exp_h = expected[fname]["headers"]
        exp_r = expected[fname]["rows"]
        if fname not in mapped:
            print(f"  MISSING  {fname} (ref {exp_r} rows)")
            missing += 1
            continue
        t = mapped[fname]
        got_h = t["headers"]
        got_r = t["rows"]
        if got_h == exp_h:
            delta = got_r - exp_r
            flag = f" rows {got_r} (ref {exp_r}, delta {delta:+d})" if delta else f" rows {got_r} OK"
            print(f"  OK       {fname} | headers match{flag}")
            ok += 1
        else:
            print(f"  MISMATCH {fname}")
            print(f"           ref:  {exp_h}")
            print(f"           got:  {got_h}")
            mismatch += 1

    extra = set(mapped) - set(expected)
    if extra:
        print("\n=== UNMAPPED / EXTRA ===")
        for name in sorted(extra):
            t = mapped[name]
            print(f"  {name}: {t['rows']}x{t['cols']}")

    print(f"\nSummary: {ok} OK, {mismatch} header mismatch, {missing} missing")
    return mapped


if __name__ == "__main__":
    main()
