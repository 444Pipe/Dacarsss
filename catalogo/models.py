"""Catálogo de productos de DACARS.

La pieza central es la **variante**, no el producto. Una llanta no se vende:
se vende una medida concreta (265/65R17), y una película no se vende: se vende
un porcentaje. El producto agrupa y describe; la variante tiene el SKU, el
precio y las existencias. Un producto que no tiene medidas igual necesita una
variante (la "única"), y el admin la crea sola para que el comercio no tenga
que entenderlo.
"""

from django.conf import settings
from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils.text import slugify


def _carpeta(sub):
    """Ruta dentro de Cloudinary (o de media/ en local)."""
    return settings.CLOUDINARY_CARPETA + "/" + sub

from sitio.paginas import SERVICIOS as SERVICIOS_DEL_SITIO

class Categoria(models.Model):
    """Agrupa productos y, cuando aplica, se enlaza con la landing del servicio."""

    # Las landings que existen. Enlazar la categoría con su servicio hace que
    # el catálogo y el SEO se alimenten entre sí en vez de competir.
    #
    # La lista se toma de sitio.paginas y no se copia acá: eran dos listas
    # que había que acordarse de tocar juntas, y al sumar un servicio esta se
    # habría quedado corta, dejando la categoría nueva sin forma de enlazarse
    # con su página.
    SERVICIOS = SERVICIOS_DEL_SITIO

    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(
        max_length=90,
        unique=True,
        blank=True,
        help_text="Se arma solo con el nombre. Es la dirección web: cambiarlo "
        "rompe los enlaces que ya estén circulando.",
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Un par de frases. Sale arriba del listado y en el buscador de Google.",
    )
    imagen = models.ImageField(
        upload_to=_carpeta("categorias"),
        blank=True,
        help_text="Opcional. Se ve en la portada del catálogo.",
    )
    servicio = models.CharField(
        max_length=60,
        choices=SERVICIOS,
        blank=True,
        verbose_name="servicio relacionado",
        help_text="Enlaza la categoría con su página de servicio.",
    )
    orden = models.PositiveSmallIntegerField(
        default=100, help_text="Menor número, más arriba."
    )
    activa = models.BooleanField(
        default=True, help_text="Desmarcá para esconderla del sitio sin borrarla."
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)[:90]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalogo:categoria", args=[self.slug])

    @property
    def url_servicio(self):
        return "/" + self.servicio + ".html" if self.servicio else ""


