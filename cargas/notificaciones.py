# -*- coding: utf-8 -*-
"""Avisos por correo de los 3 momentos clave del flujo de revisión de
cargas (ver cargas/views.py). Un problema de SMTP (host caído, credenciales
vencidas, etc.) NUNCA debe impedir aceptar/rechazar una carga real de
nómina: cada función atrapa cualquier excepción y solo la deja en el log
del servidor. Se debe llamar siempre DESPUÉS de que la transacción de BD
que cambia el estado de la carga ya se confirmó (fuera de cualquier
transaction.atomic() abierto), para no bloquear la escritura real por una
llamada de red lenta — ver notas en cada punto de disparo en views.py."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q

logger = logging.getLogger(__name__)


def _enviar(asunto, mensaje, destinatarios):
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return
    try:
        send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, destinatarios, fail_silently=False)
    except Exception:
        logger.exception(
            'No se pudo enviar el correo "%s" a %s — la operación en el sistema ya se aplicó, '
            'el aviso simplemente no llegó.', asunto, destinatarios,
        )


def _destinatarios_revision(carga):
    """Validadores de la misma dependencia de la carga + todos los
    administradores — son quienes puede_revisar_carga ya autoriza a
    aceptar/rechazar esta carga."""
    from usuarios.models import UsuarioRESP
    qs = UsuarioRESP.objects.filter(is_active=True, activo_sistema=True).filter(
        Q(rol='validador', dependencia_id=carga.dependencia_id) | Q(rol='administrador')
    ).exclude(email='')
    return list(qs.values_list('email', flat=True))


def notificar_carga_pendiente_revision(carga):
    asunto = f'RESP Tabasco — Carga pendiente de revisión ({carga.get_tipo_display()}, {carga.dependencia})'
    mensaje = (
        f'Se validó una carga de {carga.get_tipo_display()} para la dependencia {carga.dependencia} '
        f'(quincena {carga.periodo.quincena}/{carga.periodo.ejercicio}) y está lista para revisión.\n\n'
        f'Registros totales: {carga.registros_totales}  |  OK: {carga.registros_ok}  |  Con error: {carga.registros_error}\n\n'
        f'Revísela en el sistema RESP — Historial de Cargas, carga #{carga.pk}.'
    )
    _enviar(asunto, mensaje, _destinatarios_revision(carga))


def notificar_carga_aceptada(carga):
    if not carga.usuario_carga_id or not carga.usuario_carga.email:
        return
    asunto = f'RESP Tabasco — Carga aceptada ({carga.get_tipo_display()}, {carga.dependencia})'
    mensaje = (
        f'Su carga de {carga.get_tipo_display()} para {carga.dependencia} '
        f'(quincena {carga.periodo.quincena}/{carga.periodo.ejercicio}) fue ACEPTADA '
        f'y sus {carga.registros_ok} registro(s) ya se aplicaron al padrón.'
    )
    _enviar(asunto, mensaje, [carga.usuario_carga.email])


def notificar_carga_rechazada(carga):
    if not carga.usuario_carga_id or not carga.usuario_carga.email:
        return
    asunto = f'RESP Tabasco — Carga rechazada ({carga.get_tipo_display()}, {carga.dependencia})'
    mensaje = (
        f'Su carga de {carga.get_tipo_display()} para {carga.dependencia} '
        f'(quincena {carga.periodo.quincena}/{carga.periodo.ejercicio}) fue RECHAZADA.\n\n'
        f'Motivo: {carga.motivo_rechazo}\n\n'
        f'No se aplicó ningún cambio al padrón. Corrija lo indicado y vuelva a subir el archivo.'
    )
    _enviar(asunto, mensaje, [carga.usuario_carga.email])
