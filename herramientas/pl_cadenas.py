#!/usr/bin/env python3
"""pl_cadenas.py - textos que NO estan en la tabla de mensajes del exec.dat:
nombres de la caja de nombre y opciones de eleccion (Paradise Lost).
  python pl_cadenas.py extraer  exec.dat cadenas.tsv
  python pl_cadenas.py insertar exec.dat cadenas.tsv exec_nuevo.dat
Formato de exec.dat (comprobado en PL 2017): [...][u32 tam_textos][textos UTF-16][u32 tam_codigo][codigo][tabla de mensajes]
Referencias en el codigo: 0A u16 (textos < 0x10000) o 0C u32, seguidas de
   2D 48 ............ caja de nombre        -> tipo 'nombre'
   (0F) 11 n 11 01 11 10 ... opcion n       -> tipo 'opcion'
Insertar: el espanol se escribe en el espacio de los textos de depuracion '■ ...\\n' (el juego no los
muestra; tecnica de KKK) y se cambian solo las referencias de ese texto. El exec.dat NO cambia de tamano.
"""
import sys, os, re, struct, csv
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
JP = re.compile(r'[぀-ヿ一-鿿！-～]')

def regiones(d):
    """devuelve (inicio_textos, tam_textos, inicio_codigo, fin_codigo)"""
    import pl_exec_tool as pt
    T, n = pt.find_table(d)
    ce = T - 4                                     # u32 con el numero de mensajes antes de la tabla
    for p in range(0, 0x100000):
        ps = struct.unpack_from('<I', d, p)[0]
        if 0 < ps < len(d) and p + 4 + ps + 4 <= ce:
            q = p + 4 + ps
            if struct.unpack_from('<I', d, q)[0] == ce - (q + 4) and d[p+4:p+6] != b'\0\0':
                return p + 4, ps, q + 4, ce
    raise SystemExit('ERROR: no encontre el bloque de textos del codigo')

def textos(pool):
    out = {}; i = 0
    while i < len(pool):
        j = i
        while j + 1 < len(pool) and pool[j:j+2] != b'\0\0': j += 2
        out[i] = pool[i:j].decode('utf-16le', 'replace'); i = j + 2
    return out

def refs(code, off):
    """todas las referencias (pos, ancho, tipo) al texto en 'off'"""
    r = []
    pats = [(b'\x0c' + struct.pack('<I', off), 4)]
    if off < 0x10000: pats.append((b'\x0a' + struct.pack('<H', off), 2))
    for pat, n in pats:
        for m in re.finditer(re.escape(pat), code):
            p = m.start(); nx = code[p + 1 + n: p + 1 + n + 8]
            if nx[:2] == b'\x2d\x48': t = 'nombre'
            elif re.match(rb'(?:\x0f|\x11.)\x11\x01\x11\x10', nx, re.S): t = 'opcion'
            elif nx[:3] == b'\x04\x22\x01': t = 'depuracion'
            else: t = 'otro'
            r.append((p + 1, n, t))
    return r

def cargar(path):
    d = bytearray(open(path, 'rb').read())
    ps_, psz, cs, ce = regiones(d)
    return d, ps_, psz, cs, ce

def extraer(src, dst):
    d, P, PS, cs, ce = cargar(src)
    pool = bytes(d[P:P+PS]); code = bytes(d[cs:ce]); tx = textos(pool)
    n = 0
    with open(dst, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter='\t'); w.writerow(['offset', 'tipo', 'usos', 'japanese', 'spanish', 'nota'])
        for o, s in tx.items():
            if not JP.search(s) or s.startswith('■') or s.endswith('\n'): continue
            r = refs(code, o)
            if not r: continue
            tipos = sorted(set(t for _, _, t in r))
            w.writerow(['0x%X' % o, '/'.join(tipos), len(r), s, '', '']); n += 1
    print('OK: %d textos (nombres y opciones) -> %s' % (n, dst))

