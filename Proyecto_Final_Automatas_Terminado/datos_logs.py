# Datos de apoyo para el validador de logs

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

