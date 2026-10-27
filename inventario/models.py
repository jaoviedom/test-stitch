from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Categoria(models.Model):
    """
    Modelo para clasificar y organizar los artículos e inventario de la tienda.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la categoría",
        help_text="Nombre identificador único de la categoría.",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name="Slug URL",
        help_text="Identificador amigable generado automáticamente a partir del nombre.",
    )
    descripcion = models.TextField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Descripción",
        help_text="Detalle opcional sobre los artículos que engloba la categoría.",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la categoría se encuentra disponible para asociar productos.",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        db_table = 'inventario_categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self) -> str:
        return self.nombre

    @property
    def total_productos(self) -> int:
        """
        Retorna la cantidad de productos asociados (0 por defecto si la relación aún no existe).
        """
        if hasattr(self, 'productos'):
            return self.productos.count()
        return 0

    def clean(self) -> None:
        super().clean()
        if self.nombre:
            nombre_limpio = self.nombre.strip()
            # Validación case-insensitive de duplicidad excluyendo la propia instancia
            query = Categoria.objects.filter(nombre__iexact=nombre_limpio)
            if self.pk:
                query = query.exclude(pk=self.pk)
            if query.exists():
                raise ValidationError({'nombre': 'La categoría ya se encuentra registrada'})

    def save(self, *args, **kwargs) -> None:
        if not self.slug and self.nombre:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class Producto(models.Model):
    """
    Modelo para el catálogo de productos y control de existencias en tienda (HU-004).
    Relación 1:N con Categoria: cada producto pertenece a una categoría y una categoría agrupa muchos productos.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del producto",
        help_text="Nombre identificador único del producto.",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name="Slug URL",
        help_text="Identificador amigable generado automáticamente a partir del nombre.",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Categoría",
        help_text="Categoría a la que pertenece el producto.",
    )
    descripcion = models.TextField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Descripción",
        help_text="Detalle opcional sobre las especificaciones del artículo.",
    )
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio de compra",
        help_text="Costo unitario de adquisición del producto.",
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio de venta",
        help_text="Precio unitario de venta al público.",
    )
    stock_actual = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock actual",
        help_text="Cantidad de unidades físicas disponibles en inventario.",
    )
    stock_minimo = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock mínimo",
        help_text="Umbral para alertas tempranas de reabastecimiento.",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el producto está disponible para venta y catálogo.",
    )
    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True,
        verbose_name="Imagen del producto",
        help_text="Fotografía o ilustración del producto (opcional).",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        db_table = "inventario_producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre

    @property
    def en_stock(self) -> bool:
        """
        Retorna True si el producto cuenta con existencias disponibles físicas.
        """
        return self.stock_actual > 0

    @property
    def imagen_url(self) -> str:
        """
        Retorna el URL de la imagen cargada o la imagen genérica predeterminada.
        """
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        from django.templatetags.static import static
        return static('images/default-product.svg')

    def clean(self) -> None:
        super().clean()
        if self.nombre:
            nombre_limpio = self.nombre.strip()
            query = Producto.objects.filter(nombre__iexact=nombre_limpio)
            if self.pk:
                query = query.exclude(pk=self.pk)
            if query.exists():
                raise ValidationError({'nombre': 'El producto ya se encuentra registrado'})

        if self.precio_compra is not None and self.precio_compra < 0:
            raise ValidationError({'precio_compra': 'El precio de compra no puede ser negativo.'})

        if self.precio_venta is not None and self.precio_venta < 0:
            raise ValidationError({'precio_venta': 'El precio de venta no puede ser negativo.'})

        if self.stock_actual is not None and self.stock_actual < 0:
            raise ValidationError({'stock_actual': 'El stock actual no puede ser negativo.'})

        if self.stock_minimo is not None and self.stock_minimo < 0:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede ser negativo.'})

    def save(self, *args, **kwargs) -> None:
        if not self.slug and self.nombre:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

