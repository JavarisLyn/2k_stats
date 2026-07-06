# -*- coding: utf-8 -*-
"""Rename mislabeled tables in a fresh extract dir and verify headers vs reference."""
import csv
import json
import os
import shutil
import sys

REF = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extract", "20260705_230658")

# Explicit renames from inject output → canonical honor CSV names
FILE_RENAMES = {
    "Table1.csv": "最佳第六人.csv",
    "Table3.csv": "最佳新秀.csv",
    "Table8.csv": "最佳教练.csv",
    "Table15.csv": "最佳防守球员.csv",
    "Table18.csv": "进步最快球员.csv",
    "Table20.csv": "常规赛MVP.csv",
    "最佳阵容.csv": "最佳防守阵容2阵.csv",
    "最佳阵容_15.csv": "最佳阵容1阵.csv",
    "最佳阵容_16.csv": "新秀最佳阵容1阵.csv",
    "最佳阵容_17.csv": "最佳阵容3阵.csv",
    "最佳阵容_18.csv": "最佳阵容2阵.csv",
    "最佳阵容_19.csv": "新秀最佳阵容2阵.csv",
    "最佳阵容_20.csv": "最佳防守阵容1阵.csv",
}

# Honor files used by analysis (exclude player_honors.csv)
HONOR_CSV = [
    "常规赛MVP.csv", "总决赛历史.csv", "最佳防守球员.csv", "最佳新秀.csv",
    "得分王.csv", "篮板王.csv", "助攻王.csv", "抢断王.csv", "盖帽王.csv",
    "上场时间王.csv", "最佳阵容1阵.csv", "最佳阵容2阵.csv", "最佳阵容3阵.csv",
    "最佳防守阵容1阵.csv", "最佳防守阵容2阵.csv", "最佳第六人.csv",
    "新秀最佳阵容1阵.csv", "新秀最佳阵容2阵.csv",
]


def read_header(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def data_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in f) - 1


def rename_files(extract_dir):
    for old, new in FILE_RENAMES.items():
        src = os.path.join(extract_dir, old)
        dst = os.path.join(extract_dir, new)
        if os.path.isfile(src):
            if os.path.isfile(dst):
                os.remove(dst)
            os.rename(src, dst)
            print(f"  rename: {old} -> {new}")


def verify(extract_dir):
    print("\n=== Header verification vs 20260705_230658 ===\n")
    print(f"{'File':<22} {'Headers':<8} {'Rows':<12} Notes")
    print("-" * 70)
    all_ok = True
    for fname in HONOR_CSV:
        ref_p = os.path.join(REF, fname)
        new_p = os.path.join(extract_dir, fname)
        if not os.path.isfile(new_p):
            print(f"{fname:<22} MISSING")
            all_ok = False
            continue
        ref_h = read_header(ref_p)
        new_h = read_header(new_p)
        ref_n = data_rows(ref_p)
        new_n = data_rows(new_p)
        h_ok = ref_h == new_h
        delta = new_n - ref_n
        note = "OK" if h_ok and delta == 0 else (
            f"headers {'OK' if h_ok else 'DIFF'}; rows {new_n} (ref {ref_n}, {delta:+d})"
        )
        if not h_ok:
            all_ok = False
            note += f" | ref={ref_h} got={new_h}"
        print(f"{fname:<22} {'OK' if h_ok else 'FAIL':<8} {new_n:>4} (ref {ref_n:>3})  {note}")
    return all_ok


def main():
    extract_dir = sys.argv[1]
    print(f"Renaming in {extract_dir}...")
    rename_files(extract_dir)
    ok = verify(extract_dir)
    # Update all_data.json table names for traceability
    ad = os.path.join(extract_dir, "all_data.json")
    if os.path.isfile(ad):
        with open(ad, encoding="utf-8") as f:
            data = json.load(f)
        row_to_name = {v.replace(".csv", ""): k.replace(".csv", "") for k, v in FILE_RENAMES.items()}
        for t in data.get("tables", []):
            old = t.get("name", "")
            for suffix, canonical in [
                ("Table1", "最佳第六人"), ("Table3", "最佳新秀"), ("Table8", "最佳教练"),
                ("Table15", "最佳防守球员"), ("Table18", "进步最快球员"), ("Table20", "常规赛MVP"),
                ("最佳阵容", "最佳防守阵容1阵"),
                ("最佳阵容_15", "最佳阵容1阵"), ("最佳阵容_16", "新秀最佳阵容1阵"),
                ("最佳阵容_17", "最佳阵容3阵"), ("最佳阵容_18", "最佳阵容2阵"),
                ("最佳阵容_19", "新秀最佳阵容2阵"), ("最佳阵容_20", "最佳防守阵容2阵"),
            ]:
                if old == suffix or old.startswith(suffix):
                    t["name"] = canonical
                    break
        with open(ad, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n" + ("All headers match reference." if ok else "Some differences — see above."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
