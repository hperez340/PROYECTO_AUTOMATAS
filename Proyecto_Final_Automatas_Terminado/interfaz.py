import csv
from datetime import datetime
import math
import random
import re
import tkinter as tk
from collections import deque
from tkinter import filedialog, messagebox, ttk

from configuracion import *
from utilidades import *
from automata import Automata
from expresiones import *
from datos_logs import PRESETS_LOGS, LOGS_EJEMPLO
from recursos import LOGO_CABECERA_B64, LOGO_PORTADA_B64, LOGO_ICONO_B64
from registro_eventos import RegistroEventos

class Tarjeta(tk.Frame):
    """Tarjeta del menú: icono, título, descripción y botón «Abrir»."""

    ANCHO, ALTO = 320, 290

    def __init__(self, padre, clave, titulo, descripcion, comando):
        super().__init__(
            padre, width=self.ANCHO, height=self.ALTO,
            background=C_TARJETA_FONDO, highlightthickness=1,
            highlightbackground=C_BORDE, highlightcolor=C_BORDE,
            cursor="hand2"
        )
        self.pack_propagate(False)

        self.icono = tk.Canvas(
            self, width=110, height=70, background=C_TARJETA_FONDO,
            highlightthickness=0, bd=0
        )
        self.icono.pack(pady=(32, 14))
        self._dibujar_icono(clave)

        self.lbl_titulo = tk.Label(
            self, text=titulo, background=C_TARJETA_FONDO,
            foreground=C_TEXTO, font=(FUENTE_TITULO, 16, "bold")
        )
        self.lbl_titulo.pack()

        self.lbl_desc = tk.Label(
            self, text=descripcion, background=C_TARJETA_FONDO,
            foreground=C_SUAVE, font=(FUENTE_UI, 10), justify="center",
            wraplength=self.ANCHO - 70
        )
        self.lbl_desc.pack(pady=(8, 0))

        self.boton = ttk.Button(
            self, text="Abrir  ›", style="Abrir.TButton",
            command=comando, cursor="hand2"
        )
        self.boton.pack(side="bottom", pady=(0, 26))

        for widget in (self, self.icono, self.lbl_titulo, self.lbl_desc):
            widget.bind("<Button-1>", lambda _e: comando())

        for widget in (
            self, self.icono, self.lbl_titulo, self.lbl_desc, self.boton
        ):
            widget.bind("<Enter>", self._entrar)
            widget.bind("<Leave>", self._salir)

    def _dibujar_icono(self, clave):
        c, color = self.icono, C_ICONO

        if clave == "afd":      # dos estados, el segundo de aceptación
            c.create_oval(8, 21, 36, 49, outline=color, width=3)
            c.create_line(
                40, 35, 62, 35, fill=color, width=3, arrow=tk.LAST,
                arrowshape=(10, 12, 4)
            )
            c.create_oval(66, 17, 102, 53, outline=color, width=3)
            c.create_oval(72, 23, 96, 47, outline=color, width=3)
        elif clave == "regex":  # sigma: alfabeto
            c.create_line(
                76, 12, 34, 12, 58, 35, 34, 58, 76, 58,
                fill=color, width=5, joinstyle="miter", capstyle="projecting"
            )
        else:                   # documento de registros
            c.create_rectangle(32, 4, 78, 66, outline=color, width=3)

            for y in (20, 31, 42, 53):
                c.create_line(41, y, 69, y, fill=color, width=3)

    def _colorear(self, fondo, borde):
        self.configure(
            background=fondo, highlightbackground=borde,
            highlightcolor=borde
        )

        for widget in (self.icono, self.lbl_titulo, self.lbl_desc):
            widget.configure(background=fondo)

    def _entrar(self, _evento=None):
        self._colorear(C_TARJETA_HOVER, C_ACENTO)

    def _salir(self, _evento=None):
        x, y = self.winfo_pointerxy()
        izq, arriba = self.winfo_rootx(), self.winfo_rooty()

        if (
            izq <= x < izq + self.winfo_width()
            and arriba <= y < arriba + self.winfo_height()
        ):
            return

        self._colorear(C_TARJETA_FONDO, C_BORDE)


