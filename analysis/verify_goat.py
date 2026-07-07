# -*- coding: utf-8 -*-
"""校验 player_honors_all 与 goat_scores 荣誉次数、得分一致性。"""
import csv
import os

from config import RESULTS

WEIGHTS = {
    "MVP": 15, "FMVP": 15, "总冠军": 7, "最佳防守球员": 5, "最佳新秀": 1,
    "得分王": 6, "篮板王": 3, "助攻王": 3, "抢断王": 2, "盖帽王": 2,
    "最佳一阵": 5, "最佳二阵": 3, "最佳三阵": 2, "防一阵": 4, "防二阵": 2,
}
COLS = list(WEIGHTS.keys())

HONORS_CSV = os.path.join(RESULTS, "player_honors_all.csv")
GOAT_CSV = os.path.join(RESULTS, "goat_scores.csv")


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [
            {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            for r in csv.DictReader(f)
        ]


def player_key(r):
    return (r["名字"], r["姓氏"])


def main():
    honors = load(HONORS_CSV)
    goat = load(GOAT_CSV)
    hm = {player_key(r): r for r in honors}
    gm = {player_key(r): r for r in goat}

    count_mismatch = []
    score_mismatch = []
    breakdown_mismatch = []

    for k, h in hm.items():
        g = gm.get(k)
        if not g:
            continue
        for c in COLS:
            hv = int(h.get(c, 0) or 0)
            gv = int(g.get(c, 0) or 0)
            if hv != gv:
                count_mismatch.append((k, c, hv, gv))
            if c == "总冠军":
                continue
            bp = float(g.get(f"{c}_分", 0) or 0)
            expected = hv * WEIGHTS[c]
            if abs(bp - expected) > 0.01 and abs(bp - expected * 0.7) > 0.01:
                breakdown_mismatch.append((k, c, hv, expected, bp))
        flat_cols = [c for c in COLS if c != "总冠军"]
        rough = sum(int(h.get(c, 0) or 0) * WEIGHTS[c] for c in flat_cols)
        gs = float(g.get("goat_score", 0) or 0)
        if rough > gs + 0.01:
            score_mismatch.append((h["名字"] + " " + h["姓氏"], rough, gs))

    print("=== 两表一致性检查 ===")
    print(f"player_honors_all: {len(honors)} 行")
    print(f"goat_scores:       {len(goat)} 行")
    print(f"仅在 honors 中: {sorted(set(hm) - set(gm))[:5]} ..." if set(hm) - set(gm) else "仅在 honors 中: 0")
    print(f"仅在 goat 中:   {sorted(set(gm) - set(hm))[:5]} ..." if set(gm) - set(hm) else "仅在 goat 中:   0")
    print(f"荣誉次数不一致: {len(count_mismatch)}")
    print(f"分项得分不一致: {len(breakdown_mismatch)}")
    print(f"goat_score 不一致: {len(score_mismatch)}")

    if count_mismatch:
        print("\n荣誉次数差异示例:")
        for x in count_mismatch[:10]:
            print(f"  {x[0][0]} {x[0][1]} | {x[1]}: honors={x[2]} goat={x[3]}")

    if score_mismatch:
        print("\ngoat_score 差异:")
        for name, exp, got in score_mismatch[:10]:
            print(f"  {name}: 应为 {exp}, 表中 {got}")

    if not count_mismatch and not breakdown_mismatch and not score_mismatch:
        print(f"\n结论: {len(honors)} 名球员全部一致（未计 1976 折扣时粗略对比）")

    for k in [("Bob", "Cousy"), ("Kobe", "Bryant"), ("Michael", "Jordan")]:
        if k not in hm or k not in gm:
            continue
        h, g = hm[k], gm[k]
        print(f"\n--- {k[0]} {k[1]} ---")
        for c in COLS:
            pts_col = f"{c}_分"
            print(f"  {c}: honors={h[c]} | goat={g[c]} | 得分={g[pts_col]}")
        print(f"  goat_score = {g['goat_score']}")


if __name__ == "__main__":
    main()
