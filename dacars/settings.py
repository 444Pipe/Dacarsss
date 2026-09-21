"""
Configuración de DACARS.

Todo lo sensible sale de variables de entorno. En local se leen del archivo
`.env` de la raíz (no se commitea); en Railway se definen en el panel del
servicio. El proyecto arranca sin ninguna variable definida: cae a SQLite,
almacenamiento en disco y DEBUG apagado.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# .env
# --------------------------------------------------------------------------
def _cargar_env(ruta):
    """Lector mínimo de .env, para no sumar una dependencia más.

    Solo entiende `CLAVE=valor`, ignora comentarios y líneas vacías, y nunca
    pisa una variable que ya venga del entorno real: en Railway manda el panel,
    no el archivo.
    """
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor


_cargar_env(BASE_DIR / ".env")


def _bool(nombre, por_defecto=False):
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "yes", "on")


def _lista(nombre):
    return [x.strip() for x in os.environ.get(nombre, "").split(",") if x.strip()]


# --------------------------------------------------------------------------
# Básico
# --------------------------------------------------------------------------
DEBUG = _bool("DEBUG", False)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-solo-para-local-no-usar-en-produccion-0000000000"
    else:
        # En producción nunca se cae a una clave conocida: con esta clave
        # cualquiera puede firmar una cookie de sesión y entrar al panel.
        # Se genera una al azar en cada arranque. El sitio funciona; lo único
        # que se pierde es que las sesiones no sobreviven a un reinicio, así
        # que el olvido se nota (hay que volver a entrar al panel) en vez de
        # quedar abierto en silencio.
        import secrets

        SECRET_KEY = secrets.token_urlsafe(64)
        import logging

        logging.getLogger(__name__).warning(
            "SECRET_KEY no está definida. Se generó una al azar: las sesiones "
            "se van a caer en cada despliegue. Definila en las variables del "
            "servicio."
        )

# El canonical, og:url y el JSON-LD de todas las paginas salen de aca. Si
# no coincide con el dominio que de verdad sirve el sitio, Google recibe
# la orden de indexar otro: en Railway no hace falta definir DOMINIO
# mientras este valor sea el correcto.
DOMINIO = os.environ.get("DOMINIO", "www.dacarslujos.com")

ALLOWED_HOSTS = _lista("ALLOWED_HOSTS") or [DOMINIO, DOMINIO.replace("www.", "", 1)]

# Railway inyecta el dominio público del servicio.
_railway = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if _railway:
    ALLOWED_HOSTS.append(_railway)
if DEBUG:
    ALLOWED_HOSTS += ["localhost", "127.0.0.1", "[::1]", "testserver"]

_locales = ("localhost", "127.0.0.1", "[::1]", "testserver")
CSRF_TRUSTED_ORIGINS = [
    "https://" + h for h in ALLOWED_HOSTS if h not in _locales
]

# Railway termina el TLS en su borde y nos habla por HTTP. Sin esto Django
# cree que la petición es insegura y las redirecciones salen en http://.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

if not DEBUG:
    SECURE_SSL_REDIRECT = _bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    # DENY y no SAMEORIGIN: el sitio no se embebe a sí mismo en ningún lado,
    # así que permitirlo solo deja abierta la puerta al clickjacking.
    X_FRAME_OPTIONS = "DENY"
    # HSTS arranca en 0 a propósito. Se sube recién cuando el dominio
    # definitivo esté sirviendo por HTTPS sin sobresaltos: activarlo antes
    # deja el dominio clavado en HTTPS en los navegadores que ya lo visitaron.
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))


# --------------------------------------------------------------------------
# Aplicaciones
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    # El admin arranca con nuestro AdminSite: tablero con alertas de stock.
    "dacars.apps.PanelDacarsConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "cloudinary",
    "cloudinary_storage",
    "sitio",
    "catalogo",
    "inventario",
    "pedidos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dacars.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sitio.context_processors.negocio",
                "sitio.context_processors.paginas",
                "pedidos.context_processors.carrito",
            ],
        },
    },
]

WSGI_APPLICATION = "dacars.wsgi.application"


# --------------------------------------------------------------------------
# Base de datos
# --------------------------------------------------------------------------
# En Railway llega DATABASE_URL del plugin de Postgres. En local, SQLite.
DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------------------------------
# Contraseñas
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------------------------
# Idioma y zona horaria
# --------------------------------------------------------------------------
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# --------------------------------------------------------------------------
# Archivos estáticos y media
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Las fotos de producto van a Cloudinary, la misma cuenta que ya sirve los
# assets del sitio. Sin CLOUDINARY_URL definida se guardan en disco, así el
# proyecto corre en local sin credenciales.
#
# La validación de acá no es paranoia. El paquete `cloudinary` lee esta
# variable por su cuenta apenas se importa, y si el valor no arranca con
# `cloudinary://` levanta un ValueError ahí mismo: el contenedor no llega ni a
# arrancar y se cae el sitio entero, incluidas las 11 landings que no tienen
# nada que ver con subir fotos. Una credencial mal pegada no puede costar eso.
#
# Si el valor está mal, se avisa fuerte en el log y se saca del entorno. El
# sitio queda en pie y lo único que no anda es subir fotos nuevas.
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "").strip().strip('"').strip("'")

if CLOUDINARY_URL and not CLOUDINARY_URL.startswith("cloudinary://"):
    import logging

    logging.getLogger(__name__).error(
        "CLOUDINARY_URL está mal escrita (empieza con %r, tiene que empezar con "
        "'cloudinary://'). Se ignora: las fotos nuevas van al disco del "
        "contenedor y se pierden en el próximo despliegue. Revisá la variable "
        "en el panel del servicio.",
        CLOUDINARY_URL[:20],
    )
    CLOUDINARY_URL = ""

if CLOUDINARY_URL:
    # Normalizada: si venía con comillas o espacios, el paquete tiene que ver
    # el valor limpio, no el original.
    os.environ["CLOUDINARY_URL"] = CLOUDINARY_URL
else:
    os.environ.pop("CLOUDINARY_URL", None)

USAR_CLOUDINARY = bool(CLOUDINARY_URL)

STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if USAR_CLOUDINARY
            else "django.core.files.storage.FileSystemStorage"
        )
    },
    "staticfiles": {
        # Hashea el nombre de cada archivo: reemplaza al `?v=` que ponía
        # tools/versionar-assets.py en el sitio estático.
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

CLOUDINARY_STORAGE = {"PREFIX": CLOUDINARY_URL}

# Carpeta dentro de Cloudinary donde caen las fotos que suba el comercio.
# Los assets del sitio viven en `dacars/`; el catálogo va aparte para que se
# puedan borrar sin tocar los logos ni el video.
CLOUDINARY_CARPETA = os.environ.get("CLOUDINARY_CARPETA", "dacars/catalogo")


# --------------------------------------------------------------------------
# Sesiones (el carrito vive acá)
# --------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # dos semanas


# --------------------------------------------------------------------------
# Negocio
# --------------------------------------------------------------------------
# Lo que hoy está repetido en los 11 HTML. Un solo lugar.
NEGOCIO = {
    "nombre": "DACARS",
    "razon_social": "DACARS VILLAVICENCIO S.A.S.",
    "nit": "901.798.060",
    "whatsapp": os.environ.get("WHATSAPP", "573112629406"),
    "telefono_visible": "311 262 9406",
    "direccion": "Cra. 33 #24-60, Barrio San Francisco",
    "ciudad": "Villavicencio",
    "departamento": "Meta",
    "instagram": "https://www.instagram.com/dacarslujosvillavicencio/",
    "facebook": "https://www.facebook.com/Dacars.accesorios/",
    "dominio": DOMINIO,
    "sitio": "https://" + DOMINIO,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"consola": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["consola"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
