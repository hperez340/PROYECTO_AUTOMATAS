import re
from configuracion import EPSILON, OTRO

def mezclar(color_a, color_b, t):
    """Mezcla dos colores #RRGGBB; t = 0 da color_a y t = 1 da color_b."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(
        round(x + (y - x) * t) for x, y in zip(a, b)
    )


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
