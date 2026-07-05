# -*- coding: utf-8 -*-
"""从 extract/<timestamp>/ 下的 CSV 汇总球员荣誉。"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

from config import EXTRACT_HONORS_DIR, PROJECT, RESULTS

EXTRACT_DIR = EXTRACT_HONORS_DIR
RESULTS_DIR = RESULTS

# CSV 文件名 -> 荣誉列名（不含最佳教练.csv）
AWARD_FILES = [
    ("常规赛MVP.csv", "MVP"),
    ("总决赛历史.csv", "FMVP"),
    ("最佳防守球员.csv", "最佳防守球员"),
    ("最佳新秀.csv", "最佳新秀"),
    ("得分王.csv", "得分王"),
    ("篮板王.csv", "篮板王"),
    ("助攻王.csv", "助攻王"),
    ("抢断王.csv", "抢断王"),
    ("盖帽王.csv", "盖帽王"),
    ("上场时间王.csv", "上场时间王"),
    ("最佳阵容1阵.csv", "最佳一阵"),
    ("最佳阵容2阵.csv", "最佳二阵"),
    ("最佳阵容3阵.csv", "最佳三阵"),
    ("最佳防守阵容1阵.csv", "防一阵"),
    ("最佳防守阵容2阵.csv", "防二阵"),
    ("最佳第六人.csv", "最佳第六人"),
    ("进步最快球员.csv", "进步最快"),
    ("新秀最佳阵容1阵.csv", "新秀一阵"),
    ("新秀最佳阵容2阵.csv", "新秀二阵"),
]
AWARD_COLS = [col for _, col in AWARD_FILES]

GAME5 = [
    "Kobe Bryant", "Tim Duncan", "Shaquille O'Neal",
    "Kevin Garnett", "Dirk Nowitzki",
]

TOP20 = [
    "Michael Jordan", "LeBron James", "Kareem Abdul-Jabbar", "Bill Russell",
    "Magic Johnson", "Larry Bird", "Wilt Chamberlain", "Shaquille O'Neal",
    "Tim Duncan", "Kobe Bryant", "Stephen Curry", "Hakeem Olajuwon",
    "Kevin Durant", "Oscar Robertson", "Jerry West", "Kevin Garnett",
    "Dirk Nowitzki", "Moses Malone", "Isiah Thomas", "Scottie Pippen",
]


def player_name(row):
    first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
    last = (row.get("姓氏") or "").strip()
    return f"{first} {last}".strip()


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_name(full):
    parts = full.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return full, ""


def team_key(city, name):
    return (city.strip().lower(), name.strip().lower())


def build_championship_counts(extract_dir):
    """按赛季球队与冠军队匹配，FMVP 赛季直接计一枚。"""
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

    counts = Counter()
    for first, last, _ in player_rings:
        counts[(first, last)] += 1
    return counts


def build_records(extract_dir):
    honors = defaultdict(lambda: Counter())
    name_parts = {}
    file_rows = {}
    ring_counts = build_championship_counts(extract_dir)

    for fname, award in AWARD_FILES:
        path = os.path.join(extract_dir, fname)
        if not os.path.isfile(path):
            print(f"skip missing: {fname}")
            continue
        rows = load_csv(path)
        file_rows[fname] = len(rows)
        for row in rows:
            first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
            last = (row.get("姓氏") or "").strip()
            name = f"{first} {last}".strip()
            if not name:
                continue
            honors[name][award] += 1
            name_parts[name] = (first, last)

    all_players = set(name_parts.values()) | set(ring_counts.keys())
    players = []
    for first, last in all_players:
        name = f"{first} {last}".strip()
        rec = {"名字": first, "姓氏": last}
        total = 0
        for col in AWARD_COLS:
            n = honors[name].get(col, 0) if name in honors else 0
            rec[col] = n
            total += n
        rec["总冠军"] = ring_counts.get((first, last), 0)
        rec["荣誉总计"] = total
        players.append(rec)

    players.sort(key=lambda r: (-r["荣誉总计"], r["姓氏"], r["名字"]))
    return honors, players, file_rows


def main():
    extract_dir = sys.argv[1] if len(sys.argv) > 1 else EXTRACT_DIR
    honors, players, file_rows = build_records(extract_dir)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_fields = ["名字", "姓氏", "MVP", "FMVP", "总冠军"] + AWARD_COLS[2:] + ["荣誉总计"]

    results_csv = os.path.join(RESULTS_DIR, "player_honors_all.csv")
    with open(results_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader()
        w.writerows(players)

    results_json = os.path.join(RESULTS_DIR, "player_honors_all.json")
    with open(results_json, "w", encoding="utf-8") as f:
        json.dump({"source": extract_dir, "player_count": len(players), "players": players},
                  f, ensure_ascii=False, indent=2)

    summary_path = os.path.join(extract_dir, "player_honors.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"source": extract_dir, "players": players}, f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(extract_dir, "player_honors.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader()
        w.writerows(players)

    lines = []
    W = lines.append
    W("=" * 60)
    W(f"荣誉汇总 — {extract_dir}")
    W("=" * 60)
    W("")
    W("## 源文件行数")
    for fname, _ in AWARD_FILES:
        if fname in file_rows:
            W(f"  {fname}: {file_rows[fname]} 行")
    W(f"\n共 {len(players)} 名球员")
    W(f"输出: {results_csv}")
    W("")

    W("## 游戏五位球员（2K 数据）")
    W("")
    W(f"{'球员':22s} " + " ".join(f"{a:>6s}" for a in [
        "MVP", "FMVP", "一阵", "二阵", "三阵", "防一", "防二",
        "得分", "篮板", "助攻", "抢断", "盖帽", "DPOY", "ROY",
    ]))
    cols = [
        "MVP", "FMVP", "最佳一阵", "最佳二阵", "最佳三阵",
        "防一阵", "防二阵", "得分王", "篮板王", "助攻王",
        "抢断王", "盖帽王", "最佳防守球员", "最佳新秀",
    ]
    for nm in GAME5:
        c = honors.get(nm, Counter())
        W(f"{nm:22s} " + " ".join(f"{c.get(a, 0):6d}" for a in cols))

    W("")
    W("## 前20巨星（游戏内出现的荣誉；非游戏球员仍含 2K 模拟值）")
    W("")
    for nm in TOP20:
        first, last = split_name(nm)
        rec = next((p for p in players if p["名字"] == first and p["姓氏"] == last), None)
        if not rec or rec["荣誉总计"] == 0:
            W(f"  {nm}: (未出现)")
            continue
        parts = [f"{k}={rec[k]}" for k in AWARD_COLS if rec.get(k)]
        W(f"  {nm}: {', '.join(parts)}")

    report = os.path.join(extract_dir, "honor_summary.txt")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {results_csv}")
    print(f"Wrote {results_json}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {report}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
