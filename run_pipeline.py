# -*- coding: utf-8 -*-
"""项目根目录入口：转发到 analysis/run_pipeline.py"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.join(ROOT, "analysis", "run_pipeline.py")

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, PIPELINE] + sys.argv[1:], cwd=os.path.join(ROOT, "analysis")))
