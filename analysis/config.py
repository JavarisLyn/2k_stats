# -*- coding: utf-8 -*-
"""项目路径与 extract 数据源配置。"""
import os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_DIR = os.path.join(PROJECT, "analysis")
RESULTS = os.path.join(PROJECT, "results")

EXTRACT_HONORS_DIR = os.path.join(PROJECT, "extract", "20260708_002951")
EXTRACT_STATS_DIR = os.path.join(PROJECT, "extract", "20260705_182456")
