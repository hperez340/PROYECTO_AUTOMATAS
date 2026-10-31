# Simulador de autómatas

## Ejecución

Ejecuta `python main.py` desde esta carpeta. Requiere Python 3 y Tkinter.

## Validaciones

- En AFN/AFD, define los estados, el alfabeto, estado inicial, finales y transiciones; pulsa **Crear autómata** y luego prueba una cadena con **Simular cadena**.
- En Expresiones Regulares, escribe el patrón, elige AFN o AFD y pulsa **Generar autómata**. Para probar una cadena, escríbela y pulsa **Validar cadena**.
- En Validación de Logs, carga un archivo o pega registros y pulsa **Validar logs**. Cada línea queda marcada como válida o inválida, con resumen y opción de exportar CSV.

## Registro de actividad

La aplicación registra automáticamente inicios, acciones, errores y resultados línea por línea. El registro se guarda en `Documentos/SimuladorAutomatas/logs.csv`. En la pestaña de logs, pulsa **Abrir visor de eventos** para buscar, filtrar, revisar formato y analizar errores. La aplicación revisa el archivo de eventos automáticamente cada tres segundos.

## Módulos

- `main.py`: inicio.
- `interfaz.py`: interfaz y flujo de validación.
- `automata.py`: simulación AFN/AFD.
- `expresiones.py`: parser de regex y conversiones.
- `registro_eventos.py`: persistencia y consulta de actividad.
- `configuracion.py`, `utilidades.py`, `datos_logs.py`, `recursos.py`: configuración y datos auxiliares.
- `original.py`: respaldo del programa integrado.
