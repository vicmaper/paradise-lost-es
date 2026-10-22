#!/bin/sh
# Linux / Steam Deck (Modo Escritorio): abre la herramienta con ventanas.
cd "$(dirname "$0")"
python3 herramientas/pl_gui.py || echo "Si falta tkinter, usa los comandos de LEEME.txt (python3 herramientas/pl_kit.py ...)"