class Aplicacion(tk.Tk):
    RADIO_ESTADO = 26

    def __init__(self):
        super().__init__()

        self.title("Proyecto final autómatas · Universidad Mariano Gálvez")
        self.geometry("1320x820")
        self.minsize(1200, 700)
        self.cargar_logos()
        self.aplicar_tema()

        self.automata = None
        self.origen_automata = None  # ("regex", texto, tipo) o ("manual",)
        self.resultados_logs = []
        self.vista_actual = None    # "afd", "regex", "logs" o None (menú)
        self.guardados = {"afd": None, "regex": None}
        self.ultimo_automata = None
        self.registro = RegistroEventos()
        self.registro.registrar("__main__", "Inicio del Simulador de Autómatas")
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.after(1000, self.validar_logs_automaticamente)

        self.principal = ttk.Frame(self)
        self.crear_interfaz()
        self.crear_portada()
        self.mostrar_portada()

    # -- logos ---------------------------------------------------------
    def cargar_logos(self):
        """Carga el escudo incrustado al final del archivo. Si algo falla
        la aplicación sigue funcionando, solo sin logo."""
        self.img_cabecera = self.img_portada = self.img_icono = None

        try:
            self.img_cabecera = tk.PhotoImage(data=LOGO_CABECERA_B64)
            self.img_portada = tk.PhotoImage(data=LOGO_PORTADA_B64)
            self.img_icono = tk.PhotoImage(data=LOGO_ICONO_B64)
            self.iconphoto(True, self.img_icono)
        except tk.TclError:
            pass

    # -- tema ----------------------------------------------------------
    def aplicar_tema(self):
        self.configure(background=C_FONDO)
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure(
            ".",
            background=C_FONDO, foreground=C_TEXTO,
            fieldbackground=C_OSCURO, font=(FUENTE_UI, 10),
            bordercolor=C_BORDE, lightcolor=C_FONDO, darkcolor=C_FONDO,
            troughcolor=C_OSCURO, focuscolor=C_ACENTO, insertcolor=C_TEXTO
        )
        estilo.configure("TFrame", background=C_FONDO)
        estilo.configure("TLabel", background=C_FONDO, foreground=C_TEXTO)
        estilo.configure("Suave.TLabel", foreground=C_SUAVE)
        estilo.configure("TSeparator", background=C_BORDE)
        estilo.configure(
            "TLabelframe", background=C_FONDO, bordercolor=C_BORDE,
            relief="solid"
        )
        estilo.configure(
            "TLabelframe.Label", background=C_FONDO, foreground=C_SUAVE,
            font=(FUENTE_UI, 10, "bold")
        )

        estilo.configure(
            "TButton",
            background=C_BOTON, foreground=C_TEXTO, bordercolor=C_ACENTO,
            lightcolor=C_BOTON, darkcolor=C_BOTON, focuscolor=C_BOTON,
            padding=(10, 7), relief="flat", font=(FUENTE_UI, 10, "bold")
        )
        estilo.map(
            "TButton",
            background=[("pressed", "#16507F"), ("active", C_BOTON_HOVER)],
            lightcolor=[("pressed", "#16507F"), ("active", C_BOTON_HOVER)],
            darkcolor=[("pressed", "#16507F"), ("active", C_BOTON_HOVER)],
            bordercolor=[("active", C_TEXTO)]
        )

        estilo.configure(
            "Inicio.TButton",
            font=(FUENTE_TITULO, 20, "bold"), padding=(64, 16),
            borderwidth=2, bordercolor=C_TEXTO
        )
        estilo.configure(
            "Abrir.TButton",
            font=(FUENTE_UI, 10, "bold"), padding=(28, 7),
            bordercolor=C_BOTON
        )

        # Cuadernos sin pestañas visibles: el menú decide qué página se ve
        estilo.layout("Oculto.TNotebook.Tab", [])
        estilo.configure(
            "Oculto.TNotebook", background=C_FONDO, borderwidth=0,
            tabmargins=0
        )

        estilo.configure(
            "TEntry",
            fieldbackground=C_OSCURO, foreground=C_TEXTO,
            insertcolor=C_TEXTO, bordercolor=C_BORDE,
            lightcolor=C_BORDE, darkcolor=C_BORDE, padding=5
        )
        estilo.map(
            "TEntry",
            bordercolor=[("focus", C_ACENTO)],
            lightcolor=[("focus", C_ACENTO)],
            darkcolor=[("focus", C_ACENTO)]
        )

        estilo.configure(
            "TCombobox",
            fieldbackground=C_OSCURO, background=C_BOTON,
            foreground=C_TEXTO, arrowcolor=C_TEXTO, bordercolor=C_BORDE,
            lightcolor=C_BORDE, darkcolor=C_BORDE, padding=4
        )
        estilo.map(
            "TCombobox",
            fieldbackground=[("readonly", C_OSCURO)],
            foreground=[("readonly", C_TEXTO)],
            selectbackground=[("readonly", C_OSCURO)],
            selectforeground=[("readonly", C_TEXTO)],
            background=[("active", C_BOTON_HOVER)],
            bordercolor=[("focus", C_ACENTO)]
        )
        self.option_add("*TCombobox*Listbox.background", C_OSCURO)
        self.option_add("*TCombobox*Listbox.foreground", C_TEXTO)
        self.option_add("*TCombobox*Listbox.selectBackground", C_BOTON_HOVER)
        self.option_add("*TCombobox*Listbox.selectForeground", C_TEXTO)
        self.option_add("*TCombobox*Listbox.font", (FUENTE_UI, 10))

        estilo.configure(
            "TNotebook", background=C_FONDO, bordercolor=C_BORDE,
            tabmargins=(2, 6, 2, 0)
        )
        estilo.configure(
            "TNotebook.Tab",
            background=C_TARJETA, foreground=C_SUAVE, padding=(16, 7),
            bordercolor=C_BORDE, lightcolor=C_TARJETA, darkcolor=C_TARJETA,
            font=(FUENTE_UI, 10, "bold")
        )
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", C_BOTON), ("active", C_BOTON_HOVER)],
            foreground=[("selected", C_TEXTO), ("active", C_TEXTO)],
            lightcolor=[("selected", C_ACENTO)],
            bordercolor=[("selected", C_ACENTO)]
        )

        for nombre in ("TRadiobutton", "TCheckbutton"):
            estilo.configure(
                nombre, background=C_FONDO, foreground=C_TEXTO,
                indicatorbackground=C_OSCURO, indicatorforeground=C_TEXTO,
                indicatorcolor=C_OSCURO, upperbordercolor=C_ACENTO,
                lowerbordercolor=C_ACENTO, indicatormargin=(0, 0, 6, 0)
            )
            estilo.map(
                nombre,
                background=[("active", C_FONDO)],
                foreground=[("active", C_TEXTO)],
                indicatorcolor=[("selected", C_BOTON_HOVER)],
                indicatorbackground=[("selected", C_BOTON_HOVER)]
            )

        estilo.configure(
            "Treeview",
            background=C_OSCURO, fieldbackground=C_OSCURO,
            foreground=C_TEXTO, bordercolor=C_BORDE, rowheight=26,
            font=(FUENTE_MONO, 10)
        )
        estilo.configure(
            "Treeview.Heading",
            background=C_TARJETA, foreground=C_TEXTO, relief="flat",
            font=(FUENTE_UI, 10, "bold"), padding=6
        )
        estilo.map(
            "Treeview",
            background=[("selected", C_BOTON_HOVER)],
            foreground=[("selected", C_TEXTO)]
        )
        estilo.map("Treeview.Heading", background=[("active", C_BOTON)])

        for nombre in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            estilo.configure(
                nombre, background=C_BORDE, troughcolor=C_OSCURO,
                bordercolor=C_OSCURO, arrowcolor=C_TEXTO,
                lightcolor=C_BORDE, darkcolor=C_BORDE, relief="flat"
            )
            estilo.map(nombre, background=[("active", C_ACENTO)])

        # Cuadros de texto clásicos de tkinter
        for opcion, valor in (
            ("background", C_OSCURO), ("foreground", C_TEXTO),
            ("insertBackground", C_TEXTO), ("selectBackground", C_BOTON_HOVER),
            ("selectForeground", C_TEXTO), ("relief", "flat"),
            ("borderWidth", 0), ("highlightThickness", 1),
            ("highlightBackground", C_BORDE), ("highlightColor", C_ACENTO),
            ("padX", 8), ("padY", 6), ("font", (FUENTE_MONO, 10)),
        ):
            self.option_add(f"*Text.{opcion}", valor)

    # -- pantalla principal ------------------------------------------------
    def crear_portada(self):
        self.portada = tk.Canvas(
            self, background=C_FONDO, highlightthickness=0, bd=0
        )
        self.portada.bind("<Configure>", self.dibujar_portada)

        self.boton_iniciar = ttk.Button(
            self.portada, text="INICIAR", style="Inicio.TButton",
            command=self.iniciar, cursor="hand2"
        )
        self.bind("<Return>", self._tecla_iniciar)

    def _tecla_iniciar(self, _evento=None):
        if self.portada.winfo_ismapped():
            self.iniciar()

    def mostrar_portada(self):
        self.principal.pack_forget()
        self.portada.pack(fill="both", expand=True)
        self.boton_iniciar.focus_set()

    def iniciar(self):
        self.portada.pack_forget()
        self.principal.pack(fill="both", expand=True)
        self.mostrar_menu()

    def _tecla_escape(self, _evento=None):
        if self.principal.winfo_ismapped() and self.vista_actual:
            self.mostrar_menu()

    def mostrar_menu(self):
        self.vista_actual = None
        self.vista.pack_forget()
        self.lbl_titulo.config(text="Simulador de Autómatas")
        self.lbl_subtitulo.config(text=SUBTITULO)
        self.btn_regreso.config(
            text="←  Pantalla principal", command=self.mostrar_portada
        )
        self.menu.pack(fill="both", expand=True)

    def abrir_funcion(self, clave):
        datos = FUNCIONES[clave]
        self.vista_actual = clave
        self.registro.registrar("interfaz.principal", f"Se abrió el módulo de {datos['titulo']}")

        self.menu.pack_forget()
        self.lbl_titulo.config(text=datos["titulo"])
        self.lbl_subtitulo.config(text=datos["subtitulo"])
        self.btn_regreso.config(text="←  Regresar", command=self.mostrar_menu)

        self.nb_izq.select(datos["izq"])
        self.nb_der.select(datos["der"])
        self.vista.pack(fill="both", expand=True, padx=15, pady=12)
        self.update_idletasks()

        if clave in self.guardados:
            self.restaurar_vista(clave)

    def restaurar_vista(self, clave):
        """Muestra el autómata que esta función dejó creado (si hay uno)."""
        for etiqueta in (self.resultado_label, self.regex_resultado):
            etiqueta.config(text="Resultado: pendiente", foreground=C_TEXTO)

        guardado = self.guardados[clave]

        if guardado:
            self.automata, mensaje, self.origen_automata = guardado
            self.dibujar_automata()
            self.escribir_detalle(self.describir_automata(self.automata))
            self.info_label.config(text=mensaje)
            return

        self.automata = None
        self.origen_automata = None
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, 1, 1))
        self.canvas.create_text(
            28, 28, anchor="nw", text="Aquí se dibujará el autómata.",
            fill=C_SUAVE, font=(FUENTE_TITULO, 14)
        )
        self.escribir_detalle("")
        self.info_label.config(text=FUNCIONES[clave]["ayuda"])

    def crear_menu(self):
        self.menu = ttk.Frame(self.cuerpo)
        centro = ttk.Frame(self.menu)
        centro.pack(expand=True)

        ttk.Label(
            centro, text="Bienvenido", font=(FUENTE_TITULO, 30, "bold")
        ).pack()
        ttk.Label(
            centro, text="Selecciona una opción para comenzar",
            style="Suave.TLabel", font=(FUENTE_UI, 12)
        ).pack(pady=(4, 34))

        fila = ttk.Frame(centro)
        fila.pack()

        for columna, clave in enumerate(("afd", "regex", "logs")):
            datos = FUNCIONES[clave]
            Tarjeta(
                fila, clave, datos["titulo"], datos["descripcion"],
                lambda k=clave: self.abrir_funcion(k)
            ).grid(row=0, column=columna, padx=14)

        self.bind("<Escape>", self._tecla_escape)

    def dibujar_portada(self, _evento=None):
        c = self.portada
        ancho, alto = c.winfo_width(), c.winfo_height()

        if ancho < 100 or alto < 100:
            return

        c.delete("all")

        # Fondo: degradado azul con trazos suaves, como la portada de
        # referencia
        arriba, abajo = "#0F3E69", "#061A30"
        pasos = 90

        for i in range(pasos):
            c.create_rectangle(
                0, i * alto / pasos, ancho, (i + 1) * alto / pasos + 1,
                fill=mezclar(arriba, abajo, i / (pasos - 1)), outline=""
            )

        azar = random.Random(7)

        for _ in range(110):
            x = azar.uniform(-80, ancho)
            y = azar.uniform(-20, alto + 20)
            largo = azar.uniform(120, 340)
            base = mezclar(arriba, abajo, min(max(y / alto, 0), 1))
            extremo = "#4A9BD6" if azar.random() < 0.55 else "#03101F"
            c.create_line(
                x, y, x + largo, y - largo * azar.uniform(-0.45, 0.55),
                fill=mezclar(base, extremo, azar.uniform(0.015, 0.045)),
                width=azar.uniform(22, 64), capstyle="round"
            )

        # Esquina superior izquierda: escudo y nombre de la universidad
        if self.img_portada:
            c.create_image(46, 36, image=self.img_portada, anchor="nw")
            x_texto = 46 + self.img_portada.width() + 26
            y_medio = 36 + self.img_portada.height() / 2
        else:
            x_texto, y_medio = 46, 90

        c.create_text(
            x_texto, y_medio - 22, text=UNIVERSIDAD_1, anchor="w",
            fill=C_SUAVE, font=(FUENTE_TITULO, -20)
        )
        c.create_text(
            x_texto, y_medio + 16, text=UNIVERSIDAD_2, anchor="w",
            fill=C_TEXTO, font=(FUENTE_TITULO, -40, "bold")
        )

        # Título grande
        tam = int(max(32, min(64, ancho / 20)))
        y_titulo = alto * 0.30

        c.create_text(
            ancho / 2, y_titulo, text=TITULO_PROYECTO, fill=C_TEXTO,
            font=(FUENTE_TITULO, -tam, "bold"), width=ancho - 160
        )
        c.create_rectangle(
            ancho / 2 - 80, y_titulo + tam * 0.8,
            ancho / 2 + 80, y_titulo + tam * 0.8 + 3,
            fill=C_ACENTO, outline=""
        )
        c.create_text(
            ancho / 2, y_titulo + tam * 0.8 + 38, text=SUBTITULO,
            fill=C_SUAVE, font=(FUENTE_TITULO, -20)
        )

        # Botón en el centro de la pantalla
        c.create_window(ancho / 2, alto / 2 + 40, window=self.boton_iniciar)

        # Pie opcional (se completa con CURSO e INTEGRANTES)
        pie = [t for t in (CURSO, INTEGRANTES) if t]

        if pie:
            c.create_text(
                ancho / 2, alto - 40, text="\n".join(pie), fill=C_SUAVE,
                font=(FUENTE_TITULO, -18), justify="center"
            )

    # -- estructura general --------------------------------------------
    def crear_interfaz(self):
        encabezado = ttk.Frame(self.principal)
        encabezado.pack(fill="x", padx=18, pady=(12, 0))
        encabezado.columnconfigure(0, weight=1, uniform="lados")
        encabezado.columnconfigure(1, weight=0)
        encabezado.columnconfigure(2, weight=1, uniform="lados")

        # Izquierda: escudo y nombre de la universidad
        marca = ttk.Frame(encabezado)
        marca.grid(row=0, column=0, sticky="w")

        if self.img_cabecera:
            ttk.Label(marca, image=self.img_cabecera).pack(
                side="left", padx=(0, 14)
            )

        nombre = ttk.Frame(marca)
        nombre.pack(side="left")
        ttk.Label(
            nombre, text=UNIVERSIDAD_1, style="Suave.TLabel",
            font=(FUENTE_TITULO, 11)
        ).pack(anchor="w")
        ttk.Label(
            nombre, text=UNIVERSIDAD_2, font=(FUENTE_TITULO, 18, "bold")
        ).pack(anchor="w")

        # Centro: título de la aplicación
        centro = ttk.Frame(encabezado)
        centro.grid(row=0, column=1)

        self.lbl_titulo = ttk.Label(
            centro, text="Simulador de Autómatas",
            font=(FUENTE_TITULO, 28)
        )
        self.lbl_titulo.pack()
        self.lbl_subtitulo = ttk.Label(
            centro, text=SUBTITULO, style="Suave.TLabel",
            font=(FUENTE_TITULO, 11)
        )
        self.lbl_subtitulo.pack(pady=(2, 0))
        tk.Frame(centro, height=2, width=140, background=C_ACENTO).pack(
            pady=(10, 0)
        )

        # Derecha: «Regresar» (o «Pantalla principal» en el menú)
        self.btn_regreso = ttk.Button(
            encabezado, text="←  Pantalla principal",
            command=self.mostrar_portada, cursor="hand2"
        )
        self.btn_regreso.grid(row=0, column=2, sticky="e")

        self.cuerpo = ttk.Frame(self.principal)
        self.cuerpo.pack(fill="both", expand=True)

        contenedor = ttk.Frame(self.cuerpo)
        self.vista = contenedor     # se muestra al abrir una función

        self.nb_izq = ttk.Notebook(contenedor, style="Oculto.TNotebook")
        self.nb_izq.pack(side="left", fill="y", padx=(0, 10))

        tab_manual = ttk.Frame(self.nb_izq)
        tab_regex = ttk.Frame(self.nb_izq)
        tab_logs = ttk.Frame(self.nb_izq)

        self.nb_izq.add(tab_manual, text="1. Autómata")
        self.nb_izq.add(tab_regex, text="2. Regex")
        self.nb_izq.add(tab_logs, text="3. Logs")

        panel_der = ttk.Frame(contenedor)
        panel_der.pack(side="right", fill="both", expand=True)

        self.nb_der = ttk.Notebook(panel_der, style="Oculto.TNotebook")
        self.nb_der.pack(fill="both", expand=True)

        self.tab_grafico = ttk.Frame(self.nb_der)
        self.tab_resultados = ttk.Frame(self.nb_der)

        self.nb_der.add(self.tab_grafico, text="Gráfico y detalle")
        self.nb_der.add(self.tab_resultados, text="Logs")

        self.crear_formulario(tab_manual)
        self.crear_panel_regex(tab_regex)
        self.crear_panel_logs(tab_logs)
        self.crear_area_visual(self.tab_grafico)
        self.crear_area_logs(self.tab_resultados)
        self.crear_menu()

    # -- pestaña 1: Entrega 1 --------------------------------------------
    def crear_formulario(self, panel):
        ttk.Label(panel, text="Tipo de autómata:").pack(
            anchor="w", padx=10, pady=(10, 2)
        )

        self.tipo_var = tk.StringVar(value="AFN")

        ttk.Combobox(
            panel,
            textvariable=self.tipo_var,
            values=["AFN", "AFD"],
            state="readonly",
            width=28
        ).pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estados separados por coma:").pack(
            anchor="w", padx=10
        )
        self.estados_entry = ttk.Entry(panel, width=34)
        self.estados_entry.insert(0, "q0,q1,q2")
        self.estados_entry.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Alfabeto (un carácter por símbolo):").pack(
            anchor="w", padx=10
        )
        self.alfabeto_entry = ttk.Entry(panel, width=34)
        self.alfabeto_entry.insert(0, "a,b")
        self.alfabeto_entry.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estado inicial:").pack(anchor="w", padx=10)
        self.inicial_entry = ttk.Entry(panel, width=34)
        self.inicial_entry.insert(0, "q0")
        self.inicial_entry.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estados finales separados por coma:").pack(
            anchor="w", padx=10
        )
        self.finales_entry = ttk.Entry(panel, width=34)
        self.finales_entry.insert(0, "q2")
        self.finales_entry.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Transiciones:").pack(anchor="w", padx=10)

        ttk.Label(
            panel,
            text=(
                "Formato: estado,símbolo,destino\n"
                "Ejemplo: q0,a,q1\n"
                "Múltiples destinos: q0,a,q1|q2\n"
                "Epsilon: q0,ε,q1  (o q0,eps,q1)"
            ),
            style="Suave.TLabel"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        self.transiciones_text = tk.Text(panel, width=34, height=6)
        self.transiciones_text.insert(
            "1.0", "q0,a,q1\nq1,b,q2\nq0,ε,q1"
        )
        self.transiciones_text.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            panel, text="Crear autómata", command=self.crear_automata
        ).pack(fill="x", padx=10, pady=2)

        ttk.Button(
            panel,
            text="Convertir AFN activo a AFD",
            command=self.convertir_a_afd
        ).pack(fill="x", padx=10, pady=2)

        ttk.Separator(panel).pack(fill="x", padx=10, pady=8)

        ttk.Label(panel, text="Cadena a simular:").pack(anchor="w", padx=10)
        self.cadena_entry = ttk.Entry(panel, width=34)
        self.cadena_entry.pack(fill="x", padx=10, pady=(0, 6))

        ttk.Button(
            panel, text="Simular cadena", command=self.simular_cadena
        ).pack(fill="x", padx=10, pady=2)

        self.resultado_label = ttk.Label(
            panel,
            text="Resultado: pendiente",
            font=(FUENTE_UI, 12, "bold")
        )
        self.resultado_label.pack(pady=10)

    # -- pestaña 2: regex --------------------------------------------------
    def crear_panel_regex(self, panel):
        ttk.Label(panel, text="Expresión regular:").pack(
            anchor="w", padx=10, pady=(10, 2)
        )

        self.regex_entry = ttk.Entry(
            panel, width=38, font=(FUENTE_MONO, 11)
        )
        self.regex_entry.insert(0, "(a|b)*abb")
        self.regex_entry.pack(fill="x", padx=10, pady=(0, 6))

        ttk.Label(
            panel,
            text=(
                "Operadores:  |  *  +  ?  ( )  .  {n,m}\n"
                "Clases:  [a-z]  [^0-9]    Atajos:  \\d \\w \\s\n"
                "Escape:  \\.  \\|  \\*   Vacío:  ε"
            ),
            style="Suave.TLabel"
        ).pack(anchor="w", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Autómata a generar:").pack(
            anchor="w", padx=10
        )

        self.regex_tipo = tk.StringVar(value="AFN")

        ttk.Radiobutton(
            panel,
            text="AFN (construcción de Thompson)",
            variable=self.regex_tipo,
            value="AFN"
        ).pack(anchor="w", padx=20)

        ttk.Radiobutton(
            panel,
            text="AFD (subconjuntos)",
            variable=self.regex_tipo,
            value="AFD"
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ttk.Button(
            panel,
            text="Generar autómata",
            command=self.generar_desde_regex
        ).pack(fill="x", padx=10, pady=2)

        ttk.Separator(panel).pack(fill="x", padx=10, pady=10)

        ttk.Label(panel, text="Cadena a validar con la regex:").pack(
            anchor="w", padx=10
        )

        self.regex_cadena = ttk.Entry(panel, width=38)
        self.regex_cadena.pack(fill="x", padx=10, pady=(0, 6))

        ttk.Button(
            panel,
            text="Validar cadena",
            command=self.validar_con_regex
        ).pack(fill="x", padx=10, pady=2)

        self.regex_resultado = ttk.Label(
            panel,
            text="Resultado: pendiente",
            font=(FUENTE_UI, 12, "bold")
        )
        self.regex_resultado.pack(pady=10)

        ttk.Label(
            panel,
            text=(
                "El autómata generado queda guardado y puede\n"
                "usarse después en Validación de Logs."
            ),
            style="Suave.TLabel"
        ).pack(anchor="w", padx=10)

    # -- pestaña 3: controles de logs -------------------------------------
    def crear_panel_logs(self, panel):
        ttk.Label(panel, text="Fuente de validación:").pack(
            anchor="w", padx=10, pady=(10, 2)
        )

        self.fuente_logs = tk.StringVar(value="regex")

        ttk.Radiobutton(
            panel,
            text="Regex escrita aquí",
            variable=self.fuente_logs,
            value="regex"
        ).pack(anchor="w", padx=20)

        ttk.Radiobutton(
            panel,
            text="Último autómata creado (AFN/AFD o Regex)",
            variable=self.fuente_logs,
            value="actual"
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ttk.Label(panel, text="Patrones de ejemplo:").pack(
            anchor="w", padx=10
        )

        self.preset_var = tk.StringVar()
        combo = ttk.Combobox(
            panel,
            textvariable=self.preset_var,
            values=list(PRESETS_LOGS),
            state="readonly",
            width=38
        )
        combo.pack(fill="x", padx=10, pady=(0, 6))
        combo.bind("<<ComboboxSelected>>", self.aplicar_preset)

        ttk.Label(panel, text="Regex para los logs:").pack(
            anchor="w", padx=10
        )

        self.regex_logs_entry = ttk.Entry(
            panel, width=38, font=(FUENTE_MONO, 10)
        )
        self.regex_logs_entry.insert(
            0, PRESETS_LOGS["Línea completa: fecha, nivel y mensaje"][0]
        )
        self.regex_logs_entry.pack(fill="x", padx=10, pady=(0, 8))

        ttk.Label(panel, text="Una línea es válida si:").pack(
            anchor="w", padx=10
        )

        self.modo_logs = tk.StringVar(value="completa")

        ttk.Radiobutton(
            panel,
            text="La línea completa coincide",
            variable=self.modo_logs,
            value="completa"
        ).pack(anchor="w", padx=20)

        ttk.Radiobutton(
            panel,
            text="La línea contiene el patrón",
            variable=self.modo_logs,
            value="contiene"
        ).pack(anchor="w", padx=20, pady=(0, 6))

        self.ignorar_vacias = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            panel,
            text="Ignorar líneas vacías",
            variable=self.ignorar_vacias
        ).pack(anchor="w", padx=10, pady=(0, 8))

        ttk.Button(
            panel, text="Cargar archivo de log…", command=self.cargar_log
        ).pack(fill="x", padx=10, pady=2)

        ttk.Button(
            panel,
            text="Insertar logs de ejemplo",
            command=self.insertar_ejemplo
        ).pack(fill="x", padx=10, pady=2)

        ttk.Button(
            panel, text="Validar logs", command=self.validar_logs
        ).pack(fill="x", padx=10, pady=(8, 2))

        ttk.Button(
            panel,
            text="Exportar resultados (CSV)…",
            command=self.exportar_resultados
        ).pack(fill="x", padx=10, pady=2)

        ttk.Button(
            panel,
            text="Abrir visor de eventos",
            command=self.abrir_visor_eventos
        ).pack(fill="x", padx=10, pady=(8, 2))

        acciones_registro = ttk.Frame(panel)
        acciones_registro.pack(fill="x", padx=10, pady=(2, 4))
        ttk.Button(acciones_registro, text="Validar formato", command=self.validar_formato_logs).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ttk.Button(acciones_registro, text="Analizar errores", command=self.analizar_errores_logs).pack(side="left", fill="x", expand=True, padx=(3, 0))

        self.resumen_logs = ttk.Label(
            panel,
            text="Sin validar",
            font=(FUENTE_UI, 11, "bold"),
            wraplength=300
        )
        self.resumen_logs.pack(padx=10, pady=12, anchor="w")

    # -- áreas de la derecha ------------------------------------------------
    def crear_area_visual(self, panel):
        marco = ttk.LabelFrame(panel, text="Representación gráfica")
        marco.pack(fill="both", expand=True, padx=4, pady=4)

        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            marco, background=C_OSCURO, highlightthickness=0, bd=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        barra_v = ttk.Scrollbar(
            marco, orient="vertical", command=self.canvas.yview
        )
        barra_v.grid(row=0, column=1, sticky="ns")

        barra_h = ttk.Scrollbar(
            marco, orient="horizontal", command=self.canvas.xview
        )
        barra_h.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(
            xscrollcommand=barra_h.set, yscrollcommand=barra_v.set
        )

        self.info_label = ttk.Label(
            panel,
            text=""
        )
        self.info_label.pack(pady=4)

        marco_detalle = ttk.LabelFrame(panel, text="Detalle y traza")
        marco_detalle.pack(fill="x", padx=4, pady=(0, 4))

        self.detalle = tk.Text(
            marco_detalle,
            height=11,
            font=(FUENTE_MONO, 10),
            wrap="none",
            state="disabled"
        )
        scroll = ttk.Scrollbar(
            marco_detalle, orient="vertical", command=self.detalle.yview
        )
        self.detalle.configure(yscrollcommand=scroll.set)
        self.detalle.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def crear_area_logs(self, panel):
        entrada = ttk.LabelFrame(panel, text="Logs a validar (pegue o cargue)")
        entrada.pack(fill="x", padx=4, pady=4)

        self.logs_texto = tk.Text(
            entrada, height=9, font=(FUENTE_MONO, 10), wrap="none"
        )
        scroll = ttk.Scrollbar(
            entrada, orient="vertical", command=self.logs_texto.yview
        )
        self.logs_texto.configure(yscrollcommand=scroll.set)
        self.logs_texto.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        resultados = ttk.LabelFrame(panel, text="Resultados")
        resultados.pack(fill="both", expand=True, padx=4, pady=4)

        barra = ttk.Frame(resultados)
        barra.pack(fill="x")

        self.solo_invalidas = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            barra,
            text="Mostrar solo líneas inválidas",
            variable=self.solo_invalidas,
            command=self.refrescar_tabla_logs
        ).pack(side="left", padx=6, pady=4)

        columnas = ("n", "estado", "linea")
        self.tabla_logs = ttk.Treeview(
            resultados, columns=columnas, show="headings"
        )
        self.tabla_logs.heading("n", text="Línea")
        self.tabla_logs.heading("estado", text="Resultado")
        self.tabla_logs.heading("linea", text="Contenido")
        self.tabla_logs.column("n", width=60, anchor="center", stretch=False)
        self.tabla_logs.column(
            "estado", width=90, anchor="center", stretch=False
        )
        self.tabla_logs.column("linea", width=700, anchor="w")

        self.tabla_logs.tag_configure(
            "ok", background=C_OK_FONDO, foreground=C_OK
        )
        self.tabla_logs.tag_configure(
            "mal", background=C_MAL_FONDO, foreground=C_MAL
        )

        scroll_t = ttk.Scrollbar(
            resultados, orient="vertical", command=self.tabla_logs.yview
        )
        self.tabla_logs.configure(yscrollcommand=scroll_t.set)
        self.tabla_logs.pack(side="left", fill="both", expand=True)
        scroll_t.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # Entrega 1: crear / convertir / simular
    # ------------------------------------------------------------------
    def obtener_lista(self, valor):
        return {
            elemento.strip()
            for elemento in valor.split(",")
            if elemento.strip()
        }

    def crear_automata(self):
        self.registro.registrar("interfaz.ventana_afd", "Acción iniciada: crear_automata")
        try:
            tipo = self.tipo_var.get()

            estados = self.obtener_lista(self.estados_entry.get())
            alfabeto = self.obtener_lista(self.alfabeto_entry.get())
            inicial = self.inicial_entry.get().strip()
            finales = self.obtener_lista(self.finales_entry.get())

            if not estados:
                raise ValueError("Debe ingresar al menos un estado.")

            if not alfabeto:
                raise ValueError("Debe ingresar el alfabeto.")

            for simbolo in alfabeto:
                if len(simbolo) != 1:
                    raise ValueError(
                        f"El símbolo «{simbolo}» debe ser de un solo "
                        "carácter."
                    )

                if simbolo == EPSILON:
                    raise ValueError(
                        "ε no puede formar parte del alfabeto."
                    )

            if inicial not in estados:
                raise ValueError(
                    "El estado inicial debe pertenecer a los estados."
                )

            if not finales.issubset(estados):
                raise ValueError(
                    "Los estados finales deben pertenecer a los estados."
                )

            transiciones = {}

            lineas = self.transiciones_text.get(
                "1.0", tk.END
            ).strip().splitlines()

            for numero, linea in enumerate(lineas, start=1):
                if not linea.strip():
                    continue

                partes = [p.strip() for p in linea.split(",")]

                if len(partes) != 3:
                    raise ValueError(
                        f"Transición inválida en la línea {numero}: "
                        "use estado,símbolo,destino."
                    )

                origen, simbolo, destinos_texto = partes

                if origen not in estados:
                    raise ValueError(
                        f"Línea {numero}: el estado {origen} no existe."
                    )

                if simbolo == "eps":
                    simbolo = EPSILON

                if simbolo != EPSILON and simbolo not in alfabeto:
                    raise ValueError(
                        f"Línea {numero}: el símbolo «{simbolo}» no "
                        "pertenece al alfabeto."
                    )

                destinos = {
                    d.strip()
                    for d in destinos_texto.split("|")
                    if d.strip()
                }

                if not destinos:
                    raise ValueError(
                        f"Línea {numero}: falta el estado destino."
                    )

                if not destinos.issubset(estados):
                    raise ValueError(
                        f"Línea {numero}: hay destinos que no existen."
                    )

                clave = (origen, simbolo)

                if tipo == "AFD":
                    if simbolo == EPSILON:
                        raise ValueError(
                            "Un AFD no puede tener transiciones epsilon."
                        )

                    if clave in transiciones:
                        raise ValueError(
                            "Un AFD no puede tener dos transiciones "
                            "para el mismo estado y símbolo "
                            f"(línea {numero})."
                        )

                    if len(destinos) != 1:
                        raise ValueError(
                            "Cada transición de un AFD debe tener "
                            "un único destino."
                        )

                transiciones.setdefault(clave, set()).update(destinos)

            automata = Automata(
                tipo, estados, alfabeto, inicial, finales, transiciones
            )

        except ValueError as error:
            self.registro.registrar("interfaz.ventana_afd", "Error al crear autómata", "ERROR", str(error))
            messagebox.showerror("Error de validación", str(error))
            return

        self.origen_automata = ("manual",)
        self.mostrar_automata(
            automata,
            f"{tipo} creado correctamente. "
            f"Estados: {len(automata.estados)} | "
            f"Transiciones: {len(automata.transiciones)}"
        )

        messagebox.showinfo("Éxito", f"El {tipo} fue creado correctamente.")
        self.registro.registrar("interfaz.ventana_afd", f"Se creó el {tipo}", "INFO", f"Estados={len(automata.estados)}; transiciones={sum(len(v) for v in automata.transiciones.values())}")

    def convertir_a_afd(self):
        self.registro.registrar("interfaz.ventana_afd", "Acción iniciada: convertir AFN a AFD")
        if self.automata is None:
            messagebox.showwarning(
                "Advertencia", "Primero debe crear un autómata."
            )
            return

        if self.automata.tipo != "AFN":
            messagebox.showinfo(
                "Información", "El autómata activo ya es un AFD."
            )
            return

        try:
            afd = afn_a_afd(self.automata)
        except ErrorRegex as error:
            messagebox.showerror("Error", str(error))
            return

        self.origen_automata = ("convertido",)
        self.mostrar_automata(
            afd,
            f"AFN convertido a AFD por subconjuntos. "
            f"Estados: {len(afd.estados)}"
        )
        self.registro.registrar("interfaz.ventana_afd", "AFN convertido a AFD", "INFO", f"Estados={len(afd.estados)}")

    def simular_cadena(self):
        self._simular_y_mostrar(self.cadena_entry.get())

    def _simular_y_mostrar(self, cadena):
        modulo = "interfaz.ventana_regex" if self.vista_actual == "regex" else "interfaz.ventana_afd"
        self.registro.registrar(modulo, "Acción iniciada: validar cadena", "INFO", f"Cadena={cadena!r}")
        if self.automata is None:
            messagebox.showwarning(
                "Advertencia", "Primero debe crear un autómata."
            )
            return

        aceptada, pasos = self.automata.procesar(cadena)
        self.registro.registrar(modulo, "Validación de cadena", "INFO" if aceptada else "WARNING", f"Tipo={self.automata.tipo}; cadena={cadena!r}; resultado={'ACEPTADA' if aceptada else 'RECHAZADA'}")

        texto = "CADENA ACEPTADA" if aceptada else "CADENA RECHAZADA"
        color = C_OK if aceptada else C_MAL

        for etiqueta in (self.resultado_label, self.regex_resultado):
            etiqueta.config(text=f"Resultado: {texto}", foreground=color)

        self.escribir_detalle(self.texto_traza(cadena, aceptada, pasos))
        self.dibujar_automata(resaltar=set(pasos[-1][1]))

    def texto_traza(self, cadena, aceptada, pasos):
        lineas = [
            f"Traza de «{cadena}» (longitud {len(cadena)}) "
            f"en un {self.automata.tipo}",
            ""
        ]

        for indice, (descripcion, conjunto) in enumerate(pasos):
            if not conjunto:
                activos = "∅"
            elif len(conjunto) > 12:
                activos = (
                    "{" + ", ".join(conjunto[:12])
                    + f", … (+{len(conjunto) - 12})" + "}"
                )
            else:
                activos = "{" + ", ".join(conjunto) + "}"

            lineas.append(f"{indice:>3}. {descripcion:<30} → {activos}")

        lineas.append("")

        if aceptada:
            lineas.append(
                "ACEPTADA: el conjunto final contiene un estado de "
                "aceptación."
            )
        else:
            lineas.append(
                "RECHAZADA: no se alcanzó ningún estado de aceptación."
            )

        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Regex
    # ------------------------------------------------------------------
    def generar_desde_regex(self):
        self.registro.registrar("interfaz.ventana_regex", "Acción iniciada: generar autómata desde regex", "INFO", f"Regex={self.regex_entry.get()!r}; tipo={self.regex_tipo.get()}")
        texto = self.regex_entry.get()
        tipo = self.regex_tipo.get()

        try:
            automata = construir_desde_regex(texto, tipo)
        except ErrorRegex as error:
            self.registro.registrar("interfaz.ventana_regex", "Regex inválida", "ERROR", str(error))
            messagebox.showerror("Expresión regular inválida", str(error))
            return False

        self.origen_automata = ("regex", texto, tipo)
        self.mostrar_automata(
            automata,
            f"{tipo} generado desde «{texto}». "
            f"Estados: {len(automata.estados)} | "
            f"Transiciones: {sum(len(v) for v in automata.transiciones.values())}"
        )
        self.registro.registrar("interfaz.ventana_regex", "Autómata generado desde regex", "INFO", f"Regex={texto!r}; tipo={tipo}; estados={len(automata.estados)}")
        return True

    def validar_con_regex(self):
        texto = self.regex_entry.get()
        tipo = self.regex_tipo.get()

        if self.origen_automata != ("regex", texto, tipo):
            if not self.generar_desde_regex():
                return

        self._simular_y_mostrar(self.regex_cadena.get())

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------
    def aplicar_preset(self, _evento=None):
        regex, modo = PRESETS_LOGS[self.preset_var.get()]
        self.regex_logs_entry.delete(0, tk.END)
        self.regex_logs_entry.insert(0, regex)
        self.modo_logs.set(modo)
        self.fuente_logs.set("regex")

    def insertar_ejemplo(self):
        self.logs_texto.delete("1.0", tk.END)
        self.logs_texto.insert("1.0", LOGS_EJEMPLO)
        self.nb_der.select(self.tab_resultados)
        self.registro.registrar("interfaz.ventana_logs", "Se insertaron logs de ejemplo")

    def validar_logs_automaticamente(self):
        """Valida los registros persistidos desde la última revisión."""
        try:
            filas = self.registro.leer(limite=100000)
            ultima_revision = getattr(self, "ultima_revision_logs", "")
            pendientes = [fila for fila in filas if f"{fila[0]} {fila[1]}" > ultima_revision]
            if pendientes:
                self.ultima_revision_logs = f"{pendientes[-1][0]} {pendientes[-1][1]}"
                resumen = {}
                for fila in pendientes:
                    resumen[fila[2]] = resumen.get(fila[2], 0) + 1
                self.registro.registrar(
                    "validador_automatico",
                    "Revisión automática del registro de eventos",
                    "WARNING" if resumen.get("ERROR", 0) else "INFO",
                    f"nuevos={len(pendientes)}; errores={resumen.get('ERROR', 0)}; advertencias={resumen.get('WARNING', 0)}",
                )
                if getattr(self, "visor_eventos", None) is not None:
                    try:
                        if self.visor_eventos.winfo_exists():
                            self.refrescar_visor_eventos()
                    except tk.TclError:
                        self.visor_eventos = None
        except (OSError, ValueError) as error:
            self.registro.registrar("validador_automatico", "No se pudo revisar el registro", "ERROR", str(error))
        try:
            self.after(3000, self.validar_logs_automaticamente)
        except tk.TclError:
            pass

    def cargar_log(self):
        ruta = filedialog.askopenfilename(
            title="Seleccione un archivo de log",
            filetypes=[
                ("Logs y texto", "*.log *.txt *.out"),
                ("Todos los archivos", "*.*"),
            ]
        )

        if not ruta:
            return

        try:
            with open(ruta, encoding="utf-8", errors="replace") as archivo:
                contenido = archivo.read()
        except OSError as error:
            self.registro.registrar("interfaz.ventana_logs", "Error al cargar archivo de logs", "ERROR", str(error))
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{error}")
            return

        self.logs_texto.delete("1.0", tk.END)
        self.logs_texto.insert("1.0", contenido)
        self.nb_der.select(self.tab_resultados)
        self.archivo_log_cargado = ruta
        self.registro.registrar("interfaz.ventana_logs", "Archivo de logs cargado", "INFO", f"Ruta={ruta}; líneas={len(contenido.splitlines())}")

    def obtener_automata_logs(self):
        contiene = self.modo_logs.get() == "contiene"

        if self.fuente_logs.get() == "actual":
            if self.ultimo_automata is None:
                messagebox.showwarning(
                    "Advertencia",
                    "Todavía no ha creado ningún autómata en AFN / AFD "
                    "ni en Expresiones Regulares."
                )
                return None

            if contiene:
                return envolver_contiene(self.ultimo_automata)

            return self.ultimo_automata

        try:
            # El AFD es mucho más rápido para archivos grandes.
            return construir_desde_regex(
                self.regex_logs_entry.get(), "AFD", contiene
            )
        except ErrorRegex as error:
            messagebox.showerror("Expresión regular inválida", str(error))
            return None

    def validar_logs(self):
        self.registro.registrar("interfaz.ventana_logs", "Acción iniciada: validar_logs")
        self.nb_der.select(self.tab_resultados)

        lineas = self.logs_texto.get("1.0", "end-1c").splitlines()

        if not any(l.strip() for l in lineas):
            messagebox.showwarning(
                "Advertencia", "No hay logs para validar."
            )
            return

        automata = self.obtener_automata_logs()

        if automata is None:
            return

        resultados = []
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            for numero, linea in enumerate(lineas, start=1):
                if self.ignorar_vacias.get() and not linea.strip():
                    continue
                aceptada = automata.simular(linea)
                resultados.append((numero, aceptada, linea))
                self.registro.registrar("interfaz.ventana_logs", "Línea validada", "INFO" if aceptada else "WARNING", f"línea={numero}; resultado={'VÁLIDA' if aceptada else 'INVÁLIDA'}; contenido={linea[:500]}")
        except Exception as error:
            self.registro.registrar("interfaz.ventana_logs", "Error durante validación de logs", "ERROR", str(error))
            messagebox.showerror("Error de validación", f"No se pudieron validar los logs:\n{error}")
            return
        finally:
            self.config(cursor="")
        self.resultados_logs = resultados
        self.refrescar_tabla_logs()

        total = len(resultados)
        validas = sum(1 for _, ok, _ in resultados if ok)
        invalidas = total - validas
        porcentaje = (100 * validas / total) if total else 0

        self.resumen_logs.config(
            text=(
                f"Total: {total}\nVálidas: {validas} ({porcentaje:.1f}%)\n"
                f"Inválidas: {invalidas}"
            ),
            foreground=C_OK if invalidas == 0 else C_TEXTO
        )
        self.registro.registrar("interfaz.ventana_logs", "Validación de logs finalizada", "INFO", f"archivo={getattr(self, 'archivo_log_cargado', 'texto pegado/ejemplo')}; total={total}; válidas={validas}; inválidas={invalidas}")

    def refrescar_tabla_logs(self):
        self.tabla_logs.delete(*self.tabla_logs.get_children())

        for numero, ok, linea in self.resultados_logs:
            if self.solo_invalidas.get() and ok:
                continue

            visible = linea if len(linea) <= 300 else linea[:299] + "…"

            self.tabla_logs.insert(
                "",
                "end",
                values=(
                    numero,
                    "VÁLIDA" if ok else "INVÁLIDA",
                    visible
                ),
                tags=("ok" if ok else "mal",)
            )

    def exportar_resultados(self):
        if not self.resultados_logs:
            messagebox.showwarning(
                "Advertencia", "Primero valide algunos logs."
            )
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar resultados",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")]
        )

        if not ruta:
            return

        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                escritor = csv.writer(f)
                escritor.writerow(["linea", "resultado", "contenido"])

                for numero, ok, linea in self.resultados_logs:
                    escritor.writerow(
                        [numero, "VALIDA" if ok else "INVALIDA", linea]
                    )
        except OSError as error:
            self.registro.registrar("interfaz.ventana_logs", "Error al exportar validación", "ERROR", str(error))
            messagebox.showerror("Error", f"No se pudo guardar:\n{error}")
            return

        self.registro.registrar("interfaz.ventana_logs", "Resultados de validación exportados", "INFO", f"ruta={ruta}; filas={len(self.resultados_logs)}")
        messagebox.showinfo("Listo", "Resultados exportados correctamente.")

    def abrir_visor_eventos(self):
        ventana_existente = getattr(self, "visor_eventos", None)
        if ventana_existente is not None:
            try:
                if ventana_existente.winfo_exists():
                    ventana_existente.lift()
                    return
            except tk.TclError:
                pass

        self.registro.registrar("interfaz.principal", "Se solicitó abrir el visor de logs")
        ventana = tk.Toplevel(self)
        self.visor_eventos = ventana
        ventana.title("Visor de logs - Simulador de Autómatas")
        ventana.geometry("1120x680")
        ventana.minsize(800, 480)
        ventana.configure(background=C_FONDO)

        encabezado = ttk.Frame(ventana)
        encabezado.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(encabezado, text="Visor de logs", font=(FUENTE_TITULO, 20, "bold")).pack(side="left")
        ttk.Label(encabezado, text="Registro de eventos de la aplicación", style="Suave.TLabel").pack(side="left", padx=14)

        controles = ttk.Frame(ventana)
        controles.pack(fill="x", padx=16, pady=(4, 10))
        ttk.Label(controles, text="Buscar en todos los logs:").pack(side="left")
        buscar = ttk.Entry(controles)
        buscar.pack(side="left", fill="x", expand=True, padx=(8, 0))

        zona_inferior = ttk.Frame(ventana)
        zona_inferior.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        menu = ttk.Frame(zona_inferior)
        menu.pack(side="left", fill="y", padx=(0, 12))
        ttk.Label(menu, text="Mostrar", font=(FUENTE_UI, 10, "bold")).pack(anchor="w", pady=(0, 4))
        nivel = tk.StringVar(value="Toda la actividad")
        self.visor_nivel = nivel
        columnas = ("fecha", "hora", "nivel", "modulo", "accion", "detalle")
        area_tabla = ttk.Frame(zona_inferior)
        area_tabla.pack(side="left", fill="both", expand=True)
        tabla = ttk.Treeview(area_tabla, columns=columnas, show="headings", height=20)
        titulos = {"fecha": "Fecha", "hora": "Hora", "nivel": "Nivel", "modulo": "Módulo", "accion": "Acción", "detalle": "Detalle"}
        anchos = {"fecha": 100, "hora": 80, "nivel": 85, "modulo": 170, "accion": 220, "detalle": 430}
        for columna in columnas:
            tabla.heading(columna, text=titulos[columna])
            tabla.column(columna, width=anchos[columna], anchor="w")
        tabla.tag_configure("ERROR", foreground=C_MAL)
        tabla.tag_configure("WARNING", foreground="#F2C879")
        tabla.tag_configure("INFO", foreground=C_TEXTO)
        barra_v = ttk.Scrollbar(area_tabla, orient="vertical", command=tabla.yview)
        barra_h = ttk.Scrollbar(area_tabla, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        barra_v.grid(row=0, column=1, sticky="ns")
        area_tabla.rowconfigure(0, weight=1)
        area_tabla.columnconfigure(0, weight=1)
        barra_h.grid(row=1, column=0, sticky="ew")

        pie = ttk.Frame(ventana)
        pie.pack(fill="x", padx=16, pady=8)
        estado = ttk.Label(pie, text="")
        estado.pack(side="left")

        self.visor_buscar = buscar
        self.visor_tabla = tabla
        self.visor_estado = estado
        def actualizar():
            self.actualizar_visor_eventos()

        self.visor_niveles = {
            "Todas las actividades": "TODOS",
            "Procesos y resultados": "INFO",
            "Validaciones rechazadas": "WARNING",
            "Errores del programa": "ERROR",
        }
        menu_nivel = ttk.Combobox(
            menu,
            textvariable=nivel,
            values=list(self.visor_niveles),
            state="readonly",
            width=20,
        )
        menu_nivel.pack(fill="x", pady=(0, 6))
        menu_nivel.bind("<<ComboboxSelected>>", lambda _evento: actualizar())
        ttk.Separator(menu).pack(fill="x", pady=8)
        ttk.Button(menu, text="Actualizar actividad", command=actualizar).pack(fill="x", pady=2)
        ttk.Button(
            menu,
            text="Abrir archivo de registro",
            command=lambda: messagebox.showinfo("Archivo de registro", str(self.registro.archivo), parent=ventana),
        ).pack(fill="x", pady=2)
        buscar.bind("<Return>", lambda _evento: actualizar())
        ventana.protocol("WM_DELETE_WINDOW", lambda: self.cerrar_visor_eventos(ventana))
        self.registro.registrar("interfaz.ventana_logs", "Se abrió el visor de logs", "INFO", f"archivo={self.registro.archivo}")
        self.actualizar_visor_eventos()

    def cerrar_aplicacion(self):
        """Escribe el evento final y cierra la aplicación de forma ordenada."""
        try:
            self.registro.cerrar_sesion()
        finally:
            self.destroy()

    def cerrar_visor_eventos(self, ventana):
        trabajo = getattr(self, "visor_refresh_job", None)
        if trabajo is not None:
            try:
                self.after_cancel(trabajo)
            except tk.TclError:
                pass
            self.visor_refresh_job = None
        ventana.destroy()
        self.visor_eventos = None
        self.visor_tabla = None

    def actualizar_visor_eventos(self):
        self.refrescar_visor_eventos()

    def validar_formato_logs(self):
        lineas = self.logs_texto.get("1.0", "end-1c").splitlines()
        errores = []
        for numero, linea in enumerate(lineas, start=1):
            if not linea.strip() and self.ignorar_vacias.get():
                continue
            try:
                datetime.strptime(linea.strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                errores.append(numero)
        if errores:
            detalle = "Formato de fecha/hora inválido en las líneas: " + ", ".join(map(str, errores[:50]))
            if len(errores) > 50:
                detalle += f" (y {len(errores) - 50} más)"
        else:
            detalle = f"Formato válido en {len(lineas)} línea(s). Se espera AAAA-MM-DD HH:MM:SS."
        self.registro.registrar("interfaz.ventana_logs", "Validación de formato", "WARNING" if errores else "INFO", detalle)
        messagebox.showinfo("Validar formato", detalle)

    def analizar_errores_logs(self):
        resultados = getattr(self, "resultados_logs", [])
        if not resultados:
            messagebox.showinfo("Análisis de errores", "Aún no hay resultados. Carga y valida un archivo de logs primero.")
            return
        invalidas = [(numero, linea) for numero, ok, linea in resultados if not ok]
        resumen = [f"Líneas analizadas: {len(resultados)}", f"Válidas: {len(resultados) - len(invalidas)}", f"Inválidas: {len(invalidas)}"]
        resumen.extend(f"Línea {numero}: {linea[:160]}" for numero, linea in invalidas[:20])
        if len(invalidas) > 20:
            resumen.append(f"… hay {len(invalidas) - 20} más.")
        detalle = "\n".join(resumen)
        self.registro.registrar("interfaz.ventana_logs", "Análisis de errores de validación", "WARNING" if invalidas else "INFO", f"Total={len(resultados)}; válidas={len(resultados) - len(invalidas)}; inválidas={len(invalidas)}")
        messagebox.showinfo("Análisis de errores", detalle)

    def validar_formato_registro_eventos(self):
        errores = self.registro.validar_formato()
        detalle = f"El archivo de eventos tiene {len(errores)} fila(s) con formato inválido."
        if errores:
            detalle += " Filas: " + ", ".join(map(str, errores[:50]))
        self.registro.registrar("visor_logs", "Validación de formato del registro de eventos", "WARNING" if errores else "INFO", detalle)
        messagebox.showinfo("Validar formato del registro", detalle, parent=self.visor_eventos)

    def analizar_registro_eventos(self):
        filas = self.registro.leer()
        errores = sum(1 for fila in filas if fila[2] == "ERROR")
        advertencias = sum(1 for fila in filas if fila[2] == "WARNING")
        detalle = f"Registros: {len(filas)}\nErrores: {errores}\nAdvertencias: {advertencias}"
        self.registro.registrar("visor_logs", "Análisis del registro de eventos", "INFO", detalle.replace("\n", "; "))
        messagebox.showinfo("Análisis de errores del registro", detalle, parent=self.visor_eventos)

    def refrescar_visor_eventos(self):
        tabla = getattr(self, "visor_tabla", None)
        if tabla is None or not tabla.winfo_exists():
            return
        estaba_abajo = not getattr(self, "visor_inicializado", False) or tabla.yview()[1] >= 0.98
        tabla.delete(*tabla.get_children())
        try:
            filtro = self.visor_niveles.get(self.visor_nivel.get(), "TODOS")
            filas = self.registro.leer(self.visor_buscar.get().strip(), filtro)
        except tk.TclError:
            return
        for fecha, hora, tipo, modulo, accion, resultado, detalle in filas:
            tabla.insert("", "end", values=(fecha, hora, tipo, modulo, accion, detalle), tags=(tipo,))
        if estaba_abajo:
            tabla.yview_moveto(1.0)
        self.visor_inicializado = True
        self.visor_estado.config(text=f"{len(filas)} evento(s) · Actualización automática · Registro: {self.registro.archivo}")
        trabajo = getattr(self, "visor_refresh_job", None)
        if trabajo is not None:
            try:
                self.after_cancel(trabajo)
            except tk.TclError:
                pass
        try:
            self.visor_refresh_job = self.after(1500, self.refrescar_visor_eventos)
        except tk.TclError:
            self.visor_refresh_job = None

    # ------------------------------------------------------------------
    # Mostrar autómata activo
    # ------------------------------------------------------------------
    def mostrar_automata(self, automata, mensaje):
        self.automata = automata
        self.ultimo_automata = automata

        if self.vista_actual in self.guardados:
            self.guardados[self.vista_actual] = (
                automata, mensaje, self.origen_automata
            )

        self.nb_der.select(self.tab_grafico)
        self.dibujar_automata()
        self.escribir_detalle(self.describir_automata(automata))
        self.info_label.config(text=mensaje)

        for etiqueta in (self.resultado_label, self.regex_resultado):
            etiqueta.config(text="Resultado: pendiente", foreground=C_TEXTO)

    def escribir_detalle(self, texto):
        self.detalle.config(state="normal")
        self.detalle.delete("1.0", tk.END)
        self.detalle.insert("1.0", texto)
        self.detalle.config(state="disabled")

    def describir_automata(self, automata):
        estados = sorted(automata.estados, key=clave_natural)
        finales = sorted(automata.finales, key=clave_natural)

        if len(estados) > 40:
            texto_estados = (
                ", ".join(estados[:40]) + f", … (+{len(estados) - 40})"
            )
        else:
            texto_estados = ", ".join(estados)

        lineas = [
            f"Tipo: {automata.tipo}",
            f"Estados ({len(estados)}): {texto_estados}",
            "Alfabeto: "
            + etiqueta_simbolos(
                set(automata.alfabeto) - {EPSILON}, automata.universo
            ),
            f"Inicial: {automata.inicial}",
            f"Finales: {', '.join(finales) if finales else '(ninguno)'}",
            "",
            "Transiciones (origen --símbolos--> destino):"
        ]

        aristas = {}

        for (origen, simbolo), destinos in automata.transiciones.items():
            for destino in destinos:
                aristas.setdefault((origen, destino), set()).add(simbolo)

        orden = sorted(
            aristas,
            key=lambda par: (clave_natural(par[0]), clave_natural(par[1]))
        )

        for indice, (origen, destino) in enumerate(orden):
            if indice >= 400:
                lineas.append(f"  … ({len(orden) - 400} más)")
                break

            lineas.append(
                f"  {origen} --{etiqueta_simbolos(aristas[(origen, destino)], automata.universo)}--> {destino}"
            )

        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def calcular_capas(self, estados):
        ady = {}

        for (origen, _), destinos in self.automata.transiciones.items():
            ady.setdefault(origen, set()).update(destinos)

        capas = {self.automata.inicial: 0}
        cola = deque([self.automata.inicial])

        while cola:
            actual = cola.popleft()

            for destino in sorted(ady.get(actual, ()), key=clave_natural):
                if destino not in capas:
                    capas[destino] = capas[actual] + 1
                    cola.append(destino)

        ultima = max(capas.values()) + 1

        for estado in estados:
            capas.setdefault(estado, ultima)

        return capas

    def dibujar_automata(self, resaltar=None):
        canvas = self.canvas
        canvas.delete("all")

        automata = self.automata

        if automata is None or not automata.estados:
            return

        resaltar = resaltar or set()
        estados = sorted(automata.estados, key=clave_natural)
        radio = self.RADIO_ESTADO

        if len(estados) > MAX_ESTADOS_DIBUJO:
            canvas.configure(scrollregion=(0, 0, 1, 1))
            canvas.create_text(
                20,
                20,
                anchor="nw",
                text=(
                    f"El autómata tiene {len(estados)} estados: es "
                    "demasiado grande para dibujarlo.\n"
                    "Consulte la tabla de transiciones en «Detalle»."
                ),
                font=(FUENTE_UI, 12),
                fill=C_TEXTO
            )
            return

        # --- posiciones por capas (BFS desde el estado inicial) -------
        capas = self.calcular_capas(estados)
        por_capa = {}

        for estado in estados:
            por_capa.setdefault(capas[estado], []).append(estado)

        paso_x, paso_y, margen = 125, 90, 110
        n_capas = max(por_capa) + 1
        max_fila = max(len(v) for v in por_capa.values())

        ancho = max(
            canvas.winfo_width(),
            2 * margen + (n_capas - 1) * paso_x,
            600
        )
        alto = max(
            canvas.winfo_height(),
            2 * margen + (max_fila - 1) * paso_y,
            400
        )

        x0 = (ancho - (n_capas - 1) * paso_x) / 2
        posiciones = {}

        for nivel, lista in por_capa.items():
            for indice, estado in enumerate(lista):
                posiciones[estado] = (
                    x0 + nivel * paso_x,
                    alto / 2 + (indice - (len(lista) - 1) / 2) * paso_y
                )

        canvas.configure(scrollregion=(0, 0, ancho, alto))

        # --- aristas agrupadas por (origen, destino) --------------------
        aristas = {}

        for (origen, simbolo), destinos in automata.transiciones.items():
            for destino in destinos:
                aristas.setdefault((origen, destino), set()).add(simbolo)

        etiquetas = []
        alternar = 1

        for (origen, destino), simbolos in aristas.items():
            if origen not in posiciones or destino not in posiciones:
                continue

            texto = etiqueta_simbolos(simbolos, automata.universo)

            if len(texto) > 36:
                texto = texto[:35] + "…"

            if origen == destino:
                x, y = posiciones[origen]
                canvas.create_oval(
                    x - 15, y - radio - 32, x + 15, y - radio + 2,
                    outline=C_SUAVE, width=2
                )
                canvas.create_line(
                    x + 14, y - radio - 10, x + 11, y - radio + 1,
                    fill=C_SUAVE, width=2, arrow=tk.LAST,
                    arrowshape=(8, 10, 4)
                )
                etiquetas.append((x, y - radio - 44, texto))
                continue

            x1, y1 = posiciones[origen]
            x2, y2 = posiciones[destino]
            dx, dy = x2 - x1, y2 - y1
            distancia = math.hypot(dx, dy) or 1
            nx, ny = -dy / distancia, dx / distancia

            curva = 0

            if (destino, origen) in aristas:
                curva = 32
            elif abs(capas[origen] - capas[destino]) > 1:
                curva = 42 * alternar
                alternar = -alternar

            cx = (x1 + x2) / 2 + nx * curva
            cy = (y1 + y2) / 2 + ny * curva

            ux, uy = cx - x1, cy - y1
            largo = math.hypot(ux, uy) or 1
            sx, sy = x1 + ux / largo * radio, y1 + uy / largo * radio

            vx, vy = cx - x2, cy - y2
            largo = math.hypot(vx, vy) or 1
            ex, ey = x2 + vx / largo * radio, y2 + vy / largo * radio

            canvas.create_line(
                sx, sy, cx, cy, ex, ey,
                smooth=True, fill=C_SUAVE, width=2, arrow=tk.LAST
            )

            lado = -1 if curva < 0 else 1
            etiquetas.append((
                (sx + 2 * cx + ex) / 4 + nx * 12 * lado,
                (sy + 2 * cy + ey) / 4 + ny * 12 * lado,
                texto
            ))

        for x, y, texto in etiquetas:
            id_texto = canvas.create_text(
                x, y, text=texto, fill=C_TEXTO, font=(FUENTE_UI, 9, "bold")
            )
            caja = canvas.bbox(id_texto)
            fondo = canvas.create_rectangle(
                caja[0] - 2, caja[1], caja[2] + 2, caja[3],
                fill=C_OSCURO, outline=""
            )
            canvas.tag_lower(fondo, id_texto)

        # --- estados ------------------------------------------------------
        for estado, (x, y) in posiciones.items():
            activo = estado in resaltar
            relleno = "#D6EBFB" if activo else C_BOTON
            borde = C_FONDO if activo else C_SUAVE

            canvas.create_oval(
                x - radio, y - radio, x + radio, y + radio,
                fill=relleno, outline=C_SUAVE, width=2
            )

            if estado in automata.finales:
                canvas.create_oval(
                    x - radio + 5, y - radio + 5,
                    x + radio - 5, y + radio - 5,
                    outline=borde, width=2
                )

            canvas.create_text(
                x, y, text=estado, font=(FUENTE_UI, 10, "bold"),
                fill=C_FONDO if activo else C_TEXTO
            )

            if estado == automata.inicial:
                canvas.create_line(
                    x - radio - 42, y, x - radio - 2, y,
                    fill=C_OK, width=2, arrow=tk.LAST
                )
                canvas.create_text(
                    x - radio - 42, y - 12, text="inicio", fill=C_OK
                )


# ----------------------------------------------------------------------
