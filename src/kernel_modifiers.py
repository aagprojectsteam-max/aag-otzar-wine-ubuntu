"""Host-only EVIOCGKEY snapshots. Never reads the input event stream or text."""
import fcntl,os,time
from pathlib import Path
# Bit groups: Super=1, Alt=2, Control=4, Shift=8. AltGr also protects Control.
GROUPS={125:1,126:1,56:2,100:6,29:4,97:4,42:8,54:8}
class KernelModifiers:
    def __init__(self):
        self.root=Path('/dev/input');self.devices=[];self.directory_stamp=None
        self.healthy=False;self.next_rescan=0;self.rescan()
    def close(self):
        for fd,keys in self.devices:
            try:os.close(fd)
            except OSError:pass
        self.devices=[]
    def rescan(self):
        self.close();self.healthy=True;self.next_rescan=time.monotonic()+1
        try:self.directory_stamp=self.root.stat().st_mtime_ns
        except OSError:self.healthy=False;return
        for path in sorted(self.root.glob('event*')):
            fd=None
            try:
                fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
                caps=bytearray(96);fcntl.ioctl(fd,0x80604521,caps,True)
                supported=[key for key in GROUPS if caps[key//8]&(1<<(key%8))]
                if supported:self.devices.append((fd,supported));fd=None
            except OSError:self.healthy=False
            finally:
                if fd is not None:os.close(fd)
        if not self.devices:self.healthy=False
    def snapshot(self):
        try:
            if self.root.stat().st_mtime_ns!=self.directory_stamp or (not self.healthy and time.monotonic()>self.next_rescan):self.rescan()
        except OSError:self.healthy=False
        down=0;healthy=self.healthy
        for fd,keys in self.devices:
            try:
                bitmap=bytearray(96);fcntl.ioctl(fd,0x80604518,bitmap,True)
                for key in keys:
                    if bitmap[key//8]&(1<<(key%8)):down|=GROUPS[key]
            except OSError:healthy=False
        self.healthy=healthy
        return {'released_mask':15&~down if healthy else 0,
                'captured_at':time.time(),'healthy':healthy,'device_count':len(self.devices)}
