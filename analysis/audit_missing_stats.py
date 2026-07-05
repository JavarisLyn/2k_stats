# -*- coding: utf-8 -*-
"""检查荣誉榜/数据榜 Top N 缺失的基础数据字段。"""
import csv
import os
import sys

from config import RESULTS

STAT_COLS = [
    "场均得分", "场均篮板", "场均助攻", "场均抢断", "场均盖帽",
    "场均失误", "投篮命中率", "出场总数",
]

HONORS_CSV = os.path.join(RESULTS, "goat_scores.csv")
STATS_CSV = os.path.join(RESULTS, "goat_scores_stats.csv")
ALL_CSV = os.path.join(RESULTS, "player_honors_all.csv")


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def top_n(path, score_col, n):
    rows = load(path)
    rows.sort(key=lambda r: -float(r[score_col]))
    return rows[:n]


def enrich(rows):
    hmap = {(r["名字"], r["姓氏"]): r for r in load(ALL_CSV)}
    out = []
    for r in rows:
        h = hmap.get((r["名字"], r["姓氏"]), {})
        merged = dict(r)
        for c in STAT_COLS:
            if not str(merged.get(c, "")).strip():
                merged[c] = h.get(c, "")
        out.append(merged)
    return out


def report(label, rows):
    print(f"\n=== {label} ===")
    any_miss = False
    for i, r in enumerate(rows, 1):
        miss = [c for c in STAT_COLS if not str(r.get(c, "")).strip()]
        if miss:
            any_miss = True
            print(f"  #{i:>2} {r['名字']} {r['姓氏']}: {', '.join(miss)}")
    if not any_miss:
        print("  (all complete)")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    honor = enrich(top_n(HONORS_CSV, "goat_score", n))
    stats = enrich(top_n(STATS_CSV, "goat_score_stats", n))
    report(f"Honor Top {n}", honor)
    report(f"Stats Top {n}", stats)


if __name__ == "__main__":
    main()
