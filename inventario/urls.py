from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('categorias/', views.categorias_view, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria_view, name='crear_categoria'),
    path('categorias/<int:pk>/editar/', views.editar_categoria_view, name='editar_categoria'),
    path('productos/crear/', views.crear_producto_view, name='crear_producto'),
]
