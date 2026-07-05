# -*- coding: utf-8 -*-
"""按 algo.md 荣誉版权重计算 GOAT Score（1976 及以前赛季 ×0.7）。"""
import csv
import json
import os
import sys

from config import EXTRACT_HONORS_DIR, RESULTS
from extract_honors import AWARD_FILES, load_csv, team_key

EXTRACT_DIR = EXTRACT_HONORS_DIR
HONORS_CSV = os.path.join(RESULTS, "player_honors_all.csv")
OUT_CSV = os.path.join(RESULTS, "goat_scores.csv")
OUT_JSON = os.path.join(RESULTS, "goat_scores.json")

WEIGHTS = {
    "MVP": 10,
    "FMVP": 15,
    "总冠军": 5,
    "最佳防守球员": 5,
    "最佳新秀": 1,
    "得分王": 6,
    "篮板王": 3,
    "助攻王": 3,
    "抢断王": 2,
    "盖帽王": 2,
    "最佳一阵": 5,
    "最佳二阵": 3,
    "最佳三阵": 2,
    "防一阵": 3,
    "防二阵": 2,
}

SCORE_COLS = list(WEIGHTS.keys())
DISCOUNT_END_YEAR = 1976
DISCOUNT = 0.7


def season_end_year(season):
    parts = (season or "").strip().split("-")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    if parts and parts[0].isdigit():
        return int(parts[0])
    return 9999


def season_mult(season):
    return DISCOUNT if season_end_year(season) <= DISCOUNT_END_YEAR else 1.0


def build_championship_seasons(extract_dir):
    finals_path = os.path.join(extract_dir, "总决赛历史.csv")
    champions = {}
    player_rings = set()

    if os.path.isfile(finals_path):
        for row in load_csv(finals_path):
            season = (row.get("赛季") or "").strip()
            champ = team_key(row.get("冠军球队城市", ""), row.get("冠军球队名称", ""))
            if season and champ[1]:
                champions[season] = champ
            first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
            last = (row.get("姓氏") or "").strip()
            if first and last and season:
                player_rings.add((first, last, season))

    for fname, _ in AWARD_FILES:
        if fname == "总决赛历史.csv":
            continue
        path = os.path.join(extract_dir, fname)
        if not os.path.isfile(path):
            continue
        for row in load_csv(path):
            first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
            last = (row.get("姓氏") or "").strip()
            season = (row.get("赛季") or "").strip()
            city = row.get("球队城市", "")
            team = row.get("球队名称", "")
            if not (first and last and season and team):
                continue
            champ = champions.get(season)
            if champ and team_key(city, team) == champ:
                player_rings.add((first, last, season))

    return player_rings


def load_honor_counts(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for row in rows:
        clean = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        key = (clean.get("名字", ""), clean.get("姓氏", ""))
        out[key] = {col: int(clean.get(col, 0) or 0) for col in SCORE_COLS}
    return out


def calc_discounted_scores(extract_dir):
    breakdown = {}

    def add_pts(first, last, col, season):
        k = (first, last)
        if k not in breakdown:
            breakdown[k] = {c: 0.0 for c in SCORE_COLS}
        breakdown[k][col] += WEIGHTS[col] * season_mult(season)

    for fname, award in AWARD_FILES:
        if award not in WEIGHTS:
            continue
        path = os.path.join(extract_dir, fname)
        if not os.path.isfile(path):
            continue
        for row in load_csv(path):
            first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
            last = (row.get("姓氏") or "").strip()
            season = (row.get("赛季") or "").strip()
            if not (first and last and season):
                continue
            add_pts(first, last, award, season)

    for first, last, season in build_championship_seasons(extract_dir):
        add_pts(first, last, "总冠军", season)

    return breakdown


def main():
    extract_dir = sys.argv[1] if len(sys.argv) > 1 else EXTRACT_DIR
    honor_counts = load_honor_counts(HONORS_CSV)
    discounted = calc_discounted_scores(extract_dir)

    all_keys = set(honor_counts.keys()) | set(discounted.keys())
    results = []
    for key in all_keys:
        first, last = key
        counts = honor_counts.get(key, {c: 0 for c in SCORE_COLS})
        bd = discounted.get(key, {c: 0.0 for c in SCORE_COLS})
        total = round(sum(bd.values()), 2)
        row = {
            "名字": first,
            "姓氏": last,
            "goat_score": total,
        }
        for col in SCORE_COLS:
            row[col] = counts.get(col, 0)
            row[f"{col}_分"] = round(bd.get(col, 0.0), 2)
        results.append(row)

    results.sort(key=lambda r: (-r["goat_score"], r["姓氏"], r["名字"]))

    csv_fields = (
        ["名字", "姓氏", "goat_score"]
        + SCORE_COLS
        + [f"{c}_分" for c in SCORE_COLS]
    )
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader()
        w.writerows(results)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "weights": WEIGHTS,
                "discount": {"end_year": DISCOUNT_END_YEAR, "multiplier": DISCOUNT},
                "source_honors": HONORS_CSV,
                "source_extract": extract_dir,
                "players": [
                    {
                        "名字": r["名字"],
                        "姓氏": r["姓氏"],
                        "goat_score": r["goat_score"],
                        "honors": {c: r[c] for c in SCORE_COLS},
                        "breakdown": {c: r[f"{c}_分"] for c in SCORE_COLS},
                    }
                    for r in results
                ],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Wrote {OUT_CSV} ({len(results)} players)")
    print(f"Wrote {OUT_JSON}")
    print(f"规则: 赛季结束年<={DISCOUNT_END_YEAR} 的荣誉得分 ×{DISCOUNT}")
    print("\nTop 20 GOAT Score (荣誉版):")
    print(f"{'#':>3} {'球员':<24} {'分数':>8}")
    print("-" * 38)
    for i, r in enumerate(results[:20], 1):
        name = f"{r['名字']} {r['姓氏']}"
        print(f"{i:>3} {name:<24} {r['goat_score']:>8.2f}")


if __name__ == "__main__":
    main()
