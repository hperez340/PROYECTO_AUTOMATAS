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
