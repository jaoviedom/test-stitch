from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from inventario.models import Categoria, Producto
from decimal import Decimal
from typing import Optional, Any



class CrearCategoriaService:
    """
    Servicio de dominio para el registro atómico y validado de nuevas categorías (HU-001)
    """

    @staticmethod
    @transaction.atomic
    def execute(nombre: str, descripcion: str = "", activo: bool = True) -> Categoria:
        """
        Crea una categoría sanitizando los campos, generando su slug y validando
        unicidad case-insensitive bajo transacción atómica.
        """
        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            raise ValidationError({'nombre': 'El nombre de la categoría es obligatorio.'})

        if len(nombre_limpio) > 100:
            raise ValidationError({'nombre': 'El nombre no puede superar los 100 caracteres.'})

        descripcion_limpia = (descripcion or "").strip()
        if len(descripcion_limpia) > 500:
            raise ValidationError({'descripcion': 'La descripción no puede superar los 500 caracteres.'})

        # Comprobar unicidad case-insensitive
        if Categoria.objects.filter(nombre__iexact=nombre_limpio).exists():
            raise ValidationError('La categoría ya se encuentra registrada')

        slug_generado = slugify(nombre_limpio)

        categoria = Categoria(
            nombre=nombre_limpio,
            slug=slug_generado,
            descripcion=descripcion_limpia,
            activo=activo,
        )
        categoria.save()

        return categoria


class EditarCategoriaService:
    """
    Servicio de dominio para la edición y actualización atómica de categorías existentes (HU-002)
    """

    @staticmethod
    @transaction.atomic
    def execute(categoria: Categoria, nombre: str, descripcion: str = "", activo: bool = True) -> Categoria:
        """
        Actualiza los datos de una categoría, validando unicidad case-insensitive
        (excluyendo la propia categoría) y recalculando el slug de forma determinista.
        """
        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            raise ValidationError({'nombre': 'El nombre de la categoría es obligatorio.'})

        if len(nombre_limpio) > 100:
            raise ValidationError({'nombre': 'El nombre no puede superar los 100 caracteres.'})

        descripcion_limpia = (descripcion or "").strip()
        if len(descripcion_limpia) > 500:
            raise ValidationError({'descripcion': 'La descripción no puede superar los 500 caracteres.'})

        # Comprobar unicidad case-insensitive excluyendo la categoría en edición
        if Categoria.objects.filter(nombre__iexact=nombre_limpio).exclude(pk=categoria.pk).exists():
            raise ValidationError('La categoría ya se encuentra registrada')

        categoria.nombre = nombre_limpio
        categoria.slug = slugify(nombre_limpio)
        categoria.descripcion = descripcion_limpia
        categoria.activo = activo
        categoria.save()

        return categoria


class ListarCategoriasService:
    """
    Servicio de consulta para el listado, búsqueda y filtrado de categorías (HU-003)
    """

    @staticmethod
    def get_queryset(query: str = "") -> QuerySet:
        """
        Retorna el QuerySet ordenado alfabéticamente por nombre,
        aplicando filtro case-insensitive sobre nombre o descripción si se especifica búsqueda.
        """
        qs = Categoria.objects.all().order_by('nombre')
        q = (query or "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
        return qs


class CrearProductoService:
    """
    Servicio de dominio para el registro atómico y validado de nuevos productos (HU-004)
    """

    @staticmethod
    @transaction.atomic
    def execute(
        nombre: str,
        categoria: Categoria,
        precio_compra: Decimal,
        precio_venta: Decimal,
        stock_actual: int = 0,
        stock_minimo: int = 0,
        descripcion: str = "",
        activo: bool = True,
        imagen: Optional[Any] = None,
    ) -> Producto:
        """
        Crea un producto sanitizando datos, generando slug y asegurando unicidad case-insensitive
        y no negatividad en valores bajo transacción atómica.
        """
        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            raise ValidationError({'nombre': 'El nombre del producto es obligatorio.'})

        if len(nombre_limpio) > 100:
            raise ValidationError({'nombre': 'El nombre no puede superar los 100 caracteres.'})

        if not categoria:
            raise ValidationError({'categoria': 'La categoría es obligatoria.'})

        descripcion_limpia = (descripcion or "").strip()
        if len(descripcion_limpia) > 500:
            raise ValidationError({'descripcion': 'La descripción no puede superar los 500 caracteres.'})

        # Comprobar unicidad case-insensitive
        if Producto.objects.filter(nombre__iexact=nombre_limpio).exists():
            raise ValidationError('El producto ya se encuentra registrado')

        # Comprobar precios y stocks no negativos
        if precio_compra is not None and Decimal(str(precio_compra)) < 0:
            raise ValidationError({'precio_compra': 'El precio de compra no puede ser negativo.'})

        if precio_venta is not None and Decimal(str(precio_venta)) < 0:
            raise ValidationError({'precio_venta': 'El precio de venta no puede ser negativo.'})

        if stock_actual is not None and int(stock_actual) < 0:
            raise ValidationError({'stock_actual': 'El stock actual no puede ser negativo.'})

        if stock_minimo is not None and int(stock_minimo) < 0:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede ser negativo.'})

        slug_generado = slugify(nombre_limpio)

        producto = Producto(
            nombre=nombre_limpio,
            slug=slug_generado,
            categoria=categoria,
            descripcion=descripcion_limpia,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            activo=activo,
        )

        if imagen:
            producto.imagen = imagen

        producto.save()
        return producto
