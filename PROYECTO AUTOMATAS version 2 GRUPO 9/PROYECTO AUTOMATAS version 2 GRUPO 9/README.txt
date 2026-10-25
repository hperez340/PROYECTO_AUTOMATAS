PROYECTO AUTÓMATAS - VERSION 2

ARCHIVO QUE DEBE EJECUTAR
=========================

main.py

Desde PowerShell o CMD desde la carpeta ingresar:

py main.py

o:

python main.py



ALFABETO
========

Puede ingresar:

a,b,c,0,1

También:

abc01

O:

a b c 0 1

Cada símbolo debe ser un solo carácter.


EJEMPLO PARA PROBAR MANUALMENTE
===============================

Tipo:
AFD

Estados:
q0,q1

Alfabeto:
0,1

Inicial:
q0

Finales:
q1

Lenguaje:
Cadenas binarias que terminan en 1.

Transiciones:

q0,0,q0
q0,1,q1
q1,0,q0
q1,1,q1

Cadena:
0001

Resultado:
ACEPTADA


EJEMPLO CON LETRAS Y NÚMEROS
============================

Tipo:
AFD

Estados:
q0,q1

Alfabeto:
a,b,0,1

Inicial:
q0

Finales:
q1

Transiciones:

q0,a,q1
q0,b,q0
q0,0,q0
q0,1,q0
q1,a,q1
q1,b,q1
q1,0,q1
q1,1,q1

Cadena:
00ba1

Resultado:
ACEPTADA