def insertar(src, tsv, dst):
    d, P, PS, cs, ce = cargar(src)
    pool = bytearray(d[P:P+PS]); code0 = bytes(d[cs:ce]); code = bytearray(code0); tx = textos(bytes(pool))
    libres = []
    # 1) textos de depuracion '■...\n' usados una sola vez y solo por la orden de depuracion
    for o, s in sorted(tx.items()):
        if s.endswith('\n') and '%' not in s:
            r = refs(code0, o)
            if r and all(t == 'depuracion' for _, _, t in r):
                libres.append([o, o + (len(s) + 1) * 2])
    filas = [r for r in csv.DictReader(open(tsv, encoding='utf-8-sig'), delimiter='\t') if r['spanish'].strip()]
    trab = []
    for r in filas:
        o = int(r['offset'], 16); es = r['spanish'].strip()
        if tx.get(o) != r['japanese']:
            raise SystemExit('ERROR: el texto en %s no coincide con el exec.dat (%r)' % (r['offset'], tx.get(o)))
        rr = [x for x in refs(code0, o) if x[2] != 'depuracion']
        trab.append((o, es, rr))
        # 2) el hueco del japones queda libre si todas sus referencias se van a cambiar
        if all(t in ('nombre', 'opcion') for _, _, t in rr):
            libres.append([o, o + (len(tx[o]) + 1) * 2])
    # juntar huecos contiguos
    libres.sort(); m = []
    for a_, b_ in libres:
        if m and a_ <= m[-1][1]: m[-1][1] = max(m[-1][1], b_)
        else: m.append([a_, b_])
    libres = m
    libre_total = sum(b_ - a_ for a_, b_ in libres); libre_bajo = sum(min(b_, 0x10000) - a_ for a_, b_ in libres if a_ < 0x10000)
    # reparto: primero los que necesitan hueco < 0x10000 (referencias de 2 bytes), con busqueda exhaustiva
    unicos = {}
    for o, es, rr in trab:
        bajo = any(n == 2 for _, n, _ in rr)
        unicos[es] = unicos.get(es, False) or bajo
    pos = {}
    def repartir(lista, huecos):
        lista = sorted(lista, key=lambda e: -len(e))
        sizes = [len(e.encode('utf-16le')) + 2 for e in lista]
        sys.setrecursionlimit(10000)
        def bt(i):
            if i == len(lista): return True
            tried = set()
            for h in sorted(huecos, key=lambda h: h[1] - h[0]):
                lib_ = h[1] - h[0]
                if lib_ < sizes[i] or lib_ in tried: continue
                tried.add(lib_)
                pos[lista[i]] = h[0]; h[0] += sizes[i]
                if bt(i + 1): return True
                h[0] -= sizes[i]; del pos[lista[i]]
            return False
        print('  repartir: %d textos (%d bytes) en %d huecos (%d bytes, max %d)' % (len(lista), sum(sizes), len(huecos), sum(h[1]-h[0] for h in huecos), max([h[1]-h[0] for h in huecos] or [0])))
        if not bt(0): raise SystemExit('ERROR: no caben los textos; acorta algunos (sobre todo los largos)')
    bajos = [h for h in libres if h[0] < 0x10000]
    for h in bajos: h[1] = min(h[1], 0x10000)
    repartir([e for e, bj in unicos.items() if bj], bajos)
    altos = [h for h in libres if h[0] >= 0x10000] + [h for h in bajos if h[1] - h[0] > 0]
    repartir([e for e, bj in unicos.items() if not bj], altos)
    usado = sum(len(e.encode('utf-16le')) + 2 for e in pos); cambios = 0
    for o, es, rr in trab:
        for p, n, t in rr:
            struct.pack_into('<H' if n == 2 else '<I', code, p, pos[es]); cambios += 1
    # 3) escribir los textos (al final, para no pisar japones que aun se lee)
    for o, es, rr in trab: pass
    for es, no in pos.items():
        b = es.encode('utf-16le') + b'\0\0'; pool[no:no+len(b)] = b
    d[P:P+PS] = pool; d[cs:ce] = code
    open(dst, 'wb').write(d)
    print('OK: %d textos, %d referencias cambiadas, %d de %d bytes libres usados (%d bajo 64K) -> %s'
          % (len(trab), cambios, usado, libre_total, libre_bajo, dst))

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'extraer': extraer(a[1], a[2])
    elif len(a) >= 4 and a[0] == 'insertar': insertar(a[1], a[2], a[3])
    else: print(__doc__)
