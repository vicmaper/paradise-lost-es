"""malie_cipher.py - cifrado LIBP de MALIE (variante de Camellia).
Basado en el de KKK, pero la clave ya no va fija: se elige con set_key().
Si numpy esta instalado descifra mucho mas rapido (opcional)."""
import struct
M = 0xFFFFFFFF
KEY = None
def set_key(k):
    global KEY, _NK
    KEY = list(k); _NK = None
def rotl(v,s): return ((v<<s)|(v>>(32-s)))&M
def rotr(v,s): return ((v>>s)|(v<<(32-s)))&M
def bswap(v): return ((v&0xFF)<<24)|((v&0xFF00)<<8)|((v>>8)&0xFF00)|((v>>24)&0xFF)
S1=[0x70,0x82,0x2C,0xEC,0xB3,0x27,0xC0,0xE5,0xE4,0x85,0x57,0x35,0xEA,0x0C,0xAE,0x41,0x23,0xEF,0x6B,0x93,0x45,0x19,0xA5,0x21,0xED,0x0E,0x4F,0x4E,0x1D,0x65,0x92,0xBD,0x86,0xB8,0xAF,0x8F,0x7C,0xEB,0x1F,0xCE,0x3E,0x30,0xDC,0x5F,0x5E,0xC5,0x0B,0x1A,0xA6,0xE1,0x39,0xCA,0xD5,0x47,0x5D,0x3D,0xD9,0x01,0x5A,0xD6,0x51,0x56,0x6C,0x4D,0x8B,0x0D,0x9A,0x66,0xFB,0xCC,0xB0,0x2D,0x74,0x12,0x2B,0x20,0xF0,0xB1,0x84,0x99,0xDF,0x4C,0xCB,0xC2,0x34,0x7E,0x76,0x05,0x6D,0xB7,0xA9,0x31,0xD1,0x17,0x04,0xD7,0x14,0x58,0x3A,0x61,0xDE,0x1B,0x11,0x1C,0x32,0x0F,0x9C,0x16,0x53,0x18,0xF2,0x22,0xFE,0x44,0xCF,0xB2,0xC3,0xB5,0x7A,0x91,0x24,0x08,0xE8,0xA8,0x60,0xFC,0x69,0x50,0xAA,0xD0,0xA0,0x7D,0xA1,0x89,0x62,0x97,0x54,0x5B,0x1E,0x95,0xE0,0xFF,0x64,0xD2,0x10,0xC4,0x00,0x48,0xA3,0xF7,0x75,0xDB,0x8A,0x03,0xE6,0xDA,0x09,0x3F,0xDD,0x94,0x87,0x5C,0x83,0x02,0xCD,0x4A,0x90,0x33,0x73,0x67,0xF6,0xF3,0x9D,0x7F,0xBF,0xE2,0x52,0x9B,0xD8,0x26,0xC8,0x37,0xC6,0x3B,0x81,0x96,0x6F,0x4B,0x13,0xBE,0x63,0x2E,0xE9,0x79,0xA7,0x8C,0x9F,0x6E,0xBC,0x8E,0x29,0xF5,0xF9,0xB6,0x2F,0xFD,0xB4,0x59,0x78,0x98,0x06,0x6A,0xE7,0x46,0x71,0xBA,0xD4,0x25,0xAB,0x42,0x88,0xA2,0x8D,0xFA,0x72,0x07,0xB9,0x55,0xF8,0xEE,0xAC,0x0A,0x36,0x49,0x2A,0x68,0x3C,0x38,0xF1,0xA4,0x40,0x28,0xD3,0x7B,0xBB,0xC9,0x43,0xC1,0x15,0xE3,0xAD,0xF4,0x77,0xC7,0x80,0x9E]
rl8=lambda x:((x<<1)|(x>>7))&0xFF
rr8=lambda x:((x<<7)|(x>>1))&0xFF
B1=[s*0x01010100 for s in S1]
B2=[rl8(s)*0x00010101 for s in S1]
B3=[rr8(s)*0x01000101 for s in S1]
B4=[S1[rl8(x)]*0x01010001 for x in range(256)]
def F(t): return B3[(t>>8)&255]^B4[t&255]^B2[(t>>16)&255]^B1[t>>24]
def G(t): return B4[(t>>8)&255]^B1[t&255]^B3[(t>>16)&255]^B2[t>>24]
def _roundA(d,k,kt):
    U=F(kt[k+2]^d[0]); D=G(kt[k+3]^d[1]); d[2]^=U^D; d[3]^=U^D^rotr(U,8)
def _roundB(d,k,kt):
    U=F(kt[k]^d[2]); D=G(kt[k+1]^d[3]); d[0]^=U^D; d[1]^=U^D^rotr(U,8)
def _fl(d,k,kt):
    d[1]^=rotl(d[0]&kt[k+2],1); d[0]^=(d[1]|kt[k+3]); d[2]^=(d[3]|kt[k+1]); d[3]^=rotl(d[2]&kt[k],1)
