# -*- coding: utf-8 -*-
"""Validación de RFC y CURP para la carga de layout.

No existe una API pública gratuita del SAT/RENAPO para verificar en línea
que un RFC o CURP realmente exista en el padrón fiscal/poblacional — por
eso aquí solo se valida la ESTRUCTURA (longitud, caracteres, fecha
coherente), de forma local y sin depender de ningún servicio externo:

- RFC: se valida solo el formato (4 letras + fecha + 3 de homoclave para
  persona física). NO se valida la homoclave ni su dígito verificador,
  porque el SAT los deriva del nombre completo con un algoritmo propio
  (normalización de palabras, acentos, etc. — Anexo 10 de la RMF) que no
  se puede replicar de forma confiable sin arriesgarse a rechazar RFC
  verdaderos por una mala reproducción del algoritmo.
- CURP: se valida el formato oficial completo Y el dígito verificador
  (posición 18), que sí es un algoritmo público y determinista (RENAPO).
  Aun así, un CURP con dígito verificador que no coincide se reporta como
  AVISO (no bloquea la fila) por si hay algún caso límite no cubierto.
"""
import re
from datetime import date

RFC_REGEX = re.compile(r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$')

CURP_REGEX = re.compile(
    r'^[A-Z][AEIOUX][A-Z]{2}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[HM]'
    r'(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QO|QR|SL|SP|SR|TC|TS|TL|VZ|YN|ZS|NE)'
    r'[B-DF-HJ-NP-TV-Z]{3}[A-Z\d]\d$'
)

# Tabla oficial de valores por carácter (0-9, A-Z, Ñ) usada por RENAPO
# para el dígito verificador de la CURP.
_CURP_VALORES = '0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'


def _fecha_coherente(aa, mm, dd):
    """La CURP/RFC no traen el siglo; se asume 1900 salvo que el año de
    2 dígitos sea menor o igual al año actual de 2 dígitos (entonces
    podría ser 2000+), igual que hacen la mayoría de los validadores."""
    hoy = date.today()
    siglo_actual = hoy.year // 100 * 100
    anio = siglo_actual + aa
    if anio > hoy.year:
        anio -= 100
    try:
        date(anio, mm, dd)
        return True
    except ValueError:
        return False


def rfc_formato_valido(rfc):
    """Valida solo estructura (longitud/caracteres/fecha) — no homoclave
    ni dígito verificador. Ver docstring del módulo."""
    rfc = (rfc or '').strip().upper()
    if not RFC_REGEX.match(rfc):
        return False
    aa, mm, dd = int(rfc[-9:-7]), int(rfc[-7:-5]), int(rfc[-5:-3])
    return _fecha_coherente(aa, mm, dd)


def curp_formato_valido(curp):
    """Valida la estructura oficial completa de 18 posiciones."""
    curp = (curp or '').strip().upper()
    if not CURP_REGEX.match(curp):
        return False
    aa, mm, dd = int(curp[4:6]), int(curp[6:8]), int(curp[8:10])
    return _fecha_coherente(aa, mm, dd)


def curp_digito_verificador_valido(curp):
    """True si el dígito verificador (posición 18) coincide con el
    calculado a partir de los primeros 17 caracteres (algoritmo RENAPO:
    suma ponderada con pesos descendentes de 18 a 2, dígito = (10 -
    suma mod 10) mod 10). Asume que curp_formato_valido(curp) ya es True."""
    curp = (curp or '').strip().upper()
    if len(curp) != 18:
        return False
    try:
        total = sum(_CURP_VALORES.index(c) * (18 - i) for i, c in enumerate(curp[:17]))
    except ValueError:
        return False
    esperado = (10 - (total % 10)) % 10
    return curp[17] == str(esperado)
