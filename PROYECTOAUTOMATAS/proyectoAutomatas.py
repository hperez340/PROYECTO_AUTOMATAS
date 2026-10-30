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
import random
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
# Tema visual: paleta azul profundo con texto blanco
# ----------------------------------------------------------------------
C_FONDO = "#0B2B4C"        # fondo general
C_OSCURO = "#071E37"       # campos, lienzo y tablas
C_TARJETA = "#123B64"      # pestañas inactivas y encabezados
C_BOTON = "#1B568A"
C_TARJETA_FONDO = "#0E3257"   # fondo de las tarjetas del menú
C_TARJETA_HOVER = "#154273"
C_ICONO = "#7DB9EC"
C_BOTON_HOVER = "#2570AC"
C_ACENTO = "#4DA3E0"
C_BORDE = "#2F6FA8"
C_TEXTO = "#FFFFFF"
C_SUAVE = "#BBD3E8"        # texto secundario
C_OK = "#7DDBA3"
C_MAL = "#FF9FA8"
C_OK_FONDO = "#0E4A44"
C_MAL_FONDO = "#5A2233"

FUENTE_UI = "Segoe UI"
FUENTE_TITULO = "Georgia"
FUENTE_MONO = "Consolas"

# Datos que se muestran en la pantalla principal
UNIVERSIDAD_1 = "UNIVERSIDAD"
UNIVERSIDAD_2 = "Mariano Gálvez"
TITULO_PROYECTO = "Proyecto final autómatas"
SUBTITULO = "AFN  ·  AFD  ·  EXPRESIONES REGULARES  ·  VALIDACIÓN DE LOGS"
FUNCIONES = {
    "afd": {
        "titulo": "AFN / AFD",
        "subtitulo": "CREAR  ·  VISUALIZAR  ·  CONVERTIR  ·  SIMULAR",
        "descripcion": "Crea, visualiza, convierte y simula autómatas finitos.",
        "ayuda": "Configure el autómata a la izquierda y pulse «Crear autómata».",
        "izq": 0, "der": 0,
    },
    "regex": {
        "titulo": "Expresiones Regulares",
        "subtitulo": "GENERAR AUTÓMATA  ·  VALIDAR CADENAS",
        "descripcion": "Genera el autómata de una expresión y comprueba cadenas.",
        "ayuda": "Escriba una expresión regular y pulse «Generar autómata».",
        "izq": 1, "der": 0,
    },
    "logs": {
        "titulo": "Validación de Logs",
        "subtitulo": "VALIDAR REGISTROS LÍNEA POR LÍNEA",
        "descripcion": "Valida registros línea por línea y exporta los resultados.",
        "ayuda": "",
        "izq": 2, "der": 1,
    },
}

CURSO = ""          # opcional, p. ej. "Autómatas y Lenguajes Formales"
INTEGRANTES = ""    # opcional, p. ej. "Nombre Apellido · Carné 0000-00-0000"


