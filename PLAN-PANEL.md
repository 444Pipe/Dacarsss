# Plan de acción: un panel mínimo para DACARS

**Objetivo.** Dejar el panel con tres funciones y nada más: manejar el catálogo de
productos, actualizar precios y ver las alertas de existencias. Se conserva el
tablero de entrada tal como está (misma estructura, mismo estilo). Se saca todo
lo que el admin de Django trae de fábrica y que no sirve a esas tres funciones.

**Estado.** Plan aprobado en borrador el 22 de septiembre de 2026. Nada de esto
está implementado todavía.

---

## 1. Lo que hay hoy

El panel es el admin de Django con un `AdminSite` propio (`dacars/admin.py`), una
barra lateral fija (`templates/admin/base_site.html`) y una hoja de estilos
(`static/css/panel.css`). La barra lateral muestra **ocho secciones** más tres
enlaces de pie:

| Sección | Qué hace | ¿Sirve a las tres funciones? |
|---|---|---|
| Tablero | Métricas del mes, alertas, historial del usuario | Sí. Se conserva. |
| Productos | Alta y ficha del producto, con fotos y medidas | Sí. Se simplifica. |
| Variantes y existencias | Lista editable de precio y stock por medida | Sí. Es la pantalla de precios y alertas. |
| Pedidos | Pedidos del carrito: confirmar, entregar, cancelar | No. Ver decisión en §4. |
| Movimientos de inventario | Historial de entradas y salidas | Parcialmente. Se conserva solo «Llegó mercancía». |
| Categorías | Las 8 categorías del catálogo | Solo para el dueño. |
| Marcas | Marcas de producto (hay 1 cargada) | No. |
| Usuarios / Grupos | El auth de Django completo, con permisos por modelo | Solo crear cuentas, solo el dueño. |

Funciones nativas de Django que hoy quedan a la vista y no aportan:

- Menú de **acciones en lote** con casillas en cada listado (publicar, despublicar,
  destacar, borrar seleccionados).
- Botones **«Guardar y agregar otro»** y **«Guardar y continuar editando»** en
  cada formulario, más los botones duplicados arriba (`save_on_top`).
- Botón **«Historial»** en cada ficha (el log de cambios del admin).
- Iconos **«+», lápiz y ojo** al lado de cada selector relacionado, que abren
  ventanas emergentes con otro formulario adentro.
- **Grupos y permisos por modelo**: un empleado nuevo no ve nada hasta que el
  dueño le asigna permisos uno por uno.
- Campos técnicos en los formularios: `slug`, `sku`, `orden`, fechas, SEO
  («título para Google»), `precio_antes`, texto alternativo de cada foto.
- Filtros laterales de más: por marca, por destacado, por «qué le falta» con
  cuatro opciones, jerarquía por fecha.
- Columnas de más en las listas: SKU, ganancia y margen, unidades reservadas.
- Páginas intermedias de cada app (`/admin/catalogo/`) a las que ya no lleva
  ningún enlace.

Dato que pesa en las decisiones: en producción hay 19 productos, **todos «a
cotizar»** (sin precio) y **cero pedidos**. DACARS vende por WhatsApp.

---

## 2. Cómo queda el panel

### La barra lateral

```
Tablero
Productos
Precios y existencias
─────────────                (solo el dueño)
Categorías
Usuarios
─────────────
Cerrar sesión · Ver el sitio · Cambiar contraseña
```

Tres secciones para el equipo, cinco para el dueño. Un empleado con acceso al
panel puede hacer todo lo que hay en sus tres secciones, sin permisos que
configurar.

### Tablero (se conserva)

Misma estructura: encabezado con fecha y dos botones, cinco tarjetas de
métricas, «Para atender», «Lo último que hiciste» y «Cómo funciona». Solo cambia
el contenido que dependía de pedidos (ver §4). Se mantienen las alertas de
**agotadas**, **bajo el mínimo** y **sin fotos**, y el contador en el ítem
«Tablero» de la barra lateral.

