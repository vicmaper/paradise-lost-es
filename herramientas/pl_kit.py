#!/usr/bin/env python3
"""pl_kit.py - Kit de traduccion al espanol de Paradise Lost (light, 2017, motor MALIE).

  python pl_kit.py extraer  [CARPETA_DEL_JUEGO] [--forzar]   saca el guion de TU data1.dat -> trabajo/CSV_MAESTRO.csv
  python pl_kit.py revisar  [CUALQUIER.csv]                 revisa, CORRIGE lo que se pueda y lo guarda en el maestro
  python pl_kit.py validar  [CUALQUIER.csv]                 solo revisa (no cambia nada)
  python pl_kit.py generar  [CUALQUIER.csv]                 (revisa ese CSV si se da y) maestro -> data3.dat del juego

El CSV puede llamarse como quieras; necesita columnas id y spanish (las demas son opcionales).
Acepta coma, punto y coma (Excel en espanol) o tabulador, en UTF-8 o ANSI.
"""
import sys, os, re, io, csv, json, shutil, hashlib, datetime, tempfile
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
H = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):        # version .exe: las carpetas del kit estan junto al .exe
    KIT = os.path.dirname(os.path.abspath(sys.executable))
else:
    KIT = os.path.dirname(H)
sys.path.insert(0, H)
TRAB = os.path.join(KIT, 'trabajo')
MAESTRO = os.path.join(TRAB, 'CSV_MAESTRO.csv')
CADENAS = os.path.join(TRAB, 'CADENAS_MAESTRO.tsv')
EXEC0 = os.path.join(TRAB, 'exec_original.dat')
CONFIG = os.path.join(KIT, 'config.txt')
MD5_EXEC = 'aa2669877cea9684357d47d5895da9d4'     # exec.dat de Paradise Lost 2017 (malie.exe 1.1.0.0)
CAMPOS = ['id', 'voice', 'japanese', 'spanish', 'status']

# ---- parametros medidos en el juego (ver LEEME) ----
ANCHO = 68          # caracteres latinos por renglon
RENGLONES = 5       # renglones visibles (con la ventana modificada de interfaz/)
MAX_CHARS = 900     # largo maximo de un mensaje contando las marcas

def ahora(): return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def leer_config():
    c = {}
    if os.path.isfile(CONFIG):
        for l in open(CONFIG, encoding='utf-8-sig'):
            if '=' in l: k, v = l.split('=', 1); c[k.strip()] = v.strip().strip('"')
    return c

def guardar_config(c):
    with open(CONFIG, 'w', encoding='utf-8') as f:
        for k, v in c.items(): f.write('%s=%s\n' % (k, v))

def carpeta_juego(arg=None):
    c = leer_config()
    j = arg or c.get('JUEGO')
    if not j:
        try:
            print('Escribe la carpeta del juego (donde estan malie.exe y data1.dat)')
            j = input('o arrastrala a esta ventana y presiona Enter: ').strip().strip('"')
        except EOFError: j = ''
    if not j: raise SystemExit('ERROR: falta la carpeta del juego.')
    if not os.path.isfile(os.path.join(j, 'data1.dat')):
        raise SystemExit('ERROR: en "%s" no esta data1.dat. Indica la carpeta donde esta malie.exe.' % j)
    if c.get('JUEGO') != j: c['JUEGO'] = j; guardar_config(c)
    return j

def leer_tabla(path):
    """Lee un CSV/TSV con cualquier nombre. Acepta UTF-8 (con o sin BOM) y, si falla, ANSI de Windows
    (lo que guarda Excel por defecto). Detecta el separador: tabulador, punto y coma (Excel en espanol) o coma.
    Devuelve (filas, aviso)."""
    raw = open(path, 'rb').read(); aviso = ''
    for enc in ('utf-8-sig', 'cp1252'):
        try: txt = raw.decode(enc); break
        except UnicodeDecodeError: continue
    if enc == 'cp1252': aviso = 'el archivo no estaba en UTF-8 (se leyo como ANSI de Windows); revisa acentos y 「」'
    txt = txt.replace('\r\n', '\n')
    prim = txt.split('\n', 1)[0]
    sep = '\t' if '\t' in prim else (';' if prim.count(';') > prim.count(',') else ',')
    if sep == '\t':
        filas = []; cab = [c.strip() for c in prim.split('\t')]
        for l in txt.split('\n')[1:]:
            if not l.strip(): continue
            p = l.split('\t')
            if len(p) > len(cab): p = p[:len(cab) - 1] + ['\t'.join(p[len(cab) - 1:])]
            filas.append(dict(zip(cab, p + [''] * (len(cab) - len(p)))))
    else:
        filas = list(csv.DictReader(io.StringIO(txt), delimiter=sep))
    norm = []
    for f in filas:
        g = {(k or '').strip().lower().lstrip('\ufeff'): (v if v is not None else '') for k, v in f.items()}
        norm.append(g)
    return norm, aviso

