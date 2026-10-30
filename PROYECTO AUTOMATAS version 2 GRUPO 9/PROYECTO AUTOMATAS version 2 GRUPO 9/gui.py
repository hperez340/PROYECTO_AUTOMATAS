import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from parser import crear_automata_desde_campos


class ScrollableFrame(ttk.Frame):
    """
    Panel con desplazamiento vertical.
    Permite que los controles sigan accesibles en pantallas pequeñas.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.inner = ttk.Frame(self.canvas)

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.inner,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind(
            "<Configure>",
            self._actualizar_scroll
        )

        self.canvas.bind(
            "<Configure>",
            self._ajustar_ancho
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self._rueda_mouse
        )

    def _actualizar_scroll(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def _ajustar_ancho(self, event):
        self.canvas.itemconfigure(
            self.window_id,
            width=event.width
        )

    def _rueda_mouse(self, event):
        try:
            self.canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )
        except Exception:
            pass


class SimuladorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulador de Autómatas")

        # Tamaño inicial más compacto.
        self.geometry("1050x650")
        self.minsize(780, 520)

        self.automata = None
        self.posiciones = {}

        self._crear_estilos()
        self._crear_interfaz()

    def _crear_estilos(self):
        estilo = ttk.Style(self)

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "Titulo.TLabel",
            font=("Segoe UI", 18, "bold")
        )

        estilo.configure(
            "Ayuda.TLabel",
            font=("Segoe UI", 9)
        )

        estilo.configure(
            "Resultado.TLabel",
            font=("Segoe UI", 12, "bold")
        )

        estilo.configure(
            "TButton",
            padding=5
        )

    def _crear_interfaz(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        cabecera = ttk.Frame(
            self,
            padding=(10, 8)
        )
        cabecera.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        ttk.Label(
            cabecera,
            text="Simulador de Autómatas",
            style="Titulo.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            cabecera,
            text=(
                "Crea un AFD o AFN, ingresa una cadena "
                "y observa su recorrido paso a paso."
            ),
            style="Ayuda.TLabel"
        ).pack(
            anchor="w",
            pady=(2, 0)
        )

        self.principal = ttk.Panedwindow(
            self,
            orient="horizontal"
        )
        self.principal.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=(0, 8)
        )

        # Panel izquierdo desplazable.
        izquierda_scroll = ScrollableFrame(self.principal)
        derecha = ttk.Frame(
            self.principal,
            padding=6
        )

        self.principal.add(
            izquierda_scroll,
            weight=2
        )
        self.principal.add(
            derecha,
            weight=3
        )

        self._crear_panel_entrada(
            izquierda_scroll.inner
        )

        self._crear_panel_visual(derecha)

    def _crear_panel_entrada(self, padre):
        contenedor = ttk.Frame(
            padre,
            padding=(6, 4, 8, 12)
        )
        contenedor.pack(
            fill="both",
            expand=True
        )

        datos = ttk.LabelFrame(
            contenedor,
            text="Datos del autómata",
            padding=8
        )
        datos.pack(
            fill="x"
        )

        ttk.Label(
            datos,
            text="Tipo:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=3
        )

        self.tipo = ttk.Combobox(
            datos,
            values=["AFD", "AFN"],
            state="readonly",
            width=12
        )
        self.tipo.set("AFD")
        self.tipo.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=3
        )

        ttk.Label(
            datos,
            text="Estados:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=3
        )

        self.estados = ttk.Entry(datos)
        self.estados.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=3
        )

        ttk.Label(
            datos,
            text="Ej.: q0,q1,q2",
            style="Ayuda.TLabel"
        ).grid(
            row=2,
            column=1,
            sticky="w"
        )

        ttk.Label(
            datos,
            text="Alfabeto:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=3
        )

        self.alfabeto = ttk.Entry(datos)
        self.alfabeto.grid(
            row=3,
            column=1,
            sticky="ew",
            pady=3
        )

        ttk.Label(
            datos,
            text="Ej.: a,b,c,0,1",
            style="Ayuda.TLabel"
        ).grid(
            row=4,
            column=1,
            sticky="w"
        )

        ttk.Label(
            datos,
            text="Estado inicial:"
        ).grid(
            row=5,
            column=0,
            sticky="w",
            pady=3
        )

        self.inicial = ttk.Entry(datos)
        self.inicial.grid(
            row=5,
            column=1,
            sticky="ew",
            pady=3
        )

        ttk.Label(
            datos,
            text="Estados finales:"
        ).grid(
            row=6,
            column=0,
            sticky="w",
            pady=3
        )

        self.finales = ttk.Entry(datos)
        self.finales.grid(
            row=6,
            column=1,
            sticky="ew",
            pady=3
        )

        ttk.Label(
            datos,
            text="Lenguaje / descripción:"
        ).grid(
            row=7,
            column=0,
            sticky="nw",
            pady=3
        )

        self.lenguaje = tk.Text(
            datos,
            height=3,
            wrap="word"
        )
        self.lenguaje.grid(
            row=7,
            column=1,
            sticky="ew",
            pady=3
        )

        datos.columnconfigure(
            1,
            weight=1
        )

        trans = ttk.LabelFrame(
            contenedor,
            text="Transiciones",
            padding=8
        )
        trans.pack(
            fill="both",
            expand=True,
            pady=(8, 0)
        )

        ttk.Label(
            trans,
            text=(
                "Una por línea: origen,símbolo,destino\n"
                "AFD: q0,a,q1   |   "
                "AFN: q0,a,q0,q1   |   "
                "ε: q0,ε,q1"
            ),
            style="Ayuda.TLabel",
            justify="left"
        ).pack(anchor="w")

        # Menor altura para ahorrar espacio.
        self.transiciones = tk.Text(
            trans,
            height=9,
            wrap="none"
        )
        self.transiciones.pack(
            fill="both",
            expand=True,
            pady=(5, 0)
        )

        acciones = ttk.LabelFrame(
            contenedor,
            text="Acciones",
            padding=8
        )
        acciones.pack(
            fill="x",
            pady=(8, 0)
        )

        # Botones en cuadrícula adaptable.
        for columna in range(2):
            acciones.columnconfigure(
                columna,
                weight=1
            )

        ttk.Button(
            acciones,
            text="Crear / validar",
            command=self.crear_automata
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 4),
            pady=3
        )

        ttk.Button(
            acciones,
            text="Limpiar todo",
            command=self.limpiar_todo
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(4, 0),
            pady=3
        )

        prueba = ttk.LabelFrame(
            contenedor,
            text="Simulación de cadena",
            padding=8
        )
        prueba.pack(
            fill="x",
            pady=(8, 0)
        )

        ttk.Label(
            prueba,
            text="Cadena:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=3
        )

        self.cadena = ttk.Entry(prueba)
        self.cadena.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=3
        )

        ttk.Button(
            prueba,
            text="Simular",
            command=self.simular_cadena
        ).grid(
            row=0,
            column=2,
            padx=(5, 0),
            pady=3
        )

        prueba.columnconfigure(
            1,
            weight=1
        )

        ttk.Label(
            prueba,
            text=(
                "Puede usar números, letras o combinaciones: "
                "0001, abc01, a10b"
            ),
            style="Ayuda.TLabel",
            wraplength=360,
            justify="left"
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(3, 4)
        )

        extras = ttk.Frame(prueba)
        extras.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(4, 0)
        )

        for columna in range(2):
            extras.columnconfigure(
                columna,
                weight=1
            )

        ttk.Button(
            extras,
            text="Convertir AFN → AFD",
            command=self.convertir_afn
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 4),
            pady=3
        )

        ttk.Button(
            extras,
            text="Minimizar AFD",
            command=self.minimizar_afd
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(4, 0),
            pady=3
        )

        ttk.Button(
            extras,
            text="Guardar definición",
            command=self.guardar_definicion
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(4, 0)
        )

    def _crear_panel_visual(self, padre):
        padre.columnconfigure(
            0,
            weight=1
        )
        padre.rowconfigure(
            0,
            weight=1
        )

        notebook = ttk.Notebook(padre)
        notebook.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        tab_grafo = ttk.Frame(notebook)
        tab_sim = ttk.Frame(notebook)
        tab_info = ttk.Frame(notebook)

        notebook.add(
            tab_grafo,
            text="Diagrama"
        )

        notebook.add(
            tab_sim,
            text="Simulación"
        )

        notebook.add(
            tab_info,
            text="Información"
        )

        tab_grafo.columnconfigure(
            0,
            weight=1
        )
        tab_grafo.rowconfigure(
            0,
            weight=1
        )

        self.canvas = tk.Canvas(
            tab_grafo,
            bg="white",
            highlightthickness=1,
            highlightbackground="#bbbbbb"
        )
        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.dibujar_automata()
        )

        tab_sim.columnconfigure(
            0,
            weight=1
        )
        tab_sim.rowconfigure(
            1,
            weight=1
        )

        self.resultado_lbl = ttk.Label(
            tab_sim,
            text="Ingrese los datos del autómata para comenzar.",
            style="Resultado.TLabel",
            wraplength=600
        )
        self.resultado_lbl.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=8,
            pady=8
        )

        tabla_frame = ttk.Frame(tab_sim)
        tabla_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=(0, 8)
        )

        tabla_frame.columnconfigure(
            0,
            weight=1
        )
        tabla_frame.rowconfigure(
            0,
            weight=1
        )

        columnas = (
            "paso",
            "simbolo",
            "antes",
            "despues",
            "detalle"
        )

        self.tabla = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings"
        )

        titulos = {
            "paso": "Paso",
            "simbolo": "Símbolo",
            "antes": "Antes",
            "despues": "Después",
            "detalle": "Detalle"
        }

        for columna, titulo in titulos.items():
            self.tabla.heading(
                columna,
                text=titulo
            )

        self.tabla.column(
            "paso",
            width=50,
            minwidth=45,
            anchor="center",
            stretch=False
        )

        self.tabla.column(
            "simbolo",
            width=65,
            minwidth=55,
            anchor="center",
            stretch=False
        )

        self.tabla.column(
            "antes",
            width=110,
            minwidth=90
        )

        self.tabla.column(
            "despues",
            width=110,
            minwidth=90
        )

        self.tabla.column(
            "detalle",
            width=280,
            minwidth=180
        )

        scroll_y = ttk.Scrollbar(
            tabla_frame,
            orient="vertical",
            command=self.tabla.yview
        )

        scroll_x = ttk.Scrollbar(
            tabla_frame,
            orient="horizontal",
            command=self.tabla.xview
        )

        self.tabla.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.tabla.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scroll_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scroll_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        tab_info.columnconfigure(
            0,
            weight=1
        )
        tab_info.rowconfigure(
            0,
            weight=1
        )

        self.info = tk.Text(
            tab_info,
            wrap="word",
            state="disabled"
        )

        info_scroll = ttk.Scrollbar(
            tab_info,
            orient="vertical",
            command=self.info.yview
        )

        self.info.configure(
            yscrollcommand=info_scroll.set
        )

        self.info.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(8, 0),
            pady=8
        )

        info_scroll.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(0, 8),
            pady=8
        )

    def crear_automata(self, mostrar_mensaje=True):
        try:
            nuevo = crear_automata_desde_campos(
                tipo=self.tipo.get(),
                estados_txt=self.estados.get(),
                alfabeto_txt=self.alfabeto.get(),
                inicial_txt=self.inicial.get(),
                finales_txt=self.finales.get(),
                transiciones_txt=self.transiciones.get(
                    "1.0",
                    "end"
                ),
                lenguaje_txt=self.lenguaje.get(
                    "1.0",
                    "end"
                )
            )
        except ValueError as e:
            self.automata = None
            messagebox.showerror(
                "Datos incorrectos",
                str(e)
            )
            return False

        self.automata = nuevo
        self._actualizar_info()
        self.dibujar_automata()

        if mostrar_mensaje:
            messagebox.showinfo(
                "Autómata válido",
                (
                    "El autómata fue creado correctamente. "
                    "Ya puede simular una cadena."
                )
            )

        return True

    def simular_cadena(self):
        if not self.crear_automata(
            mostrar_mensaje=False
        ):
            return

        cadena = self.cadena.get().strip()

        aceptada, pasos, estados_finales = (
            self.automata.simular(cadena)
        )

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for paso in pasos:
            self.tabla.insert(
                "",
                "end",
                values=(
                    paso["indice"],
                    paso["simbolo"],
                    self._fmt(paso["antes"]),
                    self._fmt(paso["despues"]),
                    paso["mensaje"]
                )
            )

        if aceptada:
            self.resultado_lbl.config(
                text=(
                    "CADENA ACEPTADA ✓   |   "
                    "Estado(s) al terminar: "
                    f"{self._fmt(estados_finales)}"
                )
            )
        else:
            self.resultado_lbl.config(
                text=(
                    "CADENA RECHAZADA ✗   |   "
                    "Estado(s) al terminar: "
                    f"{self._fmt(estados_finales)}"
                )
            )

        self._resaltar_estados(
            estados_finales
        )

    def limpiar_todo(self):
        self.tipo.set("AFD")

        for entrada in (
            self.estados,
            self.alfabeto,
            self.inicial,
            self.finales,
            self.cadena
        ):
            entrada.delete(
                0,
                "end"
            )

        self.lenguaje.delete(
            "1.0",
            "end"
        )

        self.transiciones.delete(
            "1.0",
            "end"
        )

        self.automata = None

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        self.resultado_lbl.config(
            text="Ingrese los datos del autómata para comenzar."
        )

        self.info.config(
            state="normal"
        )
        self.info.delete(
            "1.0",
            "end"
        )
        self.info.config(
            state="disabled"
        )

        self.dibujar_automata()

    def convertir_afn(self):
        if not self.crear_automata(
            mostrar_mensaje=False
        ):
            return

        if self.automata.tipo != "AFN":
            messagebox.showwarning(
                "Conversión",
                (
                    "Debe seleccionar AFN "
                    "para realizar la conversión."
                )
            )
            return

        self.automata = (
            self.automata.convertir_afn_a_afd()
        )

        self._cargar_automata_en_campos(
            self.automata
        )

        self._actualizar_info()
        self.dibujar_automata()

        messagebox.showinfo(
            "Conversión terminada",
            "El AFN fue convertido a AFD."
        )

    def minimizar_afd(self):
        if not self.crear_automata(
            mostrar_mensaje=False
        ):
            return

        if self.automata.tipo != "AFD":
            messagebox.showwarning(
                "Minimización",
                (
                    "La minimización solamente "
                    "puede aplicarse a un AFD."
                )
            )
            return

        self.automata = (
            self.automata.minimizar_afd()
        )

        self._cargar_automata_en_campos(
            self.automata
        )

        self._actualizar_info()
        self.dibujar_automata()

        messagebox.showinfo(
            "Minimización terminada",
            "El AFD fue minimizado."
        )

    def guardar_definicion(self):
        if not self.crear_automata(
            mostrar_mensaje=False
        ):
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar autómata",
            defaultextension=".txt",
            filetypes=[
                (
                    "Archivo de texto",
                    "*.txt"
                ),
                (
                    "Todos los archivos",
                    "*.*"
                )
            ]
        )

        if not ruta:
            return

        with open(
            ruta,
            "w",
            encoding="utf-8"
        ) as archivo:
            archivo.write(
                self.automata.como_texto()
            )

        messagebox.showinfo(
            "Guardado",
            (
                "La definición del autómata "
                "fue guardada correctamente."
            )
        )

    def dibujar_automata(self):
        self.canvas.delete("all")
        self.posiciones = {}

        if self.automata is None:
            self.canvas.create_text(
                20,
                20,
                anchor="nw",
                text=(
                    "El diagrama aparecerá aquí "
                    "cuando ingrese y valide un autómata."
                ),
                font=("Segoe UI", 11),
                width=max(
                    self.canvas.winfo_width() - 40,
                    200
                )
            )
            return

        ancho = max(
            self.canvas.winfo_width(),
            320
        )

        alto = max(
            self.canvas.winfo_height(),
            300
        )

        estados = sorted(
            self.automata.estados
        )

        n = len(estados)

        if not n:
            return

        cx = ancho / 2
        cy = alto / 2

        radio_orbita = max(
            70,
            min(ancho, alto) * 0.30
        )

        radio_nodo = 26

        for i, estado in enumerate(estados):
            angulo = (
                2 * math.pi * i / n
            ) - math.pi / 2

            x = (
                cx
                + radio_orbita
                * math.cos(angulo)
            )

            y = (
                cy
                + radio_orbita
                * math.sin(angulo)
            )

            self.posiciones[estado] = (
                x,
                y
            )

        for (
            origen,
            simbolo
        ), destinos in (
            self.automata.transiciones.items()
        ):
            for destino in destinos:
                if (
                    origen not in self.posiciones
                    or destino not in self.posiciones
                ):
                    continue

                x1, y1 = self.posiciones[origen]
                x2, y2 = self.posiciones[destino]

                if origen == destino:
                    self._dibujar_bucle(
                        x1,
                        y1,
                        simbolo,
                        radio_nodo
                    )
                else:
                    self._dibujar_flecha(
                        x1,
                        y1,
                        x2,
                        y2,
                        simbolo,
                        radio_nodo
                    )

        if (
            self.automata.inicial
            in self.posiciones
        ):
            x, y = self.posiciones[
                self.automata.inicial
            ]

            largo_inicio = min(
                65,
                max(35, x - 10)
            )

            self.canvas.create_line(
                x - largo_inicio,
                y,
                x - radio_nodo,
                y,
                arrow="last",
                width=2
            )

        for estado, (
            x,
            y
        ) in self.posiciones.items():

            self.canvas.create_oval(
                x - radio_nodo,
                y - radio_nodo,
                x + radio_nodo,
                y + radio_nodo,
                width=2,
                fill="#f7f7f7"
            )

            if (
                estado
                in self.automata.finales
            ):
                self.canvas.create_oval(
                    x - radio_nodo + 5,
                    y - radio_nodo + 5,
                    x + radio_nodo - 5,
                    y + radio_nodo - 5,
                    width=2
                )

            self.canvas.create_text(
                x,
                y,
                text=estado,
                font=(
                    "Segoe UI",
                    9,
                    "bold"
                )
            )

    def _dibujar_flecha(
        self,
        x1,
        y1,
        x2,
        y2,
        simbolo,
        radio
    ):
        dx = x2 - x1
        dy = y2 - y1

        distancia = math.hypot(
            dx,
            dy
        )

        if distancia == 0:
            return

        ux = dx / distancia
        uy = dy / distancia

        inicio_x = x1 + ux * radio
        inicio_y = y1 + uy * radio

        fin_x = x2 - ux * radio
        fin_y = y2 - uy * radio

        self.canvas.create_line(
            inicio_x,
            inicio_y,
            fin_x,
            fin_y,
            arrow="last",
            width=2
        )

        mx = (
            inicio_x + fin_x
        ) / 2

        my = (
            inicio_y + fin_y
        ) / 2

        self.canvas.create_text(
            mx + (-uy * 11),
            my + (ux * 11),
            text=simbolo,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

    def _dibujar_bucle(
        self,
        x,
        y,
        simbolo,
        radio
    ):
        self.canvas.create_arc(
            x - radio,
            y - radio - 32,
            x + radio,
            y + radio - 5,
            start=20,
            extent=300,
            style="arc",
            width=2
        )

        self.canvas.create_text(
            x,
            y - radio - 37,
            text=simbolo,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

    def _resaltar_estados(
        self,
        estados
    ):
        self.dibujar_automata()

        for estado in estados:
            if (
                estado
                not in self.posiciones
            ):
                continue

            x, y = self.posiciones[
                estado
            ]

            self.canvas.create_oval(
                x - 32,
                y - 32,
                x + 32,
                y + 32,
                width=3
            )

    def _actualizar_info(self):
        self.info.config(
            state="normal"
        )

        self.info.delete(
            "1.0",
            "end"
        )

        if self.automata:
            self.info.insert(
                "1.0",
                self.automata.como_texto()
            )

        self.info.config(
            state="disabled"
        )

    def _cargar_automata_en_campos(
        self,
        automata
    ):
        self.tipo.set(
            automata.tipo
        )

        self.estados.delete(
            0,
            "end"
        )
        self.estados.insert(
            0,
            ",".join(
                sorted(
                    automata.estados
                )
            )
        )

        self.alfabeto.delete(
            0,
            "end"
        )
        self.alfabeto.insert(
            0,
            ",".join(
                sorted(
                    automata.alfabeto
                )
            )
        )

        self.inicial.delete(
            0,
            "end"
        )
        self.inicial.insert(
            0,
            automata.inicial
        )

        self.finales.delete(
            0,
            "end"
        )
        self.finales.insert(
            0,
            ",".join(
                sorted(
                    automata.finales
                )
            )
        )

        self.lenguaje.delete(
            "1.0",
            "end"
        )
        self.lenguaje.insert(
            "1.0",
            automata.lenguaje
        )

        self.transiciones.delete(
            "1.0",
            "end"
        )

        lineas = []

        for (
            origen,
            simbolo
        ), destinos in sorted(
            automata.transiciones.items()
        ):
            lineas.append(
                ",".join(
                    [origen, simbolo]
                    + sorted(destinos)
                )
            )

        self.transiciones.insert(
            "1.0",
            "\n".join(lineas)
        )

    @staticmethod
    def _fmt(estados):
        if not estados:
            return "∅"

        return (
            "{"
            + ", ".join(
                sorted(estados)
            )
            + "}"
        )
