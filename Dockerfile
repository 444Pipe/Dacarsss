# DACARS — sitio, catálogo y panel de administración.
#
# Antes esta imagen era Caddy sirviendo HTML estático (0,4 MB). Ahora corre
# Django: pesa más, pero es lo que permite que el comercio cargue productos
# sin tocar el código.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

WORKDIR /app

# Las dependencias primero: mientras requirements.txt no cambie, Docker
# reusa esta capa y el despliegue tarda segundos en vez de minutos.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Los estáticos se juntan y se hashean durante el build, no al arrancar: si
# algo está roto, falla acá y no en producción con el sitio ya abierto.
# Las variables son de mentira a propósito — collectstatic no toca la base.
RUN SECRET_KEY=solo-para-el-build \
    DEBUG=0 \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput --clear

EXPOSE 8080

# El arranque hace tres cosas antes de servir:
#
#   migrate                      deja la base al día. Railway despliega un
#                                contenedor nuevo por push, así que hacerlo
#                                acá evita un paso manual que alguien olvide.
#   categorias_iniciales         siembra las 8 categorías, pero solo si no hay
#     --si-vacio                 ninguna. Después se calla: una categoría
#                                borrada a propósito no tiene que reaparecer.
#   crear_admin                  crea el usuario del panel desde ADMIN_USUARIO
#                                y ADMIN_CLAVE. Sin esas variables no hace
#                                nada. Es la única forma de crear el primer
#                                usuario cuando la base vive solo en la nube y
#                                no es alcanzable desde afuera.
#
# Los dos últimos nunca terminan con error: una variable mal puesta no puede
# impedir que el sitio levante.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py categorias_iniciales --si-vacio && python manage.py crear_admin && exec gunicorn dacars.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 3 --threads 2 --timeout 60 --access-logfile - --error-logfile -"]
