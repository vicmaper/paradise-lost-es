# -*- coding: utf-8 -*-
"""pl_exe_es.py - malie.exe de Paradise Lost con menus de Windows y avisos en espanol.
  python pl_exe_es.py malie.exe malie_es.exe
1) Menus APP/APP2/APP3 (ファイル/設定/ヘルプ): se mueven al final de .rsrc (menu_es.py de KKK, main2).
2) Avisos en .rdata: se reescriben en su mismo lugar (deben caber; se buscan por texto, no por direccion).
3) Tabla de textos (RT_STRING): mismo largo, se rellena con espacios.
No se tocan los avisos de proteccion/disco/registro de producto."""
import sys, os, struct, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menu_es

RDATA = [
 ('タイトルに戻ります。\nよろしいですか？', '¿Volver al título?'),
 ('シーン鑑賞を中断します。\nよろしいですか？', '¿Salir de la escena?'),
 ('アナザーストーリーを中断します。\nよろしいですか？', '¿Salir de Another Story?'),
 ('中断します。\nよろしいですか？', '¿Interrumpir?'),
 ('No. %02d を上書きしますか？', '¿Reemplazar %02d?'),
 ('No. %2d を上書きしますか？', '¿Reemplazar %2d?'),
 ('コメントを入力して下さい', 'Comentario:'),
 ('セーブしました。', 'Guardado'),
 ('コメント無し', 'Vacío'),
 ('(無題)', '(—)'),
 ('(不明)', '(?)'),
 ('『萌えゲーアワード』\nのページを開きますか？', '¿Abrir Moe Game\nAward?'),
 ('light ホームページを開きます。\nよろしいですか？', '¿Abrir la página\nde light?'),
]
RES = [
 ('終了します。\nよろしいですか？', '¿Cerrar juego?'),
 ('ロードに失敗しました。\nセーブデータが存在しません。', 'Error de carga.\nSin datos.'),
 ('　コメントが作成されておりません。', 'Sin comentario'),
]

def room(d, a):
    """caracteres disponibles: el texto + los ceros que siguen (dejando un terminador)"""
    e = a
    while d[e:e+2] != b'\0\0': e += 2
    z = e
    while d[z:z+2] == b'\0\0' and z - e < 400: z += 2
    return (z - a) // 2 - 1

def main(src, dst):
    tmp = os.path.join(tempfile.mkdtemp(), 'm.exe')
    menu_es.main2(src, tmp)                       # menus + nombres de submenu en .rdata
    d = bytearray(open(tmp, 'rb').read()); ok = True
    for jp, es in RDATA:
        b = jp.encode('utf-16-le') + b'\0\0'
        hits = [i for i in range(len(d)) if False]
        hits = []; i = d.find(b)
        while i != -1:
            if i % 2 == 0 and d[i-2:i] == b'\0\0': hits.append(i)
            i = d.find(b, i + 1)
        assert len(hits) == 1, 'texto %r encontrado %d veces' % (jp, len(hits))
        a = hits[0]
        c = len(jp)   # NUNCA pasar del largo original: los ceros que siguen pueden ser otros datos (p. ej. L"")
        fits = len(es) <= c
        print('%x %2d/%2d %s %r' % (a, len(es), c, 'OK' if fits else 'NO CABE', es))
        if not fits: ok = False; continue
        n = len(jp) + 1
        new = es.encode('utf-16-le') + b'\0\0'
        d[a:a + max(len(new), 2 * n)] = new + b'\0' * max(0, 2 * n - len(new))
    for jp, es in RES:
        L = len(jp); b = struct.pack('<H', L) + jp.encode('utf-16-le'); a = d.find(b)
        assert a != -1, 'no encontre recurso %r' % jp
        fits = len(es) <= L
        print('res %x %2d/%2d %s %r' % (a, len(es), L, 'OK' if fits else 'NO CABE', es))
        if not fits: ok = False; continue
        d[a+2:a+2+2*L] = es.ljust(L).encode('utf-16-le')
    import pefile
    pe = pefile.PE(data=bytes(d)); pe.OPTIONAL_HEADER.CheckSum = pe.generate_checksum()
    open(dst, 'wb').write(pe.write())
    print('LISTO' if ok else 'ATENCION: textos que no caben')

if __name__ == '__main__': main(*sys.argv[1:3])
