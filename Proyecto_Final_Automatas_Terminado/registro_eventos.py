"""Registro local y consultable de acciones y validaciones."""

import csv
from datetime import datetime
from pathlib import Path


DIRECTORIO_DATOS = Path.home() / "Documents" / "SimuladorAutomatas"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def crear_ruta_sesion(directorio=DIRECTORIO_DATOS):
    """Genera un nombre de archivo único usando la fecha y hora de inicio."""
    directorio = Path(directorio)
    momento = datetime.now()
    base = momento.strftime("logs_%Y-%m-%d_%H-%M-%S")
    candidato = directorio / f"{base}.csv"
    sufijo = 2
    while candidato.exists():
        candidato = directorio / f"{base}_{sufijo}.csv"
        sufijo += 1
    return candidato


class RegistroEventos:
    """Guarda eventos persistentes y ofrece una lectura para la interfaz."""

    def __init__(self, archivo=None):
        self.archivo = Path(archivo) if archivo is not None else crear_ruta_sesion()
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        with self.archivo.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f, quoting=csv.QUOTE_ALL).writerow(
                ["fecha", "hora", "nivel", "modulo", "accion", "resultado", "detalle"]
            )

    def registrar(self, modulo, accion, resultado="INFO", detalle=""):
        ahora = datetime.now()
        fila = [
            ahora.strftime("%Y-%m-%d"),
            ahora.strftime("%H:%M:%S"),
            str(resultado).upper(),
            str(modulo),
            str(accion),
            str(resultado),
            str(detalle).replace("\r", " ").replace("\n", " "),
        ]
        with self.archivo.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f, quoting=csv.QUOTE_ALL).writerow(fila)

    def cerrar_sesion(self):
        """Registra el cierre; cada escritura ya queda cerrada y guardada."""
        self.registrar(
            "__main__",
            "Cierre del Simulador de Autómatas",
            "INFO",
            "Registro de sesión guardado automáticamente",
        )

    def leer(self, buscar="", nivel="TODOS", limite=5000):
        filas = []
        if not self.archivo.exists():
            return filas
        with self.archivo.open("r", newline="", encoding="utf-8") as f:
            for fila in csv.reader(f):
                if len(fila) != 7 or fila[0] == "fecha":
                    continue
                fecha, hora, tipo, modulo, accion, resultado, detalle = fila
                if nivel != "TODOS" and tipo != nivel:
                    continue
                contenido = " ".join(fila).casefold()
                if buscar.casefold() not in contenido:
                    continue
                filas.append((fecha, hora, tipo, modulo, accion, resultado, detalle))
        return filas[-limite:]

    def validar_formato(self):
        errores = []
        with self.archivo.open("r", newline="", encoding="utf-8") as f:
            for numero, fila in enumerate(csv.reader(f), start=1):
                if numero == 1:
                    continue
                if len(fila) != 7:
                    errores.append(numero)
                    continue
                try:
                    datetime.strptime(f"{fila[0]} {fila[1]}", FORMATO_FECHA)
                except ValueError:
                    errores.append(numero)
        return errores
