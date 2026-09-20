"""Crea o actualiza el superusuario del panel desde variables de entorno.

Existe porque la base vive **solo en la nube**. El Postgres de Railway no es
alcanzable desde afuera si el servicio no tiene proxy TCP público, así que
`createsuperuser` no se puede correr contra él desde una máquina de trabajo.
Este comando corre dentro del contenedor, que sí llega.

Cómo se usa:

  1. En el panel del servicio web, definir `ADMIN_USUARIO` y `ADMIN_CLAVE`.
  2. Railway redespliega y el usuario queda creado.
  3. **Borrar `ADMIN_CLAVE`.** Mientras siga ahí, cada despliegue vuelve a
     escribir esa contraseña, así que un cambio hecho desde el panel se pierde
     en el próximo deploy. Y una contraseña no tiene por qué quedar guardada
     en las variables del servicio.

Sin esas variables no hace nada y no dice nada: es lo normal en cada arranque.

Nunca termina con error. Corre en la línea de arranque del contenedor, y una
variable mal puesta no puede impedir que el sitio levante.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import DatabaseError


class Command(BaseCommand):
    help = "Crea o actualiza el superusuario desde ADMIN_USUARIO y ADMIN_CLAVE."

    def handle(self, *args, **opciones):
        usuario = os.environ.get("ADMIN_USUARIO", "").strip()
        clave = os.environ.get("ADMIN_CLAVE", "")

        if not usuario and not clave:
            return
        if not usuario or not clave:
            self.stderr.write(
                "Falta una de las dos: hay que definir ADMIN_USUARIO y "
                "ADMIN_CLAVE juntas. No se creó ningún usuario."
            )
            return

        Usuario = get_user_model()
        try:
            cuenta, nueva = Usuario.objects.get_or_create(
                username=usuario,
                defaults={"email": os.environ.get("ADMIN_EMAIL", "")},
            )
            cuenta.set_password(clave)
            cuenta.is_staff = True
            cuenta.is_superuser = True
            cuenta.is_active = True
            if os.environ.get("ADMIN_EMAIL"):
                cuenta.email = os.environ["ADMIN_EMAIL"]
            cuenta.save()
        except DatabaseError as falla:
            # Puede pasar si las migraciones todavía no corrieron. No es
            # motivo para que el contenedor no arranque.
            self.stderr.write("No se pudo crear el usuario: {}".format(falla))
            return

        self.stdout.write(
            self.style.SUCCESS(
                "Usuario «{}» {}.".format(
                    usuario, "creado" if nueva else "actualizado"
                )
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Ahora borrá ADMIN_CLAVE de las variables del servicio. "
                "Mientras siga definida, cada despliegue reescribe esa "
                "contraseña y pisa cualquier cambio hecho desde el panel."
            )
        )
