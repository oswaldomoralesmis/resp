# -*- coding: utf-8 -*-
"""
Comando: python manage.py setup_resp
Crea el superusuario administrador inicial del RESP.
"""
from django.core.management.base import BaseCommand
from usuarios.models import UsuarioRESP
import secrets, string


def gen_password(length=12):
    chars = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(chars) for _ in range(length))


class Command(BaseCommand):
    help = 'Configura el usuario administrador inicial del RESP'

    def handle(self, *args, **options):
        if UsuarioRESP.objects.filter(rol='administrador').exists():
            self.stdout.write(self.style.WARNING('Ya existe un usuario administrador.'))
            return

        pwd = gen_password()
        admin = UsuarioRESP.objects.create_superuser(
            username='admin',
            email='admin@tabasco.gob.mx',
            password=pwd,
            first_name='Administrador',
            last_name='RESP',
            rfc='ADMR000000000',
            curp='ADMR000000HXXXXX00',
            rol='administrador',
            contrasena_temporal=True,
        )
        self.stdout.write(self.style.SUCCESS('\n[OK] Usuario administrador creado:'))
        self.stdout.write(f'   Email:      admin@tabasco.gob.mx')
        self.stdout.write(f'   Contraseña: {pwd}')
        self.stdout.write(self.style.WARNING('   [!]  Cambie la contraseña en el primer inicio de sesión.\n'))