### Productos

**Lista.** Nombre, categoría, precio, existencias, y una casilla «en la web»
editable en la fila (reemplaza a las acciones de publicar y despublicar). Buscador
por nombre, resumen y compatibilidad. Dos filtros: categoría y «qué le falta»
(sin fotos, sin precio).

**Alta.** Igual que hoy, menos la marca: nombre, categoría, resumen, una fila de
precio y una de foto. Al guardar cae en la ficha completa.

**Ficha.** Tres bloques y dos tablas:

| Bloque | Campos |
|---|---|
| Lo básico | nombre, categoría, resumen |
| La ficha | descripción, características, compatibilidad, «se instala en el taller» |
| Publicación | en la web, destacado |
| Precios y existencias (inline) | medida, costo, precio, existencias, mínimo, estado, activa |
| Fotos (inline) | miniatura, imagen, tipo, referencia, orden |

Sale de la ficha: `slug`, marca, `orden` del producto, el bloque «Google
(opcional)», el `sku`, `precio_antes`, el `orden` de la variante y el texto
alternativo de la foto. Los campos siguen en la base de datos con su valor
automático; ninguno se borra en esta fase.

Sale del formulario: «Guardar y agregar otro», «Guardar y continuar», los botones
de arriba, «Historial», y los iconos «+» / lápiz / ojo del selector de categoría.
Quedan «Guardar», «Eliminar» y «Ver en el sitio».

### Precios y existencias (hoy «Variantes y existencias»)

Es la planilla: todas las medidas de todos los productos en una lista, y se
escribe directo en la fila.

| Columna | Editable |
|---|---|
| Producto (enlace a su ficha) | — |
| Medida | — |
| Costo | sí |
| Precio | sí |
| Existencias | sí (deja un ajuste en el historial, como hoy) |
| Mínimo | sí |
| Situación (agotado / quedan N / N disponibles) | — |
| Activa | sí |

Filtros: situación del stock (agotadas, bajo el mínimo, con stock) y categoría.
Buscador por producto, medida y SKU. Orden por defecto: primero las agotadas,
después las bajas.

Sin botón «Agregar» (las medidas se crean desde la ficha del producto) y sin
formulario propio por variante: el enlace de la fila lleva a la ficha del
producto. Las alertas del tablero siguen apuntando acá, ya filtradas.

### Llegó mercancía

Se conserva el botón del tablero y su formulario de tres campos (producto y
medida, qué pasó, cuántas unidades). Es la forma de sumar stock sin hacer la
cuenta a mano y deja el movimiento con su motivo.

Desaparece de la barra lateral la lista «Movimientos de inventario». El
historial sigue escribiéndose igual (nada en el proyecto toca `variante.stock`
sin pasar por `inventario/servicios.py`); solo deja de tener pantalla. Si hace
falta mirarlo, se muestra como un bloque de solo lectura al pie de la ficha del
producto: los últimos diez movimientos de sus medidas.

### Categorías (solo el dueño)

Lista con nombre, cantidad de productos y activa. Formulario con nombre,
descripción, imagen, servicio relacionado y activa. Sin `slug` ni `orden`.

### Usuarios (solo el dueño)

Un formulario propio de cuatro campos: usuario, nombre, contraseña, activa. Toda
cuenta creada entra al panel con acceso completo a las tres secciones del
equipo. Los grupos y los permisos por modelo dejan de existir en el panel.

### Lo que se va del todo

- **Marcas**: sección y campo en el formulario. El modelo queda por ahora.
- **Grupos**.
- **Acciones en lote** en todas las listas.
- **Historial** de cada objeto, y las páginas `/admin/<app>/` intermedias.
- Ventanas emergentes de objetos relacionados.

---

## 3. Cómo se hace

Un solo mecanismo para sacar lo nativo, en un solo lugar, y el resto es
configuración de cada `ModelAdmin`.

### 3.1 Una clase base para todas las pantallas

