from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch


class CategoryRegistrationUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de dominio y servicio CrearCategoriaService (HU-001)
    """

    def setUp(self):
        # Configuración inicial de roles y permisos
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')

    def test_servicio_crear_categoria_con_nombre_y_descripcion(self):
        """
        Escenario: Creación exitosa de categoría con nombre, descripción, slug y estado activo
        """
        from inventario.services import CrearCategoriaService
        from inventario.models import Categoria

        categoria = CrearCategoriaService.execute(
            nombre='Bebidas y Licores',
            descripcion='Bebidas frías, jugos naturales, gaseosas y licores varios',
            activo=True,
        )

        self.assertIsNotNone(categoria.pk)
        self.assertEqual(categoria.nombre, 'Bebidas y Licores')
        self.assertEqual(categoria.slug, 'bebidas-y-licores')
        self.assertEqual(categoria.descripcion, 'Bebidas frías, jugos naturales, gaseosas y licores varios')
        self.assertTrue(categoria.activo)

        # Verificar persistencia en base de datos
        db_categoria = Categoria.objects.get(pk=categoria.pk)
        self.assertEqual(db_categoria.nombre, 'Bebidas y Licores')
        self.assertEqual(db_categoria.slug, 'bebidas-y-licores')

    def test_servicio_crear_categoria_sin_descripcion_opcional(self):
        """
        Escenario: Creación de categoría sin descripción (campo opcional)
        """
        from inventario.services import CrearCategoriaService

        categoria = CrearCategoriaService.execute(
            nombre='Snacks y Golosinas',
        )

        self.assertIsNotNone(categoria.pk)
        self.assertEqual(categoria.nombre, 'Snacks y Golosinas')
        self.assertEqual(categoria.slug, 'snacks-y-golosinas')
        self.assertEqual(categoria.descripcion, '')
        self.assertTrue(categoria.activo)

    def test_servicio_slug_normalizado_con_caracteres_especiales(self):
        """
        Escenario: Normalización correcta de caracteres especiales y acentos en slug
        """
        from inventario.services import CrearCategoriaService

        categoria = CrearCategoriaService.execute(
            nombre='Cafés & Tés Especiales',
        )

        self.assertEqual(categoria.slug, 'cafes-tes-especiales')

    def test_servicio_rechazo_nombre_duplicado_case_insensitive(self):
        """
        Escenario: Rechazo de duplicidad en nombres independientemente de mayúsculas/minúsculas
        """
        from inventario.services import CrearCategoriaService
        from django.core.exceptions import ValidationError

        CrearCategoriaService.execute(nombre='Abarrotes')

        with self.assertRaises(ValidationError) as ctx:
            CrearCategoriaService.execute(nombre='abarrotes')

        self.assertIn('La categoría ya se encuentra registrada', str(ctx.exception))

    def test_servicio_es_atomico_ante_fallos_de_persistencia(self):
        """
        Escenario NFR: Atomicidad garantizada con rollback completo ante excepción
        """
        from inventario.services import CrearCategoriaService
        from inventario.models import Categoria

        initial_count = Categoria.objects.count()

        with patch.object(Categoria, 'save', side_effect=RuntimeError('Database disk failure')):
            with self.assertRaises(RuntimeError):
                CrearCategoriaService.execute(
                    nombre='Categoría Fallida',
                    descripcion='No debe persistirse',
                )

        self.assertEqual(Categoria.objects.count(), initial_count)
        self.assertFalse(Categoria.objects.filter(nombre='Categoría Fallida').exists())


class CategoryRegistrationViewsAndRBACSecurityTests(TestCase):
    """
    Pruebas de integración, controladores HTTP, seguridad RBAC y plantillas UI (HU-001)
    """

    def setUp(self):
        self.client = Client()

        # Configuración de permiso
        content_type, _ = ContentType.objects.get_or_create(app_label='inventario', model='categoria')
        self.perm_add_categoria, _ = Permission.objects.get_or_create(
            codename='add_categoria',
            content_type=content_type,
            defaults={'name': 'Puede agregar categorías'},
        )
        self.perm_view_categoria, _ = Permission.objects.get_or_create(
            codename='view_categoria',
            content_type=content_type,
            defaults={'name': 'Puede ver categorías'},
        )

        # Grupos / Roles
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')
        self.grupo_admin.permissions.add(self.perm_add_categoria, self.perm_view_categoria)

        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')

        # Usuarios
        self.admin_user = User.objects.create_user(username='admin_user', password='password123', is_staff=True)
        self.admin_user.groups.add(self.grupo_admin)

        self.base_user = User.objects.create_user(username='base_user', password='password123')
        self.base_user.groups.add(self.grupo_usuario)

        self.vendedor_user = User.objects.create_user(username='vendedor_user', password='password123')
        self.vendedor_user.groups.add(self.grupo_vendedor)

        self.direct_perm_user = User.objects.create_user(username='direct_user', password='password123')
        self.direct_perm_user.user_permissions.add(self.perm_add_categoria)

    def test_usuario_anonimo_redirigido_al_login(self):
        """
        Escenario RBAC NFR: Visitante no autenticado es redirigido a login
        """
        url = reverse('inventario:crear_categoria')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
        self.assertIn('next=/inventario/categorias/crear/', response.url)

    def test_usuario_rol_usuario_recibe_403_forbidden(self):
        """
        Escenario RBAC: Usuario con rol 'usuario' recibe 403 Forbidden al intentar acceder o crear
        """
        self.client.force_login(self.base_user)
        url = reverse('inventario:crear_categoria')

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 403)

        post_response = self.client.post(url, {'nombre': 'Intento Ilegal'})
        self.assertEqual(post_response.status_code, 403)

    def test_usuario_rol_vendedor_sin_permiso_recibe_403_forbidden(self):
        """
        Escenario RBAC: Usuario vendedor (sin add_categoria) recibe 403 Forbidden
        """
        self.client.force_login(self.vendedor_user)
        url = reverse('inventario:crear_categoria')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_permiso_directo_puede_acceder_al_formulario(self):
        """
        Escenario RBAC: Usuario no administrador pero con permiso directo puede acceder
        """
        self.client.force_login(self.direct_perm_user)
        url = reverse('inventario:crear_categoria')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_creacion_exitosa_categoria_por_administrador(self):
        """
        Escenario: Administrador completa formulario y categoría se crea exitosamente
        """
        from inventario.models import Categoria

        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_categoria')

        payload = {
            'nombre': 'Lácteos y Derivados',
            'descripcion': 'Leche entera, yogures, quesos frescos y madurados',
            'activo': 'on',
        }

        response = self.client.post(url, payload, follow=True)

        self.assertRedirects(response, reverse('inventario:lista_categorias'))

        # Verificar en base de datos
        categoria = Categoria.objects.get(nombre='Lácteos y Derivados')
        self.assertEqual(categoria.slug, 'lacteos-y-derivados')
        self.assertEqual(categoria.descripcion, 'Leche entera, yogures, quesos frescos y madurados')
        self.assertTrue(categoria.activo)

        # Mensaje de confirmación flash
        messages = list(response.context['messages'])
        self.assertTrue(any('creada exitosamente' in m.message.lower() or 'registrada' in m.message.lower() for m in messages))

    def test_formulario_rechaza_nombre_duplicado_con_error_accesible(self):
        """
        Escenario: Intento de registrar categoría duplicada muestra error accesible
        """
        from inventario.models import Categoria

        Categoria.objects.create(nombre='Abarrotes', slug='abarrotes')

        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_categoria')

        response = self.client.post(url, {'nombre': 'abarrotes', 'descripcion': 'Duplicado'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'La categoría ya se encuentra registrada')
        # Aserción NFR de accesibilidad
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'aria-invalid="true"')

    def test_formulario_validacion_nombre_vacio_y_longitudes_maximas(self):
        """
        Escenario: Rechazo de campos vacíos o con longitud excedida
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_categoria')

        # Nombre vacío
        response_vacio = self.client.post(url, {'nombre': ''})
        self.assertEqual(response_vacio.status_code, 200)
        self.assertContains(response_vacio, 'role="alert"')

        # Nombre que excede 100 caracteres
        nombre_largo = 'X' * 105
        response_largo = self.client.post(url, {'nombre': nombre_largo})
        self.assertEqual(response_largo.status_code, 200)
        self.assertContains(response_largo, 'role="alert"')

    def test_nfr_accesibilidad_elementos_label_asociados_a_inputs(self):
        """
        Escenario NFR: Todos los inputs del formulario cuentan con <label for="...">
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:crear_categoria')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        self.assertIn('for="id_nombre"', content)
        self.assertIn('for="id_descripcion"', content)
        self.assertIn('for="id_activo"', content)