class Marca(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    logo = models.ImageField(upload_to=_carpeta("marcas"), blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "marcas"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)[:70]
        super().save(*args, **kwargs)


class ProductoQuerySet(models.QuerySet):
    def publicados(self):
        """Lo que el público puede ver.

        Exige al menos una variante activa: un producto sin precio no se puede
        comprar, y publicarlo solo consigue que alguien pregunte por algo que
        no se le puede vender. El panel avisa cuáles están en ese estado con el
        filtro "qué le falta".
        """
        return self.filter(
            activo=True, categoria__activa=True, variantes__activa=True
        ).distinct()

    def con_todo(self):
        return self.select_related("categoria", "marca").prefetch_related(
            "imagenes", "variantes"
        )


class Producto(models.Model):
    nombre = models.CharField(max_length=140)
    slug = models.SlugField(
        max_length=160,
        unique=True,
        blank=True,
        help_text="Se arma solo con el nombre.",
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos"
    )
    marca = models.ForeignKey(
        Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos"
    )
    resumen = models.CharField(
        max_length=180,
        blank=True,
        help_text="Una línea. Es lo que se lee en la tarjeta del listado.",
    )
    descripcion = models.TextField(
        blank=True, help_text="El texto largo de la ficha. Un párrafo por línea en blanco."
    )
    caracteristicas = models.TextField(
        blank=True,
        verbose_name="características",
        help_text="Una por línea. Se muestran como lista con viñetas.",
    )
    compatibilidad = models.CharField(
        max_length=240,
        blank=True,
        help_text="Con qué vehículos sirve. Ej: Hilux, Ranger, Amarok, D-Max.",
    )
    instalacion = models.BooleanField(
        default=True,
        verbose_name="se instala en el taller",
        help_text="Si está marcado, la ficha avisa que la instalación va incluida "
        "o se cotiza aparte.",
    )
    destacado = models.BooleanField(
        default=False, help_text="Aparece primero en el catálogo y en la portada."
    )
    activo = models.BooleanField(
        default=True, help_text="Desmarcá para sacarlo del sitio sin borrarlo."
    )
    orden = models.PositiveSmallIntegerField(default=100)

    seo_titulo = models.CharField(
        max_length=70,
        blank=True,
        verbose_name="título para Google",
        help_text="Máximo 70 caracteres. Vacío = se usa el nombre del producto.",
    )
    seo_descripcion = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="descripción para Google",
        help_text="Máximo 160 caracteres. Vacío = se usa el resumen.",
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = ProductoQuerySet.as_manager()

    class Meta:
        ordering = ["-destacado", "orden", "nombre"]
        indexes = [
            models.Index(fields=["activo", "categoria"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:150] or "producto"
            slug = base
            n = 2
            while Producto.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = base[:150 - len(str(n)) - 1] + "-" + str(n)
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalogo:producto", args=[self.slug])

    # -- Lo que la ficha necesita ------------------------------------------
    @property
    def lista_caracteristicas(self):
        return [x.strip() for x in self.caracteristicas.splitlines() if x.strip()]

    @property
    def parrafos(self):
        return [p.strip() for p in self.descripcion.split("\n\n") if p.strip()]

    @property
    def imagen_principal(self):
        imagenes = list(self.imagenes.all())
        return imagenes[0] if imagenes else None

    @property
    def variantes_activas(self):
        return [v for v in self.variantes.all() if v.activa]

    @property
    def variante_unica(self):
        """La única variante, cuando el producto no maneja medidas."""
        activas = self.variantes_activas
        return activas[0] if len(activas) == 1 else None

    @property
    def precio_desde(self):
        precios = [v.precio for v in self.variantes_activas]
        return min(precios) if precios else None

    @property
    def precio_hasta(self):
        precios = [v.precio for v in self.variantes_activas]
        return max(precios) if precios else None

    @property
    def rango_de_precios(self):
        return self.precio_desde is not None and self.precio_desde != self.precio_hasta

    @property
    def disponible_total(self):
        return sum(v.disponible for v in self.variantes_activas)

    @property
    def agotado(self):
        return self.disponible_total <= 0

    @property
    def bajo_stock(self):
        return any(v.bajo_stock for v in self.variantes_activas)

    @property
    def titulo_seo(self):
        return self.seo_titulo or (self.nombre + " en Villavicencio | DACARS")[:70]

    @property
    def descripcion_seo(self):
        base = self.seo_descripcion or self.resumen or self.nombre
        return base[:160]


class ImagenProducto(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="imagenes"
    )
    imagen = models.ImageField(upload_to=_carpeta("productos"))
    alt = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="texto alternativo",
        help_text="Qué se ve en la foto. Lo lee Google y los lectores de pantalla. "
        "Vacío = se arma con el nombre del producto.",
    )
    orden = models.PositiveSmallIntegerField(
        default=0, help_text="La de menor número es la principal."
    )

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "foto"
        verbose_name_plural = "fotos"

    def __str__(self):
        return self.alt or ("Foto de " + self.producto.nombre)

    @property
    def texto_alt(self):
        if self.alt:
            return self.alt
        return self.producto.nombre + " — DACARS Villavicencio"


class VarianteQuerySet(models.QuerySet):
    def disponibles(self):
        return self.filter(activa=True).annotate(
            _disp=F("stock") - F("reservado")
        ).filter(_disp__gt=0)


class Variante(models.Model):
    """Lo que realmente se vende: un SKU con precio y existencias.

    `stock` son las unidades físicas en el local. `reservado` son las que ya
    comprometió un pedido que todavía nadie confirmó. Lo que se le ofrece al
    público es la resta: `disponible`. Sin esa resta, dos clientes compran la
    última unidad el mismo día.
    """

    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="variantes"
    )
    nombre = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="medida o presentación",
        help_text="Ej: 265/65R17, 35%, Talla M. Dejalo vacío si el producto "
        "no tiene variantes.",
    )
    sku = models.CharField(
        max_length=40,
        unique=True,
        blank=True,
        verbose_name="SKU",
        help_text="Código interno. Si lo dejás vacío se genera solo.",
    )
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        help_text="En pesos, sin puntos ni centavos. Ej: 450000",
    )
    precio_antes = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="precio anterior",
        help_text="Opcional. Si lo llenás, se muestra tachado al lado del precio.",
    )
    stock = models.PositiveIntegerField(
        default=0, verbose_name="existencias", help_text="Unidades físicas en el local."
    )
    reservado = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Unidades comprometidas por pedidos sin confirmar. Lo maneja el sistema.",
    )
    stock_minimo = models.PositiveIntegerField(
        default=2,
        verbose_name="mínimo",
        help_text="Cuando queden estas unidades o menos, salta la alerta en el tablero.",
    )
    activa = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = VarianteQuerySet.as_manager()

    class Meta:
        ordering = ["producto", "orden", "nombre"]
        verbose_name = "variante"
        verbose_name_plural = "variantes y existencias"
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "nombre"], name="variante_unica_por_producto"
            )
        ]

    def __str__(self):
        if self.nombre:
            return self.producto.nombre + " — " + self.nombre
        return self.producto.nombre

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._sku_nuevo()
        super().save(*args, **kwargs)

    def _sku_nuevo(self):
        base = slugify(self.producto.nombre)[:22].upper().replace("-", "")
        sufijo = slugify(self.nombre)[:8].upper().replace("-", "") if self.nombre else ""
        raiz = ("DC-" + base + ("-" + sufijo if sufijo else ""))[:36]
        sku = raiz
        n = 2
        while Variante.objects.filter(sku=sku).exclude(pk=self.pk).exists():
            sku = raiz[:36 - len(str(n)) - 1] + "-" + str(n)
            n += 1
        return sku

    # -- Existencias --------------------------------------------------------
    @property
    def disponible(self):
        return max(self.stock - self.reservado, 0)

    @property
    def agotada(self):
        return self.disponible <= 0

    @property
    def bajo_stock(self):
        return self.disponible <= self.stock_minimo

    @property
    def etiqueta(self):
        return self.nombre or "Única"

    @property
    def descuento(self):
        if not self.precio_antes or self.precio_antes <= self.precio:
            return 0
        return int(round((1 - self.precio / self.precio_antes) * 100))

    @classmethod
    def bajo_minimo(cls):
        """Variantes publicadas cuyo disponible ya tocó el mínimo."""
        return list(
            cls.objects.filter(activa=True, producto__activo=True)
            .annotate(_disp=F("stock") - F("reservado"))
            .filter(_disp__lte=F("stock_minimo"))
            .select_related("producto", "producto__categoria")
            .order_by("_disp", "producto__nombre")
        )
