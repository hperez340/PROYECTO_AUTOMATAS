from collections import deque
from utilidades import clave_natural, mostrar_simbolo
from configuracion import EPSILON, OTRO

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
