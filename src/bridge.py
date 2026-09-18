#!/usr/bin/env python3
"""Synchronous physical-state certificates for an owned Wine input filter."""
from pathlib import Path
import json,os,select,signal,subprocess,sys,time
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE.parent))
from kernel_modifiers import KernelModifiers
from xguard import XGuard
PID=int(sys.argv[1]);WINPATH=sys.argv[2];LOG=Path(sys.argv[3])
extra=sys.argv[4:]
if extra not in ([],['--no-timer']):raise SystemExit('INVALID_ARGUMENTS')
stat=Path(f'/proc/{PID}/stat')
def identity():return stat.read_text().rsplit(')',1)[1].split()[19]
initial=identity();running=True;checks=0;repairs=0;ready=False
if Path(f'/proc/{PID}').stat().st_uid!=os.getuid():raise SystemExit('TARGET_UID_MISMATCH')
logfile=LOG.open('a',buffering=1)
def log(kind,**data):
    if logfile.tell()>2*1024*1024:return
    logfile.write(json.dumps(dict(time=time.time(),kind=kind,**data))+'\n')
def stop(*_):
    global running
    running=False
for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,stop)
k=KernelModifiers();x=XGuard()
cmd=['nsenter','--target',str(PID),'--user','--mount','--preserve-credentials','/usr/bin/env',
 'DISPLAY=:201','HOME='+os.environ.get('HOME','/home/user'),'WINEPREFIX=/state/prefix','WINEDEBUG=-all',
 '/opt/wine-devel/bin/wine',WINPATH,*extra]
worker=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
os.set_blocking(worker.stdout.fileno(),False);os.set_blocking(worker.stderr.fileno(),False)
buffer=b'';deadline=time.monotonic()+10
log('BRIDGE_START',target=PID,worker=worker.pid,synchronous=True,timer=not bool(extra))
try:
    while running:
        try:
            if identity()!=initial:break
        except OSError:break
        available=select.select([worker.stdout,worker.stderr],[],[],.2)[0]
        if worker.stderr in available:
            text=os.read(worker.stderr.fileno(),4096)
            if text:log('NATIVE_STDERR',text=text.decode(errors='replace')[:400])
        if worker.stdout in available:
            chunk=os.read(worker.stdout.fileno(),16384)
            if not chunk:raise RuntimeError('NATIVE_FILTER_ENDED')
            buffer+=chunk
            if len(buffer)>65536:raise RuntimeError('PROTOCOL_SIZE_LIMIT')
            while b'\n' in buffer:
                line,buffer=buffer.split(b'\n',1)
                if not line.strip():continue
                data=json.loads(line);kind=data.get('kind')
                if kind=='CHECK':
                    start=time.monotonic();physical=k.snapshot();xm=x.released()
                    allowed=physical['released_mask']&xm if physical['healthy'] else 0
                    request=int(data['id']);checks+=1
                    worker.stdin.write(f'{request} {allowed}\n'.encode())
                    log('CERTIFICATE',id=request,allowed=allowed,physical=physical,xmask=xm,latency_ms=(time.monotonic()-start)*1000)
                else:
                    if kind=='FILTER_READY':ready=True
                    if kind=='REPAIR':repairs+=1
                    log('NATIVE',result=data)
        if not ready and time.monotonic()>deadline:raise RuntimeError('FILTER_START_TIMEOUT')
finally:
    try:worker.stdin.close();worker.wait(timeout=2)
    except (OSError,subprocess.TimeoutExpired):
        worker.terminate()
        try:worker.wait(timeout=2)
        except subprocess.TimeoutExpired:worker.kill();worker.wait()
    x.close();k.close();log('BRIDGE_STOPPED',checks=checks,repairs=repairs,ready=ready);logfile.close()
