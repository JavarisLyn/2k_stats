# -*- coding: utf-8 -*-
"""
数据榜指定名次段缺失项用真实 NBA 生涯数据补全（仅填空，不覆盖已有 2K 值）。
默认：第 15–30 名。可用 --from / --to 调整。
"""
import argparse
import csv
import json
import os
import subprocess
import sys

from config import ANALYSIS_DIR, RESULTS

STATS_CSV = os.path.join(RESULTS, "goat_scores_stats.csv")
HONORS_CSV = os.path.join(RESULTS, "player_honors_all.csv")
LOG_JSON = os.path.join(RESULTS, "real_stats_fill_log.json")

STAT_COLS = [
    "场均得分", "场均篮板", "场均助攻", "场均抢断", "场均盖帽",
    "场均失误", "投篮命中率", "出场总数",
]

# Basketball-Reference 生涯数据；早年未统计项不填
REAL_NBA = {
    # Top 20（历史补全）
    ("LeBron", "James"): {"投篮命中率": "50.5"},
    ("Wilt", "Chamberlain"): {
        "场均助攻": "4.4", "出场总数": "1045", "投篮命中率": "54.0",
    },
    ("Kobe", "Bryant"): {"场均盖帽": "0.5"},
    ("Kareem", "Abdul-Jabbar"): {"场均抢断": "0.9"},
    ("Carmelo", "Anthony"): {"投篮命中率": "44.7"},
    ("Kevin", "Durant"): {"投篮命中率": "50.1"},
    ("Larry", "Bird"): {
        "场均盖帽": "0.8", "场均失误": "3.0", "投篮命中率": "49.6", "出场总数": "897",
    },
    ("Chris", "Bosh"): {"投篮命中率": "47.2"},
    ("Michael", "Jordan"): {
        "场均篮板": "6.2", "场均盖帽": "0.8", "场均失误": "2.9",
        "投篮命中率": "49.7", "出场总数": "1072",
    },
    ("Pau", "Gasol"): {"场均抢断": "0.6"},
    ("Bob", "Pettit"): {
        "场均助攻": "3.0", "投篮命中率": "43.3", "出场总数": "792",
    },
    ("Chris", "Paul"): {
        "场均篮板": "4.5", "场均盖帽": "0.2", "投篮命中率": "47.1", "出场总数": "1234",
    },
    ("Elgin", "Baylor"): {
        "场均助攻": "4.3", "投篮命中率": "43.1", "出场总数": "846",
    },
    ("Dirk", "Nowitzki"): {"场均助攻": "3.0", "投篮命中率": "47.1"},
    ("Oscar", "Robertson"): {
        "场均篮板": "7.5", "投篮命中率": "48.5", "出场总数": "1040",
    },
    ("Dwyane", "Wade"): {"场均篮板": "4.7"},
    ("Paul", "Pierce"): {"场均盖帽": "0.6", "投篮命中率": "44.6"},
    # 15–30 段
    ("Shaquille", "O'Neal"): {
        "场均助攻": "2.5", "场均抢断": "0.6",
    },
    ("Elton", "Brand"): {"场均助攻": "2.1", "投篮命中率": "50.0"},
    ("Magic", "Johnson"): {
        "场均篮板": "7.2", "场均盖帽": "0.4", "场均失误": "3.9",
        "投篮命中率": "52.0", "出场总数": "906",
    },
    ("Elvin", "Hayes"): {
        "场均助攻": "1.4", "场均抢断": "1.0", "场均失误": "2.6", "投篮命中率": "45.2",
    },
    ("Karl", "Malone"): {"场均助攻": "3.6"},
    ("Jerry", "West"): {
        "场均篮板": "5.8", "投篮命中率": "47.4", "出场总数": "932",
    },
    ("Ming", "Yao"): {
        "场均助攻": "1.6", "场均抢断": "0.5", "场均失误": "2.2", "投篮命中率": "52.4",
    },
    ("Hakeem", "Olajuwon"): {
        "场均助攻": "2.5", "投篮命中率": "51.2",
    },
    ("Isiah", "Thomas"): {
        "场均篮板": "3.6", "场均盖帽": "0.3", "场均失误": "3.8",
        "投篮命中率": "45.2", "出场总数": "979",
    },
    ("Dwight", "Howard"): {
        "场均助攻": "1.3", "投篮命中率": "57.0",
    },
    ("Charles", "Barkley"): {
        "场均助攻": "4.1", "场均盖帽": "0.8", "场均失误": "3.1", "出场总数": "1073",
    },
}


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def rank_keys(rank_from, rank_to):
    rows = load_csv(STATS_CSV)
    rows.sort(key=lambda r: -float(r["goat_score_stats"]))
    slice_rows = rows[rank_from - 1 : rank_to]
    return [(r["名字"], r["姓氏"]) for r in slice_rows]


def is_empty(val):
    return val is None or str(val).strip() == ""


def fill_rows(rows, keys, log):
    for row in rows:
        k = (row["名字"], row["姓氏"])
        if k not in keys:
            continue
        real = REAL_NBA.get(k, {})
        if not real:
            continue
        for col in STAT_COLS:
            if col not in real:
                continue
            if is_empty(row.get(col)):
                row[col] = real[col]
                log.append({
                    "球员": f"{k[0]} {k[1]}",
                    "字段": col,
                    "填入值": real[col],
                    "来源": "NBA 真实生涯",
                })


def run_script(name):
    path = os.path.join(ANALYSIS_DIR, name)
    print(f"\n>>> python analysis/{name}")
    subprocess.check_call([sys.executable, path], cwd=ANALYSIS_DIR)


def main():
    parser = argparse.ArgumentParser(description="用真实 NBA 数据补全数据榜缺失项")
    parser.add_argument("--from", dest="rank_from", type=int, default=15, help="起始名次（含）")
    parser.add_argument("--to", dest="rank_to", type=int, default=30, help="结束名次（含）")
    args = parser.parse_args()

    keys = set(rank_keys(args.rank_from, args.rank_to))
    print(f"数据榜 #{args.rank_from}–#{args.rank_to}: {len(keys)} 人")

    log = []
    honor_rows = load_csv(HONORS_CSV)
    honor_fields = list(honor_rows[0].keys())
    fill_rows(honor_rows, keys, log)
    save_csv(HONORS_CSV, honor_rows, honor_fields)

    with open(LOG_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "rank_range": [args.rank_from, args.rank_to],
            "filled": log,
            "count": len(log),
        }, f, ensure_ascii=False, indent=2)

    print(f"补全 {len(log)} 项 → {LOG_JSON}")
    for item in log:
        print(f"  {item['球员']}: {item['字段']} = {item['填入值']}")

    for script in (
        "calc_goat_stats.py", "calc_goat_combined.py",
        "export_results_md.py", "export_goat_top20_html.py",
    ):
        run_script(script)


if __name__ == "__main__":
    main()
