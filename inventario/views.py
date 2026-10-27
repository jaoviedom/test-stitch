from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from inventario.models import Categoria, Producto
from inventario.forms import CategoriaForm, ProductoForm
from inventario.services import (
    CrearCategoriaService,
    EditarCategoriaService,
    ListarCategoriasService,
    CrearProductoService,
)


def dashboard_view(request):
    """
    Vista principal del panel de administración TeckStore Dashboard
    """
    context = {
        'active_nav': 'productos',
        'user_name': request.user.first_name if request.user.is_authenticated and request.user.first_name else 'Sara Jensen',
        'user_role': 'Administradora' if request.user.is_staff else 'Usuario',
    }
    return render(request, 'inventario/dashboard.html', context)


@login_required
@permission_required('inventario.view_categoria', raise_exception=True)
def categorias_view(request):
    """
    Vista protegida de categorías con soporte para búsqueda y paginación (HU-003)
    """
    q = (request.GET.get('q') or "").strip()
    qs = ListarCategoriasService.get_queryset(query=q)

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'active_nav': 'categorias',
        'page_obj': page_obj,
        'categorias': page_obj.object_list,
        'q': q,
        'total_categorias': qs.count(),
        'user_name': request.user.first_name if request.user.first_name else request.user.username,
        'user_role': 'Administradora' if request.user.is_staff else 'Usuario',
    }
    return render(request, 'inventario/categoria_list.html', context)


@login_required
@permission_required('inventario.add_categoria', raise_exception=True)
def crear_categoria_view(request):
    """
    Vista para el registro de una nueva categoría de productos (HU-001)
    """
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = CrearCategoriaService.execute(
                nombre=form.cleaned_data['nombre'],
                descripcion=form.cleaned_data['descripcion'],
                activo=form.cleaned_data['activo'],
            )
            messages.success(
                request,
                f'La categoría "{categoria.nombre}" ha sido creada exitosamente.',
            )
            return redirect('inventario:lista_categorias')
    else:
        form = CategoriaForm()

    context = {
        'form': form,
        'active_nav': 'categorias',
        'user_name': request.user.first_name if request.user.first_name else request.user.username,
        'user_role': 'Administradora' if request.user.is_staff else 'Usuario',
    }
    return render(request, 'inventario/categoria_form.html', context)


@login_required
@permission_required('inventario.change_categoria', raise_exception=True)
def editar_categoria_view(request, pk: int):
    """
    Vista para la edición y actualización de una categoría existente (HU-002)
    """
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = EditarCategoriaService.execute(
                categoria=categoria,
                nombre=form.cleaned_data['nombre'],
                descripcion=form.cleaned_data['descripcion'],
                activo=form.cleaned_data['activo'],
            )
            messages.success(
                request,
                f'La categoría "{categoria.nombre}" ha sido actualizada exitosamente.',
            )
            return redirect('inventario:lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)

    context = {
        'form': form,
        'categoria': categoria,
        'active_nav': 'categorias',
        'user_name': request.user.first_name if request.user.first_name else request.user.username,
        'user_role': 'Administradora' if request.user.is_staff else 'Usuario',
    }
    return render(request, 'inventario/categoria_form.html', context)


@login_required
@permission_required('inventario.add_producto', raise_exception=True)
def crear_producto_view(request):
    """
    Vista para el registro de un nuevo producto en el catálogo (HU-004)
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = CrearProductoService.execute(
                nombre=form.cleaned_data['nombre'],
                categoria=form.cleaned_data['categoria'],
                precio_compra=form.cleaned_data['precio_compra'],
                precio_venta=form.cleaned_data['precio_venta'],
                stock_actual=form.cleaned_data['stock_actual'],
                stock_minimo=form.cleaned_data['stock_minimo'],
                descripcion=form.cleaned_data['descripcion'],
                activo=form.cleaned_data['activo'],
                imagen=form.cleaned_data.get('imagen'),
            )
            messages.success(
                request,
                f'El producto "{producto.nombre}" ha sido creado exitosamente.',
            )
            return redirect('inventario:crear_producto')
    else:
        form = ProductoForm()

    context = {
        'form': form,
        'active_nav': 'productos',
        'user_name': request.user.first_name if request.user.first_name else request.user.username,
        'user_role': 'Administradora' if request.user.is_staff else 'Usuario',
    }
    return render(request, 'inventario/producto_form.html', context)
