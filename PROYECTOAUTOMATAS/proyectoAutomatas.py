import tkinter as tk
from collections import deque
from tkinter import filedialog, messagebox, ttk


EPSILON = "ε"


class Automata:
    def __init__(
        self,
        tipo,
        estados,
        alfabeto,
        inicial,
        finales,
        transiciones,
        comodin_otros=False,
        universo=None
    ):
        self.tipo = tipo
        self.estados = estados
        self.alfabeto = alfabeto
        self.inicial = inicial
        self.finales = finales
        self.transiciones = transiciones
        # Si es True, un carácter fuera del alfabeto se trata como OTRO
        # (en lugar de rechazar la cadena de inmediato). Lo usan los
        # autómatas generados desde regex para poder validar logs.
        self.comodin_otros = comodin_otros
        self.universo = universo
        self._cierres = {}

    # -- utilidades ----------------------------------------------------
    def _normalizar(self, caracter):
        if caracter in self.alfabeto:
            return caracter

        # Carácter conocido del universo pero sin ninguna arista: se deja
        # tal cual (no existen transiciones, así que la cadena se rechaza
        # salvo que otro camino la acepte). Solo lo desconocido es OTRO.
        if self.universo is not None and caracter in self.universo:
            return caracter

        if self.comodin_otros:
            return OTRO

        return None

    def _cierre_unitario(self, estado):
        if estado not in self._cierres:
            cierre = {estado}
            cola = deque([estado])

            while cola:
                actual = cola.popleft()

                for siguiente in self.transiciones.get(
                    (actual, EPSILON),
                    ()
                ):
                    if siguiente not in cierre:
                        cierre.add(siguiente)
                        cola.append(siguiente)

            self._cierres[estado] = frozenset(cierre)

        return self._cierres[estado]

    def epsilon_closure(self, estados):
        cierre = set()

        for estado in estados:
            cierre |= self._cierre_unitario(estado)

        return cierre

    # -- simulación ----------------------------------------------------
    def simular_afn(self, cadena):
        actuales = self.epsilon_closure({self.inicial})

        for caracter in cadena:
            simbolo = self._normalizar(caracter)

            if simbolo is None:
                return False

            siguientes = set()

            for estado in actuales:
                siguientes.update(
                    self.transiciones.get((estado, simbolo), ())
                )

            actuales = self.epsilon_closure(siguientes)

            if not actuales:
                return False

        return bool(actuales & self.finales)

    def simular_afd(self, cadena):
        actual = self.inicial

        for caracter in cadena:
            simbolo = self._normalizar(caracter)

            if simbolo is None:
                return False

            destinos = self.transiciones.get((actual, simbolo), ())

            if len(destinos) != 1:
                return False

            actual = next(iter(destinos))

        return actual in self.finales

    def simular(self, cadena):
        if self.tipo == "AFN":
            return self.simular_afn(cadena)

        return self.simular_afd(cadena)


