#!/usr/bin/env python3
"""Reliable long-running jobs (renders, builds) for the Toys for Tots Railroad project.

    python3 tools/job.py run NAME [--cpu] [--mem GB] -- COMMAND ...   run COMMAND as job NAME, in the foreground of the caller.
                                                           Start it from a background shell; the shell's exit is the
                                                           completion notice. Refuses to start if:
                                                             * job NAME is already running (no duplicates)
                                                             * --cpu and two CPU-heavy jobs are already running
                                                             * the memory it reserves (--mem, default 1 GB for --cpu)
                                                               would take running jobs past MEM_BUDGET_GB.
                                                               A 6400-wide full-map render needs --mem 3.5.
    python3 tools/job.py status [NAME]                     running / done (exit code, minutes) / failed / crashed
    python3 tools/job.py list                              every job, newest first
    python3 tools/job.py guard                             exit 1 (and say why) while any job is running; run it
                                                           before editing rendering code
    python3 tools/job.py tail NAME [n]                     last n lines of the job's log
    python3 tools/job.py wait NAME ... [--max S]           return as soon as every named job has ended (exit 0 if all
                                                           succeeded, 1 if one failed or crashed, 2 if --max seconds
                                                           ran out first, default 540: below the shell's 600 s limit)

State lives in usmap/.jobs/: NAME.json (pid, command, start, the code fingerprint) while it runs, and NAME.done
(exit code, end time, whether rendering code changed during the run) written atomically when it ends. A job is
finished only when NAME.done exists. A process that is gone without a .done file crashed or was killed.
A render whose code changed while it ran is reported as "done, CODE CHANGED", so its output is never trusted blindly.
"""
import sys, os, json, time, hashlib, glob, subprocess, signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # usmap/
JOBS = os.path.join(ROOT, '.jobs')
CODE_GLOBS = ['../folk2/*.py', '../styles2/brush.py', '../styles2/kit.py', '../styles2/a.py', '../styles2/story.py',
              '*.py', 'engine10/*.py', 'lab8/*.py']
MAX_CPU = 2
MEM_BUDGET_GB = 5.5        # the workspace's memory cgroup allows 5979 MB for everything; a 6400-wide full-map render peaks near 3.2 GB

def code_fingerprint():
    h = hashlib.sha1(); files = sorted(f for g in CODE_GLOBS for f in glob.glob(os.path.join(ROOT, g)))
    for f in files: h.update(f.encode()); h.update(open(f, 'rb').read())
    return h.hexdigest()[:16], len(files)

def alive(pid):
    try: os.kill(pid, 0); return True
    except ProcessLookupError: return False
    except PermissionError: return True

def state(name):
    j, d = os.path.join(JOBS, name + '.json'), os.path.join(JOBS, name + '.done')
    if not os.path.exists(j): return None
    info = json.load(open(j))
    if os.path.exists(d):
        info.update(json.load(open(d))); info['state'] = 'done' if info['exit'] == 0 else 'failed'
    else: info['state'] = 'running' if alive(info['pid']) else 'crashed'
    return info

def running():
    return [s for s in (state(os.path.basename(p)[:-5]) for p in glob.glob(os.path.join(JOBS, '*.json'))) if s and s['state'] == 'running']

def describe(s):
    t = s.get('end', time.time()) - s['start']; extra = ''
    if s['state'] in ('done', 'failed'):
        extra = f" exit {s['exit']}" + (', CODE CHANGED during the run' if s.get('code_changed') else '')
    return f"{s['name']:24s} {s['state']:8s} {t / 60:6.1f} min{extra}  log {os.path.relpath(s['log'], ROOT)}"

def run(name, cmd, cpu, mem):
    os.makedirs(JOBS, exist_ok=True)
    s = state(name)
    if s and s['state'] == 'running': sys.exit(f'job {name} is already running (pid {s["pid"]}); not starting a duplicate')
    if cpu:
        busy = [r for r in running() if r.get('cpu')]
        if len(busy) >= MAX_CPU: sys.exit(f'{len(busy)} CPU jobs already running ({", ".join(r["name"] for r in busy)}); limit {MAX_CPU}')
    used = sum(r.get('mem', 0) for r in running())
    if used + mem > MEM_BUDGET_GB: sys.exit(f'not enough memory: running jobs reserve {used:.1f} GB, this one needs {mem:.1f} GB, budget {MEM_BUDGET_GB} GB')
    for ext in ('.json', '.done'):
        p = os.path.join(JOBS, name + ext)
        if os.path.exists(p): os.replace(p, p + '.prev')                     # keep the previous run's record
    log = os.path.join(JOBS, name + '.log'); fp, nf = code_fingerprint()
    with open(log, 'w') as L:
        proc = subprocess.Popen(cmd, stdout=L, stderr=subprocess.STDOUT, cwd=ROOT, start_new_session=True)
        info = dict(name=name, pid=proc.pid, cmd=cmd, cpu=cpu, mem=mem, start=time.time(), log=log, code=fp, code_files=nf)
        json.dump(info, open(os.path.join(JOBS, name + '.json'), 'w'))
        def stop(sig, _):
            os.killpg(proc.pid, signal.SIGTERM)
        signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
        rc = proc.wait()
    fp2, _ = code_fingerprint()
    done = dict(exit=rc, end=time.time(), code_changed=fp2 != fp)
    tmp = os.path.join(JOBS, name + '.done.tmp'); json.dump(done, open(tmp, 'w')); os.replace(tmp, os.path.join(JOBS, name + '.done'))
    info.update(done); info['state'] = 'done' if rc == 0 else 'failed'
    print(describe(info)); sys.exit(rc)

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == 'run':
        i = a.index('--'); opts = a[1:i]
        mem = float(opts[opts.index('--mem') + 1]) if '--mem' in opts else (1.0 if '--cpu' in opts else 0.2)
        run(opts[0], a[i + 1:], '--cpu' in opts, mem)
    elif a[0] in ('status', 'list'):
        names = [a[1]] if len(a) > 1 and a[0] == 'status' else [os.path.basename(p)[:-5] for p in sorted(glob.glob(os.path.join(JOBS, '*.json')), key=os.path.getmtime, reverse=True)]
        for n in names:
            s = state(n); print(describe(s) if s else f'{n}: no such job')
    elif a[0] == 'guard':
        r = running()
        if r: print('do not edit rendering code now; running: ' + ', '.join(x['name'] for x in r)); sys.exit(1)
        print('no jobs running')
    elif a[0] == 'wait':                                         # wait NAME [NAME ...] [--max SECONDS]
        mx = float(a[a.index('--max') + 1]) if '--max' in a else 540; names = [x for x in a[1:] if not x.startswith('--') and x != str(a[a.index('--max') + 1] if '--max' in a else '')]
        t0 = time.time()
        while True:
            st = {n: state(n) for n in names}
            if any(v is None for v in st.values()): sys.exit('unknown job: ' + ', '.join(n for n, v in st.items() if v is None))
            if all(v['state'] != 'running' for v in st.values()) or time.time() - t0 > mx: break
            time.sleep(2)
        for v in st.values(): print(describe(v))
        sys.exit(0 if all(v['state'] == 'done' for v in st.values()) else 2 if any(v['state'] == 'running' for v in st.values()) else 1)
    elif a[0] == 'tail':
        s = state(a[1]); n = int(a[2]) if len(a) > 2 else 15
        print(''.join(open(s['log']).readlines()[-n:]) if s else 'no such job')
    else: sys.exit(__doc__)
