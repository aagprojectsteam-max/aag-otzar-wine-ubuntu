# AAG_WINE117_RENDER_AB_20260917
"""Owned nested display and real app runner; consumes bounded local GUI commands."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import time
from lab_x11 import LabX

state=Path('/state');# AAG_PER_LAUNCH_SESSION_LOGS_20260915
# Each production invocation owns a unique log directory.
# This removes the one-shot E2E assumption without deleting
# historical logs or touching persistent Wine/application state.
logs_root=state/'logs'
logs_root.mkdir(exist_ok=True)

session_stamp=time.strftime(
    '%Y%m%d-%H%M%S'
)

session_base='session-'+session_stamp
logs=logs_root/session_base

suffix=0
while logs.exists():
    suffix+=1
    logs=logs_root/(
        session_base+'-%02d' % suffix
    )

logs.mkdir()

print(
    json.dumps({
        'event':'production_log_session',
        'path':str(logs),
    }),
    flush=True,
);control=state/'control';control.mkdir(exist_ok=True)
runtime=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'));runtime.mkdir(parents=True,exist_ok=True);runtime.chmod(0o700)
app='C:\\OtzarApp\\OtzarLocal\\launcher\\bin\\x64\\app\\otzar.exe'

graphics_file = state/'graphics-flags.json'
if graphics_file.exists():
    app_flags = json.loads(graphics_file.read_text())["flags"]
elif (state/'software-graphics.json').exists():
    app_flags = ['--disable-gpu']
else:
    app_flags = []

wine='/opt/wine-devel/bin/wine'
def event(**row):print(json.dumps(row),flush=True)
def record(path,row):
    with path.open('x') as f:json.dump(row,f,indent=2);f.write('\n')
if not os.statvfs('/content').f_flag & os.ST_RDONLY:raise RuntimeError('Content not read-only')
if not Path('/content/otzardisk/data').is_dir():raise RuntimeError('Content layout missing')
def preflight():
    pre=logs/'preflight';pre.mkdir()
    with (pre/'temp-baseline.txt').open('xb') as out:
        env=dict(os.environ,ELECTRON_RUN_AS_NODE='1');env.pop('TEMP',None);env.pop('TMP',None)
        subprocess.run([wine,app,'Z:\\probe-temp.cjs'],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=30,check=True)
    with (pre/'engine.txt').open('xb') as out:
        env=dict(os.environ,ELECTRON_RUN_AS_NODE='1')
        r=subprocess.run([wine,app,'Z:\\preflight.cjs'],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=40)
    if r.returncode:raise RuntimeError('Candidate path/serial preflight failed')
    rows=[json.loads(l) for l in (pre/'engine.txt').read_text(errors='replace').splitlines() if l.startswith('{')]
    if not rows or rows[-1].get('event')!='e2e_preflight':raise RuntimeError('Missing path/serial evidence')
    record(pre/'result.json',rows[-1]);event(event='preflight_pass',result=rows[-1])
    for p in state.glob('bridge-*.jsonl'):shutil.move(p,pre/p.name)
# AAG_REUSABLE_RUNNER_LOGS_20260915
# Production is reusable. Runtime logs belong to the current launch,
# unlike the original one-shot E2E state.
#
# Preserve persistent prefix/application state, but replace only
# transient runner output files on each new launcher invocation.
xwayland_log = logs/'xwayland.txt'
xwayland_log.unlink(missing_ok=True)
xlog=xwayland_log.open('xb')
xserver=subprocess.Popen(['/usr/bin/Xwayland',':201','-geometry','1920x1200','-fullscreen','-shm','-nolisten','tcp','-ac','-terminate'],stdout=xlog,stderr=subprocess.STDOUT)
child=None;stream=None;lab=None;run=0;run_dir=None;deadline=time.monotonic()+604800
try:
    ready=time.monotonic()+15
    while time.monotonic()<ready:
        if xserver.poll() is not None:raise RuntimeError('Nested X server exited')
        if Path('/tmp/.X11-unix/X201').exists():
            try:lab=LabX();break
            except RuntimeError:pass
        time.sleep(.2)
    if lab is None:raise RuntimeError('Nested X display not ready')
    # AAG_REUSABLE_TOP_LEVEL_LOGS_20260915
    wineboot_log=logs/'wineboot.txt'
    wineboot_log.unlink(missing_ok=True)
    with wineboot_log.open('xb') as out:
        subprocess.run([wine,'wineboot','-u'],stdout=out,stderr=subprocess.STDOUT,timeout=150,check=True)
    logical_drives_log=logs/'logical-drives.txt'
    logical_drives_log.unlink(missing_ok=True)
    with logical_drives_log.open('xb') as out:
        subprocess.run([wine,'Z:\\logical-drive-probe.exe'],stdout=out,stderr=subprocess.STDOUT,timeout=30,check=True)
    app_drives_log=logs/'app-drives.txt'
    app_drives_log.unlink(missing_ok=True)
    with app_drives_log.open('xb') as out:
        subprocess.run([wine,app,'Z:\\check-app-drives.cjs'],env=dict(os.environ,ELECTRON_RUN_AS_NODE='1'),stdout=out,stderr=subprocess.STDOUT,timeout=40,check=True)
    preflight()
    def collect_bridge():
        for p in state.glob('bridge-*.jsonl'):
            shutil.move(p,run_dir/p.name)
    def start():
        global child,stream,run,run_dir
        if child is not None and child.poll() is None:raise ValueError('Previous application still active')
        if run_dir:collect_bridge()
        if stream:stream.close()
        run+=1;run_dir=logs/('run-%02d'%run);run_dir.mkdir()
        stream=(run_dir/'app.txt').open('xb')
        # AAG_RECOVERY_X201_TRUEGOOD_20260917
        scale_flags=[
            '--touch-events=enabled',
            '--force-device-scale-factor=1.5',
            '--in-process-gpu', '--disable-gpu-compositing']
        child=subprocess.Popen([wine,app,*scale_flags],stdout=stream,stderr=subprocess.STDOUT,
          cwd='/state/prefix/drive_c/OtzarApp/OtzarLocal/launcher/bin/x64/app')


        # AAG_TOUCH_X11_FOCUS_FIX_20260917
        touch_focus = subprocess.Popen(
            ['/usr/bin/bash','/touch-focus.sh'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        record(run_dir/'launch.json',{'command':[wine,app,*app_flags,*scale_flags],'graphics_flags':app_flags,'scale_flags':scale_flags,'diagnostic_app_flags':[],
          'ELECTRON_RUN_AS_NODE':os.environ.get('ELECTRON_RUN_AS_NODE'),
          'ELECTRON_ENABLE_LOGGING':os.environ.get('ELECTRON_ENABLE_LOGGING'),
          'WINEDEBUG':os.environ.get('WINEDEBUG'),
          'OPENCV_DUMP_ERRORS':os.environ.get('OPENCV_DUMP_ERRORS'),
          'OPENCV_FOR_THREADS_NUM':os.environ.get('OPENCV_FOR_THREADS_NUM'),
          'wine_initialization':['wine','wineboot','-u'],
          'wineprefix':os.environ['WINEPREFIX'],'content_readonly':True,'nested_display':':201',
          'unix_pid':child.pid,'started_unix':time.time()})
        event(event='application_started',run=run,pid=child.pid)
    start();seen=set();last=time.monotonic();auto_at=time.monotonic()+15;exit_reported=False
    while time.monotonic()<deadline:
        lab.pump()
        if xserver.poll() is not None:raise RuntimeError('Nested display lost')
        if (run_dir/'app.txt').stat().st_size>16*1024*1024:raise RuntimeError('Application log size bound')
        if time.monotonic()>auto_at:
            lab.screenshot(run_dir/'initial.png');record(run_dir/'initial-windows.json',lab.windows());auto_at=float('inf')
            event(event='initial_capture',run=run,path=str(run_dir/'initial.png'))
        if child.poll() is not None and not exit_reported:
            record(run_dir/'exit.json',{'exit_code':child.returncode,'forced':False,'time':time.time()})
            event(event='application_exited',run=run,exit_code=child.returncode)
            exit_reported=True

            # Production lifecycle:
            # the Windows application has exited naturally.
            # Leave the runner immediately so its finally block
            # closes the LabX connection and terminates Xwayland.
            break
        for command in sorted(control.glob('*.json')):
            if command.name in seen:continue
            seen.add(command.name)
            if command.stat().st_size>16384:raise ValueError('Command size bound')
            req=json.loads(command.read_text());action=req['action'];reply={'action':action,'run':run}
            try:
                if action=='snapshot':
                    image=run_dir/('capture-'+command.stem+'.png');lab.screenshot(image);reply.update(path=str(image),windows=lab.windows())
                elif action=='windows':reply['windows']=lab.windows()
                elif action=='fit':lab.fit(int(req['window']))
                elif action=='fit-native':
                    with (run_dir/('fit-'+command.stem+'.txt')).open('xb') as out:
                        subprocess.run([wine,'Z:\\fit-app-window.exe'],stdout=out,stderr=subprocess.STDOUT,timeout=15,check=True)
                elif action=='click':lab.click(int(req['x']),int(req['y']),int(req.get('button',1)))
                elif action=='key':lab.key(req['key'])
                elif action=='paste':lab.paste(req['text'])
                elif action=='close':lab.key('Alt_L+F4')
                elif action=='restart':
                    start();exit_reported=False;auto_at=time.monotonic()+15
                elif action=='stop':deadline=0
                else:raise ValueError('Unknown action')
                reply['ok']=True
            except Exception as e:reply.update(ok=False,error=type(e).__name__,message=str(e))
            record(logs/('reply-'+command.stem+'.json'),reply);event(event='command_result',**reply)
        if time.monotonic()-last>25:
            event(event='status',run=run,app_running=child.poll() is None,log_bytes=(run_dir/'app.txt').stat().st_size);last=time.monotonic()
        time.sleep(.1)
finally:
    if child and child.poll() is None:
        if lab:lab.key('Alt_L+F4')
        try:child.wait(timeout=8)
        except subprocess.TimeoutExpired:
            child.terminate()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait()
            record(run_dir/'forced-stop.json',{'reason':'Owned runner ending','exit_code':child.returncode})
    if run_dir:
        for p in state.glob('bridge-*.jsonl'):shutil.move(p,run_dir/p.name)
    if stream:stream.close()
    xserver.terminate()
    try:xserver.wait(timeout=3)
    except subprocess.TimeoutExpired:xserver.kill();xserver.wait()
    xlog.close()