def mezclar(color_a, color_b, t):
    """Mezcla dos colores #RRGGBB; t = 0 da color_a y t = 1 da color_b."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(
        round(x + (y - x) * t) for x, y in zip(a, b)
    )


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
            foreground=C_OK if invalidas == 0 else C_TEXTO
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
# Recursos incrustados: escudo de la Universidad Mariano Gálvez (PNG)
# ----------------------------------------------------------------------
LOGO_CABECERA_B64 = """
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
c9FolBdffBHLsnj1lRcJZuVSGNRYXf09UnubKdyog20hDxFg4vv345s6lXR/P+bgIKiqVCWiq0LEI2XqT/6p5qwjbOrfzLqt
fINcZu9JmaaS1oysbHzTphPe9Dnpzs6hRtBDJ6giVXqnK4TLBVMX/De+4fPJCHp54onHGTmynJaWFhYvXnyE79XS0kJ3dzdF
RUX09fXhcrlobW1F0zRKS0uJx+PE4/Ej6unz+SgqKsKyLMLhMH6/H1VVWblyJSUlJWRmZrJ3714e+tOfqKysxLYtLvjGt/DY
vWx+92ck9zZT+ImBiKWRhyrl0rYRmkZg9mwSzc3EG/ahSoelVhpqwwz1p4tvXHfHVzVqia8cq1BVpfRXNyoFt+qrSj+2jksO
WJYUlmpHYyguF0LXQdogFBBgRyKINITmBuivSDNh9jWUzbiCDz5ayfvvvoWqatzz61+zYsUKJk2aREFBwZd+sK2tDSEEhYWF
AMRiMSxrKBt7+NHn832p+g0QiUTo6+vjnXfeYcWKFYwbP47srByuuvq79DeuYstHdyD29FKw3QOxFFL9H6k8KbGiUYTDQFEM
yxFU1aZ52qr25alFGUvK7CU1fzu24St54mOrasUPT2i3zvpu6Vrb4hJfi+2yFSFVt1ugKIfa0JQhfyWVwjd9Ou5xlSiftKAn
NBoj6+jr2sG8ExdTVjmN42bNJDQ4wG9++1v6+vrYtWsX/f39ZGRkYBgGgUDgCCBSSgzDwOFwYBgGTqcTh8NxJAgfHBwkGo3y
ySefUFpaSk1NNS6XE1XVOOPs8znntJPYs+Zetq28F98+QeG+TFIHD4JDQ9H0/+FXClSXC6GotoZQumZogz3HOs68YvwnPWOr
asVXNWd9JWCrVyOrq6vUCy9c0XPa5cP3OREXuJos21KlEHKoZUNaJkLXqbj/AQq+9S3SgwM4Rg7HfHcTvkE3/bKVPfWvUZSb
xYiKGURTgsrKMbS3tdLU3MSnn26kpaWF9vZ2BgYG6Orqoqenh/z8fOrr60mn00QiEVRVpa6ujtbWVvbs2cNjjz5KLB7n0Ucf
Yeqxx+JwuPD6s7jk4gsxYrtY9+ZP6d62lvytTgK1JhVPPo67cgzhjZ9j9vejOJ0c2fShbk2pJ5GRGYbSOUH9xjcv+3hddXWV
etiN+Kf7JWtqaodAu2xF7amXlsR9prLIaDUtSxdCEYqwIlHK776HwJw57Dr/PNofe5TArOPI/uaFDL78Dt59aZSkZH/POvY3
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
"""

LOGO_PORTADA_B64 = """
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
+3vJJJZtY5km2WyWSDTq13+5rl+7tc819j3/H7NYPvN3tezm9fu+hudmEdKg9MU0VotGW3woL3zaZ/RZh6tV13Fh2Vagnhqw
NTd38t3vu/vVD+2bM/3UNzkP2feOvd5XDuzflM7jzECbNq1WBeZncLIQ6O7aHXI5VCaD9rzeTtkeGAcbPDL9LUQ8QvOOFYTi
5RT0HY1WHolkkkQiwSGHHMKkSZPYuHEjpaWlDB48mFGjRnHggQdywgknMH36dGbMmMFLL73Eww8/zNSpU7nkkkt4+eWXmTt3
Lg888ADr1q1j4cKFlJWVcf311/OrX/2Kqio/PXT66adTWlrKAw88wMsvv8zAgQP53ve/z4oVKxg9ejTfOP98LNtmx44dLFu2
jPfff5/77ruP2bNnEwqF2LJlC1dffTXHHXcc1dXVzJkzh+OOO65XMrjowgupHDCA3/zmN7S0tHDZ5Zczc+ZM7vzlL7nn3nsp
Kytj06ZN/OCHP6Sjo4OpU6dy8cUXs2jRIo4//ni+893v8te//pWhQ4dSVlbWmw/9LD9IIHBzaZb95Qek2+ogGiLvvQzhfaNA
IdCeh9vRAa7rb6NXyp939WmBmQDhaJ2tNEX7CKPTzIgfzr5txQ49Dzn/9U+mmk933uejNAjW9VvyxOSa57PjAifZNSklPi2D
3D1MwohE6fe97xEdPwG3o4P6+/9I17vvds94UGgDZAaKljs0HG5iheKsfv4WIoWVlA6aTEFBPlOnTmXZsmW8++67DB8+nKOO
Omo/M+G6LlJKVq5cyYIFC1i2bBl33303eXl5fPnLX+bOO+8kFotx3333MW3qVJYuXUpXVxe//MUvuOu3vyUUCnHWWWdxzDHH
8Mc//rE3lK+pqen1w5qam8nPz+8VJsPhMIFAoNdpdhyHjo4OhBCsXLmSjo4O1qxZQ58+fTAMg2HDhzNv3jymTZtGfn4+iUSC
oqIiGpua2LlrF11dXbS2tnLSSSfx+uuvc/TRR9PZ2UlTUxOdnZ3079+f0tJS7rrrLn77299+9oL0blMopOT9p+fTXrMOs7CQ
8OYM8U3eh35V94MvQyH6fuvbRCdMwO3sYO9995FcvRojEvlk5tKgDHRuQkB6Wj1x0lXLlszbJ33zKRLmpx/XzEOIBQs8Oyvn
dRTSmK0yhcjpzyxOqLr1VirOO5/YxIkUzJ7N8Lv/QOSAcX4fopS9UaK1N0v+iizKNhAa3nns/2vvzMOjqu/9//qeZdZkspEA
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
"""

LOGO_ICONO_B64 = """
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
9XznPwHBlWILGtHpZgAAAABJRU5ErkJggg==
"""


if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()
