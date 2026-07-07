# -*- coding: utf-8 -*-
"""Write canonical honor CSVs from all_data.json (row-rank + content heuristics)."""
import csv
import json
import os
import re
import sys

HONOR_CSV = [
    "常规赛MVP.csv", "总决赛历史.csv", "最佳防守球员.csv", "最佳新秀.csv",
    "得分王.csv", "篮板王.csv", "助攻王.csv", "抢断王.csv", "盖帽王.csv",
    "上场时间王.csv", "最佳阵容1阵.csv", "最佳阵容2阵.csv", "最佳阵容3阵.csv",
    "最佳防守阵容1阵.csv", "最佳防守阵容2阵.csv", "最佳第六人.csv",
    "新秀最佳阵容1阵.csv", "新秀最佳阵容2阵.csv", "最佳教练.csv", "进步最快球员.csv",
]

LINEUP_ORDER = [
    "最佳阵容1阵.csv",
    "最佳阵容2阵.csv",
    "新秀最佳阵容1阵.csv",
    "最佳防守阵容1阵.csv",
    "最佳防守阵容2阵.csv",
    "最佳阵容3阵.csv",
    "新秀最佳阵容2阵.csv",
]


def write_csv(path, headers, data):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(data)


def sample_text(rows):
    return str(rows[:5])


def map_award(t):
    rows, cols, headers, data = t["rows"], t["cols"], t["headers"], t["data"]
    h = ",".join(headers)
    text = sample_text(data)

    if cols == 9 or "比分" in h or "冠军" in h:
        return "总决赛历史.csv"
    if cols == 7 and "位置" in h:
        return None
    if cols == 7:
        try:
            val = float(data[0][-1]) if data else 0
        except ValueError:
            val = 0
        if val > 35:
            return "上场时间王.csv"
        if val > 20:
            return "得分王.csv"
        if val > 13:
            return "篮板王.csv"
        if val > 10:
            return "助攻王.csv"
        if val >= 2:
            return "盖帽王.csv"
        return "抢断王.csv"
    if cols != 6:
        return None

    if rows in (68, 69, 70):
        return "常规赛MVP.csv"
    if rows in (74, 75, 76) and "Luka" in text or rows in (74, 75, 76):
        # ROY tables often ~75 rows; coach ~63; distinguish by row band
        if rows >= 75:
            return "最佳新秀.csv"
    if rows in (61, 62, 63):
        return "最佳教练.csv"
    if rows in (37, 38, 39, 40, 41, 42, 43):
        if "Giannis" in text or "Duncan" in text or "Kawhi" in text:
            return "最佳防守球员.csv"
        if "Edwards" in text or "Conley" in text or "Harden" in text:
            return "最佳第六人.csv"
        if "Jabari" in text or "Achiuwa" in text or "Thompson" in text:
            return "进步最快球员.csv"
        return "进步最快球员.csv"
    return None


def main():
    extract_dir = sys.argv[1]
    ad_path = os.path.join(extract_dir, "all_data.json")
    with open(ad_path, encoding="utf-8") as f:
        tables = json.load(f)["tables"]

    lineup = [t for t in tables if t["cols"] == 7 and "位置" in ",".join(t["headers"]) and t["rows"] > 100]
    lineup.sort(key=lambda t: -t["rows"])

    mapping = {}
    for t, fname in zip(lineup, LINEUP_ORDER):
        mapping[id(t)] = fname

    for t in tables:
        if id(t) in mapping:
            continue
        if t["rows"] <= 5:
            continue
        fname = map_award(t)
        if fname and fname not in mapping.values():
            mapping[id(t)] = fname

    # Remove old CSVs
    for fn in os.listdir(extract_dir):
        if fn.endswith(".csv"):
            os.remove(os.path.join(extract_dir, fn))

    for t in tables:
        fname = mapping.get(id(t))
        if not fname:
            continue
        write_csv(os.path.join(extract_dir, fname), t["headers"], t["data"])
        print(f"  {fname}: {t['rows']} rows")

    missing = [f for f in HONOR_CSV if not os.path.isfile(os.path.join(extract_dir, f))]
    if missing:
        print("\nMISSING:", ", ".join(missing))
        sys.exit(1)
    print(f"\nOK: {len(HONOR_CSV)} honor CSVs in {extract_dir}")


if __name__ == "__main__":
    main()
