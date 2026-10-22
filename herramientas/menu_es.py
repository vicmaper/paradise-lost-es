# -*- coding: utf-8 -*-
"""Menu de Windows (ファイル / 設定 / ヘルプ) de malie.exe en espanol.
Reescribe las plantillas MENU en su mismo lugar; el texto nuevo debe caber en el tamano original."""
import sys, struct, pefile
ES = {
 'ファイル(&F)': '&Archivo', 'ﾌｧｲﾙ(&F)': '&Archivo',
 'クイックセーブ\tF9': 'Guardado rápido\tF9', 'クイックロード\tF10': 'Carga rápida\tF10',
 'クイックセーブデータの初期化': 'Borrar guardado rápido', 'クイックセーブデータ(&Q)': 'Datos &rápidos',
 'オートセーブデータ(&A)': 'Datos &auto.', 'タイトルに戻る(&T)\tT': 'Volver al &título\tT',
 '最小化(&N)\tF1': 'Mi&nimizar\tF1', '画面切り替え(&W)\tAlt+Enter': '&Ventana/pantalla\tAlt+Enter',
 '終了(&X)\t Alt+F4': '&Salir\tAlt+F4', '設定(&C)': '&Configuración', 'コンフィグ(&C)...': '&Opciones...',
 'オートセーブ': 'Guardado automático', 'ON': 'Sí', 'OFF': 'No', 'オートセーブデータ': 'Guardado auto.',
 'オートセーブデータの初期化': 'Borrar guardado auto.', 'オートモード': 'Modo auto',
 '常にメッセージを表示する': 'Mostrar siempre el texto', 'ボイス再生時のセリフ表示': 'Texto con voz',
 'スキップ設定': 'Saltar texto', '既読部分のみ': 'Solo lo leído', '全て': 'Todo',
 'ヘルプ(&H)': 'A&yuda', 'バージョン情報(&V)...': 'Acerca de (&versión)...',
 'ショートカットキー一覧(&K)...\tF12': 'Atajos de teclado...\tF12',
}
MENUS = ['APP', 'APP2', 'APP3']

def rebuild(d):
    ver, hs = struct.unpack_from('<HH', d, 0); p = 4 + hs; out = bytearray(d[:p]); miss = []
    while p < len(d):
        fl = struct.unpack_from('<H', d, p)[0]; out += d[p:p + 2]; p += 2
        if not fl & 0x10: out += d[p:p + 2]; p += 2
        e = p
        while d[e:e + 2] != b'\0\0': e += 2
        t = d[p:e].decode('utf-16-le'); p = e + 2
        n = ES.get(t, t)
        if n == t and t and t != 'DAMMY': miss.append(t)
        out += n.encode('utf-16-le') + b'\0\0'
        if fl & 0x80 and p >= len(d) - 1: break
    return bytes(out), miss

def main(src, dst):
    pe = pefile.PE(src); data = bytearray(open(src, 'rb').read())
    for e in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if e.id != pefile.RESOURCE_TYPE['RT_MENU']: continue
        for x in e.directory.entries:
            if str(x.name) not in MENUS: continue
            for l in x.directory.entries:
                r = l.data.struct; off = pe.get_offset_from_rva(r.OffsetToData)
                d = bytes(data[off:off + r.Size]); new, miss = rebuild(d)
                print('%-5s original %4d  nuevo %4d  %s' % (x.name, r.Size, len(new), 'OK' if len(new) <= r.Size else 'NO CABE'), miss)
                if len(new) <= r.Size:
                    data[off:off + r.Size] = new + b'\0' * (r.Size - len(new))
    open(dst, 'wb').write(data)



def main2(src, dst):
    """Version que mueve los menus al final de .rsrc (el espacio original no alcanza)."""
    pe = pefile.PE(src); s = pe.sections[-1]
    assert s.Name.startswith(b'.rsrc')
    base_rva = s.VirtualAddress + ((s.Misc_VirtualSize + 3) & ~3)
    blobs = []; rva = base_rva
    for e in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if e.id != pefile.RESOURCE_TYPE['RT_MENU']: continue
        for x in e.directory.entries:
            if str(x.name) not in MENUS: continue
            for l in x.directory.entries:
                r = l.data.struct; d = pe.get_data(r.OffsetToData, r.Size)
                new, miss = rebuild(d); assert not miss, miss
                r.OffsetToData = rva; r.Size = len(new)
                pad = (-len(new)) % 4; blobs.append(new + b'\0' * pad); rva += len(new) + pad
                print(x.name, len(new))
    extra = b''.join(blobs); new_vsize = rva - s.VirtualAddress
    end_v = s.VirtualAddress + ((new_vsize + 4095) & ~4095)
    assert end_v <= pe.OPTIONAL_HEADER.SizeOfImage, 'no cabe en la imagen'
    new_raw = (new_vsize + 511) & ~511
    old_raw = s.SizeOfRawData
    s.Misc_VirtualSize = new_vsize; s.SizeOfRawData = max(old_raw, new_raw)
    pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].Size = max(pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].Size, new_vsize)
    data = bytearray(pe.write())
    if len(data) < s.PointerToRawData + s.SizeOfRawData:
        data += b'\0' * (s.PointerToRawData + s.SizeOfRawData - len(data))
    off = s.PointerToRawData + (base_rva - s.VirtualAddress)
    data[off:off + len(extra)] = extra
    # el programa busca estos dos submenus por su nombre para meter la lista de guardados:
    # se cambia tambien el nombre que busca (.rdata), en su mismo espacio
    for jp, room in (('ファイル(&F)', 9), ('クイックセーブデータ(&Q)', 15), ('オートセーブデータ(&A)', 13)):
        es = ES[jp]; assert len(es) <= room, es
        old = jp.encode('utf-16-le') + b'\0\0'; i = bytes(data).find(old)
        sec = [x for x in pe.sections if x.Name.startswith(b'.rdata')][0]
        assert sec.PointerToRawData <= i < sec.PointerToRawData + sec.SizeOfRawData
        data[i:i + len(old)] = (es.encode('utf-16-le') + b'\0' * 2 * (len(jp) + 1 - len(es)))[:len(old)] if len(es) <= len(jp) else b''
        if len(es) > len(jp):
            new = es.encode('utf-16-le') + b'\0\0'; assert data[i + len(old):i + len(new)] == b'\0' * (len(new) - len(old)); data[i:i + len(new)] = new
        print('rdata', jp, '->', es)
    pe2 = pefile.PE(data=bytes(data)); pe2.OPTIONAL_HEADER.CheckSum = pe2.generate_checksum()
    open(dst, 'wb').write(pe2.write()); print('listo', len(data))
if __name__ == '__main__': main2(*sys.argv[1:3])