Nuevo archivo `dacars/pantallas.py` (o dentro de `dacars/admin.py`) con
`class PantallaPanel(admin.ModelAdmin)` de la que heredan todos los admins del
proyecto. Concentra:

```python
class PantallaPanel(admin.ModelAdmin):
    actions = None               # sin casillas ni menú de acciones
    save_on_top = False
    list_per_page = 50

    # Quien entra al panel puede todo. Sin permisos por modelo.
    def has_module_permission(self, request):  return request.user.is_staff
    def has_view_permission(self, request, obj=None):   return request.user.is_staff
    def has_add_permission(self, request):              return request.user.is_staff
    def has_change_permission(self, request, obj=None): return request.user.is_staff
    def has_delete_permission(self, request, obj=None): return request.user.is_staff

    # Solo «Guardar» y «Eliminar».
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context.update(show_save_and_add_another=False, show_save_and_continue=False)
        return super().changeform_view(request, object_id, form_url, extra_context)

    # Sin «+», lápiz ni ojo en los selectores.
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        w = getattr(campo, "widget", None)
        for atributo in ("can_add_related", "can_change_related", "can_delete_related", "can_view_related"):
            if hasattr(w, atributo):
                setattr(w, atributo, False)
        return campo
```

Django 5.0 lee `show_save_and_add_another` y `show_save_and_continue` del
contexto en `submit_row`, así que no hace falta pisar la plantilla de los
botones. Verificado en `django/contrib/admin/templatetags/admin_modify.py`.

Los cinco `has_*_permission` van en un mixin aparte (`PermisoUniforme`) que
también hereda un `InlinePanel(admin.TabularInline)`. Sin eso, las tablas de
medidas y fotos dentro de la ficha del producto siguen consultando los permisos
por modelo de Django, y un empleado sin permisos asignados vería la ficha pero
no podría agregar una medida.

Las pantallas «solo dueño» (Categorías, Usuarios) sobreescriben
`has_module_permission` con `request.user.is_superuser`.

### 3.2 Plantillas

- **Nueva** `templates/admin/change_form_object_tools.html`: solo el enlace «Ver
  en el sitio». Saca «Historial».
- `templates/admin/base_site.html`: sin cambios de estructura. El rail ya se arma
  desde `menu_panel`; al desregistrar modelos desaparecen solos.
- `templates/admin/dacars_index.html`: el texto de «Cómo funciona» y las tarjetas
  de métricas cambian según §4. La estructura no.
- `templates/admin/app_index.html`: se puede borrar. Sin enlaces que lleguen y
  con `has_module_permission` uniforme, la página no aporta. Si se borra, la
  URL sigue existiendo y usa la de fábrica; mejor redirigirla al tablero desde
  el `AdminSite` (`app_index` → `redirect("admin:index")`).

### 3.3 Por archivo

**`sitio/templatetags/panel.py`**

- `ORDEN_MENU` queda `["producto", "variante", "categoria", "user"]`.
- `AJUSTES` queda `{"categoria", "user"}`.
- Se borran las entradas de `pedido`, `itempedido`, `movimiento`, `marca`,
  `group` en `ICONOS_MODELO` (o se dejan: no molestan).

**`catalogo/models.py`**

- `Variante.Meta.verbose_name_plural = "precios y existencias"`. Es lo que la
  barra lateral muestra. Migración de metadatos, no toca datos.

**`catalogo/admin.py`**

- `ProductoAdmin(PantallaPanel)`: `list_display = ("nombre", "categoria",
  "precios", "existencias", "activo")`, `list_editable = ("activo",)`,
  `list_filter = ("categoria", FiltroCompletitud)`, sin `actions`, sin
  `prepopulated_fields`, sin `save_on_top`. `FIELDSETS_ALTA` sin `marca`.
  `fieldsets` con los tres bloques de §2. `FiltroCompletitud` con dos opciones:
  `sin_foto`, `sin_precio` (hoy `sin_variante`; conviene mantener el valor
  `sin_variante` en la URL porque el tablero enlaza con él).
