# -*- coding: utf-8 -*-
"""Compare career stat CSVs between two extract directories."""
import csv
import os
import sys

MERGE_FILES = [
    "场均得分.csv", "场均篮板.csv", "场均助攻.csv", "场均抢断.csv", "场均盖帽.csv",
    "投篮命中率.csv", "生涯总出场数.csv", "总失误数.csv",
    "生涯总得分.csv", "生涯总篮板.csv", "生涯总助攻.csv", "总抢断数.csv", "总盖帽数.csv",
]

EXTRA_FILES = [
    "场均上场时间.csv", "三分命中率.csv", "罚球命中率.csv", "生涯总上场时间.csv",
    "40分比赛数.csv", "50分比赛数.csv", "60分比赛次数.csv", "三双次数.csv",
    "总犯规数.csv", "总罚球命中.csv", "投篮命中数.csv", "三分命中数.csv",
]


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        first = (r.get("名字") or r.get("\ufeff名字") or "").strip()
        last = (r.get("姓氏") or "").strip()
        val = (r.get("数据") or "").strip()
        if first:
            out[(first, last)] = val
    return out


def compare_file(old_dir, new_dir, fname):
    op = os.path.join(old_dir, fname)
    np = os.path.join(new_dir, fname)
    if not os.path.isfile(np):
        return {"status": "missing_new"}
    if not os.path.isfile(op):
        return {"status": "new_only", "rows": len(load(np))}
    old, new = load(op), load(np)
    changed = []
    for k in sorted(set(old) & set(new)):
        if old[k] != new[k]:
            changed.append((k, old[k], new[k]))
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    return {
        "status": "ok",
        "old_n": len(old),
        "new_n": len(new),
        "changed": changed,
        "added": added,
        "removed": removed,
    }


def main():
    old_dir = sys.argv[1]
    new_dir = sys.argv[2]
    print(f"Old: {old_dir}\nNew: {new_dir}\n")

    any_update = False
    for fname in MERGE_FILES + EXTRA_FILES:
        r = compare_file(old_dir, new_dir, fname)
        st = r["status"]
        if st == "missing_new":
            print(f"  --  {fname}: not in new extract")
            continue
        if st == "new_only":
            print(f"  ++  {fname}: new file ({r['rows']} players)")
            any_update = True
            continue
        ch, add, rem = r["changed"], r["added"], r["removed"]
        if not ch and not add and not rem:
            print(f"  ==  {fname}: identical ({r['old_n']} players)")
            continue
        any_update = True
        print(f"  ~~  {fname}: {r['old_n']} -> {r['new_n']} players, "
              f"{len(ch)} changed, +{len(add)} -{len(rem)}")
        for k, o, n in ch[:5]:
            print(f"       {k[0]} {k[1]}: {o} -> {n}")
        if len(ch) > 5:
            print(f"       ... +{len(ch) - 5} more changes")
        for k in add[:3]:
            print(f"       + {k[0]} {k[1]} = {new_dir and load(os.path.join(new_dir, fname)).get(k, '')}")
        for k in rem[:3]:
            print(f"       - {k[0]} {k[1]}")

    print("\n" + ("有更新数据。" if any_update else "与旧版完全一致，无更新。"))


if __name__ == "__main__":
    main()
