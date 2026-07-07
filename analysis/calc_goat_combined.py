# -*- coding: utf-8 -*-
"""荣誉版 + 数据版 GOAT 综合分（7:3，Min-Max 归一化）。"""
import csv
import json
import os

from config import RESULTS

HONOR_CSV = os.path.join(RESULTS, "goat_scores.csv")
STATS_CSV = os.path.join(RESULTS, "goat_scores_stats.csv")
OUT_CSV = os.path.join(RESULTS, "goat_scores_combined.csv")
OUT_JSON = os.path.join(RESULTS, "goat_scores_combined.json")

HONOR_WEIGHT = 0.7
STATS_WEIGHT = 0.3


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [
            {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def parse_float(val, default=None):
    if val is None or val == "":
        return default
    return float(val)


def minmax_to_100(values):
    nums = {k: (v if v is not None else 0.0) for k, v in values.items()}
    lo = min(nums.values())
    hi = max(nums.values())
    if hi == lo:
        return {k: (100.0 if v > 0 else 0.0) for k, v in nums.items()}
    return {k: (v - lo) / (hi - lo) * 100.0 for k, v in nums.items()}


def main():
    honor_rows = load_csv(HONOR_CSV)
    stats_rows = load_csv(STATS_CSV)

    stats_by_key = {
        (r["名字"], r["姓氏"]): parse_float(r.get("goat_score_stats"))
        for r in stats_rows
    }

    keys = [(r["名字"], r["姓氏"]) for r in honor_rows]
    honor_raw = {
        k: parse_float(next(r["goat_score"] for r in honor_rows if (r["名字"], r["姓氏"]) == k))
        for k in keys
    }
    stats_raw = {k: stats_by_key.get(k) for k in keys}

    honor_norm = minmax_to_100(honor_raw)
    stats_with_data = {k: v for k, v in stats_raw.items() if v is not None}
    stats_norm_partial = minmax_to_100(stats_with_data) if stats_with_data else {}
    stats_norm = {k: stats_norm_partial.get(k, 0.0) for k in keys}

    results = []
    for k in keys:
        h_raw = honor_raw[k]
        s_raw = stats_raw.get(k)
        h_n = round(honor_norm[k], 2)
        s_n = round(stats_norm[k], 2)
        combined = round(HONOR_WEIGHT * h_n + STATS_WEIGHT * s_n, 2)
        first, last = k
        results.append({
            "名字": first,
            "姓氏": last,
            "goat_score_combined": combined,
            "荣誉分": round(h_raw, 2),
            "荣誉归一化": h_n,
            "数据分": round(s_raw, 2) if s_raw is not None else "",
            "数据归一化": s_n if s_raw is not None else "",
        })

    results.sort(key=lambda r: (-r["goat_score_combined"], r["姓氏"], r["名字"]))

    fields = [
        "名字", "姓氏", "goat_score_combined",
        "荣誉分", "荣誉归一化", "数据分", "数据归一化",
    ]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)

    honor_vals = list(honor_raw.values())
    stats_vals = [v for v in stats_raw.values() if v is not None]
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {
                "weights": {"荣誉": HONOR_WEIGHT, "数据": STATS_WEIGHT},
                "normalization": "min-max → 0~100（数据版仅在有数据分的球员间计算）",
                "honor_range": [min(honor_vals), max(honor_vals)],
                "stats_range": [min(stats_vals), max(stats_vals)],
                "players": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Wrote {OUT_CSV}")
    print(f"荣誉权重 {HONOR_WEIGHT} : 数据权重 {STATS_WEIGHT}")
    print(f"荣誉分范围: {min(honor_vals):.1f} ~ {max(honor_vals):.1f}")
    print(f"数据分范围: {min(stats_vals):.2f} ~ {max(stats_vals):.2f}")
    print("\nTop 20 综合 GOAT:")
    print(f"{'#':>3} {'球员':<22} {'综合':>6} {'荣誉归一':>7} {'数据归一':>7}")
    print("-" * 50)
    for i, r in enumerate(results[:20], 1):
        sn = r["数据归一化"] if r["数据归一化"] != "" else "  —"
        print(
            f"{i:>3} {r['名字']} {r['姓氏']:<18} "
            f"{r['goat_score_combined']:>6.2f} {r['荣誉归一化']:>7.1f} {sn:>7}"
        )


if __name__ == "__main__":
    main()
