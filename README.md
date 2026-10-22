# Paradise Lost (light, 2017) — Traducción al español

Traducción al español latinoamericano de **Paradise Lost** (light, 2017, motor MALIE), primera obra del
Masada-verse, hecha como proyecto de preservación. Este repositorio trae **las herramientas y la traducción**,
**no el juego** ni su texto japonés: todo funciona con **tu propia copia** del juego.

Contacto, dudas y reportes: **Discord → https://discord.gg/NV8TbQQ7B**

## Qué hace
1. Saca el guion de tu `data1.dat` (tu archivo no se modifica).
2. Le pone la traducción (la del proyecto o **tu propio CSV**).
3. Revisa todo (marcas, tamaño del texto, japonés sin traducir, estilo) y **corrige solo** lo mecánico (ver [Qué revisa la herramienta](#qué-revisa-la-herramienta-validaciones)).
4. Arma un `data3.dat` que el juego carga encima del original, más un `malie_es.exe` opcional con los menús de la ventana en español.

Para volver al japonés basta con quitar o renombrar `data3.dat`.

## Descarga fácil (Windows, sin instalar nada)
1. Entra a **[Releases](../../releases)** (a la derecha de esta página) y descarga **`PL_Traduccion_Windows.zip`** de la versión más reciente.
2. Descomprímelo (clic derecho → **Extraer todo**).
3. Abre **`PL_Traduccion.exe`**.
   Si Windows muestra «Windows protegió tu PC», pulsa **Más información → Ejecutar de todas formas**
   (pasa con cualquier programa nuevo sin firma digital).
4. Pulsa **Examinar…** y elige la carpeta del juego (la que tiene `malie.exe` y `data1.dat`).
5. Pulsa **Generar e instalar la traducción**. Espera a que diga **LISTO** (1 o 2 minutos).
6. (Opcional) **Crear malie_es.exe** para los menús de la ventana en español, y abre el juego con él.

Requisito: Paradise Lost de light, **edición 2017** (malie.exe 1.1.0.0), **sin parches oficiales**.
¿Tienes otra versión? Ver [¿Tienes otra edición del juego?](#tienes-otra-edición-del-juego) — te ayudamos en el Discord.
Para volver al japonés: botón **Quitar la traducción**.

## Con Python (Linux, Steam Deck o si prefieres no usar el .exe)
- [Python 3](https://www.python.org/) (en Windows marca *Add Python to PATH*). Opcional: `pip install numpy pefile`.
- Descarga este repositorio (**Code → Download ZIP**), descomprímelo y abre **`ABRIR_HERRAMIENTA.bat`**
  (Linux/Deck: `./abrir_herramienta.sh`). Es la misma herramienta.
- Sin ventanas: `1_EXTRAER.bat`, `2_REVISAR_Y_CORREGIR.bat`, `3_GENERAR_DAT.bat`, `4_MENUS_EXE_ES.bat` (ver `LEEME.txt`).

## ¿Tienes otra edición del juego?
Esta traducción y sus herramientas se hicieron para la **edición 2017** (malie.exe 1.1.0.0). La herramienta
comprueba tu juego y, si es otra edición (otra versión, parches oficiales, versión descargable, reedición…),
se detiene y te avisa en lugar de arriesgarse a dañar nada.

**Si tienes otra versión, te podemos ayudar a adaptar las herramientas.** Escríbenos en el
**Discord: https://discord.gg/NV8TbQQ7B** y comparte:
- de dónde es tu copia (disco, descarga, tienda) y el año o versión que dice la caja o la tienda;
- la versión de `malie.exe` (clic derecho → Propiedades → Detalles);
- una captura del mensaje que mostró la herramienta (trae un código «md5» que nos sirve para identificarla).

No compartas archivos del juego ni tu código de producto: con esos datos basta.

## Qué revisa la herramienta (validaciones)
Cada vez que usas **Revisar y corregir**, **Usar mi propio CSV** o **Generar**, cada mensaje pasa por estas revisiones.
Mientras editas en la pestaña **Editar mensajes**, también se revisa en vivo.

### Marcas (tags): son ERROR si fallan
| Revisión | Qué debe cumplir | ¿Se corrige solo? |
|---|---|---|
| `{v:…}` y `{/v}` (voz) | iguales que en el japonés: `{v:…}` al inicio y `{/v}` antes del `{end}` | Sí: las pone, quita o reubica |
| `{end}` (fin de mensaje) | la misma cantidad que en el japonés (casi siempre uno, al final) | Sí, cuando el japonés lleva uno al final |
| `{END}`, `{ n }`… | escritas exactamente así: `{n}`, `{end}`, `{/v}` | Sí |
| Marcas desconocidas o llaves sueltas `{` `}` | no puede haber otras marcas ni llaves sin cerrar | No: hay que arreglarlo a mano |
| `{r:base\|lectura}` (furigana) | no se usa en español | Sí: deja solo la base |

### Tamaño del texto: es ERROR si no cabe
| Revisión | Límite (medido en el juego) | ¿Se corrige solo? |
|---|---|---|
| Ancho | 68 caracteres latinos por renglón. La herramienta pone sola los saltos entre palabras; si el mensaje empieza con 「, los renglones siguientes tienen 2 espacios menos | — (es automático) |
| Renglones | máximo **5** renglones por mensaje | Solo si basta con quitar los `{n}` manuales; si no, hay que acortar el texto |
| Largo total | máximo 900 caracteres contando las marcas | No: hay que acortar |
| Nombres y opciones | se recomiendan 40 caracteres como máximo (es AVISO) | No |

### Texto: es ERROR si falla
| Revisión | ¿Se corrige solo? |
|---|---|
| Caracteres japoneses sin traducir (kana, kanji) | No |
| Puntuación japonesa (、。！？～・) y letras de ancho completo | Sí: las cambia por las latinas |
| Saltos de línea o tabuladores reales dentro del texto | Sí: los cambia por `{n}` o un espacio |

### Estilo: son AVISOS (no impiden generar el `.dat`)
- «...» en lugar de «…» (se corrige solo); «……» demasiado largos.
- ¿? y ¡! sin pareja; comillas 「」『』 distintas al japonés.
- Espacios dobles, antes de signos o junto a `{n}` (se corrigen solos).
- Honoríficos japoneses (-sama, -san…), formas de España (vosotros…).
- Nombres mal escritos (Sophie → Sofi, Altmarine → Altomarine…; se corrigen solos).
  La lista se puede editar en `traduccion/reglas_estilo.tsv`; si una regla tiene algo en la columna `reemplazo`, se corrige sola.

### Qué pasa con los errores
- Lo que se puede corregir sin cambiar el sentido se corrige y queda anotado.
- Lo que no se puede corregir queda marcado con `status = error` y **se ve en japonés** en el juego hasta que lo arregles.
- Al terminar, la herramienta dice **LISTO** y escribe `trabajo/reporte_revision.txt` (y `.csv`) con:
  cuántos mensajes revisó, qué errores había, cuáles corrigió y cómo, cuáles no pudo corregir y los avisos de estilo.
  Los mensajes sin traducir quedan en `trabajo/pendientes.csv`.

## Tu propia traducción
- Edita en la pestaña **Editar mensajes** de la herramienta, o
- usa **Usar mi propio CSV…** con cualquier archivo que tenga las columnas `id` y `spanish`
  (coma, punto y coma o tabulador; UTF-8 o ANSI). Se revisa, se corrige y queda como `trabajo/CSV_MAESTRO.csv`.
- Reglas de formato y estilo: [`docs/REGLAS_PARA_TRADUCTORES.md`](docs/REGLAS_PARA_TRADUCTORES.md).

## Steam Deck
Genera el `data3.dat` en una PC (o con Python en el Deck) y sigue [`docs/INSTALAR_EN_STEAMDECK.txt`](docs/INSTALAR_EN_STEAMDECK.txt)
para agregarlo a Steam, usar Proton y configurar los controles.

## Contribuir a la traducción
La traducción vive en `traduccion/traduccion_es.tsv` (solo `id` + `spanish`, sin japonés).
Para proponer cambios: edítala, pásala por **Revisar y corregir** (0 errores) y abre un *pull request*,
o comenta en el Discord.

## Licencia
- Herramientas (código): [MIT](LICENSE).
- Traducción e imágenes de interfaz: [CC BY-NC-SA 4.0](LICENCIA_TRADUCCION.txt) — compártela y mejórala citando el proyecto, sin fines comerciales.
- Paradise Lost y su contenido original pertenecen a light. Proyecto de fans, sin fines de lucro.

## Importante
- **No subas** la carpeta `trabajo/`, ningún `.dat` ni `.exe`: llevan el guion o archivos del juego
  (el `.gitignore` ya lo evita).
- Algunos mensajes no están traducidos a propósito y se ven en japonés.

## Estructura
```
.github/workflows/   arma PL_Traduccion.exe en GitHub al publicar una versión
ABRIR_HERRAMIENTA.bat / abrir_herramienta.sh   herramienta con ventanas (con Python)
1_EXTRAER … 4_MENUS_EXE_ES.bat                 lo mismo sin ventanas
herramientas/   pl_gui.py (ventanas), pl_kit.py (todo el proceso) y módulos del motor MALIE
traduccion/     traduccion_es.tsv, cadenas_es.tsv (nombres y opciones), reglas_estilo.tsv
interfaz/       imágenes y ventanas de la interfaz en español (solo las modificadas)
docs/           reglas para traductores, guía de Steam Deck
trabajo/        se llena al usarlo (CSV maestro, reportes, respaldos) — no se sube
```
