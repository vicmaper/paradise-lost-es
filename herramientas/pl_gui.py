#!/usr/bin/env python3
"""pl_gui.py - Ventana para el kit de traduccion de Paradise Lost (light, 2017).
Abrela con ABRIR_HERRAMIENTA.bat (Windows) o:  python3 herramientas/pl_gui.py
Usa las mismas funciones que pl_kit.py (extraer, revisar y corregir, generar)."""
import os, sys, io, re, csv, queue, threading, subprocess, webbrowser, traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import pl_kit as K

DISCORD = 'https://discord.gg/k3Zfp85jMr'
TITULO = 'Paradise Lost - Traducción al español'
ESTADOS = ('draft', 'reviewed', 'approved')

class Cola(io.TextIOBase):
    def __init__(self, q): self.q = q
    def write(self, s): self.q.put(s); return len(s)
    def flush(self): pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO); self.geometry('1180x780'); self.minsize(960, 640)
        self.q = queue.Queue(); self.ocupado = False
        self.rows = None; self.by = {}; self.cambios = False; self.actual = None; self.reglas = K.cargar_reglas()
        self.cad = None; self.cad_cambios = False
        self._estilo()
        nb = ttk.Notebook(self); nb.pack(fill='both', expand=True, padx=6, pady=(6, 0)); self.nb = nb
        self.t_ini = ttk.Frame(nb); self.t_ed = ttk.Frame(nb); self.t_cad = ttk.Frame(nb)
        nb.add(self.t_ini, text='  1. Inicio  '); nb.add(self.t_ed, text='  2. Editar mensajes  ')
        nb.add(self.t_cad, text='  3. Nombres y opciones  ')
        nb.bind('<<NotebookTabChanged>>', self._cambio_pestana)
        self._inicio(); self._editor(); self._cadenas(); self._log()
        self.protocol('WM_DELETE_WINDOW', self._cerrar)
        self.after(100, self._leer_cola); self._refrescar_estado()

    # ------------------------------------------------------------------ apariencia
    def _estilo(self):
        s = ttk.Style(self)
        try: s.theme_use('vista' if sys.platform == 'win32' else 'clam')
        except tk.TclError: pass
        self.fuente = ('Meiryo UI', 10) if sys.platform == 'win32' else ('Noto Sans CJK JP', 10)
        s.configure('Grande.TButton', padding=(10, 6))
        s.configure('Titulo.TLabel', font=(self.fuente[0], 13, 'bold'))
        s.configure('Nota.TLabel', foreground='#555')
        s.configure('Treeview', rowheight=22)

    # ------------------------------------------------------------------ pestaña inicio
    def _inicio(self):
        f = self.t_ini
        ttk.Label(f, text=TITULO, style='Titulo.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=12, pady=(12, 2))
        ttk.Label(f, text='Funciona con TU copia del juego (edición 2017). Tu data1.dat nunca se modifica.',
                  style='Nota.TLabel').grid(row=1, column=0, columnspan=3, sticky='w', padx=12)
        ttk.Label(f, text='Carpeta del juego (donde están malie.exe y data1.dat):').grid(row=2, column=0, columnspan=3, sticky='w', padx=12, pady=(14, 2))
        self.v_juego = tk.StringVar(value=K.leer_config().get('JUEGO', ''))
        ttk.Entry(f, textvariable=self.v_juego).grid(row=3, column=0, columnspan=2, sticky='we', padx=(12, 4))
        ttk.Button(f, text='Examinar...', command=self._elegir_juego).grid(row=3, column=2, sticky='w', padx=4)
        pasos = [
            ('Extraer el guion del juego', self.a_extraer,
             'Saca el guion de tu data1.dat y crea el CSV maestro (ya trae la traducción del kit).\nSi ya tienes un CSV maestro, no se toca.'),
            ('Usar mi propio CSV...', self.a_mi_csv,
             'Elige tu CSV (con el nombre que sea; columnas id y spanish). Se revisa, se corrige\nlo que se pueda y queda como CSV maestro.'),
            ('Revisar y corregir el CSV maestro', self.a_revisar,
             'Pasa todas las validaciones (marcas, largo, japonés sin traducir, estilo) y\ncorrige lo automático. Reporte en trabajo\\reporte_revision.txt.'),
            ('Generar e instalar la traducción (data3.dat)', self.a_generar,
             'Revisa el CSV maestro, arma el data3.dat con guion, nombres, opciones e interfaz\nen español y lo copia a la carpeta del juego (con respaldo del anterior).'),
            ('Crear malie_es.exe (menús en español)', self.a_exe,
             'Copia de malie.exe con los menús de la ventana y avisos en español.\nmalie.exe queda intacto. Abre el juego con malie_es.exe.'),
            ('Quitar la traducción', self.a_quitar,
             'Renombra data3.dat a data3.dat.bak: el juego vuelve a estar en japonés.'),
        ]
        self.botones = []
        for k, (txt, fn, desc) in enumerate(pasos):
            b = ttk.Button(f, text=txt, command=fn, style='Grande.TButton', width=42)
            b.grid(row=4 + k, column=0, sticky='w', padx=12, pady=5); self.botones.append(b)
            ttk.Label(f, text=desc, style='Nota.TLabel').grid(row=4 + k, column=1, columnspan=2, sticky='w', padx=8)
        fr = ttk.Frame(f); fr.grid(row=11, column=0, columnspan=3, sticky='we', padx=12, pady=(14, 4))
        ttk.Button(fr, text='Abrir reporte', command=lambda: self._abrir(os.path.join(K.TRAB, 'reporte_revision.txt'))).pack(side='left')
        ttk.Button(fr, text='Abrir carpeta de trabajo', command=lambda: self._abrir(K.TRAB)).pack(side='left', padx=6)
        ttk.Button(fr, text='Instrucciones (LEEME)', command=lambda: self._abrir(os.path.join(K.KIT, 'LEEME.txt'))).pack(side='left')
        ttk.Button(fr, text='Abrir el juego', command=self.a_jugar).pack(side='left', padx=6)
        ttk.Button(fr, text='¿Qué se revisa?', command=self.a_ayuda).pack(side='left')
        ttk.Button(fr, text='Discord del proyecto', command=lambda: webbrowser.open(DISCORD)).pack(side='right')
        self.v_estado = tk.StringVar()
        ttk.Label(f, textvariable=self.v_estado, style='Nota.TLabel', justify='left').grid(row=12, column=0, columnspan=3, sticky='w', padx=12, pady=(6, 0))
        f.columnconfigure(1, weight=1)

    def _elegir_juego(self):
        d = filedialog.askdirectory(title='Carpeta del juego (malie.exe y data1.dat)', initialdir=self.v_juego.get() or None)
        if d: self.v_juego.set(os.path.normpath(d)); self._guardar_juego(); self._refrescar_estado()

    def _guardar_juego(self):
        j = self.v_juego.get().strip().strip('"')
        if not j or not os.path.isfile(os.path.join(j, 'data1.dat')):
            messagebox.showerror(TITULO, 'Elige la carpeta del juego: la que tiene malie.exe y data1.dat.'); return None
        c = K.leer_config(); c['JUEGO'] = j; K.guardar_config(c); return j

    def _refrescar_estado(self):
        partes = []
        if os.path.isfile(K.MAESTRO):
            try:
                rr = list(csv.DictReader(open(K.MAESTRO, encoding='utf-8-sig')))
                es = sum(1 for r in rr if r['spanish'].strip()); er = sum(1 for r in rr if r['status'] == 'error')
                partes.append('CSV maestro: %d mensajes, %d en español, %d sin traducir%s.' % (len(rr), es, len(rr) - es, (', %d con error' % er) if er else ''))
            except Exception as e: partes.append('CSV maestro: no se pudo leer (%s).' % e)
        else: partes.append('CSV maestro: todavía no existe (paso "Extraer" o "Usar mi propio CSV").')
        j = self.v_juego.get().strip()
        if j and os.path.isdir(j):
            partes.append('data3.dat en el juego: %s.   malie_es.exe: %s.' % (
                'SI' if os.path.isfile(os.path.join(j, 'data3.dat')) else 'no',
                'SI' if os.path.isfile(os.path.join(j, 'malie_es.exe')) else 'no'))
        self.v_estado.set('\n'.join(partes))

    # ------------------------------------------------------------------ tareas en segundo plano
    def _correr(self, titulo, fn, al_terminar=None):
        if self.ocupado: messagebox.showinfo(TITULO, 'Espera a que termine la tarea actual.'); return
        self.ocupado = True
        for b in self.botones: b.state(['disabled'])
        self._escribir('\n' + '=' * 70 + '\n' + titulo + '\n' + '=' * 70 + '\n')
        def trabajo():
            viejo = sys.stdout; sys.stdout = Cola(self.q); ok = True
            try: fn()
            except SystemExit as e:
                if e.code not in (None, 0): print(str(e.code)); ok = False
            except Exception:
                print('ERROR inesperado:\n' + traceback.format_exc()); ok = False
            finally: sys.stdout = viejo
            self.q.put(('FIN', ok, al_terminar))
        threading.Thread(target=trabajo, daemon=True).start()

    def _leer_cola(self):
        try:
            while True:
                x = self.q.get_nowait()
                if isinstance(x, tuple) and x and x[0] == 'FIN':
                    self.ocupado = False
                    for b in self.botones: b.state(['!disabled'])
                    self._refrescar_estado()
                    if x[2]: x[2](x[1])
                else: self._escribir(x)
        except queue.Empty: pass
        self.after(100, self._leer_cola)

    def _escribir(self, s):
        self.log.configure(state='normal'); self.log.insert('end', s); self.log.see('end'); self.log.configure(state='disabled')

    def _log(self):
        fr = ttk.LabelFrame(self, text='Mensajes'); fr.pack(fill='x', padx=6, pady=6)
        self.log = tk.Text(fr, height=9, wrap='word', state='disabled', font=('Consolas', 9) if sys.platform == 'win32' else ('Monospace', 9))
        sb = ttk.Scrollbar(fr, command=self.log.yview); self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side='left', fill='both', expand=True); sb.pack(side='right', fill='y')

    def _listo(self, texto):
        def f(ok):
            if ok: messagebox.showinfo(TITULO, 'LISTO.\n\n' + texto)
            else: messagebox.showwarning(TITULO, 'No se completo. Lee los mensajes de abajo.')
        return f

    def _guardar_pendientes(self):
        if self.cambios or self.cad_cambios:
            r = messagebox.askyesnocancel(TITULO, 'Tienes cambios sin guardar en el editor. ¿Guardarlos antes de seguir?')
            if r is None: return False
            if r: self.ed_guardar_csv(); self.cad_guardar()
            else: self.cambios = self.cad_cambios = False
        return True

    def _recargar_editor(self, ok=True):
        self.rows = None; self.cad = None
        if self.nb.index('current') == 1: self.ed_cargar()
        if self.nb.index('current') == 2: self.cad_cargar()

    # ------------------------------------------------------------------ acciones
    def a_extraer(self):
        j = self._guardar_juego()
        if not j or not self._guardar_pendientes(): return
        self._correr('Extraer el guion', lambda: K.cmd_extraer([j]), lambda ok: (self._recargar_editor(), self._listo('Se creo trabajo\\CSV_MAESTRO.csv.')(ok)))

    def a_mi_csv(self):
        p = filedialog.askopenfilename(title='Elige tu CSV traducido', filetypes=[('CSV o TSV', '*.csv *.tsv *.txt'), ('Todos', '*.*')])
        if not p or not self._guardar_pendientes(): return
        self._correr('Revisar y corregir: ' + os.path.basename(p), lambda: K.cmd_revisar([p]),
                     lambda ok: (self._recargar_editor(), self._listo('Tu CSV se revisó y quedó como CSV maestro.\n'
                                 'Detalle de errores y correcciones: botón "Abrir reporte".')(ok)))

    def a_revisar(self):
        if not self._guardar_pendientes(): return
        self._correr('Revisar y corregir el CSV maestro', lambda: K.cmd_revisar([]),
                     lambda ok: (self._recargar_editor(), self._listo('Revisión terminada. Detalle: botón "Abrir reporte".')(ok)))

    def a_generar(self):
        j = self._guardar_juego()
        if not j or not self._guardar_pendientes(): return
        self._correr('Generar data3.dat', lambda: K.cmd_generar([]),
                     self._listo('data3.dat instalado en la carpeta del juego.\nAbre el juego (de preferencia con malie_es.exe).'))

    def a_exe(self):
        j = self._guardar_juego()
        if not j: return
        dst = os.path.join(j, 'malie_es.exe')
        if os.path.isfile(dst) and not messagebox.askyesno(TITULO, 'Ya existe malie_es.exe. ¿Rehacerlo? (se guarda respaldo)'): return
        try: import pefile  # noqa
        except ImportError:
            if not messagebox.askyesno(TITULO, 'Para este paso hace falta el módulo "pefile" de Python.\n¿Instalarlo ahora? (necesita internet)'): return
            r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'pefile'], capture_output=True, text=True)
            self._escribir(r.stdout[-1500:] + r.stderr[-1500:])
            if r.returncode != 0: messagebox.showerror(TITULO, 'No se pudo instalar pefile. Prueba en CMD:  python -m pip install pefile'); return
        def fn():
            import shutil, pl_exe_es
            if os.path.isfile(dst):
                os.makedirs(os.path.join(K.TRAB, 'respaldos'), exist_ok=True)
                shutil.copyfile(dst, os.path.join(K.TRAB, 'respaldos', 'malie_es_%s.exe' % K.ahora()))
            pl_exe_es.main(os.path.join(j, 'malie.exe'), dst)
        self._correr('Crear malie_es.exe', fn, self._listo('Se creo malie_es.exe en la carpeta del juego.\nmalie.exe queda intacto.'))

    def a_quitar(self):
        j = self._guardar_juego()
        if not j: return
        p = os.path.join(j, 'data3.dat')
        if not os.path.isfile(p): messagebox.showinfo(TITULO, 'No hay data3.dat: el juego ya está en japonés.'); return
        if not messagebox.askyesno(TITULO, '¿Quitar la traducción? (data3.dat se renombra a data3.dat.bak)'): return
        b = p + '.bak'
        if os.path.exists(b): b = p + '.%s.bak' % K.ahora()
        os.replace(p, b); self._escribir('data3.dat renombrado a %s\n' % os.path.basename(b)); self._refrescar_estado()

    def a_ayuda(self):
        messagebox.showinfo(TITULO, (
            'Cada mensaje se revisa así:\n\n'
            'MARCAS (error si fallan)\n'
            '- {v:..} al inicio y {/v} antes del {end}, igual que el japonés (se corrige solo)\n'
            '- misma cantidad de {end} que el japonés (se corrige solo)\n'
            '- sin marcas desconocidas ni llaves sueltas; sin furigana {r:..} (se deja la base)\n\n'
            'TAMAÑO (error si no cabe)\n'
            '- %d caracteres por renglón (los saltos se ponen solos)\n'
            '- máximo %d renglones (si sobran, se prueba quitar los {n}; si no, hay que acortar)\n'
            '- máximo %d caracteres por mensaje\n\n'
            'TEXTO (error)\n'
            '- sin japonés sin traducir; la puntuación japonesa se cambia sola\n\n'
            'ESTILO (avisos, no impiden generar)\n'
            '- «...» → «…», ¿? y ¡! en pareja, espacios, honoríficos, vosotros, nombres\n\n'
            'Lo que no se puede corregir queda con status "error" y se ve en japonés.\n'
            'Detalle completo en README.md y en trabajo\\reporte_revision.txt.') % (K.ANCHO, K.RENGLONES, K.MAX_CHARS))

    def a_jugar(self):
        j = self.v_juego.get().strip()
        exe = next((os.path.join(j, x) for x in ('malie_es.exe', 'malie.exe') if os.path.isfile(os.path.join(j, x))), None)
        if not exe: messagebox.showerror(TITULO, 'No encuentro malie.exe en la carpeta del juego.'); return
        if sys.platform != 'win32': messagebox.showinfo(TITULO, 'En Linux/Steam Deck abre el juego desde Steam (con Proton).'); return
        subprocess.Popen([exe], cwd=j)

    def _abrir(self, p):
        if not os.path.exists(p): messagebox.showinfo(TITULO, 'Todavía no existe:\n' + p); return
        if sys.platform == 'win32': os.startfile(p)
        else: subprocess.Popen(['xdg-open', p])

    # ------------------------------------------------------------------ pestaña editor
    def _editor(self):
        f = self.t_ed
        top = ttk.Frame(f); top.pack(fill='x', padx=8, pady=6)
        ttk.Label(top, text='Buscar (id o texto):').pack(side='left')
        self.v_buscar = tk.StringVar(); e = ttk.Entry(top, textvariable=self.v_buscar, width=34); e.pack(side='left', padx=4)
        e.bind('<Return>', lambda ev: self.ed_filtrar())
        ttk.Label(top, text='Mostrar:').pack(side='left', padx=(10, 2))
        self.v_filtro = tk.StringVar(value='Todos')
        cb = ttk.Combobox(top, textvariable=self.v_filtro, state='readonly', width=18,
                          values=['Todos', 'Sin traducir', 'Con error', 'Con avisos de estilo', 'Editados en esta sesión'])
        cb.pack(side='left'); cb.bind('<<ComboboxSelected>>', lambda ev: self.ed_filtrar())
        ttk.Button(top, text='Buscar', command=self.ed_filtrar).pack(side='left', padx=4)
        ttk.Button(top, text='Guardar CSV maestro', command=self.ed_guardar_csv).pack(side='right')
        self.v_info_lista = tk.StringVar(); ttk.Label(top, textvariable=self.v_info_lista, style='Nota.TLabel').pack(side='right', padx=10)
        pan = ttk.PanedWindow(f, orient='vertical'); pan.pack(fill='both', expand=True, padx=8, pady=(0, 4))
        lf = ttk.Frame(pan); pan.add(lf, weight=3)
        cols = ('id', 'estado', 'japonés', 'español')
        self.tv = ttk.Treeview(lf, columns=cols, show='headings', selectmode='browse')
        for c, w, t in (('id', 60, 'id'), ('estado', 80, 'estado'), ('japonés', 420, 'japonés'), ('español', 520, 'español')):
            self.tv.heading(c, text=t); self.tv.column(c, width=w, stretch=c in ('japonés', 'español'))
        sb = ttk.Scrollbar(lf, command=self.tv.yview); self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side='left', fill='both', expand=True); sb.pack(side='right', fill='y')
        self.tv.bind('<<TreeviewSelect>>', self.ed_seleccion)
        self.tv.tag_configure('error', foreground='#b00020'); self.tv.tag_configure('vacio', foreground='#888')
        df = ttk.Frame(pan); pan.add(df, weight=2)
        ttk.Label(df, text='Japonés (solo lectura):').grid(row=0, column=0, sticky='w')
        self.tx_jp = tk.Text(df, height=4, wrap='word', font=self.fuente, background='#f4f4f4'); self.tx_jp.grid(row=1, column=0, sticky='nsew')
        ttk.Label(df, text='Español (editable; usa {n} para salto de renglón; conserva {v:..}{/v} y {end}):').grid(row=2, column=0, sticky='w', pady=(4, 0))
        self.tx_es = tk.Text(df, height=5, wrap='word', font=self.fuente, undo=True); self.tx_es.grid(row=3, column=0, sticky='nsew')
        self.tx_es.bind('<KeyRelease>', lambda ev: self._programar_revision())
        self.v_chk = tk.StringVar(); self.lb_chk = ttk.Label(df, textvariable=self.v_chk, justify='left'); self.lb_chk.grid(row=4, column=0, sticky='w', pady=2)
        bf = ttk.Frame(df); bf.grid(row=5, column=0, sticky='we', pady=(2, 4))
        for txt, fn in (('<< Anterior', lambda: self.ed_mover(-1)), ('Siguiente >>', lambda: self.ed_mover(1)),
                        ('Siguiente sin traducir', self.ed_sig_pend), ('Corrección automática', self.ed_autocorregir),
                        ('Deshacer cambios', self.ed_deshacer), ('Guardar este mensaje  (Ctrl+S)', self.ed_guardar_msg)):
            ttk.Button(bf, text=txt, command=fn).pack(side='left', padx=2)
        self.tx_es.bind('<Control-s>', lambda ev: (self.ed_guardar_msg(), 'break')[1])
        df.columnconfigure(0, weight=1); df.rowconfigure(3, weight=1)
        self._rev_id = None

    def _cambio_pestana(self, ev=None):
        i = self.nb.index('current')
        if i == 1 and self.rows is None: self.ed_cargar()
        if i == 2 and self.cad is None: self.cad_cargar()

    def ed_cargar(self):
        if not os.path.isfile(K.MAESTRO):
            self.v_info_lista.set('No hay CSV maestro: usa "Extraer" o "Usar mi propio CSV" en Inicio.'); return
        self.rows = list(csv.DictReader(open(K.MAESTRO, encoding='utf-8-sig'))); self.by = {r['id']: r for r in self.rows}
        self.editados = set(); self.cambios = False; self.ed_filtrar()

    def _estado_fila(self, r):
        if not r['spanish'].strip(): return 'sin traducir'
        if r.get('status') == 'error': return 'error'
        return r.get('status') or 'draft'

    def ed_filtrar(self):
        if self.rows is None: self.ed_cargar()
        if self.rows is None: return
        q = self.v_buscar.get().strip(); fl = self.v_filtro.get()
        res = []
        for r in self.rows:
            if q:
                if q.isdigit() and '-' not in q:
                    if r['id'] != q: continue
                elif q.lower() not in r['japanese'].lower() and q.lower() not in r['spanish'].lower(): continue
            if fl == 'Sin traducir' and r['spanish'].strip(): continue
            if fl == 'Con error' and not (r['spanish'].strip() and (r.get('status') == 'error' or K.errores_de(r['japanese'], r['spanish'], self.reglas))): continue
            if fl == 'Con avisos de estilo' and not (r['spanish'].strip() and any(n != 'ERROR' for n, _ in K.revisar(r['japanese'], r['spanish'], self.reglas))): continue
            if fl == 'Editados en esta sesión' and r['id'] not in self.editados: continue
            res.append(r)
        self.tv.delete(*self.tv.get_children())
        LIM = 3000
        for r in res[:LIM]:
            st = self._estado_fila(r)
            self.tv.insert('', 'end', iid=r['id'], values=(r['id'], st, self._corto(r['japanese']), self._corto(r['spanish'])),
                           tags=('error',) if st == 'error' else (('vacio',) if st == 'sin traducir' else ()))
        self.v_info_lista.set('%d resultados%s' % (len(res), (' (se muestran %d; afina la búsqueda)' % LIM) if len(res) > LIM else ''))

    @staticmethod
    def _corto(s):
        s = re.sub(r'\{v:[^}]*\}|\{/v\}|\{end\}', '', s).replace('{n}', ' / ')
        return s[:140]

    def ed_seleccion(self, ev=None):
        sel = self.tv.selection()
        if not sel: return
        i = sel[0]
        if self.actual and self.actual != i and self._texto_es() != self.by[self.actual]['spanish']:
            r = messagebox.askyesnocancel(TITULO, 'El mensaje %s tiene cambios sin guardar. ¿Guardarlos?' % self.actual)
            if r is None:
                self.tv.selection_set(self.actual); return
            if r: self.ed_guardar_msg(mover=False)
        self.actual = i; r = self.by[i]
        self.tx_jp.configure(state='normal'); self.tx_jp.delete('1.0', 'end'); self.tx_jp.insert('1.0', r['japanese']); self.tx_jp.configure(state='disabled')
        self.tx_es.delete('1.0', 'end'); self.tx_es.insert('1.0', r['spanish']); self.tx_es.edit_reset()
        self.ed_revisar_vivo()

    def _texto_es(self): return self.tx_es.get('1.0', 'end-1c')

    def _programar_revision(self):
        if self._rev_id: self.after_cancel(self._rev_id)
        self._rev_id = self.after(250, self.ed_revisar_vivo)

    def ed_revisar_vivo(self):
        if not self.actual: return
        import pl_build as pb
        jp = self.by[self.actual]['japanese']; es = self._texto_es()
        if not es.strip(): self.v_chk.set('Sin traducir: en el juego se vera en japonés.'); self.lb_chk.configure(foreground='#555'); return
        _, n = pb.wrap_lines(es.replace('\n', '{n}'), K.ANCHO)
        res = K.revisar(jp, es, self.reglas)
        err = [p for k, p in res if k == 'ERROR']; av = [p for k, p in res if k != 'ERROR']
        txt = 'Renglones: %d de %d   |   caracteres: %d de %d' % (n, K.RENGLONES, len(es), K.MAX_CHARS)
        if err: txt += '\nERRORES: ' + ' | '.join(err)
        if av: txt += '\nAvisos: ' + ' | '.join(av)
        if not err and not av: txt += '   |   OK'
        self.v_chk.set(txt); self.lb_chk.configure(foreground='#b00020' if err else ('#8a5a00' if av else '#1b5e20'))

    def ed_autocorregir(self):
        if not self.actual: return
        es, hechos = K.corregir(self.by[self.actual]['japanese'], self._texto_es(), self.reglas)
        if not hechos: messagebox.showinfo(TITULO, 'No hay nada que corregir automáticamente en este mensaje.'); return
        self.tx_es.delete('1.0', 'end'); self.tx_es.insert('1.0', es); self.ed_revisar_vivo()
        messagebox.showinfo(TITULO, 'Se corrigio:\n- ' + '\n- '.join(hechos) + '\n\n(Todavía no se guarda: pulsa "Guardar este mensaje".)')

    def ed_deshacer(self):
        if not self.actual: return
        self.tx_es.delete('1.0', 'end'); self.tx_es.insert('1.0', self.by[self.actual]['spanish']); self.ed_revisar_vivo()

    def ed_guardar_msg(self, mover=True):
        if not self.actual: return
        r = self.by[self.actual]; jp = r['japanese']
        es, hechos = K.corregir(jp, self._texto_es(), self.reglas) if self._texto_es().strip() else ('', [])
        err = K.errores_de(jp, es, self.reglas) if es else []
        r['spanish'] = es; r['status'] = 'error' if err else ('draft' if es else 'untranslated')
        self.cambios = True; self.editados.add(self.actual)
        st = self._estado_fila(r)
        self.tv.item(self.actual, values=(r['id'], st, self._corto(jp), self._corto(es)),
                     tags=('error',) if st == 'error' else (('vacio',) if st == 'sin traducir' else ()))
        self.tx_es.delete('1.0', 'end'); self.tx_es.insert('1.0', es); self.ed_revisar_vivo()
        msg = 'Mensaje %s guardado en memoria' % self.actual + (' (con corrección automática: %s)' % ', '.join(hechos) if hechos else '')
        msg += ('. OJO, tiene errores: ' + '; '.join(err) + ' (se vera en japonés hasta corregirlo)') if err else '.'
        self._escribir(msg + ' Recuerda "Guardar CSV maestro".\n')
        if mover and not err: self.ed_mover(1)

    def ed_mover(self, d):
        hijos = self.tv.get_children()
        if not hijos: return
        i = hijos.index(self.actual) if self.actual in hijos else -1
        j = max(0, min(len(hijos) - 1, i + d))
        self.tv.selection_set(hijos[j]); self.tv.see(hijos[j])

    def ed_sig_pend(self):
        if self.rows is None: return
        ids = [r['id'] for r in self.rows]
        k = ids.index(self.actual) + 1 if self.actual in ids else 0
        for r in self.rows[k:] + self.rows[:k]:
            if not r['spanish'].strip() or r.get('status') == 'error':
                if not self.tv.exists(r['id']):
                    self.v_buscar.set(''); self.v_filtro.set('Todos'); self.ed_filtrar()
                self.tv.selection_set(r['id']); self.tv.see(r['id']); return
        messagebox.showinfo(TITULO, 'No quedan mensajes sin traducir ni con error.')

    def ed_guardar_csv(self):
        if self.rows is None: return
        if self.actual and self._texto_es() != self.by[self.actual]['spanish']: self.ed_guardar_msg(mover=False)
        b = K.respaldar(K.MAESTRO); K.escribir_maestro(self.rows); self.cambios = False
        self._escribir('CSV maestro guardado (respaldo del anterior: %s).\n' % (os.path.basename(b) if b else '-'))
        self._refrescar_estado()

    # ------------------------------------------------------------------ pestaña nombres y opciones
    def _cadenas(self):
        f = self.t_cad
        ttk.Label(f, text='Nombres de la caja de nombre y opciones de elección (máximo recomendado: 40 caracteres).',
                  style='Nota.TLabel').pack(anchor='w', padx=8, pady=6)
        lf = ttk.Frame(f); lf.pack(fill='both', expand=True, padx=8)
        cols = ('offset', 'tipo', 'japonés', 'español')
        self.tc = ttk.Treeview(lf, columns=cols, show='headings', selectmode='browse')
        for c, w in (('offset', 80), ('tipo', 80), ('japonés', 380), ('español', 380)):
            self.tc.heading(c, text=c); self.tc.column(c, width=w, stretch=c in ('japonés', 'español'))
        sb = ttk.Scrollbar(lf, command=self.tc.yview); self.tc.configure(yscrollcommand=sb.set)
        self.tc.pack(side='left', fill='both', expand=True); sb.pack(side='right', fill='y')
        self.tc.bind('<<TreeviewSelect>>', self.cad_sel)
        bf = ttk.Frame(f); bf.pack(fill='x', padx=8, pady=6)
        ttk.Label(bf, text='Español:').pack(side='left')
        self.v_cad = tk.StringVar(); e = ttk.Entry(bf, textvariable=self.v_cad, width=60, font=self.fuente); e.pack(side='left', padx=4)
        e.bind('<Return>', lambda ev: self.cad_aplicar())
        ttk.Button(bf, text='Aplicar', command=self.cad_aplicar).pack(side='left')
        ttk.Button(bf, text='Guardar nombres y opciones', command=self.cad_guardar).pack(side='right')

    def cad_cargar(self):
        self.tc.delete(*self.tc.get_children())
        if not os.path.isfile(K.CADENAS): self.cad = []; return
        self.cad = list(csv.DictReader(open(K.CADENAS, encoding='utf-8-sig'), delimiter='\t'))
        for k, r in enumerate(self.cad): self.tc.insert('', 'end', iid=str(k), values=(r['offset'], r['tipo'], r['japanese'], r['spanish']))
        self.cad_cambios = False

    def cad_sel(self, ev=None):
        s = self.tc.selection()
        if s: self.v_cad.set(self.cad[int(s[0])]['spanish'])

    def cad_aplicar(self):
        s = self.tc.selection()
        if not s: return
        v = self.v_cad.get().strip()
        if re.search(r'[぀-ヿ㐀-鿿]', v) or '\t' in v or '{' in v:
            messagebox.showerror(TITULO, 'El texto no puede llevar japonés, tabuladores ni llaves { }.'); return
        if len(v) > 40 and not messagebox.askyesno(TITULO, 'Tiene %d caracteres; puede no caber. ¿Usarlo igual?' % len(v)): return
        k = int(s[0]); self.cad[k]['spanish'] = v; r = self.cad[k]
        self.tc.item(s[0], values=(r['offset'], r['tipo'], r['japanese'], v)); self.cad_cambios = True

    def cad_guardar(self):
        if not self.cad: return
        K.respaldar(K.CADENAS)
        with open(K.CADENAS, 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.DictWriter(fh, fieldnames=['offset', 'tipo', 'usos', 'japanese', 'spanish', 'nota'], delimiter='\t', extrasaction='ignore')
            w.writeheader(); w.writerows(self.cad)
        self.cad_cambios = False; self._escribir('Nombres y opciones guardados.\n')

    # ------------------------------------------------------------------ cerrar
    def _cerrar(self):
        if self.ocupado and not messagebox.askyesno(TITULO, 'Hay una tarea en curso. ¿Cerrar de todos modos?'): return
        if (self.cambios or self.cad_cambios):
            r = messagebox.askyesnocancel(TITULO, 'Hay cambios sin guardar. ¿Guardarlos antes de salir?')
            if r is None: return
            if r: self.ed_guardar_csv(); self.cad_guardar()
        self.destroy()

if __name__ == '__main__':
    App().mainloop()
