from collections import deque
from automata import Automata
from configuracion import BASE_ALFABETO, DIGITOS, ESPACIOS, MAX_ESTADOS_CONSTRUCCION, OTRO, PALABRA, EPSILON
from utilidades import clave_natural

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


