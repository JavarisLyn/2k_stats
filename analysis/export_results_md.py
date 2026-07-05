# -*- coding: utf-8 -*-
"""将 results/*.csv 导出为 Markdown 表格。"""
import csv
import os
from datetime import date

from config import EXTRACT_HONORS_DIR, EXTRACT_STATS_DIR, RESULTS

HONORS_CSV = os.path.join(RESULTS, "player_honors_all.csv")
GOAT_CSV = os.path.join(RESULTS, "goat_scores.csv")
GOAT_STATS_CSV = os.path.join(RESULTS, "goat_scores_stats.csv")
GOAT_COMBINED_CSV = os.path.join(RESULTS, "goat_scores_combined.csv")
OUT_MD = os.path.join(RESULTS, "results.md")

GOAT_DISPLAY_COLS = [
    "MVP", "FMVP", "总冠军", "最佳防守球员", "最佳新秀",
    "得分王", "篮板王", "助攻王", "抢断王", "盖帽王",
    "最佳一阵", "最佳二阵", "最佳三阵", "防一阵", "防二阵",
]

CAREER_COLS = [
    "场均得分", "场均篮板", "场均助攻", "场均抢断", "场均盖帽",
    "场均失误", "投篮命中率", "出场总数",
]


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [
            {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def esc(val):
    return str(val).replace("|", "\\|")


def to_md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(":---" if i == 0 else "---:" for i in range(len(headers))) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(esc(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines)


def main():
    honors = load_csv(HONORS_CSV)
    goat = load_csv(GOAT_CSV)
    stats_path = GOAT_STATS_CSV
    goat_stats = load_csv(stats_path) if os.path.isfile(stats_path) else []
    combined_path = GOAT_COMBINED_CSV
    goat_combined = load_csv(combined_path) if os.path.isfile(combined_path) else []

    combined_rows = []
    for i, r in enumerate(goat_combined, 1):
        combined_rows.append({
            "排名": i,
            "姓名": f"{r['名字']} {r['姓氏']}",
            "综合分": r["goat_score_combined"],
            "荣誉分": r.get("荣誉分", ""),
            "荣誉归一化": r.get("荣誉归一化", ""),
            "数据分": r.get("数据分", ""),
            "数据归一化": r.get("数据归一化", ""),
        })

    combined_section = ""
    if combined_rows:
        combined_headers = ["排名", "姓名", "综合分", "荣誉分", "荣誉归一化", "数据分", "数据归一化"]
        combined_section = f"""
---

## GOAT Score 排名（综合版 6:4）

共 {len(combined_rows)} 名球员。`综合分 = 0.65×荣誉归一化 + 0.35×数据归一化`（各自 Min-Max 至 0~100）。

{to_md_table(combined_headers, combined_rows)}
"""

    goat_rows = []
    for i, r in enumerate(goat, 1):
        goat_rows.append({
            "排名": i,
            "姓名": f"{r['名字']} {r['姓氏']}",
            "GOAT Score": r["goat_score"],
            **{c: r.get(c, 0) for c in GOAT_DISPLAY_COLS},
            **{c: r.get(c, "") for c in CAREER_COLS},
        })

    honor_rows = []
    for r in honors:
        honor_rows.append({
            "姓名": f"{r['名字']} {r['姓氏']}",
            **{c: r.get(c, 0) for c in GOAT_DISPLAY_COLS + [
                "上场时间王", "最佳第六人", "进步最快", "新秀一阵", "新秀二阵", "荣誉总计",
            ]},
            **{c: r.get(c, "") for c in CAREER_COLS},
        })

    goat_headers = ["排名", "姓名", "GOAT Score"] + GOAT_DISPLAY_COLS + CAREER_COLS
    honor_headers = ["姓名"] + GOAT_DISPLAY_COLS + [
        "上场时间王", "最佳第六人", "进步最快", "新秀一阵", "新秀二阵", "荣誉总计",
    ] + CAREER_COLS

    stats_headers = ["排名", "姓名", "GOAT Score(数据版)", "场均综合分", "耐久系数"] + CAREER_COLS
    stats_rows = []
    for i, r in enumerate(goat_stats, 1):
        stats_rows.append({
            "排名": i,
            "姓名": f"{r['名字']} {r['姓氏']}",
            "GOAT Score(数据版)": r["goat_score_stats"],
            "场均综合分": r.get("场均综合分", ""),
            "耐久系数": r.get("耐久系数", ""),
            **{c: r.get(c, "") for c in CAREER_COLS},
        })

    stats_section = ""
    if stats_rows:
        stats_section = f"""
---

## GOAT Score 排名（数据版）

共 {len(stats_rows)} 名球员（至少有一项场均数据）。`数据分 = 场均综合分 × (出场/1000)^0.4`；无出场时耐久系数=1.0。

{to_md_table(stats_headers, stats_rows)}
"""

    honors_rel = os.path.relpath(EXTRACT_HONORS_DIR, os.path.dirname(RESULTS)).replace("\\", "/")
    stats_rel = os.path.relpath(EXTRACT_STATS_DIR, os.path.dirname(RESULTS)).replace("\\", "/")

    md = f"""# 2K Stats 结果汇总

> 数据来源：`{honors_rel}`  
> GOAT Score 权重见 `algo.md` 荣誉版；**1976 年及以前赛季**（如 1975-1976）荣誉得分 ×0.7  
> 生涯数据：`{stats_rel}`（各榜单 Top ~100，无数据留空）  
> 生成日期：{date.today().isoformat()}
{combined_section}
---

## GOAT Score 排名（荣誉版）

共 {len(goat_rows)} 名球员，按 GOAT Score 降序。

{to_md_table(goat_headers, goat_rows)}
{stats_section}
---

## 球员荣誉汇总

共 {len(honor_rows)} 名球员。完整 CSV：`player_honors_all.csv`

{to_md_table(honor_headers, honor_rows)}
"""

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Wrote {OUT_MD}")
    print(f"  GOAT 排名: {len(goat_rows)} 行")
    print(f"  荣誉汇总: {len(honor_rows)} 行")


if __name__ == "__main__":
    main()
