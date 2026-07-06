import json, os, re
try:
    from PyQt5.QtWidgets import QApplication, QTableView
    from PyQt5.QtCore import Qt
    app = QApplication.instance()

    tables = []
    for widget in app.allWidgets():
        try:
            if isinstance(widget, QTableView):
                model = widget.model()
                if model and model.rowCount() > 0:
                    rows = model.rowCount()
                    cols = model.columnCount()
                    headers = [str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or '') for c in range(cols)]
                    data = [[str(model.data(model.index(r, c), Qt.DisplayRole) or '') for c in range(cols)] for r in range(min(rows, 1000))]
                    h = ','.join(headers)
                    last_col = float(data[0][-1]) if data and data[0][-1].replace('.','').isdigit() else 0

                    name = ''
                    if any(kw in h for kw in ['冠军', '亚军', '比分']):
                        name = '总决赛历史'
                    elif rows in (39, 40, 41, 42) and cols == 6:
                        if rows in (39, 37):
                            name = '进步最快球员'
                        elif 'Giannis' in str(data) or 'Duncan' in str(data):
                            name = '最佳防守球员'
                        elif 'Edwards' in str(data) or 'Conley' in str(data):
                            name = '最佳第六人'
                        else:
                            name = '最佳第六人'
                    elif rows in (67, 68, 69) and cols == 6:
                        name = '常规赛MVP'
                    elif rows in (73, 74, 75) and cols == 6:
                        name = '最佳新秀'
                    elif rows == 37 and cols == 6:
                        name = '进步最快球员'
                    elif rows in (60, 61, 62) and cols == 6:
                        name = '最佳教练'
                    elif cols == 7 and '位置' in h:
                        if rows >= 300:
                            name = '最佳新秀阵容' if any(p in str(data[:3]) for p in ['Mobley','Giddey','Cunningham']) else '最佳防守阵容' if any(p in str(data[:3]) for p in ['Simmons','George']) else '最佳阵容'
                        else:
                            name = '最佳阵容'
                    elif cols == 8 and last_col > 50000:
                        name = '生涯总上场时间'
                    elif cols == 8 and last_col > 30000:
                        name = '生涯总得分'
                    elif cols == 8 and last_col > 15000:
                        name = '生涯总篮板' if last_col > 20000 else '生涯总助攻'
                    elif cols == 8 and last_col > 5000:
                        name = '生涯总抢断' if last_col < 8000 else '生涯总盖帽'
                    elif cols == 8 and last_col > 1000:
                        name = '生涯总出场数'
                    elif cols == 8:
                        name = '生涯数据'
                    elif cols == 7 and last_col > 35:
                        name = '上场时间王'
                    elif cols == 7 and last_col > 20:
                        name = '得分王'
                    elif cols == 7 and last_col > 10:
                        name = '篮板王' if last_col > 13 else '助攻王'
                    elif cols == 7 and last_col >= 2:
                        name = '盖帽王'
                    elif cols == 7 and last_col > 0:
                        name = '抢断王'

                    if not name:
                        name = f'Table{len(tables)+1}'

                    tables.append({'rows': rows, 'cols': cols, 'headers': headers, 'data': data, 'name': name})
        except:
            pass

    # Post-processing: career stats corrections based on user's 更正.txt
    # Map from (cols, first_value_range, sample_player) → correct_name
    corrections = {
        # Career totals (cols=8, 100 rows)
        ('Kevin Garnett', 1757): '生涯总出场数',
        ('Magic Johnson', 11.2): '场均助攻',
        ('Wilt Chamberlain', 271): '40分比赛数',
        ('Wilt Chamberlain', 22.9): '场均篮板',
        ('Wilt Chamberlain', 118): '50分比赛数',
        ('Kobe Bryant', 4880): '总失误数',
        ('John Stockton', 3370): '总抢断数',
        ('Marcelo Huertas', 0.96): '罚球命中率',
        ('Tyson Chandler', 5250): '总犯规数',
        ('Kevin Garnett', 61417): '生涯总上场时间',
        ('Kobe Bryant', 48087): '生涯总得分',
        ('Hakeem Olajuwon', 4046): '总盖帽数',
        ('Wilt Chamberlain', 23924): '生涯总篮板',
        ('Michael Jordan', 30.34): '场均得分',
        ('Travis Oliver', 0.64): '投篮命中率',
        ('LeBron James', 183): '三双次数',
        ('John Stockton', 16539): '生涯总助攻',
        ('Kobe Bryant', 17439): '投篮命中数',
        ('Steve Kerr', 0.46): '三分命中率',
        ('Stephen Curry', 4436): '三分命中数',
        ('Wilt Chamberlain', 32): '60分比赛次数',
        ('Alvin Robertson', 2.7): '场均抢断',
        ('Kobe Bryant', 10477): '总罚球命中',
        ('Mark Eaton', 3.5): '场均盖帽',
        ('Wilt Chamberlain', 45.8): '场均上场时间',
    }

    final = []
    all_nba_teams = []

    for t in tables:
        n = t['name']
        d = t['data']
        if d and len(d[0]) >= 1:
            first_player = d[0][0] + ' ' + d[0][1] if len(d[0]) >= 2 else d[0][0]
            first_val = float(d[0][-1]) if d[0][-1].replace('.','').replace('-','').isdigit() else 0
            key = (first_player.strip(), round(first_val, 2))
            if key in corrections:
                t['name'] = corrections[key]
        d = t['data']
        sample = str(d[:3])

        # Best lineup tables (have 位置 column, rows > 100)
        if t['cols'] == 7 and '位置' in ','.join(t['headers']) and t['rows'] > 100:
            all_nba_teams.append(t)
            continue

        final.append(t)

    # Sort all-NBA tables: 1st team, 2nd team, 3rd team
    for tn in ['最佳阵容1阵', '最佳阵容2阵', '最佳阵容3阵',
               '最佳防守阵容1阵', '最佳防守阵容2阵',
               '新秀最佳阵容1阵', '新秀最佳阵容2阵']:
        target_rows = {'最佳阵容1阵': 391, '最佳阵容2阵': 389, '最佳阵容3阵': 180,
                       '最佳防守阵容1阵': 285, '最佳防守阵容2阵': 284,
                       '新秀最佳阵容1阵': 313, '新秀最佳阵容2阵': 177}
        for t in all_nba_teams:
            if t['rows'] == target_rows.get(tn, 0):
                t['name'] = tn
                final.append(t)
                all_nba_teams.remove(t)
                break

    # Any remaining
    for t in all_nba_teams:
        final.append(t)

    result = {'tables': final}
    out_dir = 'C:/Users/LeeeYF/Desktop/2kstats/extract'
    with open(out_dir + '/latest_extract.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(out_dir + '/done.txt', 'w') as f:
        f.write(f'OK: {len(final)} tables')
except Exception as e:
    with open('C:/Users/LeeeYF/Desktop/2kstats/extract/error.txt', 'w') as f:
        f.write(str(e))
