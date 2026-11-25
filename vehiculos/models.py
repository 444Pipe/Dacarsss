"""Los carros que el local tiene a la venta.

Van aparte del catálogo a propósito: un carro no tiene variantes, ni stock,
ni carrito. Se muestra, y quien se interesa escribe por WhatsApp. Lo que sí
comparte con el catálogo es dónde viven las fotos (Cloudinary) y el panel.

Casi todos los datos son opcionales. El comercio suele tener primero las
fotos y después el resto, y un carro sin precio cargado sale como «Consultar
precio» en vez de no salir.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from catalogo.models import _carpeta


class VehiculoQuerySet(models.QuerySet):
    def publicados(self):
        return self.filter(publicado=True)


class Vehiculo(models.Model):
    DISPONIBLE = "disponible"
    RESERVADO = "reservado"
    VENDIDO = "vendido"
    ESTADOS = [
        (DISPONIBLE, "Disponible"),
        (RESERVADO, "Reservado"),
        (VENDIDO, "Vendido"),
    ]

    TRANSMISIONES = [("automatica", "Automática"), ("mecanica", "Mecánica")]

    COMBUSTIBLES = [
        ("gasolina", "Gasolina"),
        ("diesel", "Diésel"),
        ("hibrido", "Híbrido"),
        ("electrico", "Eléctrico"),
        ("gas", "Gas y gasolina"),
    ]

    marca = models.CharField(max_length=60, help_text="Toyota, Nissan, Mazda…")
    modelo = models.CharField(max_length=80, help_text="Prado, Frontier, CX-5…")
    version = models.CharField(
        "versión", max_length=80, blank=True, help_text="TX.L, LE 4x4… Opcional."
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        blank=True,
        help_text="La dirección de la ficha. Si lo dejas vacío se arma solo.",
    )
    anio = models.PositiveSmallIntegerField("año (modelo)", null=True, blank=True)
    kilometraje = models.PositiveIntegerField(
        null=True, blank=True, help_text="En kilómetros, sin puntos."
    )
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="En pesos, sin puntos. Vacío: la ficha dice «Consultar precio».",
    )
    negociable = models.BooleanField(default=False)
    transmision = models.CharField(
        "transmisión", max_length=12, choices=TRANSMISIONES, blank=True
    )
    combustible = models.CharField(max_length=12, choices=COMBUSTIBLES, blank=True)
    traccion = models.CharField("tracción", max_length=20, blank=True, help_text="4x4, 4x2…")
    motor = models.CharField(max_length=40, blank=True, help_text="2.5 turbo, 4.0 V6… Opcional.")
    color = models.CharField(max_length=40, blank=True)
    placa_ciudad = models.CharField("ciudad de la placa", max_length=60, blank=True)
    resumen = models.CharField(
        max_length=180, blank=True, help_text="Una frase para la tarjeta y para Google."
    )
    descripcion = models.TextField("descripción", blank=True)
    caracteristicas = models.TextField(
        "características",
        blank=True,
        help_text="Una por línea: cojinería en cuero, techo corredizo, único dueño…",
    )
    estado = models.CharField(
        max_length=12,
        choices=ESTADOS,
        default=DISPONIBLE,
        help_text="Un carro vendido sigue en la página con el aviso «Vendido» "
        "hasta que lo despubliques.",
    )
    publicado = models.BooleanField(
        default=True, help_text="Desmárcalo para sacarlo del sitio sin borrarlo."
    )
    orden = models.PositiveSmallIntegerField(
        default=0, help_text="Los números bajos salen primero."
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = VehiculoQuerySet.as_manager()

    class Meta:
        verbose_name = "carro en venta"
        verbose_name_plural = "carros en venta"
        ordering = ["orden", "-creado"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:130] or "carro"
            slug, n = base, 2
            while Vehiculo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = "{}-{}".format(base, n)
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("vehiculos:detalle", args=[self.slug])

    @property
    def nombre(self):
        partes = [self.marca, self.modelo, self.version, str(self.anio) if self.anio else ""]
        return " ".join(p for p in partes if p)

    @property
    def vendido(self):
        return self.estado == self.VENDIDO

    @property
    def reservado(self):
        return self.estado == self.RESERVADO

    @property
    def foto_principal(self):
        # .all() y no .first(): aprovecha el prefetch de las listas.
        fotos = list(self.fotos.all())
        return fotos[0] if fotos else None

    @property
    def lista_caracteristicas(self):
        return [linea.strip() for linea in self.caracteristicas.splitlines() if linea.strip()]

    @property
    def parrafos(self):
        return [p.strip() for p in self.descripcion.split("\n") if p.strip()]

    @property
    def kilometraje_txt(self):
        if self.kilometraje is None:
            return ""
        return "{:,} km".format(self.kilometraje).replace(",", ".")

    @property
    def datos(self):
        """Los datos de la ficha que estén cargados, como pares (rótulo, valor)."""
        pares = [
            ("Año", self.anio or ""),
            ("Kilometraje", self.kilometraje_txt),
            ("Transmisión", self.get_transmision_display() if self.transmision else ""),
            ("Combustible", self.get_combustible_display() if self.combustible else ""),
            ("Tracción", self.traccion),
            ("Motor", self.motor),
            ("Color", self.color),
            ("Placa de", self.placa_ciudad),
        ]
        return [(rotulo, valor) for rotulo, valor in pares if valor]

    @property
    def datos_cortos(self):
        """Lo que cabe en la tarjeta: año, kilometraje y caja."""
        return [v for k, v in self.datos if k in ("Año", "Kilometraje", "Transmisión")]

    @property
    def descripcion_seo(self):
        if self.resumen:
            return self.resumen
        return (
            "{} en venta en Villavicencio, Meta. Míralo en DACARS o pide "
            "información por WhatsApp.".format(self.nombre)
        )


class FotoVehiculo(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, related_name="fotos", on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to=_carpeta("vehiculos"))
    alt = models.CharField(
        "descripción de la foto",
        max_length=160,
        blank=True,
        help_text="Qué se ve: frente, tablero, platón…",
    )
    orden = models.PositiveSmallIntegerField(
        default=0, help_text="La de número más bajo es la portada."
    )

    class Meta:
        verbose_name = "foto"
        verbose_name_plural = "fotos"
        ordering = ["orden", "pk"]

    def __str__(self):
        return self.alt or "Foto de {}".format(self.vehiculo)

    @property
    def texto_alt(self):
        if self.alt:
            return "{} — {}".format(self.vehiculo.nombre, self.alt)
        return self.vehiculo.nombre
