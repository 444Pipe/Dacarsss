# -*- coding: utf-8 -*-
"""
Sube los assets de statics/ a Cloudinary.

    python tools/subir-cloudinary.py            # todo
    python tools/subir-cloudinary.py imagenes   # solo png/jpg
    python tools/subir-cloudinary.py video      # solo mp4

Idempotente: cada archivo tiene un public_id fijo derivado de su ruta
(statics/video/hero-16x9.mp4 -> dacars/video/hero-16x9), asi que volver a
correrlo sobrescribe en el mismo sitio en vez de duplicar.

Deja el inventario en tools/cloudinary-map.json. Ese archivo SI se commitea:
es lo que usa tools/usar-cloudinary.py para escribir las URLs en el HTML,
y no contiene ningun secreto (solo public_id y version, que son publicos).

CREDENCIALES
Se leen de la variable CLOUDINARY_URL, que vive en el .env de la raiz
(ignorado por git). Ver .env.example. El sitio publicado nunca las necesita:
las URLs de entrega solo llevan el cloud name.
"""

import io
import json
import os
import sys

try:
    import cloudinary
    import cloudinary.uploader
    from dotenv import load_dotenv
except ImportError:
    sys.exit("Falta instalar dependencias:\n\n    pip install cloudinary python-dotenv\n")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATICS = os.path.join(ROOT, "statics")
MAPA = os.path.join(ROOT, "tools", "cloudinary-map.json")

CARPETA = "dacars"  # prefijo de todos los public_id en Cloudinary

IMAGENES = (".png", ".jpg", ".jpeg", ".webp")
VIDEOS = (".mp4", ".webm")

# No se suben: material fuente, temporales y notas.
EXCLUIR_DIRS = ("hero video", "_tmp")
EXCLUIR_ARCHIVOS = ("LEEME.txt", ".gitkeep")


def configurar():
    """Carga el .env y deja el SDK listo. Falla temprano y claro."""
    load_dotenv(os.path.join(ROOT, ".env"))
    url = os.environ.get("CLOUDINARY_URL", "").strip()
    if not url:
        sys.exit(
            "No hay CLOUDINARY_URL.\n\n"
            "Copia .env.example a .env y pone el valor real:\n"
            "    CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>\n"
        )
    # El SDK lee CLOUDINARY_URL del entorno, pero ya se configuro al importarse
    # (antes de que load_dotenv existiera). Hay que resetear para que relea.
    cloudinary.reset_config()
    cfg = cloudinary.config(secure=True)
    if not cfg.cloud_name:
        sys.exit("CLOUDINARY_URL mal formada: no se pudo leer el cloud name.")
    return cfg.cloud_name


def tipo_de(nombre):
    ext = os.path.splitext(nombre)[1].lower()
    if ext in VIDEOS:
        return "video"
    if ext in IMAGENES:
        return "image"
    return None


def recolectar(filtro):
    """Devuelve [(ruta_relativa_posix, ruta_absoluta, resource_type)] ordenado."""
    items = []
    for base, dirs, archivos in os.walk(STATICS):
        dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS]
        for nombre in archivos:
            if nombre in EXCLUIR_ARCHIVOS:
                continue
            rtype = tipo_de(nombre)
            if rtype is None:
                continue
            if filtro == "imagenes" and rtype != "image":
                continue
            if filtro == "video" and rtype != "video":
                continue
            absoluta = os.path.join(base, nombre)
            rel = os.path.relpath(absoluta, ROOT).replace(os.sep, "/")
            items.append((rel, absoluta, rtype))
    return sorted(items)


def public_id_de(rel):
    """statics/video/hero-16x9.mp4 -> dacars/video/hero-16x9"""
    sin_statics = rel[len("statics/"):]
    sin_ext = os.path.splitext(sin_statics)[0]
    return "%s/%s" % (CARPETA, sin_ext)


def cargar_mapa():
    if os.path.exists(MAPA):
        with io.open(MAPA, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def main():
    filtro = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if filtro not in ("todo", "imagenes", "video"):
        sys.exit("Uso: python tools/subir-cloudinary.py [todo|imagenes|video]")

    cloud_name = configurar()
    items = recolectar(filtro)
    if not items:
        sys.exit("No se encontro nada que subir en statics/.")

    print("Cloud: %s" % cloud_name)
    print("Subiendo %d archivos...\n" % len(items))

    mapa = cargar_mapa()
    mapa["_cloud_name"] = cloud_name
    total_local = 0
    fallos = []

    for rel, absoluta, rtype in items:
        pid = public_id_de(rel)
        peso = os.path.getsize(absoluta)
        total_local += peso
        try:
            res = cloudinary.uploader.upload(
                absoluta,
                public_id=pid,
                resource_type=rtype,
                overwrite=True,     # idempotente: reemplaza en el mismo public_id
                invalidate=True,    # purga la copia cacheada en el CDN
                use_filename=False,
                unique_filename=False,
                timeout=600,
            )
        except Exception as err:  # noqa: BLE001 - se reporta y se sigue
            print("  FALLO  %-44s %s" % (rel, err))
            fallos.append(rel)
            continue

        mapa[rel] = {
            "public_id": res["public_id"],
            "version": res["version"],
            "resource_type": rtype,
            "format": res.get("format", ""),
            "width": res.get("width"),
            "height": res.get("height"),
            "bytes": res.get("bytes", peso),
        }
        print("  OK     %-44s %6.1f KB -> %s" % (rel, peso / 1024.0, res["public_id"]))

    with io.open(MAPA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(mapa, indent=2, ensure_ascii=False, sort_keys=True))
        fh.write("\n")

    subidos = len(items) - len(fallos)
    print("\n  %d/%d subidos, %.1f MB de origen" % (subidos, len(items), total_local / 1048576.0))
    print("  inventario -> tools/cloudinary-map.json")

    if fallos:
        print("\n  FALLARON %d:" % len(fallos))
        for f in fallos:
            print("    %s" % f)
        sys.exit(1)

    print("\n  Siguiente paso:  python tools/usar-cloudinary.py")


if __name__ == "__main__":
    main()
