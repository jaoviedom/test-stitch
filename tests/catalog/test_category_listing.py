from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventario.models import Categoria


class CategoryListingUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de dominio y servicio ListarCategoriasService (HU-003)
    """

    def setUp(self):
        self.c1 = Categoria.objects.create(nombre='Bebidas', slug='bebidas', descripcion='Refrescos')
        self.c2 = Categoria.objects.create(nombre='Abarrotes', slug='abarrotes', descripcion='Alimentos secos')
        self.c3 = Categoria.objects.create(nombre='Lácteos y Quesos', slug='lacteos-y-quesos', descripcion='Leche y yogur')
        self.c4 = Categoria.objects.create(nombre='Bebidas Alcohólicas', slug='bebidas-alcoholicas', descripcion='Licores varios')

    def test_servicio_listar_categorias_retorna_ordenadas_por_nombre(self):
        """
        Escenario: Listado retorna todas las categorías ordenadas alfabéticamente
        """
        from inventario.services import ListarCategoriasService

        qs = ListarCategoriasService.get_queryset()
        nombres = list(qs.values_list('nombre', flat=True))
        self.assertEqual(nombres, ['Abarrotes', 'Bebidas', 'Bebidas Alcohólicas', 'Lácteos y Quesos'])

    def test_servicio_listar_categorias_filtra_por_busqueda(self):
        """
        Escenario: Filtrado case-insensitive por nombre o descripción
        """
        from inventario.services import ListarCategoriasService

        qs = ListarCategoriasService.get_queryset(query='bebidas')
        nombres = list(qs.values_list('nombre', flat=True))
        self.assertEqual(len(nombres), 2)
        self.assertIn('Bebidas', nombres)
        self.assertIn('Bebidas Alcohólicas', nombres)
        self.assertNotIn('Abarrotes', nombres)

    def test_servicio_busqueda_sin_coincidencias_retorna_vacio(self):
        """
        Escenario: Búsqueda con término no coincidente retorna QuerySet vacío
        """
        from inventario.services import ListarCategoriasService

        qs = ListarCategoriasService.get_queryset(query='ElectrodomésticosInexistentes')
        self.assertEqual(qs.count(), 0)


class CategoryListingViewsAndRBACSecurityTests(TestCase):
    """
    Pruebas de integración para vistas, paginación, filtros RBAC y UI/UX (HU-003)
    """

    def setUp(self):
        self.client = Client()

        content_type, _ = ContentType.objects.get_or_create(app_label='inventario', model='categoria')
        self.perm_view_categoria, _ = Permission.objects.get_or_create(
            codename='view_categoria',
            content_type=content_type,
            defaults={'name': 'Puede ver categorías'},
        )
        self.perm_add_categoria, _ = Permission.objects.get_or_create(
            codename='add_categoria',
            content_type=content_type,
            defaults={'name': 'Puede agregar categorías'},
        )
        self.perm_change_categoria, _ = Permission.objects.get_or_create(
            codename='change_categoria',
            content_type=content_type,
            defaults={'name': 'Puede cambiar/editar categorías'},
        )

        # Grupos / Roles
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')
        self.grupo_admin.permissions.add(
            self.perm_view_categoria,
            self.perm_add_categoria,
            self.perm_change_categoria,
        )

        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')
        self.grupo_vendedor.permissions.add(self.perm_view_categoria)

        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')

        # Usuarios
        self.admin_user = User.objects.create_user(username='admin_list', password='password123', is_staff=True)
        self.admin_user.groups.add(self.grupo_admin)

        self.vendedor_user = User.objects.create_user(username='vendedor_list', password='password123')
        self.vendedor_user.groups.add(self.grupo_vendedor)

        self.base_user = User.objects.create_user(username='base_list', password='password123')
        self.base_user.groups.add(self.grupo_usuario)

        self.direct_perm_user = User.objects.create_user(username='direct_list', password='password123')
        self.direct_perm_user.user_permissions.add(self.perm_view_categoria)

    def test_usuario_anonimo_redirigido_al_login_al_listar(self):
        """
        Escenario RBAC NFR: Visitante no autenticado es redirigido a login
        """
        url = reverse('inventario:lista_categorias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
        self.assertIn('next=/inventario/categorias/', response.url)

    def test_usuario_rol_usuario_recibe_403_forbidden(self):
        """
        Escenario RBAC: Usuario con rol base recibe 403 Forbidden
        """
        self.client.force_login(self.base_user)
        url = reverse('inventario:lista_categorias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_usuario_rol_vendedor_puede_listar_categorias(self):
        """
        Escenario RBAC: Vendedor puede listar pero no ve botones de creación ni edición
        """
        Categoria.objects.create(nombre='Panadería', slug='panaderia')
        self.client.force_login(self.vendedor_user)
        url = reverse('inventario:lista_categorias')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panadería')
        # No debe contener enlaces a crear ni editar
        self.assertNotContains(response, reverse('inventario:crear_categoria'))

    def test_usuario_con_permiso_directo_view_categoria_puede_listar(self):
        """
        Escenario RBAC: Usuario con permiso directo accede exitosamente
        """
        self.client.force_login(self.direct_perm_user)
        url = reverse('inventario:lista_categorias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_vista_listado_paginado_primera_y_segunda_pagina(self):
        """
        Escenario: Paginación de categorías (10 por página)
        """
        # Crear 15 categorías
        Categoria.objects.all().delete()
        for i in range(1, 16):
            Categoria.objects.create(
                nombre=f'Categoría {i:02d}',
                slug=f'categoria-{i:02d}',
                descripcion=f'Descripción {i}',
            )

        self.client.force_login(self.admin_user)
        url = reverse('inventario:lista_categorias')

        # Primera página
        resp1 = self.client.get(url)
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue('page_obj' in resp1.context)
        page1 = resp1.context['page_obj']
        self.assertEqual(len(page1.object_list), 10)
        self.assertTrue(page1.has_next())
        self.assertFalse(page1.has_previous())

        # Segunda página
        resp2 = self.client.get(f'{url}?page=2')
        self.assertEqual(resp2.status_code, 200)
        page2 = resp2.context['page_obj']
        self.assertEqual(len(page2.object_list), 5)
        self.assertFalse(page2.has_next())
        self.assertTrue(page2.has_previous())

    def test_vista_busqueda_por_parametro_q(self):
        """
        Escenario: Búsqueda con ?q= filtra los resultados adecuadamente
        """
        Categoria.objects.all().delete()
        Categoria.objects.create(nombre='Bebidas', slug='bebidas')
        Categoria.objects.create(nombre='Abarrotes', slug='abarrotes')
        Categoria.objects.create(nombre='Bebidas Calientes', slug='bebidas-calientes')

        self.client.force_login(self.admin_user)
        url = reverse('inventario:lista_categorias')

        response = self.client.get(url, {'q': 'bebidas'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bebidas')
        self.assertContains(response, 'Bebidas Calientes')
        self.assertNotContains(response, 'Abarrotes')

    def test_vista_busqueda_sin_resultados_muestra_estado_vacio(self):
        """
        Escenario: Búsqueda sin coincidencias muestra mensaje accesible y botón de limpiar
        """
        Categoria.objects.create(nombre='Golosinas', slug='golosinas')

        self.client.force_login(self.admin_user)
        url = reverse('inventario:lista_categorias')

        response = self.client.get(url, {'q': 'NoExisteNinguna'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontraron categorías que coincidan')
        self.assertContains(response, 'Limpiar búsqueda')

    def test_paginacion_preserva_parametro_de_busqueda_en_enlaces(self):
        """
        Escenario: Los links de paginación mantienen el término de búsqueda ?q=
        """
        Categoria.objects.all().delete()
        for i in range(1, 16):
            Categoria.objects.create(
                nombre=f'Fruta {i:02d}',
                slug=f'fruta-{i:02d}',
            )

        self.client.force_login(self.admin_user)
        url = reverse('inventario:lista_categorias')

        response = self.client.get(url, {'q': 'Fruta'})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Debe contener q=Fruta en el enlace de la siguiente página
        self.assertIn('q=Fruta', content)
        self.assertIn('page=2', content)

    def test_nfr_accesibilidad_buscador_y_paginacion(self):
        """
        Escenario NFR: Input de búsqueda con label accesible y controles con aria-label
        """
        Categoria.objects.create(nombre='Verduras', slug='verduras')

        self.client.force_login(self.admin_user)
        url = reverse('inventario:lista_categorias')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        self.assertIn('id="search-input"', content)
        self.assertIn('for="search-input"', content)
        self.assertIn('tabular-nums', content)
