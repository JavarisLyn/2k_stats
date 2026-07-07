# -*- coding: utf-8 -*-
"""
荣誉榜 / 数据榜 Top N：用真实 NBA 生涯统计补全 Roster Editor 未提取或不可靠的字段。
REAL_NBA 中列出的球员/字段以真实生涯数据为准（覆盖错误的 2K 导出值）。
"""
import argparse
import csv
import json
import os
import subprocess
import sys

from config import ANALYSIS_DIR, RESULTS

STATS_CSV = os.path.join(RESULTS, "goat_scores_stats.csv")
HONORS_ALL_CSV = os.path.join(RESULTS, "player_honors_all.csv")
GOAT_CSV = os.path.join(RESULTS, "goat_scores.csv")
LOG_JSON = os.path.join(RESULTS, "real_stats_fill_log.json")

STAT_COLS = [
    "场均得分", "场均篮板", "场均助攻", "场均抢断", "场均盖帽",
    "场均失误", "投篮命中率", "出场总数",
]

# Basketball-Reference 生涯数据；1973-74 前无抢断/盖帽统计则不填
REAL_NBA = {
    ("Michael", "Jordan"): {
        "场均篮板": "6.2", "场均助攻": "5.3", "场均抢断": "2.3", "场均盖帽": "0.8",
        "场均失误": "2.9", "投篮命中率": "49.7", "出场总数": "1072",
    },
    ("LeBron", "James"): {"投篮命中率": "50.5"},
    ("Kobe", "Bryant"): {
        "场均得分": "27.9", "场均篮板": "5.8", "场均助攻": "5.1",
        "场均抢断": "1.4", "场均盖帽": "0.5", "场均失误": "2.8",
        "投篮命中率": "47.1", "出场总数": "1726",
    },
    ("Kareem", "Abdul-Jabbar"): {
        "场均抢断": "0.9", "场均助攻": "3.6", "场均盖帽": "2.6",
        "场均失误": "3.0", "投篮命中率": "55.9", "出场总数": "1560",
    },
    ("Wilt", "Chamberlain"): {
        "场均助攻": "4.4", "场均抢断": "0.8", "场均盖帽": "0.4",
        "场均失误": "3.5", "投篮命中率": "54.0", "出场总数": "1045",
    },
    ("Bill", "Russell"): {
        "场均得分": "15.1", "场均篮板": "22.5", "场均助攻": "4.3",
        "投篮命中率": "44.0", "出场总数": "963",
    },
    ("Larry", "Bird"): {
        "场均盖帽": "0.8", "场均失误": "3.0", "投篮命中率": "49.6", "出场总数": "897",
    },
    ("Magic", "Johnson"): {
        "场均篮板": "7.2", "场均盖帽": "0.4", "场均失误": "3.9",
        "投篮命中率": "52.0", "出场总数": "906",
    },
    ("Tim", "Duncan"): {
        "场均助攻": "3.0", "场均抢断": "0.7", "场均盖帽": "2.2",
        "场均失误": "2.4", "投篮命中率": "50.6", "出场总数": "1392",
    },
    ("Shaquille", "O'Neal"): {
        "场均助攻": "2.5", "场均抢断": "0.6", "场均失误": "2.7",
        "投篮命中率": "58.2", "出场总数": "1207",
    },
    ("Hakeem", "Olajuwon"): {
        "场均助攻": "2.5", "投篮命中率": "51.2", "出场总数": "1238",
    },
    ("Chris", "Paul"): {
        "场均篮板": "4.5", "场均盖帽": "0.2", "投篮命中率": "47.1", "出场总数": "1234",
    },
    ("Kevin", "Garnett"): {
        "场均助攻": "3.7", "场均抢断": "1.3", "场均盖帽": "1.4",
        "场均失误": "2.2", "投篮命中率": "49.7", "出场总数": "1462",
    },
    ("Kevin", "Durant"): {"投篮命中率": "50.1", "出场总数": "1123"},
    ("Carmelo", "Anthony"): {"投篮命中率": "44.7", "出场总数": "1260"},
    ("Dwyane", "Wade"): {"场均篮板": "4.7", "投篮命中率": "48.0", "出场总数": "1054"},
    ("Karl", "Malone"): {"场均助攻": "3.6", "投篮命中率": "51.6", "出场总数": "1476"},
    ("Oscar", "Robertson"): {
        "场均助攻": "9.5", "场均篮板": "7.5", "场均盖帽": "0.1", "场均失误": "3.8",
        "投篮命中率": "48.5", "出场总数": "1040",
    },
    ("Jerry", "West"): {
        "场均篮板": "5.8", "场均抢断": "1.4", "场均盖帽": "0.5",
        "场均失误": "3.3", "投篮命中率": "47.4", "出场总数": "932",
    },
    ("Moses", "Malone"): {
        "场均助攻": "1.4", "场均抢断": "0.8", "场均盖帽": "1.3",
        "投篮命中率": "49.1", "出场总数": "1455",
    },
    ("John", "Stockton"): {
        "场均得分": "13.1", "场均篮板": "2.7", "场均盖帽": "0.2",
        "投篮命中率": "51.5", "出场总数": "1504",
    },
    ("John", "Havlicek"): {
        "场均得分": "20.8", "场均篮板": "6.3", "场均助攻": "4.8",
        "场均抢断": "1.2", "场均盖帽": "0.6", "场均失误": "2.8",
        "投篮命中率": "47.1", "出场总数": "1270",
    },
    ("Scottie", "Pippen"): {
        "场均得分": "16.1", "场均篮板": "6.4", "场均助攻": "5.2",
        "场均盖帽": "0.8", "投篮命中率": "47.3", "出场总数": "1178",
    },
    ("Dennis", "Rodman"): {
        "场均得分": "7.3", "场均篮板": "13.1", "场均助攻": "1.8",
        "场均抢断": "0.7", "场均盖帽": "0.6", "投篮命中率": "52.1", "出场总数": "911",
    },
    ("Bob", "Cousy"): {
        "场均得分": "18.4", "场均篮板": "5.2", "场均助攻": "7.5",
        "投篮命中率": "37.5", "出场总数": "917",
    },
    ("David", "Robinson"): {
        "场均助攻": "2.5", "投篮命中率": "51.8", "出场总数": "987",
    },
    ("Jason", "Kidd"): {
        "场均得分": "12.6", "场均篮板": "6.3", "场均盖帽": "0.3",
        "投篮命中率": "40.0", "出场总数": "1391",
    },
    ("James", "Harden"): {
        "场均得分": "24.1", "场均篮板": "5.6", "场均助攻": "7.1",
        "场均抢断": "1.5", "场均盖帽": "0.6", "场均失误": "3.7",
        "投篮命中率": "44.3", "出场总数": "1112",
    },
    ("Luka", "Doncic"): {
        "场均得分": "28.7", "场均篮板": "8.7", "场均助攻": "8.3",
        "场均抢断": "1.2", "场均盖帽": "0.4", "场均失误": "4.0",
        "投篮命中率": "47.6", "出场总数": "515",
    },
    ("Giannis", "Antetokounmpo"): {
        "场均得分": "23.9", "场均篮板": "10.0", "场均助攻": "4.9",
        "场均抢断": "1.1", "场均盖帽": "1.2", "场均失误": "3.2",
        "投篮命中率": "55.6", "出场总数": "859",
    },
    ("Anthony", "Davis"): {
        "场均得分": "24.0", "场均篮板": "10.4", "场均助攻": "2.5",
        "场均抢断": "1.3", "场均盖帽": "2.4", "场均失误": "2.4",
        "投篮命中率": "52.0", "出场总数": "787",
    },
    ("Ben", "Simmons"): {
        "场均得分": "15.4", "场均篮板": "8.0", "场均助攻": "7.4",
        "场均抢断": "1.5", "场均盖帽": "0.7", "场均失误": "3.0",
        "投篮命中率": "53.9", "出场总数": "416",
    },
    ("Paul", "George"): {
        "场均得分": "20.4", "场均篮板": "6.4", "场均助攻": "3.5",
        "场均抢断": "1.6", "场均盖帽": "0.4", "场均失误": "2.8",
        "投篮命中率": "45.3", "出场总数": "908",
    },
    ("Derrick", "Rose"): {
        "场均得分": "17.4", "场均篮板": "3.2", "场均助攻": "5.2",
        "场均抢断": "0.7", "场均盖帽": "0.3", "场均失误": "2.4",
        "投篮命中率": "47.1", "出场总数": "723",
    },
    ("Dennis", "Johnson"): {
        "场均得分": "14.1", "场均篮板": "3.9", "场均助攻": "5.0",
        "场均抢断": "1.4", "场均盖帽": "0.6", "投篮命中率": "44.9", "出场总数": "1100",
    },
    ("Allen", "Iverson"): {
        "场均篮板": "3.7", "场均助攻": "6.2", "场均盖帽": "0.2",
        "场均失误": "3.6", "投篮命中率": "42.5", "出场总数": "914",
    },
    ("Gary", "Payton"): {
        "场均篮板": "3.9", "场均盖帽": "0.2", "投篮命中率": "46.6", "出场总数": "1335",
    },
    ("Willis", "Reed"): {
        "场均得分": "18.7", "场均篮板": "12.9", "场均助攻": "1.8",
        "场均盖帽": "0.6", "投篮命中率": "47.6", "出场总数": "650",
    },
    ("Charles", "Barkley"): {
        "场均助攻": "4.1", "场均抢断": "1.5", "场均盖帽": "0.8",
        "场均失误": "3.1", "投篮命中率": "54.1", "出场总数": "1073",
    },
    ("Dikembe", "Mutombo"): {
        "场均得分": "9.8", "场均篮板": "10.3", "场均助攻": "1.0",
        "场均失误": "1.8", "投篮命中率": "51.8", "出场总数": "1001",
    },
    ("Bill", "Walton"): {
        "场均得分": "13.3", "场均篮板": "10.5", "场均助攻": "3.4",
        "场均失误": "2.7", "出场总数": "468",
    },
    ("Bob", "Pettit"): {
        "场均助攻": "3.0", "场均抢断": "0.5", "场均盖帽": "0.3", "场均失误": "2.8",
        "投篮命中率": "43.3", "出场总数": "792",
    },
    ("George", "Gervin"): {
        "场均篮板": "5.3", "场均助攻": "2.6", "场均抢断": "1.2",
        "场均失误": "2.2", "出场总数": "791",
    },
    ("George", "Mikan"): {
        "场均得分": "23.1", "场均篮板": "13.4", "场均助攻": "2.8",
        "投篮命中率": "40.4", "出场总数": "439",
    },
    ("Michael", "Cooper"): {
        "场均得分": "8.9", "场均篮板": "3.2", "场均助攻": "4.2",
        "场均抢断": "1.2", "场均盖帽": "0.4", "投篮命中率": "46.5", "出场总数": "873",
    },
    ("Andrei", "Kirilenko"): {
        "场均得分": "11.8", "场均篮板": "5.5", "场均助攻": "2.7",
        "场均失误": "1.8", "投篮命中率": "47.4", "出场总数": "798",
    },
    ("Elgin", "Baylor"): {
        "场均助攻": "4.3", "场均抢断": "0.8", "场均盖帽": "0.4", "场均失误": "3.2",
        "投篮命中率": "43.1", "出场总数": "846",
    },
    ("Pau", "Gasol"): {"场均抢断": "0.6", "投篮命中率": "50.7", "出场总数": "1226"},
    ("Chris", "Bosh"): {"投篮命中率": "47.2", "出场总数": "893"},
    ("Dirk", "Nowitzki"): {"场均助攻": "3.0", "投篮命中率": "47.1", "出场总数": "1522"},
    ("Elton", "Brand"): {"场均助攻": "2.1", "投篮命中率": "50.0", "出场总数": "1020"},
    ("Dwight", "Howard"): {
        "场均助攻": "1.3", "投篮命中率": "57.0", "出场总数": "1245",
    },
    ("Elvin", "Hayes"): {
        "场均助攻": "1.4", "场均抢断": "1.0", "场均失误": "2.6", "投篮命中率": "45.2",
    },
    ("Ming", "Yao"): {
        "场均助攻": "1.6", "场均抢断": "0.5", "场均失误": "2.2", "投篮命中率": "52.4",
    },
    ("Isiah", "Thomas"): {
        "场均篮板": "3.6", "场均盖帽": "0.3", "场均失误": "3.8",
        "投篮命中率": "45.2", "出场总数": "979",
    },
    ("Paul", "Pierce"): {"场均盖帽": "0.6", "投篮命中率": "44.6", "出场总数": "1343"},
    ("Tracy", "McGrady"): {
        "场均助攻": "4.4", "场均抢断": "1.2", "投篮命中率": "43.5", "出场总数": "938",
    },
    ("Rick", "Barry"): {
        "场均助攻": "4.9", "场均盖帽": "0.5", "场均失误": "3.2",
        "投篮命中率": "44.9", "出场总数": "1020",
    },
    ("Bob", "McAdoo"): {
        "场均助攻": "2.3", "场均抢断": "0.8", "场均失误": "2.5",
        "投篮命中率": "50.3", "出场总数": "889",
    },
    ("Clyde", "Drexler"): {
        "场均助攻": "6.1", "场均盖帽": "0.7", "场均失误": "2.8",
        "投篮命中率": "47.2", "出场总数": "1107",
    },
    ("Gilbert", "Arenas"): {"场均篮板": "3.2", "投篮命中率": "42.1", "出场总数": "552"},
    ("Chris", "Webber"): {"场均助攻": "4.2", "投篮命中率": "47.9", "出场总数": "831"},
    ("Andrea", "Bargnani"): {"场均助攻": "1.2", "投篮命中率": "43.9", "出场总数": "616"},
    ("Pete", "Maravich"): {
        "场均篮板": "4.2", "场均助攻": "5.4", "场均抢断": "1.4",
        "场均失误": "3.7", "投篮命中率": "44.1", "出场总数": "658",
    },
    ("Tony", "Parker"): {
        "场均篮板": "2.7", "场均盖帽": "0.1", "投篮命中率": "49.1", "出场总数": "1254",
    },
    ("Walt", "Bellamy"): {
        "场均助攻": "2.4", "场均盖帽": "0.4", "场均失误": "2.5", "出场总数": "1043",
    },
    ("Amar'e", "Stoudemire"): {"场均助攻": "1.2", "投篮命中率": "53.7", "出场总数": "846"},
    ("Shawn", "Marion"): {"场均助攻": "2.0", "投篮命中率": "48.4", "出场总数": "1163"},
    ("Ray", "Allen"): {
        "场均助攻": "3.4", "场均盖帽": "0.2", "投篮命中率": "45.2", "出场总数": "1300",
    },
    ("Kyle", "Lowry"): {
        "场均篮板": "4.4", "场均盖帽": "0.2", "投篮命中率": "42.3", "出场总数": "1112",
    },
    ("Paul", "Arizin"): {
        "场均篮板": "9.8", "场均助攻": "2.3", "场均抢断": "0.6",
        "场均失误": "2.8", "投篮命中率": "42.1", "出场总数": "713",
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


def top_keys(csv_path, score_col, n):
    rows = load_csv(csv_path)
    rows.sort(key=lambda r: -float(r[score_col]))
    return {(r["名字"], r["姓氏"]) for r in rows[:n]}


def collect_keys(honor_top, stats_top, rank_from, rank_to):
    keys = set()
    if honor_top:
        keys |= top_keys(GOAT_CSV, "goat_score", honor_top)
    if stats_top:
        keys |= top_keys(STATS_CSV, "goat_score_stats", stats_top)
    if rank_from and rank_to:
        rows = load_csv(STATS_CSV)
        rows.sort(key=lambda r: -float(r["goat_score_stats"]))
        keys |= {(r["名字"], r["姓氏"]) for r in rows[rank_from - 1 : rank_to]}
    return keys


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
            if not is_empty(row.get(col)) and row.get(col) == real[col]:
                continue
            old = row.get(col, "")
            row[col] = real[col]
            if is_empty(old) or old != real[col]:
                log.append({
                    "球员": f"{k[0]} {k[1]}",
                    "字段": col,
                    "填入值": real[col],
                    "原值": old if not is_empty(old) else "",
                    "来源": "NBA 真实生涯",
                })


def run_script(name):
    path = os.path.join(ANALYSIS_DIR, name)
    print(f"\n>>> python analysis/{name}")
    subprocess.check_call([sys.executable, path], cwd=ANALYSIS_DIR)


def main():
    parser = argparse.ArgumentParser(description="用真实 NBA 数据补全缺失基础数据")
    parser.add_argument("--honor-top", type=int, default=50, help="荣誉榜 Top N（0=跳过）")
    parser.add_argument("--stats-top", type=int, default=50, help="数据榜 Top N（0=跳过）")
    parser.add_argument("--from", dest="rank_from", type=int, default=0, help="数据榜名次段起始（可选）")
    parser.add_argument("--to", dest="rank_to", type=int, default=0, help="数据榜名次段结束（可选）")
    args = parser.parse_args()

    keys = collect_keys(args.honor_top, args.stats_top, args.rank_from, args.rank_to)
    print(f"补全范围: 荣誉 Top{args.honor_top} ∪ 数据 Top{args.stats_top} → {len(keys)} 人")

    log = []
    for path in (HONORS_ALL_CSV, GOAT_CSV):
        rows = load_csv(path)
        fields = list(rows[0].keys())
        fill_rows(rows, keys, log)
        save_csv(path, rows, fields)

    with open(LOG_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "honor_top": args.honor_top,
            "stats_top": args.stats_top,
            "players": len(keys),
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
