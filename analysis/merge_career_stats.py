# -*- coding: utf-8 -*-
"""从 extract 生涯数据目录合并到 results。"""
import csv
import json
import os

from config import EXTRACT_STATS_DIR, RESULTS

STATS_DIR = EXTRACT_STATS_DIR

STAT_FILES = {
    "场均得分.csv": "场均得分",
    "场均篮板.csv": "场均篮板",
    "场均助攻.csv": "场均助攻",
    "场均抢断.csv": "场均抢断",
    "场均盖帽.csv": "场均盖帽",
    "投篮命中率.csv": "投篮命中率",
    "生涯总出场数.csv": "出场总数",
    "总失误数.csv": "总失误",
}

TOTAL_FILES = {
    "生涯总得分.csv": "总得分",
    "生涯总篮板.csv": "总篮板",
    "生涯总助攻.csv": "总助攻",
    "总抢断数.csv": "总抢断",
    "总盖帽数.csv": "总盖帽",
}

DERIVED_AVG = [
    ("场均得分", "总得分"),
    ("场均篮板", "总篮板"),
    ("场均助攻", "总助攻"),
    ("场均抢断", "总抢断"),
    ("场均盖帽", "总盖帽"),
    ("场均失误", "总失误"),
]

STAT_COLS = [
    "场均得分", "场均篮板", "场均助攻", "场均抢断", "场均盖帽",
    "场均失误", "投篮命中率", "出场总数",
]


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def player_key(row):
    first = (row.get("名字") or row.get("\ufeff名字") or "").strip()
    last = (row.get("姓氏") or "").strip()
    return (first, last)


def load_stat_maps(stats_dir):
    maps = {}
    for fname, col in {**STAT_FILES, **TOTAL_FILES}.items():
        path = os.path.join(stats_dir, fname)
        m = {}
        if not os.path.isfile(path):
            print(f"skip missing: {fname}")
            continue
        for row in load_csv(path):
            k = player_key(row)
            if not k[0]:
                continue
            val = row.get("数据", "").strip()
            if val:
                m[k] = val
        maps[col] = m
        print(f"  {fname}: {len(m)} players")
    return maps


def derive_avg(total, games, digits=2):
    if not total or not games:
        return ""
    g = float(games)
    if g <= 0:
        return ""
    return fmt_float(float(total) / g, digits)


def fmt_float(val, digits=2):
    if val is None or val == "":
        return ""
    return f"{float(val):.{digits}f}"


def fmt_fg(val):
    if val is None or val == "":
        return ""
    v = float(val)
    if v <= 1.0:
        return f"{v * 100:.1f}"
    return f"{v:.1f}"


def build_stats(maps):
    all_keys = set()
    for m in maps.values():
        all_keys |= set(m.keys())

    stats = {}
    filled = {c: 0 for c, _ in DERIVED_AVG}

    for k in all_keys:
        rec = {}
        for col in (
            "场均得分", "场均篮板", "场均助攻", "场均抢断", "场均盖帽",
            "投篮命中率", "出场总数", "总失误",
            "总得分", "总篮板", "总助攻", "总抢断", "总盖帽",
        ):
            raw = maps.get(col, {}).get(k, "")
            if col == "投篮命中率":
                rec[col] = fmt_fg(raw) if raw else ""
            elif col in ("出场总数", "总失误", "总得分", "总篮板", "总助攻", "总抢断", "总盖帽"):
                rec[col] = fmt_float(raw, 0) if raw else ""
            else:
                rec[col] = fmt_float(raw) if raw else ""

        games = rec.get("出场总数", "")
        for avg_col, total_col in DERIVED_AVG:
            if rec.get(avg_col):
                continue
            derived = derive_avg(rec.get(total_col, ""), games)
            if derived:
                rec[avg_col] = derived
                filled[avg_col] += 1

        for col in STAT_COLS:
            rec.setdefault(col, "")
        stats[k] = rec

    print("\n  由总量÷出场补全:")
    for avg_col, n in filled.items():
        if n:
            print(f"    {avg_col}: +{n} 人")
    return stats


def main():
    print("Loading stats from", STATS_DIR)
    maps = load_stat_maps(STATS_DIR)
    stats = build_stats(maps)

    honors_path = os.path.join(RESULTS, "player_honors_all.csv")
    goat_path = os.path.join(RESULTS, "goat_scores.csv")

    honor_rows = load_csv(honors_path)
    honor_cols = [k.strip() for k in honor_rows[0].keys() if k.strip() not in STAT_COLS]

    h_out = []
    h_matched = 0
    for row in honor_rows:
        clean = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        k = (clean.get("名字", ""), clean.get("姓氏", ""))
        st = stats.get(k, {c: "" for c in STAT_COLS})
        if any(st[c] for c in STAT_COLS):
            h_matched += 1
        merged = {c: clean[c] for c in honor_cols}
        merged.update({c: st.get(c, "") for c in STAT_COLS})
        h_out.append(merged)

    honor_fields = honor_cols + STAT_COLS
    with open(honors_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=honor_fields)
        w.writeheader()
        w.writerows(h_out)

    goat_rows = load_csv(goat_path)
    goat_cols = [k.strip() for k in goat_rows[0].keys() if k.strip() not in STAT_COLS]
    g_out = []
    g_matched = 0
    for row in goat_rows:
        clean = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        k = (clean.get("名字", ""), clean.get("姓氏", ""))
        st = stats.get(k, {c: "" for c in STAT_COLS})
        if any(st[c] for c in STAT_COLS):
            g_matched += 1
        merged = {c: clean[c] for c in goat_cols}
        merged.update({c: st.get(c, "") for c in STAT_COLS})
        g_out.append(merged)

    goat_fields = goat_cols + STAT_COLS
    with open(goat_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=goat_fields)
        w.writeheader()
        w.writerows(g_out)

    with open(os.path.join(RESULTS, "player_honors_all.json"), encoding="utf-8") as f:
        doc = json.load(f)
    doc["career_stats_source"] = STATS_DIR
    by_key = {(r["名字"], r["姓氏"]): r for r in h_out}
    for p in doc["players"]:
        k = (p["名字"], p["姓氏"])
        if k in by_key:
            for c in STAT_COLS:
                p[c] = by_key[k].get(c, "")
    with open(os.path.join(RESULTS, "player_honors_all.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    with open(os.path.join(RESULTS, "goat_scores.json"), encoding="utf-8") as f:
        gdoc = json.load(f)
    gdoc["career_stats_source"] = STATS_DIR
    by_key = {(r["名字"], r["姓氏"]): r for r in g_out}
    for p in gdoc["players"]:
        k = (p["名字"], p["姓氏"])
        if k in by_key:
            for c in STAT_COLS:
                p[c] = by_key[k].get(c, "")
    with open(os.path.join(RESULTS, "goat_scores.json"), "w", encoding="utf-8") as f:
        json.dump(gdoc, f, ensure_ascii=False, indent=2)

    print(f"\nMerged into {honors_path} ({h_matched}/{len(h_out)} with stats)")
    print(f"Merged into {goat_path} ({g_matched}/{len(g_out)} with stats)")
    print(f"Stat columns: {STAT_COLS}")


if __name__ == "__main__":
    main()
