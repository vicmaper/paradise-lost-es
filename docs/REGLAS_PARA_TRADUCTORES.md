# Reglas para traducir Paradise Lost

Se traduce **solo la columna `spanish`**, a partir de la columna `japanese`. Las columnas `id`, `voice` y `japanese` no se tocan.
Español latinoamericano neutro. Traducción fiel, sin añadir ni quitar (escenas para adultos incluidas).

## Marcas (copiar exacto)
| Marca | Qué es | Qué hacer |
|---|---|---|
| `{v:v_as1070}` … `{/v}` | voz del personaje | igual que en el japonés: `{v:…}` al inicio, `{/v}` antes del `{end}` |
| `{end}` | fin del mensaje | misma cantidad que en el japonés (casi siempre uno, al final) |
| `{n}` | salto de renglón | solo para separar ideas; sin espacios alrededor |
| `{r:base\|lectura}` | furigana | no se usa: se traduce el sentido como texto normal |

## Largo
- 68 caracteres por renglón, **5 renglones** como máximo (el kit acomoda los saltos solo).
- Tras 「 『 o （ el juego sangra los renglones siguientes 2 espacios.
- Máximo 900 caracteres por mensaje contando las marcas.

## Signos
- Diálogos entre 「 」 como en el japonés; 『 』 se conserva cuando el japonés lo usa.
- «…» (un carácter), nunca «...». ―― (raya doble) como en el original.
- ¿? y ¡! siempre en pareja.
- Ningún carácter japonés (kana, kanji, 、。・～ っ, letras de ancho completo).
- Sin tabuladores ni saltos de línea reales dentro del texto.

## Estilo y nombres
- «ustedes», nunca «vosotros»; sin modismos de España.
- Sin honoríficos japoneses (-sama, -san…): «señor», «señora» o nada.
- Nombres según VNDB: Ryle, Lil (Lilliel), Ast (Astaroth), Know Christ, Sofia / Sofi, Lilith Altomarine,
  Neros Satanail, Ennis Cardinal, Carmine Onyx, Judas Strife, Vera Cross.
  Ángeles en forma inglesa: Michael, Raphael, Uriel, Gabriel.
- Ast habla de usted a todos.

## Ejemplo
- japanese: `{v:v_as1071}「(texto en japonés)」{/v}{end}`
- spanish: `{v:v_as1071}「…Absurdo.」{/v}{end}`

La herramienta (`ABRIR_HERRAMIENTA.bat` → "Revisar y corregir") comprueba todo esto y corrige sola lo mecánico.