- `VarianteInline`: `CAMPOS_ALTA = ("nombre", "costo", "precio", "stock",
  "stock_minimo")` (igual), `CAMPOS = ("nombre", "costo", "precio", "stock",
  "stock_minimo", "situacion", "activa")`.
- `ImagenInline`: `CAMPOS = ("vista", "imagen", "tipo", "referencia", "orden")`,
  `CAMPOS_ALTA = ("imagen", "tipo")`.
- `VarianteAdmin(PantallaPanel)`: `list_display = ("producto_enlace", "medida",
  "costo", "precio", "stock", "stock_minimo", "situacion", "activa")`,
  `list_display_links = None`, `has_add_permission → False`,
  `list_filter = (FiltroSituacion, "producto__categoria")`, `ordering` por
  disponible ascendente (anotado en `get_queryset`). `FiltroSituacion` pierde la
  opción «reservadas». Sin `fieldsets` (la ficha propia deja de usarse; se puede
  dejar el cambio individual funcionando para no romper `list_editable`).
- `CategoriaAdmin(PantallaPanel)`: `has_module_permission → is_superuser`,
  `fields = ("nombre", "descripcion", "imagen", "servicio", "activa")`, sin
  `prepopulated_fields`, sin `list_editable`. Se borra `FIELDSETS_ALTA` y el
  `get_prepopulated_fields`: ya no hay alta desde ventana emergente.
- `MarcaAdmin`: se borra. `admin.site.unregister` no hace falta si no se
  registra.
- Nuevo bloque al pie de la ficha del producto con los últimos movimientos:
  un `readonly_fields = ("historial",)` en un fieldset «Historial de
  existencias» colapsado, que renderiza una tabla chica con `format_html`.

**`inventario/admin.py`**

- `MovimientoAdmin(PantallaPanel)`: `has_module_permission → False` (no aparece
  en el rail), `has_view_permission → False`, `has_change_permission → False`,
  `has_delete_permission → False`, `has_add_permission → is_staff`.
- `response_add` redirige a `admin:catalogo_variante_changelist` con el mensaje
  «X queda con N unidades», que ya existe. Sin esto, al guardar Django manda al
  tablero (no tiene permiso de ver la lista), y lo natural después de cargar
  mercancía es ver la planilla con el número nuevo.
- `autocomplete_fields = ("variante",)` sigue funcionando: usa `search_fields`
  de `VarianteAdmin`.

**`dacars/admin.py`** (el `AdminSite`)

- Registrar `User` con un `UsuarioPanelAdmin(PantallaPanel, UserAdmin)`. Hereda
  de `UserAdmin` a propósito: es lo que trae la vista de cambio de contraseña
  (`<id>/password/`) y el widget que muestra la clave como «ya cargada» sin
  exponer el hash. Se recorta a `fieldsets = ((None, {"fields": ("username",
  "first_name", "password", "is_active")}),)`, `add_fieldsets` de fábrica
  (usuario y contraseña dos veces), `list_display = ("username", "first_name",
  "is_active")`, `list_filter = ()`, `filter_horizontal = ()`,
  `has_module_permission → is_superuser`, y `save_model` fuerza
  `is_staff = True`.
- No registrar `Group`. `django.contrib.auth` registra `User` y `Group` en
  `admin.site` durante `autodiscover`, que corre en `AdminConfig.ready()`. Por
  eso el `unregister(Group)`, el `unregister(User)` y el registro del propio
  van en `PanelDacarsConfig.ready()`, **después** de `super().ready()`. En el
  módulo `dacars/admin.py` sería demasiado temprano: se importa al cargar
  `settings`, antes de que exista nada registrado.
- `app_index` redirige al tablero.
- `_alertas` y `_resumen` cambian según §4.

**`static/css/panel.css`**