class Aplicacion(tk.Tk):
    RADIO_ESTADO = 26

    def __init__(self):
        super().__init__()

        self.title("Simulador de Autómatas - Entrega 1")
        self.geometry("1150x750")
        self.minsize(950, 650)

        self.automata = None

        self.principal = ttk.Frame(self)
        self.crear_interfaz()

    def crear_interfaz(self):
        titulo = ttk.Label(
            self,
            text="Simulador de Autómatas",
            font=("Arial", 22, "bold")
        )
        titulo.pack(pady=10)

        subtitulo = ttk.Label(
            self,
            text="Primera etapa: AFN, AFD y simulación de cadenas",
            font=("Arial", 11)
        )
        subtitulo.pack()

        contenedor = ttk.Frame(self)
        contenedor.pack(fill="both", expand=True, padx=15, pady=15)

        panel_entrada = ttk.LabelFrame(
            contenedor,
            text="Configuración del autómata"
        )
        panel_entrada.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )

        panel_visual = ttk.Frame(contenedor)
        panel_visual.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.crear_formulario(panel_entrada)
        self.crear_area_visual(panel_visual)

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
            width=25
        )
        tipo_combo.pack(padx=10, pady=(0, 8))

        ttk.Label(
            panel,
            text="Estados separados por coma:"
        ).pack(anchor="w", padx=10)

        self.estados_entry = ttk.Entry(panel, width=30)
        self.estados_entry.insert(0, "q0,q1,q2")
        self.estados_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(
            panel,
            text="Alfabeto separado por coma:"
        ).pack(anchor="w", padx=10)

        self.alfabeto_entry = ttk.Entry(panel, width=30)
        self.alfabeto_entry.insert(0, "a,b")
        self.alfabeto_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estado inicial:").pack(
            anchor="w",
            padx=10
        )

        self.inicial_entry = ttk.Entry(panel, width=30)
        self.inicial_entry.insert(0, "q0")
        self.inicial_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(
            panel,
            text="Estados finales separados por coma:"
        ).pack(anchor="w", padx=10)

        self.finales_entry = ttk.Entry(panel, width=30)
        self.finales_entry.insert(0, "q2")
        self.finales_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(
            panel,
            text=(
                "Formato: estado,símbolo,destino\n"
                "Ejemplo: q0,a,q1\n"
                "Múltiples destinos: q0,a,q1|q2\n"
                "Epsilon: q0,ε,q1"
            ),
            foreground="#555555"
        )
        instrucciones.pack(anchor="w", padx=10, pady=(0, 5))

        self.transiciones_text = tk.Text(
            panel,
            width=30,
            height=10
        )
        self.transiciones_text.insert(
            "1.0",
            "q0,a,q1\nq1,b,q2\nq0,ε,q1"
        )
        self.transiciones_text.pack(padx=10, pady=(0, 10))

        ttk.Button(
            panel,
            text="Crear autómata",
            command=self.crear_automata
        ).pack(fill="x", padx=10, pady=4)

        ttk.Separator(panel).pack(
            fill="x",
            padx=10,
            pady=10
        )

        ttk.Label(
            panel,
            text="Cadena a simular:"
        ).pack(anchor="w", padx=10)

        self.cadena_entry = ttk.Entry(panel, width=30)
        self.cadena_entry.pack(padx=10, pady=(0, 8))

        ttk.Radiobutton(
            panel,
            text="Simular cadena",
            command=self.simular_cadena
        ).pack(fill="x", padx=10, pady=4)

        self.resultado_label = ttk.Label(
            panel,
            text="Resultado: pendiente",
            font=("Arial", 12, "bold")
        )
        self.resultado_label.pack(pady=15)

    def crear_area_visual(self, panel):
        marco = ttk.LabelFrame(
            panel,
            text="Representación gráfica"
        )
        marco.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            marco,
            background="white"
        )
        self.canvas.pack(fill="both", expand=True)

        self.info_label = ttk.Label(
            panel,
            text="Configure el autómata y presione «Crear autómata»."
        )
        self.info_label.pack(pady=8)

    def obtener_lista(self, valor):
        return {
            elemento.strip()
            for elemento in valor.split(",")
            if elemento.strip()
        }

    def crear_automata(self):
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

    def convertir_a_afd(self):
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

    def simular_cadena(self):
        self._simular_y_mostrar(self.cadena_entry.get())

    def _simular_y_mostrar(self, cadena):
        if self.automata is None:
            messagebox.showwarning(
                "Advertencia", "Primero debe crear un autómata."
            )
            return

        cadena = self.cadena_entry.get()

        aceptada = self.automata.simular(cadena)

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
        texto = self.regex_entry.get()
        tipo = self.regex_tipo.get()

        try:
            automata = construir_desde_regex(texto, tipo)
        except ErrorRegex as error:
            messagebox.showerror("Expresión regular inválida", str(error))
            return False

        self.origen_automata = ("regex", texto, tipo)
        self.mostrar_automata(
            automata,
            f"{tipo} generado desde «{texto}». "
            f"Estados: {len(automata.estados)} | "
            f"Transiciones: {sum(len(v) for v in automata.transiciones.values())}"
        )
        return True

    def validar_con_regex(self):
        texto = self.regex_entry.get()
        tipo = self.regex_tipo.get()

        if self.origen_automata != ("regex", texto, tipo):
            if not self.generar_desde_regex():
                return

        ancho = max(self.canvas.winfo_width(), 600)
        alto = max(self.canvas.winfo_height(), 450)

        centro_x = ancho // 2
        centro_y = alto // 2
        radio_distribucion = min(ancho, alto) // 3

        posiciones = {}

        for indice, estado in enumerate(estados):
            import math

            angulo = (
                2 * math.pi * indice / len(estados)
                - math.pi / 2
            )

            x = centro_x + radio_distribucion * math.cos(angulo)
            y = centro_y + radio_distribucion * math.sin(angulo)

            posiciones[estado] = (x, y)

        # Dibujar transiciones
        etiquetas = {}

        for (origen, simbolo), destinos in (
            self.automata.transiciones.items()
        ):
            for destino in destinos:
                if origen not in posiciones:
                    continue

                if destino not in posiciones:
                    continue

                x1, y1 = posiciones[origen]
                x2, y2 = posiciones[destino]

                if origen == destino:
                    self.canvas.create_oval(
                        x1 - 28,
                        y1 - 45,
                        x1 + 28,
                        y1 - 5,
                        outline="#333333",
                        width=2
                    )

                    self.canvas.create_text(
                        x1,
                        y1 - 55,
                        text=simbolo,
                        fill="#333333"
                    )
                else:
                    self.canvas.create_line(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill="#555555",
                        width=2,
                        arrow=tk.LAST
                    )

                    punto_medio_x = (x1 + x2) / 2
                    punto_medio_y = (y1 + y2) / 2

                    clave = (
                        round(punto_medio_x),
                        round(punto_medio_y)
                    )

                    etiquetas.setdefault(clave, []).append(simbolo)

        for (x, y), simbolos in etiquetas.items():
            self.canvas.create_text(
                x,
                y - 10,
                text=", ".join(simbolos),
                fill="blue",
                font=("Arial", 10, "bold")
            )

        # Dibujar estados
        for estado, (x, y) in posiciones.items():
            color = "#d9edf7"

            self.canvas.create_oval(
                x - 30,
                y - 30,
                x + 30,
                y + 30,
                fill=color,
                outline="#1f4e79",
                width=2
            )

            if estado in self.automata.finales:
                self.canvas.create_oval(
                    x - 24,
                    y - 24,
                    x + 24,
                    y + 24,
                    outline="#1f4e79",
                    width=2
                )

            self.canvas.create_text(
                x,
                y,
                text=estado,
                font=("Arial", 11, "bold")
            )

            if estado == self.automata.inicial:
                self.canvas.create_line(
                    x - 70,
                    y,
                    x - 32,
                    y,
                    fill="green",
                    width=2,
                    arrow=tk.LAST
                )

                self.canvas.create_text(
                    x - 75,
                    y - 15,
                    text="inicio",
                    fill="green"
                )


if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()
