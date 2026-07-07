# -*- coding: utf-8 -*-
"""Validate career stat CSVs: signatures, duplicates, diff vs reference extract."""
import csv
import os
import sys
from collections import defaultdict

MERGE_FILES = [
    "场均得分.csv", "场均篮板.csv", "场均助攻.csv", "场均抢断.csv", "场均盖帽.csv",
    "投篮命中率.csv", "生涯总出场数.csv", "总失误数.csv",
    "生涯总得分.csv", "生涯总篮板.csv", "生涯总助攻.csv", "总抢断数.csv", "总盖帽数.csv",
]

EXPECTED_FIRST = {
    "场均得分.csv": ("Michael", "Jordan"),
    "场均篮板.csv": ("Wilt", "Chamberlain"),
    "场均助攻.csv": ("Magic", "Johnson"),
    "场均抢断.csv": ("Alvin", "Robertson"),
    "场均盖帽.csv": ("Mark", "Eaton"),
    "投篮命中率.csv": ("Travis", "Oliver"),
    "生涯总出场数.csv": ("Kevin", "Garnett"),
    "生涯总得分.csv": ("Kobe", "Bryant"),
    "生涯总篮板.csv": ("Wilt", "Chamberlain"),
    "生涯总助攻.csv": ("John", "Stockton"),
    "总盖帽数.csv": ("Hakeem", "Olajuwon"),
}


def first_row(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None, None, None
    r = rows[0]
    first = (r.get("名字") or "").strip()
    last = (r.get("姓氏") or "").strip()
    val = (r.get("数据") or "").strip()
    return first, last, val


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        k = ((r.get("名字") or "").strip(), (r.get("姓氏") or "").strip())
        if k[0]:
            out[k] = (r.get("数据") or "").strip()
    return out


def check_signatures(extract_dir):
    print("=== 首行签名检查 ===")
    issues = []
    for fn in MERGE_FILES:
        path = os.path.join(extract_dir, fn)
        if not os.path.isfile(path):
            issues.append(f"{fn}: 缺失")
            print(f"  !! {fn}: 缺失")
            continue
        f, l, v = first_row(path)
        exp = EXPECTED_FIRST.get(fn)
        if exp and (f, l) != exp:
            msg = f"{fn}: 首行应为 {exp[0]} {exp[1]}，实际 {f} {l} (数据={v})"
            issues.append(msg)
            print(f"  !! {msg}")
        else:
            print(f"  OK {fn}: {f} {l} = {v}")
    return issues


def check_duplicate_signatures(extract_dir):
    print("\n=== 首行重复检测 (可能误标) ===")
    sig_map = defaultdict(list)
    for fn in os.listdir(extract_dir):
        if not fn.endswith(".csv"):
            continue
        f, l, v = first_row(os.path.join(extract_dir, fn))
        if not f:
            continue
        try:
            key = (f, l, round(float(v), 2))
        except ValueError:
            key = (f, l, v)
        sig_map[key].append(fn)
    dup_issues = []
    for sig, files in sorted(sig_map.items(), key=lambda x: -len(x[1])):
        if len(files) > 1:
            msg = f"重复首行 {sig[0]} {sig[1]} {sig[2]}: {files}"
            dup_issues.append(msg)
            print(f"  !! {msg}")
    if not dup_issues:
        print("  无重复首行")
    return dup_issues


def compare_merge(old_dir, new_dir):
    print("\n=== MERGE 文件 vs 参考 extract (共同球员数值) ===")
    summary = []
    for fn in MERGE_FILES:
        op = os.path.join(old_dir, fn)
        np = os.path.join(new_dir, fn)
        if not os.path.isfile(np):
            summary.append((fn, "missing_new"))
            print(f"  -- {fn}: 新版缺失")
            continue
        if not os.path.isfile(op):
            summary.append((fn, "new_only"))
            print(f"  ++ {fn}: 参考版无此文件")
            continue
        old, new = load(op), load(np)
        common = set(old) & set(new)
        diffs = []
        for k in common:
            if old[k] != new[k]:
                try:
                    o, n = float(old[k]), float(new[k])
                    pct = abs(n - o) / o * 100 if o else 999
                except ValueError:
                    pct = 0
                diffs.append((pct, k, old[k], new[k]))
        if not diffs:
            print(f"  == {fn}: {len(common)} 共同球员，数值全同")
            summary.append((fn, "identical"))
        else:
            diffs.sort(reverse=True)
            big = sum(1 for d in diffs if d[0] > 5)
            print(f"  ~~ {fn}: {len(diffs)}/{len(common)} 人有差异，>5%变化 {big} 人")
            for pct, k, o, n in diffs[:3]:
                extra = f" ({pct:.1f}%)" if pct < 900 else ""
                print(f"       {k[0]} {k[1]}: {o} -> {n}{extra}")
            if len(diffs) > 3:
                print(f"       ... +{len(diffs) - 3} more")
            summary.append((fn, f"{len(diffs)} changed"))
    return summary


def main():
    ref_dir = sys.argv[1]
    new_dir = sys.argv[2]
    print(f"参考: {ref_dir}\n新版: {new_dir}\n")

    sig_issues = check_signatures(new_dir)
    dup_issues = check_duplicate_signatures(new_dir)
    compare_merge(ref_dir, new_dir)

    print("\n=== 结论 ===")
    if sig_issues:
        print("签名异常:", len(sig_issues))
        for x in sig_issues:
            print(f"  - {x}")
    else:
        print("签名检查: 全部通过")

    if dup_issues:
        print("重复首行:", len(dup_issues))
    else:
        print("重复首行: 无")

    fallback = ["总失误数.csv", "总抢断数.csv", "生涯总助攻.csv"]
    print("\nFallback 文件 (应从参考版复制):")
    for fn in fallback:
        op, np = os.path.join(ref_dir, fn), os.path.join(new_dir, fn)
        if os.path.isfile(op) and os.path.isfile(np):
            same = load(op) == load(np)
            print(f"  {fn}: {'与参考版一致' if same else '有差异 !!!'}")


if __name__ == "__main__":
    main()
