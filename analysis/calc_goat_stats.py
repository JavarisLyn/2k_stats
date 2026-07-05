# -*- coding: utf-8 -*-
"""按 algo.md 数据版权重计算 GOAT Score（含出场耐久系数）。"""
import csv
import json
import os

from config import RESULTS

HONORS_CSV = os.path.join(RESULTS, "player_honors_all.csv")
OUT_CSV = os.path.join(RESULTS, "goat_scores_stats.csv")
OUT_JSON = os.path.join(RESULTS, "goat_scores_stats.json")

WEIGHTS = {
    "场均得分": 1.0,
    "场均篮板": 0.8,
    "场均助攻": 1.3,
    "场均抢断": 1.9,
    "场均盖帽": 1.5,
    "场均失误": -1.9,
}

GAMES_REF = 1000
DURABILITY_ALPHA = 0.4

STAT_COLS = list(WEIGHTS.keys())
EXTRA_COLS = ["投篮命中率", "出场总数"]


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [
            {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def parse_num(val):
    if val is None or val == "":
        return None
    return float(val)


def durability_mult(games):
    if games is None or games <= 0:
        return 1.0
    return (games / GAMES_REF) ** DURABILITY_ALPHA


def calc_per_game_score(rec):
    breakdown = {}
    total = 0.0
    used = 0
    for col, w in WEIGHTS.items():
        v = parse_num(rec.get(col))
        if v is None:
            breakdown[col] = None
            continue
        pts = v * w
        breakdown[col] = round(pts, 3)
        total += pts
        used += 1
    return round(total, 2), breakdown, used


def main():
    rows = load_csv(HONORS_CSV)
    results = []

    for rec in rows:
        per_game, breakdown, used = calc_per_game_score(rec)
        if used == 0:
            continue
        games = parse_num(rec.get("出场总数"))
        dur = round(durability_mult(games), 4)
        final = round(per_game * dur, 2)

        row = {
            "名字": rec["名字"],
            "姓氏": rec["姓氏"],
            "goat_score_stats": final,
            "场均综合分": per_game,
            "耐久系数": dur,
        }
        for col in STAT_COLS + EXTRA_COLS:
            row[col] = rec.get(col, "")
        for col in STAT_COLS:
            row[f"{col}_分"] = breakdown[col] if breakdown[col] is not None else ""
        results.append(row)

    results.sort(key=lambda r: (-r["goat_score_stats"], r["姓氏"], r["名字"]))

    csv_fields = (
        ["名字", "姓氏", "goat_score_stats", "场均综合分", "耐久系数"]
        + STAT_COLS
        + EXTRA_COLS
        + [f"{c}_分" for c in STAT_COLS]
    )
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader()
        w.writerows(results)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "weights": WEIGHTS,
                "durability": {
                    "formula": f"(出场总数 / {GAMES_REF}) ^ {DURABILITY_ALPHA}",
                    "games_ref": GAMES_REF,
                    "alpha": DURABILITY_ALPHA,
                    "missing_games_multiplier": 1.0,
                },
                "source": HONORS_CSV,
                "player_count": len(results),
                "players": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Wrote {OUT_CSV} ({len(results)} players)")
    print(f"耐久系数 = (出场 / {GAMES_REF})^{DURABILITY_ALPHA}，无出场=1.0")
    print("\nTop 20 GOAT Score (数据版):")
    print(f"{'#':>3} {'球员':<22} {'数据分':>7} {'场均综合':>7} {'耐久':>6} {'出场':>6}")
    print("-" * 55)
    for i, r in enumerate(results[:20], 1):
        g = r.get("出场总数", "")
        print(
            f"{i:>3} {r['名字']} {r['姓氏']:<18} "
            f"{r['goat_score_stats']:>7.2f} {r['场均综合分']:>7.2f} "
            f"{r['耐久系数']:>6.3f} {g:>6}"
        )


if __name__ == "__main__":
    main()