def _fl_inv(d,k,kt):
    d[3]^=rotl(d[2]&kt[k],1); d[2]^=(d[3]|kt[k+1]); d[0]^=(d[1]|kt[k+3]); d[1]^=rotl(d[0]&kt[k+2],1)
def decrypt_block(blk,offset,kt=None):
    kt=kt or KEY
    d=list(struct.unpack('<4L',blk)); r=((offset>>4)&15)+16
    d=[rotl(d[0],r),rotr(d[1],r),rotl(d[2],r),rotr(d[3],r)]
    d=[bswap(x) for x in d]
    for i in range(4): d[i]^=kt[i]
    k=4
    for i in range(3):
        for j in range(3):
            _roundA(d,k,kt); _roundB(d,k,kt); k+=4
        if i<2: _fl(d,k,kt); k+=4
    d[0],d[2]=d[2],d[0]; d[1],d[3]=d[3],d[1]
    for i in range(4): d[i]^=kt[k+i]
    d=[bswap(x) for x in d]
    return struct.pack('<4L',*d)
def encrypt_block(blk,offset,kt=None):
    kt=kt or KEY
    d=list(struct.unpack('<4L',blk)); r=((offset>>4)&15)+16
    d=[bswap(x) for x in d]
    for i in range(4): d[i]^=kt[48+i]
    d[0],d[2]=d[2],d[0]; d[1],d[3]=d[3],d[1]
    ks=[];k=4
    for i in range(3):
        for j in range(3): ks.append(('R',k)); k+=4
        if i<2: ks.append(('F',k)); k+=4
    for typ,k in reversed(ks):
        if typ=='R': _roundB(d,k,kt); _roundA(d,k,kt)
        else: _fl_inv(d,k,kt)
    for i in range(4): d[i]^=kt[i]
    d=[bswap(x) for x in d]
    d=[rotr(d[0],r),rotl(d[1],r),rotr(d[2],r),rotl(d[3],r)]
    return struct.pack('<4L',*d)

# ---------- version rapida con numpy (solo descifrar) ----------
try:
    import numpy as np
except Exception:
    np = None
_NK = None
def _np_tables():
    global _T
    _T = [np.array(t, dtype=np.uint32) for t in (B1,B2,B3,B4)]
_T = None
def _nrotl(v,s): return ((v<<np.uint32(s))|(v>>np.uint32(32-s)))
def _nrotr(v,s): return ((v>>np.uint32(s))|(v<<np.uint32(32-s)))
def _nrotl_var(v,s): return ((v<<s)|(v>>(32-s)))
def _nrotr_var(v,s): return ((v>>s)|(v<<(32-s)))
def _nbswap(v): return v.byteswap()
def _nF(t):
    T1,T2,T3,T4=_T; return T3[(t>>8)&255]^T4[t&255]^T2[(t>>16)&255]^T1[t>>24]
def _nG(t):
    T1,T2,T3,T4=_T; return T4[(t>>8)&255]^T1[t&255]^T3[(t>>16)&255]^T2[t>>24]
def decrypt_fast(data, start):
    """descifra bloques de 16 bytes con numpy; start = posicion (multiplo de 16) en el archivo"""
    if _T is None: _np_tables()
    kt=[np.uint32(x) for x in KEY]
    a=np.frombuffer(bytes(data),dtype='<u4').reshape(-1,4).copy()
    pos=np.arange(a.shape[0],dtype=np.uint32)*np.uint32(16)+np.uint32(start)
    r=((pos>>np.uint32(4))&np.uint32(15))+np.uint32(16)
    d=[_nrotl_var(a[:,0],r),_nrotr_var(a[:,1],r),_nrotl_var(a[:,2],r),_nrotr_var(a[:,3],r)]
    d=[_nbswap(x)^kt[i] for i,x in enumerate(d)]
    k=4
    for i in range(3):
        for j in range(3):
            U=_nF(kt[k+2]^d[0]); D=_nG(kt[k+3]^d[1]); d[2]=d[2]^U^D; d[3]=d[3]^U^D^_nrotr(U,8)
            U=_nF(kt[k]^d[2]); D=_nG(kt[k+1]^d[3]); d[0]=d[0]^U^D; d[1]=d[1]^U^D^_nrotr(U,8)
            k+=4
        if i<2:
            d[1]=d[1]^_nrotl(d[0]&kt[k+2],1); d[0]=d[0]^(d[1]|kt[k+3]); d[2]=d[2]^(d[3]|kt[k+1]); d[3]=d[3]^_nrotl(d[2]&kt[k],1)
            k+=4
    d=[d[2],d[3],d[0],d[1]]
    d=[_nbswap(d[i]^kt[k+i]) for i in range(4)]
    return np.stack(d,axis=1).astype('<u4').tobytes()

def crypt(data,fn,start=0):
    if fn is decrypt_block and np is not None and len(data)>=4096:
        return decrypt_fast(data,start)
    out=bytearray(len(data))
    for i in range(0,len(data),16):
        out[i:i+16]=fn(bytes(data[i:i+16]),start+i)
    return bytes(out)
