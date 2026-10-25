"""
Simulador de Autómatas - Entrega 2 (integrada con la Entrega 1)

Incluye:
  * Entrega 1: creación manual de AFN / AFD y simulación de cadenas.
  * Regex -> AFN (construcción de Thompson) y AFN -> AFD (subconjuntos).
  * Validación de cadenas con el autómata generado desde una regex.
  * Validación de logs línea por línea (con regex o con el autómata activo).

Sintaxis de regex soportada (motor propio, no usa el módulo `re`):
  a|b      unión              ab        concatenación
  a*  a+  a?   repeticiones   a{3} a{2,4} a{2,}   cuantificadores
  ( )      agrupación         .         cualquier carácter
  [abc] [a-z] [^0-9]          clases de caracteres
  \\d \\w \\s \\D \\W \\S         atajos           \\.  \\|  \\*  ...   escapes
  ε        cadena vacía
"""

import csv
import math
import re
import tkinter as tk
from collections import deque
from tkinter import filedialog, messagebox, ttk


EPSILON = "ε"
OTRO = "\uffff"  # representa «cualquier otro carácter» fuera del alfabeto

BASE_ALFABETO = frozenset(chr(c) for c in range(32, 127)) | {"\t", OTRO}
DIGITOS = frozenset("0123456789")
PALABRA = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)
ESPACIOS = frozenset(" \t")

MAX_ESTADOS_CONSTRUCCION = 5000
MAX_ESTADOS_DIBUJO = 150


# ----------------------------------------------------------------------
# Utilidades de presentación
# ----------------------------------------------------------------------
def clave_natural(texto):
    """Ordena q2 antes que q10."""
    return [
        int(parte) if parte.isdigit() else parte
        for parte in re.split(r"(\d+)", texto)
    ]


def mostrar_simbolo(simbolo):
    if simbolo == OTRO:
        return "otro"
    if simbolo == " ":
        return "␣"
    if simbolo == "\t":
        return "\\t"
    return simbolo


def _compactar(caracteres):
    """Convierte {a,b,c,x} en 'a-c,x'."""
    codigos = sorted(ord(c) for c in caracteres if c != OTRO)
    partes = []
    i = 0

    while i < len(codigos):
        j = i

        while j + 1 < len(codigos) and codigos[j + 1] == codigos[j] + 1:
            j += 1

        if j - i >= 2:
            partes.append(
                f"{mostrar_simbolo(chr(codigos[i]))}-"
                f"{mostrar_simbolo(chr(codigos[j]))}"
            )
        else:
            partes.extend(
                mostrar_simbolo(chr(c)) for c in codigos[i:j + 1]
            )

        i = j + 1

    if OTRO in caracteres:
        partes.append("otro")

    return ",".join(partes)


def etiqueta_simbolos(simbolos, universo=None):
    """Etiqueta legible para un conjunto de símbolos de una arista."""
    simbolos = set(simbolos)
    partes = []

    if EPSILON in simbolos:
        partes.append(EPSILON)
        simbolos.discard(EPSILON)

    if simbolos:
        if universo and len(simbolos) > 0.6 * len(universo):
            faltan = set(universo) - simbolos

            if not faltan:
                partes.append("Σ")
            else:
                partes.append("Σ∖{" + _compactar(faltan) + "}")
        else:
            partes.append(_compactar(simbolos))

    return ",".join(partes)


# ----------------------------------------------------------------------
# Autómata (Entrega 1, ampliado)
# ----------------------------------------------------------------------
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

    def procesar(self, cadena):
        """Simula y devuelve (aceptada, pasos) para mostrar la traza.

        Cada paso es (descripcion, lista_de_estados_activos).
        """
        actuales = self.epsilon_closure({self.inicial})
        pasos = [("inicio", sorted(actuales, key=clave_natural))]

        for caracter in cadena:
            simbolo = self._normalizar(caracter)

            if simbolo is None:
                pasos.append(
                    (f"'{caracter}' fuera del alfabeto", [])
                )
                return False, pasos

            siguientes = set()

            for estado in actuales:
                siguientes.update(
                    self.transiciones.get((estado, simbolo), ())
                )

            actuales = self.epsilon_closure(siguientes)
            pasos.append((
                f"leer '{mostrar_simbolo(caracter)}'",
                sorted(actuales, key=clave_natural)
            ))

            if not actuales:
                return False, pasos

        return bool(actuales & self.finales), pasos