def escribir_maestro(rows, path=MAESTRO):
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)

def respaldar(path):
    if not os.path.isfile(path): return None
    d = os.path.join(TRAB, 'respaldos'); os.makedirs(d, exist_ok=True)
    b, e = os.path.splitext(os.path.basename(path))
    dst = os.path.join(d, '%s_%s%s' % (b, ahora(), e)); shutil.copyfile(path, dst); return dst

# =====================================================================================
# 1) EXTRAER
# =====================================================================================
def cmd_extraer(args, aviso_final=True):
    forzar = '--forzar' in args; args = [a for a in args if a != '--forzar']
    juego = carpeta_juego(args[0] if args else None)
    os.makedirs(TRAB, exist_ok=True)
    import pl_extraer as px, pl_exec_tool as pt, pl_cadenas as pc
    print('[1/4] Abriendo %s ...' % os.path.join(juego, 'data1.dat'))
    d = px.Dat(os.path.join(juego, 'data1.dat'))
    print('      clave: %s' % d.clave)
    open(EXEC0, 'wb').write(d.data(d.find('data/system/exec.dat')))
    m = md5(EXEC0)
    print('[2/4] exec.dat md5 %s %s' % (m, '(edicion correcta)' if m == MD5_EXEC else '(EDICION DISTINTA)'))
    if m != MD5_EXEC and not forzar:
        raise SystemExit('ERROR: tu juego no es la edicion 2017 para la que se hizo esta traduccion\n'
                         '(codigo md5 de tu guion: %s). No se cambio nada.\n'
                         'Te podemos ayudar a adaptar la herramienta a tu version: escribe en el Discord\n'
                         'https://discord.gg/k3Zfp85jMr con de donde es tu copia, la version de malie.exe\n'
                         '(clic derecho > Propiedades > Detalles) y una captura de este mensaje.\n'
                         'No apliques parches oficiales. Para intentarlo de todos modos: 1_EXTRAER con --forzar' % m)
    print('[3/4] Creando el CSV maestro ...')
    if os.path.isfile(MAESTRO) and not forzar:
        print('      Ya existe trabajo/CSV_MAESTRO.csv: NO se toca (tu trabajo esta a salvo).')
        print('      Para rehacerlo desde cero: 1_EXTRAER con --forzar (se guarda respaldo).')
    else:
        respaldar(MAESTRO)
        tmp = os.path.join(TRAB, '_extraido.csv'); pt.extract(EXEC0, tmp)
        rows = list(csv.DictReader(open(tmp, encoding='utf-8-sig'))); os.remove(tmp)
        es = {}
        ruta = os.path.join(KIT, 'traduccion', 'traduccion_es.tsv')
        if os.path.isfile(ruta):
            for r in leer_tabla(ruta)[0]:
                if r.get('spanish', '').strip(): es[r['id'].strip()] = r['spanish']
        for r in rows:
            if r['id'] in es: r['spanish'] = es[r['id']]; r['status'] = 'draft'
        escribir_maestro(rows)
        print('      %d mensajes, %d con traduccion del kit -> %s' % (len(rows), len(es), MAESTRO))
    print('[4/4] Nombres y opciones ...')
    tmp = os.path.join(TRAB, '_cad.tsv'); pc.extraer(EXEC0, tmp)
    cad = list(csv.DictReader(open(tmp, encoding='utf-8-sig'), delimiter='\t')); os.remove(tmp)
    previo = {}
    if os.path.isfile(CADENAS):
        for r in csv.DictReader(open(CADENAS, encoding='utf-8-sig'), delimiter='\t'): previo[r['offset']] = r['spanish']
    kit = {}
    rk = os.path.join(KIT, 'traduccion', 'cadenas_es.tsv')
    if os.path.isfile(rk):
        for r in csv.DictReader(open(rk, encoding='utf-8-sig'), delimiter='\t'): kit[r['offset']] = r['spanish']
    for r in cad: r['spanish'] = previo.get(r['offset']) or kit.get(r['offset'], '')
    with open(CADENAS, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['offset', 'tipo', 'usos', 'japanese', 'spanish', 'nota'], delimiter='\t')
        w.writeheader(); w.writerows(cad)
    print('      %d textos (%d en espanol) -> %s' % (len(cad), sum(1 for r in cad if r['spanish']), CADENAS))
    if aviso_final: print('\nLISTO. Siguiente paso: 2_REVISAR_Y_CORREGIR (con tu CSV o con el maestro) y luego 3_GENERAR_DAT.')

