# -*- coding: utf-8 -*-
"""
GOAT Score 计算流水线。

用法:
  python run_pipeline.py              # 完整流程
  python run_pipeline.py --with-fill    # 含数据榜 Top20 真实 NBA 补全
  python run_pipeline.py --from merge   # 从指定步骤起执行
"""
import argparse
import os
import subprocess
import sys

from config import ANALYSIS_DIR

STEPS = [
    ("extract_honors", "extract_honors.py", "汇总荣誉 CSV"),
    ("honors", "calc_goat_honors.py", "荣誉版 GOAT"),
    ("merge", "merge_career_stats.py", "合并生涯数据"),
    ("stats", "calc_goat_stats.py", "数据版 GOAT"),
    ("fill", "fill_real_stats_top20.py", "Top20 真实数据补全"),
    ("combined", "calc_goat_combined.py", "综合版 GOAT"),
    ("export", "export_results_md.py", "导出 results.md"),
    ("html", "export_goat_top20_html.py", "导出 Top20 HTML"),
]

STEP_IDS = [s[0] for s in STEPS]


def run_script(script):
    path = os.path.join(ANALYSIS_DIR, script)
    print(f"\n{'=' * 50}\n>>> {script}\n{'=' * 50}")
    subprocess.check_call([sys.executable, path], cwd=ANALYSIS_DIR)


def main():
    parser = argparse.ArgumentParser(description="GOAT Score 计算流水线")
    parser.add_argument(
        "--with-fill",
        action="store_true",
        help="在数据版计算后，用真实 NBA 数据补全 Top20 缺失项并重算",
    )
    parser.add_argument(
        "--from",
        dest="from_step",
        choices=STEP_IDS,
        default=STEP_IDS[0],
        help="从哪一步开始（默认 extract_honors）",
    )
    args = parser.parse_args()

    skip_fill = not args.with_fill
    start = STEP_IDS.index(args.from_step)
    selected = STEPS[start:]

    for step_id, script, _desc in selected:
        if step_id == "fill" and skip_fill:
            continue
        run_script(script)
        if step_id == "fill":
            # fill 脚本内部已重算 stats/combined/export，跳过后续重复步骤
            break

    print("\n完成。")


if __name__ == "__main__":
    main()