# ----------------------------------------------------------------------
# Expresiones regulares: parser -> AST
# ----------------------------------------------------------------------
class ErrorRegex(ValueError):
    pass


class ParserRegex:
    """Parser descendente recursivo.

    Nodos del AST:
      ("eps",)                 cadena vacía
      ("chars", frozenset)     uno de estos caracteres
      ("comp", frozenset)      cualquier carácter del universo salvo estos
      ("cat", [nodos])         concatenación
      ("alt", [nodos])         unión
      ("star"|"plus"|"opt", nodo)
    """

    def __init__(self, texto):
        self.t = texto
        self.i = 0
        self.extra = set()  # caracteres literales fuera de BASE_ALFABETO

    def parsear(self):
        if self.t == "":
            raise ErrorRegex("Ingrese una expresión regular.")

        nodo = self.union()

        if self.i < len(self.t):
            raise ErrorRegex(
                f"Carácter inesperado '{self.t[self.i]}' en la posición "
                f"{self.i + 1} (¿paréntesis de cierre sin abrir?)."
            )

        return nodo

    def mirar(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def literal(self, caracter):
        if caracter not in BASE_ALFABETO:
            self.extra.add(caracter)

        return ("chars", frozenset({caracter}))

    def union(self):
        ramas = [self.concatenacion()]

        while self.mirar() == "|":
            self.i += 1
            ramas.append(self.concatenacion())

        return ramas[0] if len(ramas) == 1 else ("alt", ramas)

    def concatenacion(self):
        partes = []

        while self.mirar() is not None and self.mirar() not in "|)":
            partes.append(self.repeticion())

        if not partes:
            return ("eps",)

        return partes[0] if len(partes) == 1 else ("cat", partes)

    def repeticion(self):
        nodo = self.atomo()

        while True:
            c = self.mirar()

            if c == "*":
                self.i += 1
                nodo = ("star", nodo)
            elif c == "+":
                self.i += 1
                nodo = ("plus", nodo)
            elif c == "?":
                self.i += 1
                nodo = ("opt", nodo)
            elif c == "{":
                nodo = self.cuantificador(nodo)
            else:
                break

        return nodo

    def cuantificador(self, nodo):
        fin = self.t.find("}", self.i)

        if fin == -1:
            raise ErrorRegex("Falta cerrar un cuantificador con '}'.")

        cuerpo = self.t[self.i + 1:fin]
        self.i = fin + 1
        partes = cuerpo.split(",")

        try:
            if len(partes) == 1:
                minimo = maximo = int(partes[0])
            elif len(partes) == 2:
                minimo = int(partes[0])
                maximo = (
                    None if partes[1].strip() == "" else int(partes[1])
                )
            else:
                raise ValueError
        except ValueError:
            raise ErrorRegex(
                f"Cuantificador inválido: {{{cuerpo}}}."
            ) from None

        if (
            minimo < 0
            or minimo > 50
            or (maximo is not None and (maximo < minimo or maximo > 50))
        ):
            raise ErrorRegex(
                "En {n,m} debe cumplirse 0 ≤ n ≤ m ≤ 50."
            )

        copias = [nodo] * minimo

        if maximo is None:
            copias.append(("star", nodo))
        else:
            copias.extend([("opt", nodo)] * (maximo - minimo))

        if not copias:
            return ("eps",)

        return copias[0] if len(copias) == 1 else ("cat", copias)

    def atomo(self):
        c = self.mirar()

        if c == "(":
            self.i += 1
            nodo = self.union()

            if self.mirar() != ")":
                raise ErrorRegex("Falta cerrar un paréntesis ')'.")

            self.i += 1
            return nodo

        if c == "[":
            return self.clase()

        if c == ".":
            self.i += 1
            return ("comp", frozenset())

        if c == "\\":
            return self.escape()

        if c in "*+?{":
            raise ErrorRegex(
                f"El operador '{c}' no tiene nada que repetir "
                f"(posición {self.i + 1}). Use \\{c} para el símbolo."
            )

        self.i += 1

        if c == EPSILON:
            return ("eps",)

        return self.literal(c)

    def escape(self):
        self.i += 1
        c = self.mirar()

        if c is None:
            raise ErrorRegex(
                "La barra invertida '\\' está al final de la expresión."
            )

        self.i += 1

        atajos = {
            "d": ("chars", DIGITOS),
            "D": ("comp", DIGITOS),
            "w": ("chars", PALABRA),
            "W": ("comp", PALABRA),
            "s": ("chars", ESPACIOS),
            "S": ("comp", ESPACIOS),
        }

        if c in atajos:
            return atajos[c]

        if c == "n":
            return self.literal("\n")

        if c == "t":
            return self.literal("\t")

        return self.literal(c)

    def _unidad_clase(self):
        c = self.mirar()
        self.i += 1

        if c != "\\":
            return ("car", c)

        d = self.mirar()

        if d is None:
            raise ErrorRegex("Falta cerrar un corchete ']'.")

        self.i += 1

        if d == "d":
            return ("conj", DIGITOS)
        if d == "w":
            return ("conj", PALABRA)
        if d == "s":
            return ("conj", ESPACIOS)
        if d in "DWS":
            raise ErrorRegex(f"\\{d} no se admite dentro de [ ].")
        if d == "n":
            return ("car", "\n")
        if d == "t":
            return ("car", "\t")

        return ("car", d)

    def clase(self):
        self.i += 1  # '['
        negada = False

        if self.mirar() == "^":
            negada = True
            self.i += 1

        conjunto = set()
        primero = True

        while True:
            c = self.mirar()

            if c is None:
                raise ErrorRegex("Falta cerrar un corchete ']'.")

            if c == "]" and not primero:
                self.i += 1
                break

            primero = False
            tipo, valor = self._unidad_clase()

            if tipo == "conj":
                conjunto |= valor
                continue

            if (
                self.mirar() == "-"
                and self.i + 1 < len(self.t)
                and self.t[self.i + 1] != "]"
            ):
                self.i += 1
                tipo2, valor2 = self._unidad_clase()

                if tipo2 == "conj":
                    raise ErrorRegex("Rango inválido dentro de [ ].")

                if ord(valor) > ord(valor2):
                    raise ErrorRegex(
                        f"Rango inválido '{valor}-{valor2}'."
                    )

                if ord(valor2) - ord(valor) > 2000:
                    raise ErrorRegex("Rango demasiado grande en [ ].")

                for codigo in range(ord(valor), ord(valor2) + 1):
                    conjunto.add(chr(codigo))
            else:
                conjunto.add(valor)

        for caracter in conjunto:
            if caracter not in BASE_ALFABETO:
                self.extra.add(caracter)

        if negada:
            return ("comp", frozenset(conjunto))

        return ("chars", frozenset(conjunto))


# ----------------------------------------------------------------------
# Construcción de Thompson
# ----------------------------------------------------------------------
class ConstructorThompson:
    def __init__(self, universo):
        self.universo = universo
        self.contador = 0
        self.trans = {}

    def nuevo(self):
        if self.contador >= MAX_ESTADOS_CONSTRUCCION:
            raise ErrorRegex(
                "La expresión genera un autómata demasiado grande."
            )

        nombre = f"q{self.contador}"
        self.contador += 1
        return nombre

    def arista(self, origen, simbolo, destino):
        self.trans.setdefault((origen, simbolo), set()).add(destino)

    def construir(self, nodo):
        """Devuelve (estado_inicial, estado_final) del fragmento."""
        tipo = nodo[0]

        if tipo == "cat":
            fragmentos = [self.construir(p) for p in nodo[1]]

            for (_, fin), (inicio, _) in zip(fragmentos, fragmentos[1:]):
                self.arista(fin, EPSILON, inicio)

            return fragmentos[0][0], fragmentos[-1][1]

        inicio = self.nuevo()

        if tipo == "eps":
            fin = self.nuevo()
            self.arista(inicio, EPSILON, fin)
        elif tipo in ("chars", "comp"):
            fin = self.nuevo()

            if tipo == "chars":
                simbolos = nodo[1]
            else:
                simbolos = self.universo - nodo[1]

            for simbolo in simbolos:
                self.arista(inicio, simbolo, fin)
        elif tipo == "alt":
            ramas = [self.construir(r) for r in nodo[1]]
            fin = self.nuevo()

            for r_ini, r_fin in ramas:
                self.arista(inicio, EPSILON, r_ini)
                self.arista(r_fin, EPSILON, fin)
        else:  # star, plus, opt
            sub_ini, sub_fin = self.construir(nodo[1])
            fin = self.nuevo()
            self.arista(inicio, EPSILON, sub_ini)
            self.arista(sub_fin, EPSILON, fin)

            if tipo in ("star", "plus"):
                self.arista(sub_fin, EPSILON, sub_ini)

            if tipo in ("star", "opt"):
                self.arista(inicio, EPSILON, fin)

        return inicio, fin


def afn_desde_ast(ast, extra):
    universo = BASE_ALFABETO | frozenset(extra)
    constructor = ConstructorThompson(universo)
    inicio, fin = constructor.construir(ast)
    trans = constructor.trans

    # Renumerar q0, q1, ... en orden de descubrimiento (BFS)
    ady = {}

    for (origen, _), destinos in trans.items():
        ady.setdefault(origen, set()).update(destinos)

    orden = {inicio: "q0"}
    cola = deque([inicio])

    while cola:
        actual = cola.popleft()

        for destino in sorted(ady.get(actual, ()), key=clave_natural):
            if destino not in orden:
                orden[destino] = f"q{len(orden)}"
                cola.append(destino)

    nuevas = {}

    for (origen, simbolo), destinos in trans.items():
        nuevas[(orden[origen], simbolo)] = {orden[d] for d in destinos}

    alfabeto = {s for (_, s) in nuevas if s != EPSILON}

    return Automata(
        "AFN",
        set(orden.values()),
        alfabeto,
        "q0",
        {orden[fin]},
        nuevas,
        comodin_otros=True,
        universo=universo
    )


def afn_a_afd(afn):
    """Construcción de subconjuntos (el AFD resultante es parcial:
    no incluye el estado de error)."""
    por_origen = {}

    for (origen, simbolo), destinos in afn.transiciones.items():
        if simbolo != EPSILON:
            por_origen.setdefault(origen, {})[simbolo] = destinos

    inicial = frozenset(afn.epsilon_closure({afn.inicial}))
    nombres = {inicial: "q0"}
    cola = deque([inicial])
    trans = {}

    while cola:
        conjunto = cola.popleft()
        movimientos = {}

        for estado in conjunto:
            for simbolo, destinos in por_origen.get(estado, {}).items():
                movimientos.setdefault(simbolo, set()).update(destinos)

        for simbolo in sorted(movimientos):
            destino = frozenset(
                afn.epsilon_closure(movimientos[simbolo])
            )

            if destino not in nombres:
                if len(nombres) >= MAX_ESTADOS_CONSTRUCCION:
                    raise ErrorRegex(
                        "El AFD resultante es demasiado grande."
                    )

                nombres[destino] = f"q{len(nombres)}"
                cola.append(destino)

            trans[(nombres[conjunto], simbolo)] = {nombres[destino]}

    finales = {
        nombre
        for conjunto, nombre in nombres.items()
        if conjunto & afn.finales
    }

    return Automata(
        "AFD",
        set(nombres.values()),
        set(afn.alfabeto),
        "q0",
        finales,
        trans,
        comodin_otros=afn.comodin_otros,
        universo=afn.universo
    )


def construir_desde_regex(texto, tipo="AFN", contiene=False):
    """Regex -> Automata. Con contiene=True el patrón puede aparecer en
    cualquier parte de la cadena (Σ* · regex · Σ*)."""
    parser = ParserRegex(texto)
    ast = parser.parsear()

    if contiene:
        cualquiera = ("star", ("comp", frozenset()))
        ast = ("cat", [cualquiera, ast, cualquiera])

    afn = afn_desde_ast(ast, parser.extra)

    return afn if tipo == "AFN" else afn_a_afd(afn)


def envolver_contiene(automata):
    """Devuelve un AFN que acepta las cadenas que CONTIENEN alguna
    cadena del lenguaje del autómata dado."""
    inicio = "_inicio"
    fin = "_fin"

    while inicio in automata.estados:
        inicio += "_"

    while fin in automata.estados:
        fin += "_"

    trans = {k: set(v) for k, v in automata.transiciones.items()}
    simbolos = set(automata.alfabeto) | {OTRO}

    if automata.universo is not None:
        simbolos |= set(automata.universo)

    for simbolo in simbolos:
        trans.setdefault((inicio, simbolo), set()).add(inicio)
        trans.setdefault((fin, simbolo), set()).add(fin)

    trans.setdefault((inicio, EPSILON), set()).add(automata.inicial)

    for final in automata.finales:
        trans.setdefault((final, EPSILON), set()).add(fin)

    return Automata(
        "AFN",
        set(automata.estados) | {inicio, fin},
        simbolos,
        inicio,
        {fin},
        trans,
        comodin_otros=True,
        universo=automata.universo
    )


# ----------------------------------------------------------------------
# Datos de apoyo para el validador de logs
# ----------------------------------------------------------------------
PRESETS_LOGS = {
    "Línea completa: fecha, nivel y mensaje": (
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} "
        r"\[(INFO|WARN|ERROR|DEBUG)\] .+",
        "completa"
    ),
    "Contiene fecha y hora ISO": (
        r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",
        "contiene"
    ),
    "Contiene nivel de severidad": (
        r"\[(INFO|WARN|ERROR|DEBUG)\]",
        "contiene"
    ),
    "Contiene ERROR o FATAL": (r"(ERROR|FATAL)", "contiene"),
    "Contiene dirección IPv4 (formato)": (
        r"\d{1,3}(\.\d{1,3}){3}",
        "contiene"
    ),
    "Contiene correo electrónico": (
        r"[\w.]+@[\w.]+\.[a-z]{2,}",
        "contiene"
    ),
}

