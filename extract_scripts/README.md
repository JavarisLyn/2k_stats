# NBA 2K26 Roster Editor 数据提取工具

## 概述

通过 Frida 代码注入技术，从 NBA 2K26 Roster Editor Trial 的 Qt 表格中提取数据，自动保存为 CSV + JSON 格式。

## 环境要求

- Python 3.14 64-bit：`C:\Users\LeeeYF\AppData\Local\Programs\Python\Python314\python.exe`
- 已安装包：`frida`、`frida-tools`（`pip install frida frida-tools`）
- NBA 2K26 Roster Editor Trial：`G:\BaiduNetdiskDownload\NBA2K26 Roster Editor Trial_20251225_140610\`

## 文件说明

```
C:\Users\LeeeYF\nba2k26_extractor\
├── inject_code.py      # 注入到 Roster Editor 的 Python 提取代码
├── run_inject.py        # 主运行脚本（自动检测PID、注入、保存结果）
├── extract_tool.py      # 单标签页提取工具（备用）
├── extract_all.py       # 全标签页自动切换提取（实验性，可能不稳定）
└── extracted_data\      # 输出目录
    ├── latest_extract.json    # 最新提取的JSON
    ├── YYYYMMDD_HHMMSS_table1.csv  # 按时间戳命名的CSV文件
    └── ...
```

## 使用方法

### 基本用法（推荐）

1. 启动 NBA 2K26 Roster Editor Trial，加载存档
2. 切换到想提取的标签页
3. 运行：
```
C:\Users\LeeeYF\AppData\Local\Programs\Python\Python314\python.exe C:\Users\LeeeYF\nba2k26_extractor\run_inject.py
```
4. CSV 文件自动保存到 `extracted_data\` 目录

### 工作原理

```
run_inject.py
  │
  ├─ 1. 通过 Frida API 枚举进程，找到 Roster Editor Trial
  ├─ 2. 尝试 attach 两个 PID（stub + 主进程），找到有 python311.dll 的那个
  ├─ 3. 读取 inject_code.py 的内容
  ├─ 4. 通过 Frida 调用 PyGILState_Ensure → PyRun_SimpleString → PyGILState_Release
  │     在 Roster Editor 的 Python 运行时中执行代码
  └─ 5. inject_code.py：
        ├─ 获取 QApplication 实例
        ├─ 遍历所有 QTableView 控件
        ├─ 读取 model().rowCount() / columnCount() / headerData() / data()
        └─ 写入 latest_extract.json

Frida 注入链：
  python311.dll
    ├─ PyGILState_Ensure()  # 获取 GIL 锁
    ├─ PyRun_SimpleString(code)  # 执行 Python 代码
    └─ PyGILState_Release()  # 释放 GIL 锁
```

### 注入代码（inject_code.py）

```python
import json, os
from PyQt5.QtWidgets import QApplication, QTableView
from PyQt5.QtCore import Qt

app = QApplication.instance()
tables = []
for widget in app.allWidgets():
    if isinstance(widget, QTableView):
        model = widget.model()
        if model and model.rowCount() > 0:
            # 读取表头
            headers = [str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or '')
                       for c in range(model.columnCount())]
            # 读取数据行
            data = [[str(model.data(model.index(r, c), Qt.DisplayRole) or '')
                     for c in range(model.columnCount())]
                    for r in range(min(model.rowCount(), 1000))]
            tables.append({'rows': model.rowCount(), 'cols': model.columnCount(),
                           'headers': headers, 'data': data})
# 写入JSON
with open('C:/Users/LeeeYF/nba2k26_extractor/extracted_data/latest_extract.json', 'w') as f:
    json.dump(tables, f, indent=2, ensure_ascii=False)
```

## 关键发现（存档格式研究历程）

### 尝试过的方案

| 方案 | 结果 |
|------|------|
| 直接解析 MyLEAGUE0001 文件 | ❌ EBNH 格式 AES 加密，密钥嵌入 Nuitka 编译代码 |
| NBA2K26.exe 内存读取 | ❌ Easy Anti-Cheat 保护 |
| Frida Hook libcrypto AES 函数 | ❌ 解密不走 OpenSSL，内联在 Nuitka DLL 中 |
| Ghidra 静态反汇编（52MB DLL） | ❌ 密钥被编译器优化分散，无法静态提取 |
| 搜索内存中解密后数据 | ❌ 数据以 Python 对象存储，不连续 |
| UI Automation 读取 Qt 表格 | ❌ Qt 无原生 Windows 控件 |
| **Frida 代码注入** | ✅ **成功！直接调用 Python C API** |

### EBNH 文件格式（供后续研究）

```
偏移    内容
[0:4]   "EBNH" 魔法数
[4:8]   0x00000000（版本？）
[8:16]  8字节（文件特定数据，可能是 IV/Seed）
[16:24] 8字节（所有文件共享，可能是格式标识）
[24:]   AES 加密的数据
```

加密模式：疑似 AES-ECB（重复的零块产生相同密文 `822adb62867731d0...`）

### 存档路径

```
D:\game\steam\userdata\866425829\3472040\remote\
├── MyLEAGUE0001          # MyNBA 联盟存档（主数据文件）
├── SaveDescriptions       # 存档描述元数据
├── CareerModeBuilds       # 生涯模式
├── UserData               # 用户数据
└── Settings               # 设置
```

Steam App ID: `3472040`

## 其他已提取数据

| 文件 | 内容 | 来源 |
|------|------|------|
| `player_names.txt` | 1,851 个球员名称 | Roster Editor 内存扫描 |
| `all_tables.json` | 第一次成功提取（4张表） | Frida 注入 |

## 后续改进方向

1. 批量自动化：修改 inject_code.py 遍历 QStackedWidget 索引
2. 直接解密存档：找到 AES 密钥后可独立解密 MyLEAGUE0001
3. 合并 Ghidra 分析：在 `G:\software\ghidra_11.0_PUBLIC\` 已有项目
