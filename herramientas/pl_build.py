#!/usr/bin/env python3
"""pl_build.py - CSV del guion -> data3.dat para Paradise Lost (un solo comando).
Uso (en C:\\PL_Project\\tools\\PL_tools):
  python pl_build.py ..\\..\\traduccion\\pl_script.csv
Opciones:
  --exec  exec.dat ORIGINAL (por defecto C:\\PL_Project\\work\\extraido\\data\\system\\exec.dat; NO se modifica)
  --out   data3_nuevo.dat
  --width 68     medios-anchos por renglon (medido en el juego: 68 latinas = 34 japonesas; 0 = no tocar)
  --cadenas cadenas.tsv  nombres de la caja y opciones (pl_cadenas.py)
  --ui CARPETA   archivos de interfaz con la ruta del juego (CARPETA\\data\\screen\\...); cada carpeta va COMPLETA
  --lines 4      renglones visibles (medido: 4; el 5o queda debajo de la barra de botones)
El data3.dat lleva data/system/exec.dat (+ la interfaz de --ui). data3 tiene prioridad sobre data1
(VERIFICADO en Paradise Lost, prueba 1). Usa la misma clave que data1.dat.
"""
import sys, os, re, struct, csv, json, tempfile
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import malie_cipher as mc, pl_exec_tool as pt

def arg(n, d): return sys.argv[sys.argv.index(n)+1] if n in sys.argv else d

def usar_clave(nombre='Paradise Lost'):
    ks = json.load(open(os.path.join(AQUI, 'malie_claves_garbro.json'), encoding='utf-8'))
    mc.set_key(ks[nombre]['key'])

def w(ch): return 2 if ord(ch) >= 0x2000 and not (0xFF61 <= ord(ch) <= 0xFF9F) else 1
def vis(tok):
    tok = re.sub(r'\{r:([^}|]*)\|[^}]*\}', r'\1', tok); tok = re.sub(r'\{[^}]*\}', '', tok)
    return sum(w(c) for c in tok)

def wrap_lines(t, width):
    """pone {n} entre palabras para que ningun renglon pase de `width`; devuelve (texto, renglones).
    Verificado en el juego (prueba 2): si el mensaje empieza con 「 『 o （, el motor sangra con 1 caracter
    japones (2 medios-anchos) todos los renglones siguientes; por eso esos renglones tienen width-2."""
    end = t.endswith('{end}')
    if end: t = t[:-5]
    plano = re.sub(r'\{[^}]*\}', '', t).lstrip()
    sang = 2 if plano[:1] in ('「', '『', '（') else 0
    res = ''
    for k, para in enumerate(t.split('{n}')):
        if k: res += '{n}'
        toks = re.findall(r'\{[^}]*\}|[^\s{]+(?:\{[^}]*\}[^\s{]*)*|\s+', para)
        ini = sang if k else 0
        line = ''; col = ini
        for tok in toks:
            if tok.isspace():
                if col > ini: line += ' '; col += 1
                continue
            L = vis(tok)
            if col > ini and col + L > width:
                res += line.rstrip() + '{n}'; line = ''; col = sang
            line += tok; col += L
        res += line.rstrip()
    return res + ('{end}' if end else ''), res.count('{n}') + 1

def escribir_libp(tree, out):
    """tree = {'data': {'system': {'exec.dat': bytes}}} -> LIBP cifrado (mismo formato que kkk_agregar_carpeta)"""
    ents = [['', tree]]; q = [0]; files = []
    while q:
        i = q.pop(0); kids = ents[i][1]
        if isinstance(kids, dict):
            first = len(ents)
            for n in sorted(kids): ents.append([n, kids[n]])
            ents[i] += [first, len(kids)]
            q += range(first, first + len(kids))
    hdr = bytearray(); body = bytearray(); offs = []
    for e in ents:
        name = e[0].encode('ascii')
        if isinstance(e[1], dict): fl, a, b = 0, e[2], e[3]
        else: fl, a, b = 0x10000, len(files), len(e[1]); files.append(e[1])
        hdr += name.ljust(22, b'\0') + struct.pack('<HII', fl >> 16, a, b)
    for f in files:
        offs.append(len(body) // 1024); body += f; body += b'\0' * ((-len(body)) % 4096)
    head = b'LIBP' + struct.pack('<III', len(ents), len(files), 0) + hdr + struct.pack('<%dI' % len(offs), *offs)
    base = (len(head) + 0xFFF) & ~0xFFF
    raw = head + b'\0' * (base - len(head)) + body; raw += b'\0' * ((-len(raw)) % 4096)
    open(out, 'wb').write(mc.crypt(raw, mc.encrypt_block, 0))

def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith('--'): print(__doc__); sys.exit(1)
    csvp = sys.argv[1]
    exp = arg('--exec', r'C:\PL_Project\work\extraido\data\system\exec.dat')
    out = arg('--out', 'data3_nuevo.dat'); width = int(arg('--width', '68')); maxl = int(arg('--lines', '4'))
    usar_clave()
    rows = list(csv.DictReader(open(csvp, newline='', encoding='utf-8-sig')))
    largos = []; malos = []
    for r in rows:
        es = r['spanish'].strip()
        if not (es and r['status'].strip().lower() in ('draft', 'reviewed', 'approved')): continue
        if es.count('{end}') != r['japanese'].count('{end}'): malos.append(r['id'])
        if width:
            es, n = wrap_lines(es, width)
            if maxl and n > maxl: largos.append((r['id'], n))
        r['spanish'] = es
    if malos: raise SystemExit('ERROR: cantidad de {end} distinta al japones en ids: ' + ', '.join(malos[:50]))
    tmp = tempfile.mkdtemp()
    tcsv = os.path.join(tmp, 'w.csv'); texe = os.path.join(tmp, 'e.dat')
    with open(tcsv, 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys()); wr.writeheader(); wr.writerows(rows)
    cad = arg('--cadenas', None)
    if cad:                                   # nombres y opciones (pl_cadenas.py)
        import pl_cadenas
        tex0 = os.path.join(tmp, 'c.dat'); pl_cadenas.insertar(exp, cad, tex0); exp = tex0
    pt.insert(exp, tcsv, texe, 0)
    ne = open(texe, 'rb').read()
    tree = {'data': {'system': {'exec.dat': ne}}}
    ui = arg('--ui', None)                    # carpeta con la misma forma que el juego: <ui>\data\screen\...
    nui = 0
    if ui:
        for raiz, dirs, fs in os.walk(ui):
            for fn in fs:
                rel = os.path.relpath(os.path.join(raiz, fn), ui).replace('\\', '/').split('/')
                if rel == ['data', 'system', 'exec.dat']: continue
                node = tree
                for p in rel[:-1]: node = node.setdefault(p, {})
                node[rel[-1]] = open(os.path.join(raiz, fn), 'rb').read(); nui += 1
    escribir_libp(tree, out)
    # comprobacion: releer con el extractor y comparar TODO
    import pl_extraer as px
    d = px.Dat(out)
    def check(node, path):
        for k, v in node.items():
            p = path + '/' + k if path else k
            if isinstance(v, dict): check(v, p)
            else: assert d.data(d.find(p)) == v, 'la relectura no coincide: ' + p
    check(tree, '')
    print('OK: %s creado y verificado (%d bytes, clave %s, exec + %d archivos de interfaz)' % (out, os.path.getsize(out), d.clave, nui))
    if largos:
        print('AVISO: %d mensajes pasan de %d renglones:' % (len(largos), maxl))
        for i, n in largos[:100]: print('   id %s -> %d renglones' % (i, n))

if __name__ == '__main__': main()
