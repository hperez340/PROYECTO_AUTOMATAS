from automata import Automata


def separar_csv(texto):
    return [x.strip() for x in texto.split(",") if x.strip()]


def parsear_alfabeto(texto):
    """
    Formatos aceptados:
    a,b,c,0,1
    a b c 0 1
    abc01
    """
    texto = texto.strip()

    if not texto:
        return set()

    if "," in texto:
        simbolos = [x.strip() for x in texto.split(",") if x.strip()]
    elif " " in texto:
        simbolos = [x.strip() for x in texto.split() if x.strip()]
    else:
        simbolos = list(texto)

    return set(simbolos)


def parsear_transiciones(texto, tipo):
    transiciones = {}

    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()

        if not linea:
            continue

        partes = [x.strip() for x in linea.split(",")]

        if len(partes) < 3:
            raise ValueError(
                f"Línea {numero}: use el formato origen,símbolo,destino."
            )

        origen = partes[0]
        simbolo = partes[1]
        destinos = {x for x in partes[2:] if x}

        if not origen or not simbolo or not destinos:
            raise ValueError(f"Línea {numero}: hay datos incompletos.")

        clave = (origen, simbolo)

        if tipo.upper() == "AFD" and clave in transiciones:
            raise ValueError(
                f"Línea {numero}: ya existe una transición para "
                f"({origen}, {simbolo})."
            )

        if tipo.upper() == "AFD" and len(destinos) != 1:
            raise ValueError(
                f"Línea {numero}: un AFD debe tener un único destino."
            )

        transiciones.setdefault(clave, set()).update(destinos)

    return transiciones


def crear_automata_desde_campos(
    tipo,
    estados_txt,
    alfabeto_txt,
    inicial_txt,
    finales_txt,
    transiciones_txt,
    lenguaje_txt=""
):
    automata = Automata(
        tipo=tipo,
        estados=set(separar_csv(estados_txt)),
        alfabeto=parsear_alfabeto(alfabeto_txt),
        inicial=inicial_txt.strip(),
        finales=set(separar_csv(finales_txt)),
        transiciones=parsear_transiciones(transiciones_txt, tipo),
        lenguaje=lenguaje_txt.strip()
    )

    errores = automata.validar_definicion()

    if errores:
        raise ValueError("\n".join(f"• {error}" for error in errores))

    return automata
