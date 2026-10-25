from collections import deque

EPSILON = "ε"


class Automata:
    def __init__(self, tipo, estados, alfabeto, inicial, finales, transiciones, lenguaje=""):
        self.tipo = tipo.upper()
        self.estados = set(estados)
        self.alfabeto = set(alfabeto)
        self.inicial = inicial
        self.finales = set(finales)
        self.transiciones = transiciones
        self.lenguaje = lenguaje

    def validar_definicion(self):
        errores = []

        if self.tipo not in {"AFD", "AFN"}:
            errores.append("El tipo debe ser AFD o AFN.")

        if not self.estados:
            errores.append("Debe ingresar al menos un estado.")

        if not self.alfabeto:
            errores.append("Debe ingresar al menos un símbolo en el alfabeto.")

        if self.inicial not in self.estados:
            errores.append("El estado inicial no pertenece al conjunto de estados.")

        if not self.finales:
            errores.append("Debe ingresar al menos un estado final.")
        elif not self.finales.issubset(self.estados):
            errores.append("Todos los estados finales deben pertenecer al conjunto de estados.")

        for simbolo in self.alfabeto:
            if simbolo == EPSILON:
                errores.append("ε no debe escribirse dentro del alfabeto.")
            if len(simbolo) != 1:
                errores.append(
                    f"El símbolo '{simbolo}' debe ser de un solo carácter. "
                    "Ejemplos válidos: a, b, c, 0, 1."
                )

        for (origen, simbolo), destinos in self.transiciones.items():
            if origen not in self.estados:
                errores.append(f"El estado origen '{origen}' no existe.")

            if simbolo != EPSILON and simbolo not in self.alfabeto:
                errores.append(
                    f"El símbolo '{simbolo}' usado en una transición no pertenece al alfabeto."
                )

            if self.tipo == "AFD" and simbolo == EPSILON:
                errores.append("Un AFD no puede tener transiciones ε.")

            if self.tipo == "AFD" and len(destinos) != 1:
                errores.append(
                    f"En un AFD, ({origen}, {simbolo}) debe tener exactamente un destino."
                )

            for destino in destinos:
                if destino not in self.estados:
                    errores.append(f"El estado destino '{destino}' no existe.")

        return errores

    def epsilon_closure(self, estados):
        cierre = set(estados)
        cola = deque(estados)

        while cola:
            estado = cola.popleft()
            for siguiente in self.transiciones.get((estado, EPSILON), set()):
                if siguiente not in cierre:
                    cierre.add(siguiente)
                    cola.append(siguiente)

        return cierre

    def mover(self, estados, simbolo):
        siguientes = set()
        for estado in estados:
            siguientes.update(self.transiciones.get((estado, simbolo), set()))
        return siguientes

    def simular(self, cadena):
        for posicion, simbolo in enumerate(cadena, start=1):
            if simbolo not in self.alfabeto:
                return False, [{
                    "indice": posicion,
                    "simbolo": simbolo,
                    "antes": set(),
                    "despues": set(),
                    "mensaje": (
                        f"Símbolo inválido en la posición {posicion}: "
                        f"'{simbolo}' no pertenece al alfabeto."
                    )
                }], set()

        if self.tipo == "AFD":
            return self._simular_afd(cadena)

        return self._simular_afn(cadena)

    def _simular_afd(self, cadena):
        actual = self.inicial
        pasos = [{
            "indice": 0,
            "simbolo": "INICIO",
            "antes": {actual},
            "despues": {actual},
            "mensaje": f"La simulación comienza en el estado {actual}."
        }]

        for i, simbolo in enumerate(cadena, start=1):
            destinos = self.transiciones.get((actual, simbolo), set())

            if not destinos:
                pasos.append({
                    "indice": i,
                    "simbolo": simbolo,
                    "antes": {actual},
                    "despues": set(),
                    "mensaje": (
                        f"No existe transición desde {actual} usando '{simbolo}'. "
                        "La cadena se rechaza."
                    )
                })
                return False, pasos, set()

            siguiente = next(iter(destinos))

            pasos.append({
                "indice": i,
                "simbolo": simbolo,
                "antes": {actual},
                "despues": {siguiente},
                "mensaje": f"{actual} --{simbolo}--> {siguiente}"
            })

            actual = siguiente

        aceptada = actual in self.finales
        return aceptada, pasos, {actual}

    def _simular_afn(self, cadena):
        actuales = self.epsilon_closure({self.inicial})

        pasos = [{
            "indice": 0,
            "simbolo": "INICIO",
            "antes": {self.inicial},
            "despues": set(actuales),
            "mensaje": (
                f"Inicio en {self.inicial}. "
                f"Cierre-ε inicial = {self._fmt(actuales)}"
            )
        }]

        for i, simbolo in enumerate(cadena, start=1):
            antes = set(actuales)
            movidos = self.mover(actuales, simbolo)
            actuales = self.epsilon_closure(movidos)

            pasos.append({
                "indice": i,
                "simbolo": simbolo,
                "antes": antes,
                "despues": set(actuales),
                "mensaje": (
                    f"{self._fmt(antes)} --{simbolo}--> "
                    f"{self._fmt(movidos)}; "
                    f"cierre-ε = {self._fmt(actuales)}"
                )
            })

            if not actuales:
                break

        aceptada = bool(actuales & self.finales)
        return aceptada, pasos, actuales

    def convertir_afn_a_afd(self):
        if self.tipo != "AFN":
            raise ValueError("La conversión AFN → AFD solamente puede hacerse desde un AFN.")

        inicial_conjunto = frozenset(self.epsilon_closure({self.inicial}))
        cola = deque([inicial_conjunto])
        visitados = {inicial_conjunto}
        nombres = {inicial_conjunto: self._nombre_conjunto(inicial_conjunto)}
        nuevas_transiciones = {}

        while cola:
            conjunto_actual = cola.popleft()
            nombre_actual = nombres[conjunto_actual]

            for simbolo in sorted(self.alfabeto):
                movidos = self.mover(set(conjunto_actual), simbolo)
                cierre = frozenset(self.epsilon_closure(movidos))

                if not cierre:
                    continue

                if cierre not in nombres:
                    nombres[cierre] = self._nombre_conjunto(cierre)

                nuevas_transiciones[(nombre_actual, simbolo)] = {nombres[cierre]}

                if cierre not in visitados:
                    visitados.add(cierre)
                    cola.append(cierre)

        nuevos_estados = {nombres[c] for c in visitados}
        nuevos_finales = {
            nombres[c] for c in visitados if set(c) & self.finales
        }

        return Automata(
            "AFD",
            nuevos_estados,
            set(self.alfabeto),
            nombres[inicial_conjunto],
            nuevos_finales,
            nuevas_transiciones,
            self.lenguaje
        )

    def minimizar_afd(self):
        if self.tipo != "AFD":
            raise ValueError("La minimización solamente puede aplicarse a un AFD.")

        alcanzables = self._estados_alcanzables()
        finales = self.finales & alcanzables
        no_finales = alcanzables - finales

        particiones = []
        if finales:
            particiones.append(set(finales))
        if no_finales:
            particiones.append(set(no_finales))

        cambio = True
        while cambio:
            cambio = False
            nuevas = []

            for grupo in particiones:
                firmas = {}

                for estado in grupo:
                    firma = []

                    for simbolo in sorted(self.alfabeto):
                        destinos = self.transiciones.get((estado, simbolo), set())
                        destino = next(iter(destinos), None)
                        firma.append(self._indice_particion(destino, particiones))

                    firmas.setdefault(tuple(firma), set()).add(estado)

                nuevas.extend(firmas.values())

                if len(firmas) > 1:
                    cambio = True

            particiones = nuevas

        nombre_grupo = {}
        for grupo in particiones:
            nombre = "{" + ",".join(sorted(grupo)) + "}"
            for estado in grupo:
                nombre_grupo[estado] = nombre

        nuevas_transiciones = {}

        for grupo in particiones:
            representante = next(iter(grupo))
            origen_nuevo = nombre_grupo[representante]

            for simbolo in self.alfabeto:
                destinos = self.transiciones.get((representante, simbolo), set())
                destino = next(iter(destinos), None)

                if destino is not None and destino in nombre_grupo:
                    nuevas_transiciones[(origen_nuevo, simbolo)] = {
                        nombre_grupo[destino]
                    }

        return Automata(
            "AFD",
            set(nombre_grupo.values()),
            set(self.alfabeto),
            nombre_grupo[self.inicial],
            {nombre_grupo[e] for e in finales},
            nuevas_transiciones,
            self.lenguaje
        )

    def _estados_alcanzables(self):
        vistos = {self.inicial}
        cola = deque([self.inicial])

        while cola:
            estado = cola.popleft()

            for simbolo in self.alfabeto:
                for destino in self.transiciones.get((estado, simbolo), set()):
                    if destino not in vistos:
                        vistos.add(destino)
                        cola.append(destino)

        return vistos

    @staticmethod
    def _indice_particion(estado, particiones):
        if estado is None:
            return -1

        for i, grupo in enumerate(particiones):
            if estado in grupo:
                return i

        return -1

    @staticmethod
    def _nombre_conjunto(conjunto):
        if not conjunto:
            return "∅"
        return "{" + ",".join(sorted(conjunto)) + "}"

    @staticmethod
    def _fmt(estados):
        if not estados:
            return "∅"
        return "{" + ", ".join(sorted(estados)) + "}"

    def como_texto(self):
        lineas = [
            f"Tipo: {self.tipo}",
            f"Estados: {', '.join(sorted(self.estados))}",
            f"Alfabeto: {', '.join(sorted(self.alfabeto))}",
            f"Inicial: {self.inicial}",
            f"Finales: {', '.join(sorted(self.finales))}",
            f"Lenguaje: {self.lenguaje or '(sin descripción)'}",
            "",
            "Transiciones:"
        ]

        for (origen, simbolo), destinos in sorted(self.transiciones.items()):
            lineas.append(
                f"{origen},{simbolo},{','.join(sorted(destinos))}"
            )

        return "\n".join(lineas)
