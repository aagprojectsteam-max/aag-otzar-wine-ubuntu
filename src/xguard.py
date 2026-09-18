"""Read-only additional guard for modifiers held by XTEST or desktop input APIs."""
import ctypes as C
class MM(C.Structure):
    _fields_=[('n',C.c_int),('codes',C.POINTER(C.c_ubyte))]
class XGuard:
    def __init__(self):
        self.x=x=C.CDLL('libX11.so.6');P=C.c_void_p
        x.XOpenDisplay.argtypes=[C.c_char_p];x.XOpenDisplay.restype=P
        x.XQueryKeymap.argtypes=[P,P];x.XQueryKeymap.restype=C.c_int
        x.XGetModifierMapping.argtypes=[P];x.XGetModifierMapping.restype=C.POINTER(MM)
        x.XFreeModifiermap.argtypes=[C.POINTER(MM)];x.XCloseDisplay.argtypes=[P]
        self.d=x.XOpenDisplay(b':201')
        if not self.d:raise RuntimeError('PRIVATE_DISPLAY_UNAVAILABLE')
    def released(self):
        x=self.x;m=x.XGetModifierMapping(self.d)
        if not m:return 0
        try:
            n=m.contents.n
            if not 1<=n<=64:return 0
            groups={}
            for mod,g in ((0,8),(2,4),(3,2),(6,1),(7,6)):
                for j in range(n):
                    k=m.contents.codes[mod*n+j]
                    if k:groups[k]=groups.get(k,0)|g
            bits=C.create_string_buffer(32)
            if not x.XQueryKeymap(self.d,bits):return 0
            down=0
            for k,g in groups.items():
                if bits.raw[k//8]&(1<<(k%8)):down|=g
            return 15&~down
        finally:x.XFreeModifiermap(m)
    def close(self):self.x.XCloseDisplay(self.d)