- Nada obligatorio. Al desaparecer acciones, `save_on_top` y las emergentes,
  quedan reglas huérfanas (`.actions`, `.related-widget-wrapper`,
  `#changelist-form .action-*`, el bloque de `submit-row` superior). Se limpian
  al final, con la hoja delante, para no dejar CSS muerto.
- No se colorea la fila entera en «Precios y existencias»: Django no deja
  ponerle una clase a un `tr` del listado sin JavaScript. La situación se lee
  en la columna coloreada que ya existe, y el orden por defecto pone primero
  lo urgente.

### 3.4 Pruebas que cambian

| Prueba | Qué pasa |
|---|---|
| `dacars/tests.py::ElPanelSeDibuja.test_todas_las_pantallas_abren` | Salen `pedidos`, `movimientos` (lista) y `existencias reservadas`. Entran `usuarios` (como superuser) y un caso de empleado `is_staff` que ve Productos y no ve Usuarios. |
| `dacars/tests.py::test_la_ficha_de_un_pedido_abre` | Se borra (opción A de §4) o se mantiene (opción B). |
| `catalogo/tests.py::test_la_categoria_se_puede_crear_desde_el_alta` | Se borra: ya no hay «+» al lado del selector. Se reemplaza por «el selector de categoría no ofrece crear una nueva». |
| `catalogo/tests.py::test_el_alta_pide_lo_minimo…` | Se suma `marca` a los campos que no se preguntan y `slug` sale de los que sí aparecen al editar. |
| `catalogo/tests.py::test_crear_un_producto_deja_su_precio_y_su_costo` | Se quita `"marca": ""` del POST. |
| `inventario/tests.py::test_editar_las_existencias_desde_el_panel_deja_un_ajuste` y `test_editar_solo_el_precio…` | Postean contra la ficha de la variante, que sigue existiendo (hace falta para `list_editable`). Deberían pasar sin cambios; si se define `fields` en `VarianteAdmin`, sacar del POST `sku`, `orden` y `precio_antes`. Conviene sumar una prueba que postee contra la planilla (`changelist` con `_save`), que es el camino que va a usar el comercio. |
| `inventario/tests.py::test_el_historial_se_puede_mirar_pero_no_editar` | Cambia a «no hay pantalla de historial: la lista y la ficha dan 403, el registro sigue escribiéndose». |
| `inventario/tests.py::test_el_tablero_muestra_lo_que_hay_que_atender` | Igual. |
| Nueva | Un `is_staff` sin permisos asignados abre Productos y guarda un producto. Es la garantía de que no hacen falta grupos. |
| Nueva | La ficha del producto no trae «Guardar y agregar otro» ni «Historial». |

---

## 4. Decisión pendiente: los pedidos

El panel mínimo no tiene sección de pedidos. Pero el sitio público **enciende el
carrito solo** en cuanto un producto tiene una medida con precio: la ficha
cambia «Cotizar por WhatsApp» por «Agregar al carrito», y cada pedido **reserva
existencias**. Si el panel no muestra pedidos, esas reservas nunca se confirman
ni se liberan, y las alertas de stock quedan mal (lo reservado descuenta de lo
disponible). No se puede sacar Pedidos del panel y dejar el carrito prendido.

Dos opciones coherentes:

### Opción A (recomendada): sin carrito

El sitio vende como vende hoy, por WhatsApp. Un producto con precio muestra el
precio y el botón de WhatsApp, con el precio incluido en el mensaje. Sin
pedidos, sin reservas: las existencias solo se mueven desde el panel.

- `templates/catalogo/producto.html` (líneas 120–159): el formulario de compra se
  reemplaza por el botón de cotizar, que ya existe para los productos sin precio.
- `templates/sitio/_encabezado.html` línea 33: sale el enlace al carrito.
- `dacars/urls.py`: sale `include("pedidos.urls")`. `dacars/settings.py`: sale el
  context processor `pedidos.context_processors.carrito`. La app `pedidos` queda
  instalada (sus tablas existen en producción); se saca de `INSTALLED_APPS`
  en una fase posterior, con una migración que borre las tablas.
