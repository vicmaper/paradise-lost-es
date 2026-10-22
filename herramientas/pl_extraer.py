#!/usr/bin/env python3
"""pl_extraer.py - lee los dataN.dat de MALIE (Paradise Lost) sin modificarlos.
Basado en kkk_extraer.py (KKK). Diferencia: la clave se detecta sola probando
las claves conocidas (malie_claves_garbro.json) contra la cabecera del .dat.

Uso:
  python pl_extraer.py DATA.dat --probar                 (detecta la clave y muestra la raiz)
  python pl_extraer.py DATA.dat --listar data/system
  python pl_extraer.py DATA.dat --buscar exec
  python pl_extraer.py DATA.dat --inventario lista.tsv   (todos los archivos con tamano)
  python pl_extraer.py DATA.dat data/system SALIDA       (extrae una carpeta, nombres exactos)
  python pl_extraer.py DATA.dat --todo SALIDA            (extrae todo; salta lo ya extraido)
Solo lee el .dat: no modifica nada.
"""
import sys, os, struct, json
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import malie_cipher as mc

PREFERIDAS = ['Paradise Lost', 'Kajiri Kamui Kagura', 'Dies irae']

def cargar_claves():
    ks = json.load(open(os.path.join(AQUI, 'malie_claves_garbro.json'), encoding='utf-8'))
    orden = [n for n in PREFERIDAS if n in ks] + [n for n in ks if n not in PREFERIDAS]
    return [(n, ks[n]['key'], ks[n].get('align', 0x1000)) for n in orden]

class Dat:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        raw = self.f.read(16)
        self.clave = None
        for nombre, key, al in cargar_claves():
            mc.set_key(key)
            h = mc.decrypt_block(raw, 0)
            if h[:4] == b'LIBP':
                cnt, fcnt = struct.unpack_from('<II', h, 4)
                if 0 < cnt < 2000000 and 0 < fcnt < 2000000:
                    self.clave = nombre; self.align_pref = al; break
        if not self.clave:
            raise SystemExit('ERROR: ninguna clave conocida abre %s (cabecera cifrada: %s)' % (path, raw.hex()))
        h = self.read(0, 16)
        self.cnt, self.fcnt = struct.unpack_from('<II', h, 4)
        self.tbl = 16 + 32 * self.cnt
        head = self.read(0, self.tbl + 4 * self.fcnt)
        self.ents = []
        for i in range(self.cnt):
            o = 16 + 32 * i
            name = head[o:o + 22].split(b'\0')[0].decode('ascii', 'replace')
            fl16, a_, b_ = struct.unpack_from('<HII', head, o + 22)
            self.ents.append((name, fl16 << 16, a_, b_))
        self.offs = struct.unpack_from('<%dI' % self.fcnt, head, self.tbl)
        self.base = self._find_base()

    def read(self, pos, size):
        a = pos & ~15; b = (pos + size + 15) & ~15
        self.f.seek(a); raw = self.f.read(b - a)
        raw += b'\0' * ((-len(raw)) % 16)
        dec = mc.crypt(raw, mc.decrypt_block, a)
        return dec[pos - a: pos - a + size]

    def _find_base(self):
        end = self.tbl + 4 * self.fcnt
        probe = None
        for i, (n, fl, a, sz) in enumerate(self.ents):
            if fl & 0x10000 and (n.endswith('.dzi') or n.endswith('.svg')) and sz > 4:
                probe = (n, a); break
        als = [self.align_pref] + [x for x in (0x1000, 0x400, 0x2000, 0x800, 0x10000) if x != self.align_pref]
        for al in als:
            base = (end + al - 1) & ~(al - 1)
            if probe is None: return base
            d = self.read(base + self.offs[probe[1]] * 1024, 4)
            if d[:3] == b'DZI' or d[:1] == b'<' or d[:3] == b'\xef\xbb\xbf':
                return base
        raise SystemExit('ERROR: no pude ubicar el inicio de los datos')

    def kids(self, i):
        n, fl, a, b = self.ents[i]
        return [] if fl & 0x10000 else list(range(a, a + b))

    def find(self, path):
        i = 0
        for part in [p for p in path.replace('\\', '/').split('/') if p]:
            for j in self.kids(i):
                if self.ents[j][0].lower() == part.lower(): i = j; break
            else: raise SystemExit('ERROR: no existe "%s" (buscando "%s")' % (path, part))
        return i

    def data(self, i):
        n, fl, a, sz = self.ents[i]
        return self.read(self.base + self.offs[a] * 1024, sz)

    def save(self, i, dst):
        n, fl, a, sz = self.ents[i]
        pos = self.base + self.offs[a] * 1024; CH = 8 << 20; hecho = 0
        with open(dst + '.part', 'wb') as o:
            while hecho < sz:
                k = min(CH, sz - hecho); o.write(self.read(pos + hecho, k)); hecho += k
        os.replace(dst + '.part', dst)
        return sz

    def walk(self, i, prefix=''):
        for j in self.kids(i):
            n, fl = self.ents[j][0], self.ents[j][1]
            p = prefix + '/' + n if prefix else n
            yield j, p, not (fl & 0x10000)
            if not (fl & 0x10000): yield from self.walk(j, p)

def extraer(d, i, out, saltar=True):
    n = 0; tot = 0; saltados = 0
    for j, p, isdir in d.walk(i):
        dst = os.path.join(out, *p.split('/'))
        if isdir: os.makedirs(dst, exist_ok=True); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if saltar and os.path.isfile(dst) and os.path.getsize(dst) == d.ents[j][3]:
            saltados += 1; continue
        tot += d.save(j, dst); n += 1
        if n % 200 == 0: print('  ... %d archivos (%.0f MB)' % (n, tot / 1e6), flush=True)
    print('OK: %d archivos extraidos (%.1f MB), %d ya estaban -> %s' % (n, tot / 1e6, saltados, out))

def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    d = Dat(a[0])
    print('archivo: %s | clave: %s | entradas: %d | inicio datos: 0x%X | numpy: %s'
          % (a[0], d.clave, d.cnt, d.base, 'si' if mc.np is not None else 'no (sera lento)'))
    if a[1] == '--probar':
        for j in d.kids(0):
            n, fl, x, sz = d.ents[j]
            print(('   %-22s %10d bytes' if fl & 0x10000 else '[C] %-22s %6d elementos') % (n, sz))
        json.dump({'archivo': os.path.basename(a[0]), 'clave': d.clave, 'base': d.base},
                  open(os.path.join(AQUI, 'clave_detectada.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    elif a[1] == '--listar':
        i = d.find(a[2]) if len(a) > 2 else 0
        for j in d.kids(i):
            n, fl, x, sz = d.ents[j]
            print(('   %-22s %10d bytes' if fl & 0x10000 else '[C] %-22s %6d elementos') % (n, sz))
    elif a[1] == '--buscar':
        key = a[2].lower(); hits = 0
        for j, p, isdir in d.walk(0):
            if key in p.split('/')[-1].lower():
                print(('[C] ' if isdir else '    ') + p); hits += 1
                if hits >= 200: print('... (hay mas)'); break
        print('encontrados: %d' % hits)
    elif a[1] == '--inventario':
        with open(a[2], 'w', encoding='utf-8') as o:
            o.write('ruta\tbytes\n')
            for j, p, isdir in d.walk(0):
                if not isdir: o.write('%s\t%d\n' % (p, d.ents[j][3]))
        print('inventario guardado en', a[2])
    elif a[1] == '--todo':
        extraer(d, 0, a[2])
    else:
        extraer(d, d.find(a[1]), a[2])

if __name__ == '__main__': main()
