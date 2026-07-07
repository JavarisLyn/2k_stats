# -*- coding: utf-8 -*-
"""Write canonical career stat CSVs from all_data.json (first-row signature match)."""
import csv
import json
import os
import shutil
import sys

# (名字, 姓氏, 数据) → canonical name; 数据为表首行
SIGNATURES = {
    ("Kevin", "Garnett", 61417.0): "生涯总上场时间",
    ("Mark", "Eaton", 3.5): "场均盖帽",
    ("Michael", "Jordan", 30.34): "场均得分",
    ("Kobe", "Bryant", 48087.0): "生涯总得分",
    ("Steve", "Kerr", 0.46): "三分命中率",
    ("Tyson", "Chandler", 5250.0): "总犯规数",
    ("Wilt", "Chamberlain", 118.0): "50分比赛数",
    ("Hakeem", "Olajuwon", 4046.0): "总盖帽数",
    ("Wilt", "Chamberlain", 32.0): "60分比赛次数",
    ("Wilt", "Chamberlain", 22.9): "场均篮板",
    ("Marcelo", "Huertas", 0.96): "罚球命中率",
    ("Wilt", "Chamberlain", 271.0): "40分比赛数",
    ("Wilt", "Chamberlain", 23924.0): "生涯总篮板",
    ("Kobe", "Bryant", 10477.0): "总罚球命中",
    ("Stephen", "Curry", 5438.0): "三分命中数",
    ("Wilt", "Chamberlain", 45.8): "场均上场时间",
    ("LeBron", "James", 184.0): "三双次数",
    ("Alvin", "Robertson", 2.7): "场均抢断",
    ("LeBron", "James", 17746.0): "投篮命中数",
    ("Magic", "Johnson", 11.2): "场均助攻",
    ("Kevin", "Garnett", 1757.0): "生涯总出场数",
    ("Travis", "Oliver", 0.64): "投篮命中率",
}

MERGE_FILES = [
    "场均得分.csv", "场均篮板.csv", "场均助攻.csv", "场均抢断.csv", "场均盖帽.csv",
    "投篮命中率.csv", "生涯总出场数.csv", "总失误数.csv",
    "生涯总得分.csv", "生涯总篮板.csv", "生涯总助攻.csv", "总抢断数.csv", "总盖帽数.csv",
]

FALLBACK_FROM_OLD = ["总失误数.csv", "总抢断数.csv", "生涯总助攻.csv"]

# merge 用到的表，首行球员用于校验是否误标
EXPECTED_FIRST = {
    "场均得分.csv": ("Michael", "Jordan"),
    "场均篮板.csv": ("Wilt", "Chamberlain"),
    "场均助攻.csv": ("Magic", "Johnson"),
    "场均抢断.csv": ("Alvin", "Robertson"),
    "场均盖帽.csv": ("Mark", "Eaton"),
    "投篮命中率.csv": ("Travis", "Oliver"),
    "生涯总出场数.csv": ("Kevin", "Garnett"),
    "生涯总得分.csv": ("Kobe", "Bryant"),
    "生涯总篮板.csv": ("Wilt", "Chamberlain"),
    "生涯总助攻.csv": ("John", "Stockton"),
    "总抢断数.csv": ("John", "Stockton"),
    "总盖帽数.csv": ("Hakeem", "Olajuwon"),
}


def first_player(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None, None
    r = rows[0]
    return (r.get("名字") or "").strip(), (r.get("姓氏") or "").strip()


def validate_merge_files(extract_dir):
    bad = []
    for fname, exp in EXPECTED_FIRST.items():
        path = os.path.join(extract_dir, fname)
        if not os.path.isfile(path):
            bad.append(f"{fname}: missing")
            continue
        got = first_player(path)
        if got != exp:
            bad.append(f"{fname}: expected {exp[0]} {exp[1]}, got {got[0]} {got[1]}")
    if bad:
        print("SIGNATURE CHECK FAILED:")
        for msg in bad:
            print(f"  !! {msg}")
        sys.exit(1)
    print("Signature check: all merge files OK")


def sig_key(data):
    if not data:
        return None
    r = data[0]
    if len(r) < 3:
        return None
    try:
        val = round(float(r[-1]), 2)
    except ValueError:
        return None
    return (r[0], r[1], val)


def match_name(data):
    key = sig_key(data)
    if key is None:
        return None
    return SIGNATURES.get(key)


def write_csv(path, headers, data):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(data)


def main():
    extract_dir = sys.argv[1]
    old_dir = sys.argv[2] if len(sys.argv) > 2 else None
    ad = os.path.join(extract_dir, "all_data.json")
    with open(ad, encoding="utf-8") as f:
        tables = json.load(f)["tables"]

    assigned = {}
    for t in tables:
        name = match_name(t["data"])
        if name and name not in assigned:
            assigned[name] = t

    all_stat_names = sorted(
        set(SIGNATURES.values())
        | {f.replace(".csv", "") for f in MERGE_FILES}
        | {f.replace(".csv", "") for f in FALLBACK_FROM_OLD}
    )
    for fn in os.listdir(extract_dir):
        base = fn.replace(".csv", "")
        if fn.endswith(".csv") and base in all_stat_names:
            os.remove(os.path.join(extract_dir, fn))

    for name, t in sorted(assigned.items()):
        write_csv(os.path.join(extract_dir, f"{name}.csv"), t["headers"], t["data"])
        print(f"  {name}.csv: {t['rows']} rows")

    if old_dir:
        for fname in FALLBACK_FROM_OLD:
            src = os.path.join(old_dir, fname)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(extract_dir, fname)
            shutil.copy2(src, dst)
            print(f"  {fname}: copied from old extract")

    missing_merge = [f for f in MERGE_FILES if not os.path.isfile(os.path.join(extract_dir, f))]
    if missing_merge:
        print("MISSING for merge:", ", ".join(missing_merge))
        sys.exit(1)
    validate_merge_files(extract_dir)
    print(f"\nOK: {len(assigned)} stat tables + fallbacks in {extract_dir}")


if __name__ == "__main__":
    main()