- `pedidos/admin.py`: se borra.
- Tablero: la alerta «Pedidos sin responder» se va. Las tarjetas «pedidos este
  mes», «vendido este mes» y «ganado este mes» se reemplazan por tres que
  hablan del catálogo: **con precio publicado**, **bajo el mínimo** y
  **unidades en existencia**. «Cómo funciona» pasa a tres frases sobre
  precios, existencias y «a cotizar».
- `pedidos/tests.py` se borra entero; `catalogo/tests.py` pierde
  `test_la_ficha_a_cotizar_no_ofrece_carrito` y gana «un producto con precio
  muestra el precio y cotiza por WhatsApp».
- Queda intacto: el modelo `Variante.reservado` (siempre 0), `servicios.reservar`
  y `liberar` (sin llamadores). Se limpian en la misma fase posterior.

Es la opción consistente con «solamente eso» y con cómo opera DACARS. Cambia el
sitio público, por eso la decide el dueño.

### Opción B: carrito prendido, pedidos mínimos

Pedidos vuelve al rail, en cuarto lugar, reducido a lo mínimo: lista con número,
fecha, cliente, teléfono (enlace a WhatsApp), total y estado; ficha de solo
lectura con tres botones (confirmar, entregar, cancelar) en lugar del selector
de estado; sin acciones en lote, sin jerarquía por fecha, sin filtro por ciudad.
El tablero se queda como está.

Cuesta una sección más y obliga a que alguien mire los pedidos todos los días.

---

## 5. Fases

Cada fase deja el panel funcionando y las pruebas en verde. Se puede parar
después de cualquiera.

| # | Fase | Qué incluye | Depende de §4 |
|---|---|---|---|
| 1 | La base | `PantallaPanel`, `change_form_object_tools.html`, permisos uniformes, sin Grupos, Usuarios mínimo, `app_index` al tablero | No |
| 2 | Productos | Ficha y lista simplificadas, sin marca, sin «+», historial de existencias al pie | No |
| 3 | Precios y existencias | Renombrar, columnas, sin alta, enlace a la ficha del producto, orden por situación. Movimientos fuera del rail, «Llegó mercancía» redirige a la planilla | No |
| 4 | Pedidos | Opción A o B | **Sí** |
| 5 | Tablero | Métricas y «Cómo funciona» según la opción elegida | Sí |
| 6 | Limpieza | CSS huérfano, `README.md` (sección «El panel»), y si fue A: `pedidos` fuera de `INSTALLED_APPS`, `reservado` y `Marca` fuera del modelo con migración | Sí |

Fases 1 a 3 se pueden hacer ya. La 4 espera la respuesta a §4.

Verificación al cierre de cada fase:

```bash
python manage.py test
python manage.py runserver   # y recorrer: tablero, productos, alta, ficha, precios, llegó mercancía
```

Y con un usuario `is_staff` sin ser superuser, comprobar que ve tres secciones y
puede guardar un producto.

---

## 6. Lo que queda fuera a propósito

- **Avisos de stock por correo o WhatsApp.** Hoy la alerta vive en el tablero y
  en el contador de la barra lateral, que se ve en todas las pantallas. Mandar
  un aviso afuera pide SMTP o una API de WhatsApp: infraestructura nueva para
  un panel que se busca achicar. Si más adelante hace falta, es un comando de
  gestión (`alertas_stock`) corrido por cron en Railway.
- **Importar precios desde Excel.** Con 19 productos, la planilla del panel
  alcanza.
- **Volver a mostrar** `precio_antes`, la marca o el SEO por producto. Los campos
  quedan en la base; es sumar una línea a `fields` cuando se necesite.
- **Borrar campos del modelo** (`slug`, `orden`, `seo_*`, `alt`). Los usa el
  sitio público o se calculan solos. No molestan escondidos.
