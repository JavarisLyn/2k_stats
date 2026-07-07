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
    "MVP": 15,
    "FMVP": 15,
    "总冠军": 7,
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
    "防一阵": 4,
    "防二阵": 2,
}

# 总冠军分层：FMVP(15)+总冠军(7)=22 为基准
RING_BASE = WEIGHTS["FMVP"] + WEIGHTS["总冠军"]
RING_FMVP_SCORE = RING_BASE
RING_MVP_SCORE = RING_BASE * 0.9
RING_STAR_SCORE = RING_BASE * 0.8
RING_SUPPORT_SCORE = RING_BASE * 0.7
RING_ROLE_SCORE = RING_BASE * 0.2

# 非 FMVP 冠军：当赛季荣誉 → 分层得分（MVP 优先于主力/轮换）
RING_MVP_AWARDS = {"MVP"}
RING_STAR_AWARDS = {
    "最佳防守球员", "得分王", "篮板王", "助攻王", "最佳一阵", "防一阵",
}
RING_SUPPORT_AWARDS = {
    "抢断王", "盖帽王", "最佳二阵", "最佳三阵", "防二阵",
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


def build_fmvp_seasons(extract_dir):
    path = os.path.join(extract_dir, "总决赛历史.csv")
    fmvp = set()
    if os.path.isfile(path):
        for row in load_csv(path):
            season = (row.get("赛季") or "").strip()
            first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
            last = (row.get("姓氏") or "").strip()
            if season and first and last:
                fmvp.add((first, last, season))
    return fmvp


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


def build_honor_seasons(extract_dir, awards):
    """指定荣誉类型的球员-赛季集合。"""
    seasons = set()
    for fname, award in AWARD_FILES:
        if award not in awards:
            continue
        path = os.path.join(extract_dir, fname)
        if not os.path.isfile(path):
            continue
        for row in load_csv(path):
            first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
            last = (row.get("姓氏") or "").strip()
            season = (row.get("赛季") or "").strip()
            if first and last and season:
                seasons.add((first, last, season))
    return seasons


def ring_score(first, last, season, fmvp_seasons, mvp_seasons, star_seasons, support_seasons):
    key = (first, last, season)
    if key in fmvp_seasons:
        return RING_FMVP_SCORE
    if key in mvp_seasons:
        return RING_MVP_SCORE
    if key in star_seasons:
        return RING_STAR_SCORE
    if key in support_seasons:
        return RING_SUPPORT_SCORE
    return RING_ROLE_SCORE


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
    fmvp_seasons = build_fmvp_seasons(extract_dir)
    mvp_seasons = build_honor_seasons(extract_dir, RING_MVP_AWARDS)
    star_seasons = build_honor_seasons(extract_dir, RING_STAR_AWARDS)
    support_seasons = build_honor_seasons(extract_dir, RING_SUPPORT_AWARDS)

    def add_pts(first, last, col, season, points=None):
        k = (first, last)
        if k not in breakdown:
            breakdown[k] = {c: 0.0 for c in SCORE_COLS}
        pts = (points if points is not None else WEIGHTS[col]) * season_mult(season)
        breakdown[k][col] += pts

    for fname, award in AWARD_FILES:
        if award not in WEIGHTS or award == "总冠军":
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
        pts = ring_score(first, last, season, fmvp_seasons, mvp_seasons, star_seasons, support_seasons)
        add_pts(first, last, "总冠军", season, points=pts)

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
                "ring_scoring": {
                    "fmvp": RING_FMVP_SCORE,
                    "mvp": RING_MVP_SCORE,
                    "star": RING_STAR_SCORE,
                    "support": RING_SUPPORT_SCORE,
                    "role": RING_ROLE_SCORE,
                    "mvp_awards": sorted(RING_MVP_AWARDS),
                    "star_awards": sorted(RING_STAR_AWARDS),
                    "support_awards": sorted(RING_SUPPORT_AWARDS),
                },
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
    print(
        f"总冠军: FMVP={RING_FMVP_SCORE}, MVP={RING_MVP_SCORE}, "
        f"主力={RING_STAR_SCORE}, 轮换={RING_SUPPORT_SCORE}, 角色={RING_ROLE_SCORE}"
    )
    print("\nTop 20 GOAT Score (荣誉版):")
    print(f"{'#':>3} {'球员':<24} {'分数':>8}")
    print("-" * 38)
    for i, r in enumerate(results[:20], 1):
        name = f"{r['名字']} {r['姓氏']}"
        print(f"{i:>3} {name:<24} {r['goat_score']:>8.2f}")


if __name__ == "__main__":
    main()