LOGS_EJEMPLO = (
    "2026-10-25 10:15:32 [INFO] Servidor iniciado en el puerto 8080\n"
    "2026-10-25 10:15:40 [ERROR] No se pudo conectar a la base de datos\n"
    "2026-10-25 10:16:02 [WARN] Memoria al 85%\n"
    "2026-10-25 10:16:10 [TRACE] Nivel no reconocido\n"
    "25/10/2026 10:17:00 INFO formato de fecha incorrecto\n"
    "2026-10-25 10:17:30 [DEBUG] Usuario 192.168.1.15 inició sesión\n"
    "2026-10-25 10:18:01 [INFO] Reporte enviado a admin@ejemplo.com\n"
)


# ----------------------------------------------------------------------
# Interfaz gráfica
# ----------------------------------------------------------------------
class Aplicacion(tk.Tk):
    RADIO_ESTADO = 26

    def __init__(self):
        super().__init__()

        self.title("Simulador de Autómatas - Entrega 2 (integrada)")
        self.geometry("1320x820")
        self.minsize(1100, 700)

        self.automata = None
        self.origen_automata = None  # ("regex", texto, tipo) o ("manual",)
        self.resultados_logs = []

        self.crear_interfaz()

    # -- estructura general --------------------------------------------
    def crear_interfaz(self):
        ttk.Label(
            self,
            text="Simulador de Autómatas",
            font=("Arial", 22, "bold")
        ).pack(pady=(10, 0))

        ttk.Label(
            self,
            text=(
                "AFN / AFD  ·  Expresiones regulares  ·  "
                "Validación de logs"
            ),
            font=("Arial", 11)
        ).pack()

        contenedor = ttk.Frame(self)
        contenedor.pack(fill="both", expand=True, padx=15, pady=12)

        self.nb_izq = ttk.Notebook(contenedor)
        self.nb_izq.pack(side="left", fill="y", padx=(0, 10))

        tab_manual = ttk.Frame(self.nb_izq)
        tab_regex = ttk.Frame(self.nb_izq)
        tab_logs = ttk.Frame(self.nb_izq)

        self.nb_izq.add(tab_manual, text="1. Autómata")
        self.nb_izq.add(tab_regex, text="2. Regex")
        self.nb_izq.add(tab_logs, text="3. Logs")

        panel_der = ttk.Frame(contenedor)
        panel_der.pack(side="right", fill="both", expand=True)

        self.nb_der = ttk.Notebook(panel_der)
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
        ).pack(padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estados separados por coma:").pack(
            anchor="w", padx=10
        )
        self.estados_entry = ttk.Entry(panel, width=34)
        self.estados_entry.insert(0, "q0,q1,q2")
        self.estados_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(panel, text="Alfabeto (un carácter por símbolo):").pack(
            anchor="w", padx=10
        )
        self.alfabeto_entry = ttk.Entry(panel, width=34)
        self.alfabeto_entry.insert(0, "a,b")
        self.alfabeto_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estado inicial:").pack(anchor="w", padx=10)
        self.inicial_entry = ttk.Entry(panel, width=34)
        self.inicial_entry.insert(0, "q0")
        self.inicial_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(panel, text="Estados finales separados por coma:").pack(
            anchor="w", padx=10
        )
        self.finales_entry = ttk.Entry(panel, width=34)
        self.finales_entry.insert(0, "q2")
        self.finales_entry.pack(padx=10, pady=(0, 8))

        ttk.Label(panel, text="Transiciones:").pack(anchor="w", padx=10)

        ttk.Label(
            panel,
            text=(
                "Formato: estado,símbolo,destino\n"
                "Ejemplo: q0,a,q1\n"
                "Múltiples destinos: q0,a,q1|q2\n"
                "Epsilon: q0,ε,q1  (o q0,eps,q1)"
            ),
            foreground="#555555"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        self.transiciones_text = tk.Text(panel, width=34, height=9)
        self.transiciones_text.insert(
            "1.0", "q0,a,q1\nq1,b,q2\nq0,ε,q1"
        )
        self.transiciones_text.pack(padx=10, pady=(0, 10))

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
        self.cadena_entry.pack(padx=10, pady=(0, 6))

        ttk.Button(
            panel, text="Simular cadena", command=self.simular_cadena
        ).pack(fill="x", padx=10, pady=2)

        self.resultado_label = ttk.Label(
            panel,
            text="Resultado: pendiente",
            font=("Arial", 12, "bold")
        )
        self.resultado_label.pack(pady=10)

    # -- pestaña 2: regex --------------------------------------------------
    def crear_panel_regex(self, panel):
        ttk.Label(panel, text="Expresión regular:").pack(
            anchor="w", padx=10, pady=(10, 2)
        )

        self.regex_entry = ttk.Entry(
            panel, width=38, font=("Consolas", 11)
        )
        self.regex_entry.insert(0, "(a|b)*abb")
        self.regex_entry.pack(padx=10, pady=(0, 6))

        ttk.Label(
            panel,
            text=(
                "Operadores:  |  *  +  ?  ( )  .  {n,m}\n"
                "Clases:  [a-z]  [^0-9]    Atajos:  \\d \\w \\s\n"
                "Escape:  \\.  \\|  \\*   Vacío:  ε"
            ),
            foreground="#555555"
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
        self.regex_cadena.pack(padx=10, pady=(0, 6))

        ttk.Button(
            panel,
            text="Validar cadena",
            command=self.validar_con_regex
        ).pack(fill="x", padx=10, pady=2)

        self.regex_resultado = ttk.Label(
            panel,
            text="Resultado: pendiente",
            font=("Arial", 12, "bold")
        )
        self.regex_resultado.pack(pady=10)

        ttk.Label(
            panel,
            text=(
                "El autómata generado queda activo: también puede\n"
                "simularse desde la pestaña 1 y usarse en Logs."
            ),
            foreground="#555555"
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
            text="Autómata activo (Entrega 1 / pestaña Regex)",
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
        combo.pack(padx=10, pady=(0, 6))
        combo.bind("<<ComboboxSelected>>", self.aplicar_preset)

        ttk.Label(panel, text="Regex para los logs:").pack(
            anchor="w", padx=10
        )

        self.regex_logs_entry = ttk.Entry(
            panel, width=38, font=("Consolas", 10)
        )
        self.regex_logs_entry.insert(
            0, PRESETS_LOGS["Línea completa: fecha, nivel y mensaje"][0]
        )
        self.regex_logs_entry.pack(padx=10, pady=(0, 8))

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

        self.resumen_logs = ttk.Label(
            panel,
            text="Sin validar",
            font=("Arial", 11, "bold"),
            wraplength=300
        )
        self.resumen_logs.pack(padx=10, pady=12, anchor="w")

    # -- áreas de la derecha ------------------------------------------------
    def crear_area_visual(self, panel):
        marco = ttk.LabelFrame(panel, text="Representación gráfica")
        marco.pack(fill="both", expand=True, padx=4, pady=4)

        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(marco, background="white")
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
            text=(
                "Cree un autómata (pestaña 1) o genere uno "
                "desde una regex (pestaña 2)."
            )
        )
        self.info_label.pack(pady=4)

        marco_detalle = ttk.LabelFrame(panel, text="Detalle y traza")
        marco_detalle.pack(fill="x", padx=4, pady=(0, 4))

        self.detalle = tk.Text(
            marco_detalle,
            height=11,
            font=("Consolas", 10),
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
            entrada, height=9, font=("Consolas", 10), wrap="none"
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
            "ok", background="#e6f4ea", foreground="#1e6b32"
        )
        self.tabla_logs.tag_configure(
            "mal", background="#fdecea", foreground="#a61b1b"
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

        aceptada, pasos = self.automata.procesar(cadena)

        texto = "CADENA ACEPTADA" if aceptada else "CADENA RECHAZADA"
        color = "green" if aceptada else "red"

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
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{error}")
            return

        self.logs_texto.delete("1.0", tk.END)
        self.logs_texto.insert("1.0", contenido)
        self.nb_der.select(self.tab_resultados)

    def obtener_automata_logs(self):
        contiene = self.modo_logs.get() == "contiene"

        if self.fuente_logs.get() == "actual":
            if self.automata is None:
                messagebox.showwarning(
                    "Advertencia",
                    "No hay un autómata activo. Cree uno o use una regex."
                )
                return None

            if contiene:
                return envolver_contiene(self.automata)

            return self.automata

        try:
            # El AFD es mucho más rápido para archivos grandes.
            return construir_desde_regex(
                self.regex_logs_entry.get(), "AFD", contiene
            )
        except ErrorRegex as error:
            messagebox.showerror("Expresión regular inválida", str(error))
            return None

    def validar_logs(self):
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

        self.config(cursor="watch")
        self.update_idletasks()

        resultados = []

        for numero, linea in enumerate(lineas, start=1):
            if self.ignorar_vacias.get() and not linea.strip():
                continue

            resultados.append((numero, automata.simular(linea), linea))

            if numero % 2000 == 0:
                self.update_idletasks()

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
            foreground="green" if invalidas == 0 else "#a61b1b"
        )

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
            messagebox.showerror("Error", f"No se pudo guardar:\n{error}")
            return

        messagebox.showinfo("Listo", "Resultados exportados correctamente.")

    # ------------------------------------------------------------------
    # Mostrar autómata activo
    # ------------------------------------------------------------------
    def mostrar_automata(self, automata, mensaje):
        self.automata = automata
        self.nb_der.select(self.tab_grafico)
        self.dibujar_automata()
        self.escribir_detalle(self.describir_automata(automata))
        self.info_label.config(text=mensaje)

        for etiqueta in (self.resultado_label, self.regex_resultado):
            etiqueta.config(text="Resultado: pendiente", foreground="black")

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
                font=("Arial", 12)
            )
            return

        # --- posiciones por capas (BFS desde el estado inicial) -------
        capas = self.calcular_capas(estados)
        por_capa = {}

        for estado in estados:
            por_capa.setdefault(capas[estado], []).append(estado)

        paso_x, paso_y, margen = 125, 90, 80
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
                    outline="#333333", width=2
                )
                canvas.create_line(
                    x + 14, y - radio - 10, x + 11, y - radio + 1,
                    fill="#333333", width=2, arrow=tk.LAST,
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
                smooth=True, fill="#555555", width=2, arrow=tk.LAST
            )

            lado = -1 if curva < 0 else 1
            etiquetas.append((
                (sx + 2 * cx + ex) / 4 + nx * 12 * lado,
                (sy + 2 * cy + ey) / 4 + ny * 12 * lado,
                texto
            ))

        for x, y, texto in etiquetas:
            id_texto = canvas.create_text(
                x, y, text=texto, fill="#0b3d91", font=("Arial", 9, "bold")
            )
            caja = canvas.bbox(id_texto)
            fondo = canvas.create_rectangle(
                caja[0] - 2, caja[1], caja[2] + 2, caja[3],
                fill="white", outline=""
            )
            canvas.tag_lower(fondo, id_texto)

        # --- estados ------------------------------------------------------
        for estado, (x, y) in posiciones.items():
            relleno = "#ffe08a" if estado in resaltar else "#d9edf7"

            canvas.create_oval(
                x - radio, y - radio, x + radio, y + radio,
                fill=relleno, outline="#1f4e79", width=2
            )

            if estado in automata.finales:
                canvas.create_oval(
                    x - radio + 5, y - radio + 5,
                    x + radio - 5, y + radio - 5,
                    outline="#1f4e79", width=2
                )

            canvas.create_text(
                x, y, text=estado, font=("Arial", 10, "bold")
            )

            if estado == automata.inicial:
                canvas.create_line(
                    x - radio - 42, y, x - radio - 2, y,
                    fill="green", width=2, arrow=tk.LAST
                )
                canvas.create_text(
                    x - radio - 42, y - 12, text="inicio", fill="green"
                )


if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()