# =====================================================================================
# 2) VALIDAR
# =====================================================================================
JP = re.compile(r'[぀-ヿ㐀-鿿！-～、。・～〜っ]')
MARCA = re.compile(r'\{(?:n|end|/v|v:[^}]*|r:[^}|]*\|[^}]*|u[0-9A-Fa-f]{4})\}')

def cargar_reglas():
    p = os.path.join(KIT, 'traduccion', 'reglas_estilo.tsv'); reglas = []
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter='\t'):
            if r.get('patron') and not r['patron'].startswith('#'):
                fl = 0 if r.get('mayusculas', '').strip() == 'si' else re.I
                reglas.append((re.compile(r['patron'], fl), r.get('problema', ''), r.get('nivel', 'AVISO').strip() or 'AVISO', r.get('reemplazo') or None))
    return reglas

def revisar(jp, es, reglas):
    """devuelve lista de (nivel, problema)"""
    import pl_build as pb
    out = []
    E = lambda m: out.append(('ERROR', m)); A = lambda m: out.append(('AVISO', m))
    if es.count('{end}') != jp.count('{end}'): E('cantidad de {end} distinta al japones (%d en vez de %d)' % (es.count('{end}'), jp.count('{end}')))
    vj = re.findall(r'\{v:[^}]*\}|\{/v\}', jp); ve = re.findall(r'\{v:[^}]*\}|\{/v\}', es)
    if vj != ve: E('marcas de voz {v:..}{/v} distintas al japones (debe ser: %s)' % (''.join(vj) or 'ninguna'))
    if '{r:' in es: E('furigana {r:...} sin traducir')
    for m in re.findall(r'\{[^}]*\}?', es):
        if not MARCA.fullmatch(m): E('marca desconocida o rota: %s' % m)
    if re.search(r'(?<!\{)[{}](?![^{]*\})', re.sub(r'\{[^}]*\}', '', es)): E('llave { o } suelta')
    plano = re.sub(r'\{[^}]*\}', '', es)
    t = plano.replace('「', '').replace('」', '').replace('『', '').replace('』', '')
    jj = JP.findall(t)
    if jj and es != jp: E('caracteres japoneses: ' + ''.join(sorted(set(jj))))
    if '\t' in es or '\n' in es or '\r' in es: E('tabulador o salto de linea real (usa {n})')
    if len(es) > MAX_CHARS: E('mas de %d caracteres (%d)' % (MAX_CHARS, len(es)))
    _, n = pb.wrap_lines(es, ANCHO)
    if n > RENGLONES: E('%d renglones (maximo %d de %d caracteres): acortar' % (n, RENGLONES, ANCHO))
    # ---- estilo (avisos) ----
    for a_, c_ in (('「', '」'), ('『', '』')):
        if (es.count(a_), es.count(c_)) != (jp.count(a_), jp.count(c_)):
            A('comillas %s%s distintas al japones (%d/%d en vez de %d/%d)' % (a_, c_, es.count(a_), es.count(c_), jp.count(a_), jp.count(c_)))
    if plano.count('¿') != plano.count('?'): A('¿ y ? no estan en pareja')
    if plano.count('¡') != plano.count('!'): A('¡ y ! no estan en pareja')
    if re.search(r'\s{2,}', plano): A('espacios dobles')
    if re.search(r' [,.;:!?」』]', plano): A('espacio antes de un signo')
    if re.search(r'^\s|\s$', re.sub(r'\{(?:v:[^}]*|/v|end)\}', '', es)): A('espacio al inicio o al final')
    if re.search(r'\{n\}\s|\s\{n\}', es): A('espacio junto a {n}')
    for rx, prob, niv, *_ in reglas:
        m = rx.search(plano)
        if m: out.append((niv, '%s: «%s»' % (prob, m.group(0))))
    return out


