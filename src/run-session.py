#!/usr/bin/env python3
"""Own one unchanged application runtime and its scoped input-state bridge."""
import ctypes,fcntl,hashlib,json,os,signal,subprocess,sys,time,uuid
from pathlib import Path
V=Path(__file__).resolve().parent
FINAL=Path(os.environ.get('OTZAR_FINAL_ROOT','/mnt/data/AAG/Otzar-Wine/final/Otzar-Wine-3.2.0'))
S=FINAL/'state'
diagnostic=sys.argv[1:]==['--diagnostic']
if sys.argv[1:] and not diagnostic:raise SystemExit('Usage: run-session.py [--diagnostic]')
uid=os.getuid();runtime=Path(f'/run/user/{uid}')
lock=(runtime/'aag-otzar-input-sync.lock').open('a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('INPUT_SYNC_SESSION_ALREADY_RUNNING')
for name,digest in json.loads((V/'baseline.json').read_text()).items():
 if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise SystemExit('BASELINE_CHANGED: '+name)
def processes():
 rows={}
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=[os.fsdecode(a) for a in (p/'cmdline').read_bytes().split(b'\0') if a]
   stat=(p/'stat').read_text().rsplit(')',1)[1].split();rows[int(p.name)]=(int(stat[1]),args)
  except (OSError,ValueError):continue
 return rows
if any(a and Path(a[0]).name=='Xwayland' and ':201' in a for _,a in processes().values()):
 raise SystemExit('CLOSE_EXISTING_X201_SESSION_FIRST')
if not (runtime/'bus').is_socket():raise SystemExit('USER_SESSION_BUS_UNAVAILABLE')
wayland=os.environ.get('WAYLAND_DISPLAY','wayland-0')
socket=Path(wayland) if wayland.startswith('/') else runtime/wayland
if not socket.is_socket():raise SystemExit('WAYLAND_SOCKET_UNAVAILABLE')
session=S/'input-sync-runs'/('session-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
control=session/'control';control.mkdir(parents=True)
window_control=session/'window-control';window_control.mkdir()
window_done=session/'window-control-done';window_done.mkdir()
env=dict(os.environ,DBUS_SESSION_BUS_ADDRESS=f'unix:path={runtime}/bus',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=wayland,
 AAG_INPUT_RUNTIME=str(V),AAG_INPUT_CONTROL=str(control),AAG_INPUT_RUNNER=str(V/('diagnostics/runner.py' if diagnostic else 'original-runner.py')),
 AAG_WINDOW_CONTROL=str(window_control),AAG_PATCHED_ASAR=str(V/'overlay/app.asar'),AAG_SCALE_INDEX=str(V/'index-scale15.html'))
stop=False;owner=None;bridge=None;mainpid=None;code=0
status=(session/'supervisor.jsonl').open('a',buffering=1)
def log(kind,**data):
 row=dict(time=time.time(),kind=kind,**data);status.write(json.dumps(row)+'\n');print(json.dumps(row),flush=True)
def request_stop(*_):
 global stop
 stop=True
for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,request_stop)
def parent_guard():
 ctypes.CDLL(None).prctl(1,signal.SIGTERM)
def find_main(root):
 rows=processes()
 for pid,(parent,args) in rows.items():
  if not args or not args[0].lower().endswith('otzar.exe') or '--touch-events=enabled' not in args or any(a.startswith('--type=') for a in args):continue
  seen=set()
  while parent in rows and parent not in seen:
   if parent==root:return pid
   seen.add(parent);parent=rows[parent][0]
 return None

def runner_logs():
 try:
  lines=(session/'application-session.log').read_text(errors='replace').splitlines()
 except OSError:
  return None
 for line in lines:
  try: row=json.loads(line)
  except json.JSONDecodeError: continue
  if row.get('event')=='production_log_session':
   raw=Path(row['path'])
   try:return S/raw.relative_to('/state')
   except ValueError:return None
 return None

def runner_request(action):
 name='window-'+uuid.uuid4().hex
 target=control/(name+'.json');temp=target.with_suffix('.tmp')
 temp.write_text(json.dumps({'action':action}));temp.replace(target)
 deadline=time.monotonic()+6
 while time.monotonic()<deadline:
  logs=runner_logs()
  if logs:
   reply=logs/('reply-'+name+'.json')
   if reply.exists():
    try:return json.loads(reply.read_text())
    except json.JSONDecodeError:pass
  time.sleep(.04)
 return {'ok':False,'error':'RUNNER_REPLY_TIMEOUT','action':action}

def host_minimize():
 bus=dict(os.environ,DBUS_SESSION_BUS_ADDRESS=f'unix:path={runtime}/bus',XDG_RUNTIME_DIR=str(runtime))
 args=['gdbus','call','--session','--dest','org.gnome.Shell',
       '--object-path','/org/gnome/Shell/Extensions/RunOrRaise',
       '--method','org.gnome.Shell.Extensions.RunOrRaise.Call',
       ':minimize-when-unfocused,,,Xwayland on :201']
 run=subprocess.run(args,env=bus,capture_output=True,text=True,timeout=4)
 return {'ok':run.returncode==0 and 'Success' in run.stdout,
         'returncode':run.returncode,'stdout':run.stdout.strip(),'stderr':run.stderr.strip()}

window_seen=set()
def service_window_control():
 for request in sorted(window_control.glob('*.json')):
  if request.name in window_seen:continue
  window_seen.add(request.name)
  result={'ok':False,'error':'UNPROCESSED'}
  action=None
  try:
   if request.stat().st_size>4096:raise ValueError('REQUEST_TOO_LARGE')
   data=json.loads(request.read_text());action=data.get('action')
   if action=='maximize':result=runner_request('fit-native')
   elif action=='minimize':result=host_minimize()
   else:raise ValueError('UNKNOWN_WINDOW_ACTION')
  except Exception as error:
   result={'ok':False,'error':type(error).__name__+': '+str(error)}
  log('WINDOW_CONTROL',action=action,request=request.name,result=result)
  try:request.replace(window_done/request.name)
  except OSError:pass
appout=(session/'application-session.log').open('wb')
bridgeout=(session/'bridge-stderr.log').open('wb')
try:
 owner=subprocess.Popen([str(V/'launch.sh'),'normal'],env=env,stdout=appout,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=parent_guard)
 (session/'owner.json').write_text(json.dumps(dict(owner=owner.pid,diagnostic=diagnostic,control=str(control),version='3.2.0')))
 log('SESSION_STARTED',owner=owner.pid,session=str(session),diagnostic=diagnostic)
 deadline=time.monotonic()+210
 while not stop and owner.poll() is None:
  if mainpid is None:
   mainpid=find_main(owner.pid)
   if mainpid:
    bridge=subprocess.Popen([sys.executable,str(V/'bridge.py'),str(mainpid),r'Z:\aag-input-sync\input-filter.exe',str(session/'bridge.jsonl')],env=env,stdout=bridgeout,stderr=subprocess.STDOUT,preexec_fn=parent_guard)
    log('BRIDGE_STARTED',application=mainpid,bridge=bridge.pid)
   elif time.monotonic()>deadline:raise RuntimeError('APPLICATION_START_TIMEOUT')
  elif bridge.poll() is not None and Path(f'/proc/{mainpid}').exists():
   raise RuntimeError('INPUT_BRIDGE_EXITED: '+str(bridge.returncode))
  if mainpid is not None:service_window_control()
  if (session/'application-session.log').stat().st_size>4*1024*1024:raise RuntimeError('SESSION_LOG_LIMIT')
  time.sleep(.05)
 if owner.poll() is not None:code=owner.returncode
except Exception as error:
 code=1;log('SESSION_ERROR',error=str(error))
finally:
 if bridge and bridge.poll() is None:
  bridge.terminate()
  try:bridge.wait(timeout=4)
  except subprocess.TimeoutExpired:bridge.kill();bridge.wait()
 if owner and owner.poll() is None:
  p=control/('stop-'+uuid.uuid4().hex+'.json');q=p.with_suffix('.tmp')
  q.write_text('{"action":"stop"}');q.replace(p)
  try:owner.wait(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(owner.pid,signal.SIGTERM)
   try:owner.wait(timeout=8)
   except subprocess.TimeoutExpired:os.killpg(owner.pid,signal.SIGKILL);owner.wait()
 appout.close();bridgeout.close();log('SESSION_STOPPED',returncode=code);status.close();lock.close()
raise SystemExit(code)
