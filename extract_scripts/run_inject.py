"""Inject extraction code into Roster Editor - auto-detect correct PID."""
import frida, time, os, json, re
from datetime import datetime

EXTRACT_DIR = r'C:\Users\LeeeYF\Desktop\2kstats\extract'

# Find Roster Editor PIDs
pids = []
for p in frida.get_local_device().enumerate_processes():
    if 'Roster Editor Trial' in p.name:
        pids.append(p.pid)

if not pids:
    raise Exception('Roster Editor not running!')

print(f'PIDs: {pids}')

# Read inject code
with open(r'C:\Users\LeeeYF\Desktop\2kstats\extract_scripts\inject_code.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

# Escape for Frida JS string
escaped = (py_code
    .replace('\\', '\\\\')
    .replace('\n', '\\n')
    .replace('"', '\\"'))

code_tpl = '''var python=Process.findModuleByName("python311.dll");
if(python){{
var ex=python.enumerateExports();
var pr=null,ge=null,gr=null;
ex.forEach(function(e){{if(e.name=="PyRun_SimpleString")pr=e.address;if(e.name=="PyGILState_Ensure")ge=e.address;if(e.name=="PyGILState_Release")gr=e.address;}});
var en=new NativeFunction(ge,"int",[]);
var re=new NativeFunction(gr,"void",["int"]);
var rn=new NativeFunction(pr,"int",["pointer"]);
var g=en();
var s=Memory.allocUtf8String("{code}");
rn(s);
re(g);
send({{ok:1}});
}}else{{send({{ok:0}});}}'''

# Try each PID
for test_pid in sorted(pids):
    try:
        code = code_tpl.format(code=escaped)
        session = frida.attach(test_pid)
        ok = []
        script = session.create_script(code)
        script.on('message', lambda msg, data: ok.append(msg.get('payload', {}).get('ok', 0)))
        script.load()
        for _ in range(10):
            time.sleep(0.3)
            if ok and ok[0] == 1:
                print(f'PID {test_pid}: SUCCESS')
                time.sleep(2)
                session.detach()
                jf = os.path.join(EXTRACT_DIR, 'latest_extract.json')
                if os.path.exists(jf):
                    result = json.load(open(jf, encoding='utf-8'))
                    tables = result.get('tables', result if isinstance(result, list) else [])
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    run_dir = os.path.join(EXTRACT_DIR, ts)
                    os.makedirs(run_dir, exist_ok=True)
                    for ti, t in enumerate(tables):
                        name = t.get('name', f'Table{ti+1}')
                        safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)[:60]
                        csv_path = os.path.join(run_dir, f'{safe_name}.csv')
                        if os.path.exists(csv_path):
                            csv_path = os.path.join(run_dir, f'{safe_name}_{ti+1}.csv')
                        with open(csv_path, 'w', encoding='utf-8-sig') as csvf:
                            csvf.write(','.join(t['headers']) + '\n')
                            for row in t['data']:
                                csvf.write(','.join(str(c) for c in row) + '\n')
                        print(f'  {name}: {t["rows"]}x{t["cols"]} -> {ts}/{os.path.basename(csv_path)}')
                        for r in t['data'][:2]:
                            print(f'    {r}')
                    with open(os.path.join(run_dir, 'all_data.json'), 'w', encoding='utf-8') as jf2:
                        json.dump(result, jf2, indent=2, ensure_ascii=False)
                import sys; sys.exit(0)
        session.detach()
    except Exception as e:
        pass

print('All PIDs failed')