def maestro_filas():
    if not os.path.isfile(MAESTRO): return None
    return list(csv.DictReader(open(MAESTRO, encoding='utf-8-sig')))

# =====================================================================================
# 2) REVISAR Y CORREGIR  (cualquier CSV -> CSV_MAESTRO.csv corregido + reporte)
# =====================================================================================
ANCHO_A_LATINO = {ord(c): ord(c) - 0xFEE0 for c in
                  'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９'}
PUNT_JP = [('、', ', '), ('。', '. '), ('！', '!'), ('？', '?'), ('：', ':'), ('；', ';'), ('（', '('), ('）', ')'),
           ('・', ' '), ('～', ''), ('〜', ''), ('，', ', '), ('．', '.'), ('％', '%'), ('＆', '&')]

def corregir(jp, es, reglas):
    """Arreglos mecanicos y seguros. Devuelve (texto, [lista de arreglos hechos])."""
    import pl_build as pb
    hechos = []
    def cambio(nuevo, que):
        nonlocal es
        if nuevo != es: es = nuevo; hechos.append(que)
    cambio(es.replace('\r\n', '{n}').replace('\n', '{n}').replace('\r', '{n}').replace('\t', ' '), 'saltos/tabuladores reales -> {n}/espacio')
    cambio(re.sub(r'\{r:([^}|]*)\|[^}]*\}', r'\1', es), 'furigana {r:..} -> solo la base')
    cambio(re.sub(r'\{\s*(n|end|/v)\s*\}', r'{\1}', es, flags=re.I).replace('{N}', '{n}').replace('{END}', '{end}'), 'marcas escritas con espacios o mayusculas')
    # puntuacion japonesa y ancho completo (no se tocan 「」『』)
    t = es
    for a, b in PUNT_JP: t = t.replace(a, b)
    t = t.translate(ANCHO_A_LATINO)
    cambio(t, 'puntuacion japonesa / letras de ancho completo -> latinas')
    cambio(re.sub(r'\.{3,}', '…', es), '«...» -> «…»')
    # {end}: misma cantidad que el japones (caso normal: uno al final)
    if es.count('{end}') != jp.count('{end}') and jp.count('{end}') == 1 and jp.endswith('{end}'):
        cambio(es.replace('{end}', '').rstrip() + '{end}', '{end} corregido (uno al final)')
    # voz: {v:ID} al inicio y {/v} antes del {end}, como en el japones
    mv = re.fullmatch(r'(\{v:[^}]*\})(.*)\{/v\}((?:\{end\})?)', jp, re.S)
    vj = re.findall(r'\{v:[^}]*\}|\{/v\}', jp); ve = re.findall(r'\{v:[^}]*\}|\{/v\}', es)
    if mv and vj != ve:
        cuerpo = re.sub(r'\{v:[^}]*\}|\{/v\}', '', es)
        fin = '{end}' if cuerpo.endswith('{end}') else ''
        if fin: cuerpo = cuerpo[:-5]
        cambio(mv.group(1) + cuerpo.strip() + '{/v}' + fin, 'marcas de voz {v:..}{/v} puestas como en el japones')
    elif not vj and ve:
        cambio(re.sub(r'\{v:[^}]*\}|\{/v\}', '', es), 'marcas de voz sobrantes quitadas')
    # espacios
    t = re.sub(r'[  ]{2,}', ' ', es)
    t = re.sub(r' +([,.;:!?」』])', r'\1', t)
    t = re.sub(r' *\{n\} *', '{n}', t)
    t = re.sub(r'^((?:\{v:[^}]*\})?) +', r'\1', t)
    t = re.sub(r' +((?:\{/v\})?(?:\{end\})?)$', r'\1', t)
    cambio(t, 'espacios sobrantes')
    # reemplazos de reglas_estilo.tsv (nombres, etc.)
    for rx, prob, niv, rep in reglas:
        if rep:
            partes = re.split(r'(\{[^}]*\})', es)
            nuevo = ''.join(p if p.startswith('{') else rx.sub(rep, p) for p in partes)
            cambio(nuevo, prob)
    # mas renglones de los que caben: probar quitando los {n} manuales (solo cambia la distribucion)
    _, n = pb.wrap_lines(es, ANCHO)
    if n > RENGLONES and '{n}' in es:
        t = es.replace('{n}', ' '); t = re.sub(r' {2,}', ' ', t)
        if pb.wrap_lines(t, ANCHO)[1] <= RENGLONES: cambio(t, 'saltos {n} manuales quitados para que quepa en %d renglones' % RENGLONES)
    return es, hechos

