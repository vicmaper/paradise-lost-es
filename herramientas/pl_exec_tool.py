#!/usr/bin/env python3
"""pl_exec_tool.py - extrae/inserta el texto de data/system/exec.dat de MALIE (Paradise Lost).
Basado en kkk_exec_tool.py (KKK). Diferencia: la tabla de mensajes se DETECTA sola
(en KKK estaba fija en 0x2F2A6A).
  python pl_exec_tool.py info    exec.dat
  python pl_exec_tool.py extract exec.dat script.csv
  python pl_exec_tool.py insert  exec.dat script.csv exec_new.dat [--wrap 0]
CSV: id, voice, japanese, spanish, status
Etiquetas: {n}=salto(07 04) {end}=pausa(07 06) {v:ID}..{/v}=voz {r:base|ruby}=furigana {uXXXX}=otro control
"""
import sys, struct, csv, re
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

def find_table(d):
    """Busca al final del archivo: [tabla (offset,len) x N][u32 tamano_pool][pool UTF-16].
    Devuelve (TABLE, count). Prueba cada posicion p con u32(p) == len-p-4 y camina hacia atras."""
    L = len(d); best = None
    for p in range(L - 8, max(0, L - 0x2000000), -1):
        psize = struct.unpack_from('<I', d, p)[0]
        if psize != L - p - 4: continue
        n = 0; q = p - 8; prev_off = None
        while q >= 0:
            o, l = struct.unpack_from('<II', d, q)
            if o > psize or l > psize or o + l > psize or l % 2: break
            if prev_off is not None and o >= prev_off: break
            prev_off = o; n += 1
            if o == 0: break
            q -= 8
        if n and prev_off == 0 and (best is None or n > best[1]):
            best = (q, n)
    if not best: raise SystemExit('ERROR: no encontre la tabla de mensajes en este exec.dat')
    return best

def load(path):
    d = open(path, 'rb').read()
    TABLE, count = find_table(d)
    ents = [struct.unpack_from('<II', d, TABLE + 8*k) for k in range(count)]
    base = TABLE + 8*count + 4
    msgs = [d[base+o:base+o+l].decode('utf-16le') for o, l in ents]
    return d, msgs, base, TABLE

def to_tags(s):
    out = []; i = 0
    while i < len(s):
        c = s[i]
        if c == '\x07' and i+1 < len(s):
            k = s[i+1]
            if k == '\x04': out.append('{n}'); i += 2; continue
            if k == '\x06': out.append('{end}'); i += 2; continue
            if k == '\x09': out.append('{/v}'); i += 2; continue
            if k == '\x08':
                j = s.index('\0', i); out.append('{v:%s}' % s[i+2:j]); i = j+1; continue
            if k == '\x01':
                j = s.index('\0', i); b, r = s[i+2:j].split('\n', 1)
                out.append('{r:%s|%s}' % (b, r)); i = j+1; continue
        if ord(c) < 0x20 or 0x600 <= ord(c) < 0x700:
            out.append('{u%04X}' % ord(c))
        elif c in '{}': out.append('{u%04X}' % ord(c))
        else: out.append(c)
        i += 1
    return ''.join(out)

TAG = re.compile(r'\{(?:n|end|/v|v:[^}]*|r:[^}|]*\|[^}]*|u[0-9A-Fa-f]{4})\}')
def from_tags(t):
    def rep(m):
        g = m.group(0)[1:-1]
        if g == 'n': return '\x07\x04'
        if g == 'end': return '\x07\x06'
        if g == '/v': return '\x07\x09'
        if g.startswith('v:'): return '\x07\x08' + g[2:] + '\0'
        if g.startswith('r:'):
            b, r = g[2:].split('|', 1); return '\x07\x01' + b + '\n' + r + '\0'
        return chr(int(g[1:], 16))
    return TAG.sub(rep, t)

def wrap(t, width):
    """Column padding: the game hard-wraps at `width` chars/column (62 measured) and splits words.
    Pad with spaces so a word that does not fit starts the next column. {n}/{end} reset the column."""
    if not width: return t
    parts = re.split(r'(\{[^}]*\})', t)
    out = []; col = 0
    for p in parts:
        if TAG.fullmatch(p):
            out.append(p)
            if p in ('{n}', '{end}'): col = 0
            continue
        for tok in re.findall(r'\S+|\s+', p):
            if tok.isspace():
                if col and col < width: out.append(' '); col += 1
                if col >= width: col = 0
                continue
            L = len(tok)
            if col and col + L > width:
                out.append(' ' * (width - col)); col = 0
            out.append(tok); col += L
            while col >= width: col -= width
    return ''.join(out)

def extract(src, dst):
    d, msgs, _, _ = load(src)
    with open(dst, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['id', 'voice', 'japanese', 'spanish', 'status'])
        for k, m in enumerate(msgs):
            v = ' '.join(re.findall(r'\x07\x08([^\0]*)\0', m))
            w.writerow([k, v, to_tags(m), '', 'untranslated'])

def insert(src, csvp, dst, width=0, accept=('draft', 'reviewed', 'approved')):
    """Rows keep their ORIGINAL numeric id. A row whose id is not a number (e.g. new1) is a NEW message
    inserted at that position (everything after it shifts by one). Final order = CSV row order."""
    d, msgs, base, TABLE = load(src)
    new = []; used = 0; added = 0; seen = set()
    with open(csvp, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rid = r['id'].strip(); es = r['spanish']
            ok = r['status'].strip().lower() in accept and es.strip()
            if rid.isdigit():
                k = int(rid); seen.add(k); cur = msgs[k]
                if ok:
                    es = wrap(es, width)
                    if not es.endswith('{end}') and cur.endswith('\x07\x06'): es += '{end}'
                    cur = from_tags(es); used += 1
                new.append(cur)
            else:
                if not es.strip(): continue
                es = wrap(es, width)
                if not es.endswith('{end}'): es += '{end}'
                new.append(from_tags(es)); added += 1
    assert seen == set(range(len(msgs))), 'CSV is missing original ids (every original id must appear once)'
    pool = bytearray(); table = bytearray()
    for m in new:
        b = m.encode('utf-16le'); table += struct.pack('<II', len(pool), len(b)); pool += b + b'\0\0'
    out = d[:TABLE] + table + struct.pack('<I', len(pool)) + pool
    open(dst, 'wb').write(out)
    print('translated:', used, '| new messages inserted:', added, '| total messages:', len(new), '| exec size', len(out))

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    if a[0] == 'info':
        d, msgs, base, T = load(a[1])
        nch = sum(len(m) for m in msgs); mx = max(len(m) for m in msgs)
        print('tabla de mensajes: 0x%X | mensajes: %d | caracteres: %d | mensaje mas largo: %d | tamano: %d' % (T, len(msgs), nch, mx, len(d)))
    elif a[0] == 'extract': extract(a[1], a[2]); print('CSV guardado:', a[2])
    elif a[0] == 'insert':
        wd = int(a[a.index('--wrap')+1]) if '--wrap' in a else 0
        insert(a[1], a[2], a[3], wd)
    else: print(__doc__)