def errores_de(jp, es, reglas):
    return [p for n, p in revisar(jp, es, reglas) if n == 'ERROR']

def cmd_revisar(args):
    solo = '--solo-revisar' in args; args = [a for a in args if not a.startswith('--')]
    m = maestro_filas()
    ruta = args[0] if args else MAESTRO
    if not os.path.isfile(ruta):
        if ruta == MAESTRO: raise SystemExit('ERROR: todavia no hay CSV maestro. Arrastra tu CSV a esta ventana, o corre primero 1_EXTRAER.')
        raise SystemExit('ERROR: no encuentro el archivo: %s' % ruta)
    filas, aviso_enc = leer_tabla(ruta)
    if not filas or 'id' not in filas[0] or 'spanish' not in filas[0]:
        raise SystemExit('ERROR: el archivo debe tener al menos las columnas "id" y "spanish" (columnas encontradas: %s)'
                         % ', '.join(filas[0].keys() if filas else []))
    if m is None:
        # sin 1_EXTRAER: si el CSV trae el guion completo con japones, se usa como base del maestro
        if 'japanese' in filas[0] and all((f.get('japanese') or '').strip() for f in filas) and len(filas) >= 24744:
            os.makedirs(TRAB, exist_ok=True)
            m = [{'id': f['id'].strip(), 'voice': f.get('voice', ''), 'japanese': f['japanese'], 'spanish': '',
                  'status': 'untranslated'} for f in filas]
            print('No habia CSV maestro: se crea a partir de tu archivo (trae el guion completo con japones).')
            print('Al generar el .dat solo se te pedira la carpeta del juego.\n')
        else:
            raise SystemExit('ERROR: todavia no hay CSV maestro y tu archivo no trae el guion completo con la columna japanese.\n'
                             'Corre primero 1_EXTRAER (crea el maestro desde tu juego) y despues vuelve a este paso.')
    reglas = cargar_reglas(); by = {r['id']: r for r in m}
    es_maestro = os.path.abspath(ruta) == os.path.abspath(MAESTRO)
    rep = []          # (id, estado, detalle)
    n_tot = n_ok = n_corr = n_mal = n_vacio = n_noid = 0; n_avisos = 0
    for f in filas:
        i = (f.get('id') or '').strip()
        if not i: continue
        es0 = f.get('spanish') or ''
        if i not in by: n_noid += 1; rep.append((i, 'IGNORADO', 'id que no existe en el juego')); continue
        if not es0.strip():
            n_vacio += 1; continue
        n_tot += 1; jp = by[i]['japanese']
        antes = errores_de(jp, es0, reglas)
        es1, hechos = corregir(jp, es0, reglas)
        despues = errores_de(jp, es1, reglas)
        avisos = [p for n, p in revisar(jp, es1, reglas) if n != 'ERROR']; n_avisos += len(avisos)
        if hechos: n_corr += 1; rep.append((i, 'CORREGIDO', ' | '.join(hechos) + ((' || errores que habia: ' + '; '.join(antes)) if antes else '')))
        if despues:
            n_mal += 1; rep.append((i, 'ERROR SIN CORREGIR', '; '.join(despues) + ' -> se quedara en japones hasta que lo arregles'))
        else: n_ok += 1
        for a in avisos: rep.append((i, 'aviso', a))
        if not solo:
            by[i]['spanish'] = es1
            st = (f.get('status') or '').strip().lower()
            by[i]['status'] = 'error' if despues else (st if st in ('draft', 'reviewed', 'approved') else 'draft')
    # filas del maestro sin espanol (pendientes)
    pend = [r for r in m if not r['spanish'].strip()] if not solo else []
    if not solo:
        b = respaldar(MAESTRO); escribir_maestro(m)
    # reporte
    os.makedirs(TRAB, exist_ok=True)
    base = os.path.join(TRAB, 'reporte_revision')
    with open(base + '.csv', 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['id', 'estado', 'detalle']); w.writerows(rep)
    with open(os.path.join(TRAB, 'pendientes.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['id', 'voice', 'japanese', 'spanish', 'status'])
        for r in pend: w.writerow([r['id'], r['voice'], r['japanese'], '', 'pendiente'])
    L = ['REVISION de "%s"  (%s)' % (os.path.basename(ruta), datetime.datetime.now().strftime('%Y-%m-%d %H:%M')),
         'Parametros del juego: %d caracteres por renglon, %d renglones, maximo %d caracteres por mensaje.' % (ANCHO, RENGLONES, MAX_CHARS)]
    if aviso_enc: L.append('OJO: ' + aviso_enc)
    L += ['',
          'Mensajes con espanol revisados ..... %d' % n_tot,
          '  correctos al final .............. %d' % n_ok,
          '  con arreglos automaticos ........ %d' % n_corr,
          '  con ERRORES que no pude corregir  %d' % n_mal,
          'Filas sin espanol en tu archivo .... %d' % n_vacio,
          'ids que no existen (ignorados) ..... %d' % n_noid,
          'Avisos de estilo (revisar a mano) .. %d' % n_avisos]
    if not solo:
        L += ['', 'RESULTADO: trabajo\\CSV_MAESTRO.csv actualizado (respaldo del anterior en trabajo\\respaldos).',
              'Mensajes que aun faltan por traducir en el maestro: %d (lista en trabajo\\pendientes.csv)' % len(pend)]
    else:
        L += ['', 'Modo solo revisar: no se cambio ningun archivo.']
    mal = [x for x in rep if x[1] == 'ERROR SIN CORREGIR']; cor = [x for x in rep if x[1] == 'CORREGIDO']
    if mal: L += ['', '== ERRORES QUE NO SE PUDIERON CORREGIR (arreglalos a mano) =='] + ['id %s: %s' % (x[0], x[2]) for x in mal]
    if cor: L += ['', '== ARREGLOS AUTOMATICOS =='] + ['id %s: %s' % (x[0], x[2]) for x in cor]
    av = [x for x in rep if x[1] == 'aviso']
    if av: L += ['', '== AVISOS DE ESTILO (no impiden generar el .dat) =='] + ['id %s: %s' % (x[0], x[2]) for x in av]
    ign = [x for x in rep if x[1] == 'IGNORADO']
    if ign: L += ['', '== IGNORADOS =='] + ['id %s: %s' % (x[0], x[2]) for x in ign]
    open(base + '.txt', 'w', encoding='utf-8-sig').write('\n'.join(L) + '\n')
    print('\n'.join(L[:16]))
    for x in mal[:30]: print('  ERROR id %s: %s' % (x[0], x[2]))
    if len(mal) > 30: print('  ... y %d mas' % (len(mal) - 30))
    for x in cor[:15]: print('  corregido id %s: %s' % (x[0], x[2][:150]))
    if len(cor) > 15: print('  ... y %d mas' % (len(cor) - 15))
    print('\nReporte completo: %s.txt (y .csv)' % base)
    print('\nLISTO.' + ('' if solo else ' Siguiente paso: 3_GENERAR_DAT.'))
    return n_mal

# =====================================================================================
# 3) GENERAR DAT  (CSV_MAESTRO.csv -> data3.dat)
# =====================================================================================
def cmd_generar(args):
    args = [a for a in args if not a.startswith('--')]
    if args:                                      # si te pasan un CSV, primero se revisa y corrige
        cmd_revisar(args); print('\n' + '=' * 70 + '\n')
    juego = carpeta_juego()
    if not (os.path.isfile(MAESTRO) and os.path.isfile(EXEC0) and os.path.isfile(CADENAS)):
        print('Leyendo el guion original de tu juego (solo la primera vez) ...')
        cmd_extraer([juego], aviso_final=False); print()
    import pl_build as pb, pl_exec_tool as pt, pl_cadenas as pc, pl_extraer as px
    pb.usar_clave(); reglas = cargar_reglas()
    rows = list(csv.DictReader(open(MAESTRO, encoding='utf-8-sig')))
    print('[1/4] Revisando el CSV maestro ...')
    usados = 0; malos = []
    for r in rows:
        es = r['spanish']
        if not es.strip(): r['spanish'] = ''; continue
        es, _ = corregir(r['japanese'], es, reglas)
        e = errores_de(r['japanese'], es, reglas)
        if e: malos.append((r['id'], '; '.join(e))); r['spanish'] = ''; continue
        r['spanish'], _ = pb.wrap_lines(es.strip(), ANCHO); r['status'] = 'draft'; usados += 1
    print('      %d mensajes en espanol, %d sin traducir%s' % (usados, sum(1 for r in rows if not r['spanish']) - len(malos),
          (', %d con errores (se quedan en japones)' % len(malos)) if malos else ''))
    for i, e in malos[:20]: print('      ERROR id %s: %s' % (i, e))
    tmp = tempfile.mkdtemp()
    tcsv = os.path.join(tmp, 'w.csv'); texe = os.path.join(tmp, 'e.dat'); exe1 = EXEC0
    with open(tcsv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print('[2/4] Guion, nombres y opciones ...')
    if os.path.isfile(CADENAS) and any(r['spanish'].strip() for r in csv.DictReader(open(CADENAS, encoding='utf-8-sig'), delimiter='\t')):
        exe1 = os.path.join(tmp, 'c.dat'); pc.insertar(EXEC0, CADENAS, exe1)
    pt.insert(exe1, tcsv, texe, 0)
    tree = {'data': {'system': {'exec.dat': open(texe, 'rb').read()}}}
    print('[3/4] Interfaz ...')
    lista = os.path.join(KIT, 'interfaz', 'lista_interfaz.txt'); nui = ndat = 0
    if os.path.isfile(lista):
        d1 = px.Dat(os.path.join(juego, 'data1.dat'))
        for rel in [l.strip() for l in open(lista, encoding='utf-8') if l.strip()]:
            p = os.path.join(KIT, 'interfaz', *rel.split('/'))
            if os.path.isfile(p): b = open(p, 'rb').read(); nui += 1
            else: b = d1.data(d1.find(rel)); ndat += 1
            node = tree
            for x in rel.split('/')[:-1]: node = node.setdefault(x, {})
            node[rel.split('/')[-1]] = b
        print('      %d archivos traducidos del kit + %d originales de tu data1.dat' % (nui, ndat))
    print('[4/4] Escribiendo y comprobando data3.dat (puede tardar un poco) ...')
    out = os.path.join(TRAB, 'data3.dat')
    pb.escribir_libp(tree, out)
    d = px.Dat(out)
    def check(node, path):
        for k, v in node.items():
            pp = path + '/' + k if path else k
            if isinstance(v, dict): check(v, pp)
            elif d.data(d.find(pp)) != v: raise SystemExit('ERROR: la relectura del data3 no coincide en ' + pp)
    check(tree, ''); d.f.close()
    dst = os.path.join(juego, 'data3.dat')
    if os.path.isfile(dst):
        rd = os.path.join(TRAB, 'respaldos'); os.makedirs(rd, exist_ok=True)
        b = os.path.join(rd, 'data3_anterior_%s.dat' % ahora()); shutil.copyfile(dst, b)
        print('      respaldo del data3.dat anterior: %s' % b)
    shutil.copyfile(out, dst)
    print('\nLISTO: %s (%d bytes, comprobado).' % (dst, os.path.getsize(dst)))
    print('Abre el juego para probarlo. Para volver al japones, quita o renombra ese data3.dat.')

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    c, r = a[0], a[1:]
    if c == 'extraer': cmd_extraer(r)
    elif c in ('revisar', 'corregir'): cmd_revisar(r)
    elif c == 'validar': cmd_revisar(r + ['--solo-revisar'])
    elif c in ('generar', 'integrar'): cmd_generar(r)
    else: print(__doc__); sys.exit(1)

if __name__ == '__main__': main()
