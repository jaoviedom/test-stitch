from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch
from inventario.models import Categoria


class CategoryEditionUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de dominio y servicio EditarCategoriaService (HU-002)
    """

    def setUp(self):
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')
        self.categoria = Categoria.objects.create(
            nombre='Lácteos',
            slug='lacteos',
            descripcion='Productos lácteos básicos',
            activo=True,
        )

    def test_servicio_editar_categoria_exitosamente(self):
        """
        Escenario: Edición exitosa de datos y recálculo automático de slug
        """
        from inventario.services import EditarCategoriaService

        categoria_actualizada = EditarCategoriaService.execute(
            categoria=self.categoria,
            nombre='Lácteos y Quesos',
            descripcion='Quesos frescos, madurados y leches',
            activo=True,
        )

        self.assertEqual(categoria_actualizada.pk, self.categoria.pk)
        self.assertEqual(categoria_actualizada.nombre, 'Lácteos y Quesos')
        self.assertEqual(categoria_actualizada.slug, 'lacteos-y-quesos')
        self.assertEqual(categoria_actualizada.descripcion, 'Quesos frescos, madurados y leches')
        self.assertTrue(categoria_actualizada.activo)

        # Verificar en base de datos
        db_cat = Categoria.objects.get(pk=self.categoria.pk)
        self.assertEqual(db_cat.nombre, 'Lácteos y Quesos')
        self.assertEqual(db_cat.slug, 'lacteos-y-quesos')

    def test_servicio_editar_conservando_mismo_nombre(self):
        """
        Escenario: Actualización exitosa manteniendo el mismo nombre (sin conflicto de unicidad)
        """
        from inventario.services import EditarCategoriaService

        categoria_actualizada = EditarCategoriaService.execute(
            categoria=self.categoria,
            nombre='Lácteos',
            descripcion='Nueva descripción complementaria',
            activo=False,
        )

        self.assertEqual(categoria_actualizada.nombre, 'Lácteos')
        self.assertEqual(categoria_actualizada.slug, 'lacteos')
        self.assertEqual(categoria_actualizada.descripcion, 'Nueva descripción complementaria')
        self.assertFalse(categoria_actualizada.activo)

    def test_servicio_rechazo_renombrar_a_nombre_existente_case_insensitive(self):
        """
        Escenario: Rechazo al intentar renombrar a un nombre ya existente en otra categoría
        """
        from inventario.services import EditarCategoriaService
        from django.core.exceptions import ValidationError

        Categoria.objects.create(nombre='Bebidas', slug='bebidas')

        with self.assertRaises(ValidationError) as ctx:
            EditarCategoriaService.execute(
                categoria=self.categoria,
                nombre='bebidas',
                descripcion='Intento de colisión',
            )

        self.assertIn('La categoría ya se encuentra registrada', str(ctx.exception))

    def test_servicio_edicion_normaliza_slug_con_caracteres_especiales(self):
        """
        Escenario: Normalización de nuevo slug con tildes y caracteres especiales al editar
        """
        from inventario.services import EditarCategoriaService

        categoria_actualizada = EditarCategoriaService.execute(
            categoria=self.categoria,
            nombre='Frutas & Cítricos Seleccionados',
        )

        self.assertEqual(categoria_actualizada.slug, 'frutas-citricos-seleccionados')

    def test_servicio_edicion_es_atomica_con_rollback(self):
        """
        Escenario NFR: Atomicidad garantizada ante fallos de persistencia en edición
        """
        from inventario.services import EditarCategoriaService

        original_nombre = self.categoria.nombre
        original_slug = self.categoria.slug

        with patch.object(Categoria, 'save', side_effect=RuntimeError('Database disk write failure')):
            with self.assertRaises(RuntimeError):
                EditarCategoriaService.execute(
                    categoria=self.categoria,
                    nombre='Nombre Corrupto',
                    descripcion='No debe persistir',
                )

        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.nombre, original_nombre)
        self.assertEqual(self.categoria.slug, original_slug)


class CategoryEditionViewsAndRBACSecurityTests(TestCase):
    """
    Pruebas de integración, controladores HTTP, seguridad RBAC y plantillas UI para edición (HU-002)
    """

    def setUp(self):
        self.client = Client()

        content_type, _ = ContentType.objects.get_or_create(app_label='inventario', model='categoria')
        self.perm_view_categoria, _ = Permission.objects.get_or_create(
            codename='view_categoria',
            content_type=content_type,
            defaults={'name': 'Puede ver categorías'},
        )
        self.perm_change_categoria, _ = Permission.objects.get_or_create(
            codename='change_categoria',
            content_type=content_type,
            defaults={'name': 'Puede cambiar/editar categorías'},
        )

        # Grupos / Roles
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')
        self.grupo_admin.permissions.add(self.perm_view_categoria, self.perm_change_categoria)

        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')

        # Usuarios
        self.admin_user = User.objects.create_user(username='admin_edicion', password='password123', is_staff=True)
        self.admin_user.groups.add(self.grupo_admin)

        self.base_user = User.objects.create_user(username='base_edicion', password='password123')
        self.base_user.groups.add(self.grupo_usuario)

        self.vendedor_user = User.objects.create_user(username='vendedor_edicion', password='password123')
        self.vendedor_user.groups.add(self.grupo_vendedor)

        self.direct_perm_user = User.objects.create_user(username='direct_edicion', password='password123')
        self.direct_perm_user.user_permissions.add(self.perm_view_categoria, self.perm_change_categoria)

        # Categoría de prueba
        self.categoria = Categoria.objects.create(
            nombre='Lácteos',
            slug='lacteos',
            descripcion='Productos lácteos básicos',
            activo=True,
        )

    def test_usuario_anonimo_redirigido_al_login_al_editar(self):
        """
        Escenario RBAC NFR: Visitante no autenticado es redirigido a login
        """
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
        self.assertIn(f'next=/inventario/categorias/{self.categoria.pk}/editar/', response.url)

    def test_usuario_rol_usuario_recibe_403_forbidden_al_editar(self):
        """
        Escenario RBAC: Usuario con rol 'usuario' recibe 403 Forbidden al intentar acceder o editar
        """
        self.client.force_login(self.base_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 403)

        post_response = self.client.post(url, {'nombre': 'Intento Ilegal'})
        self.assertEqual(post_response.status_code, 403)

    def test_usuario_rol_vendedor_sin_permiso_recibe_403_forbidden_al_editar(self):
        """
        Escenario RBAC: Usuario vendedor (sin change_categoria) recibe 403 Forbidden
        """
        self.client.force_login(self.vendedor_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_permiso_directo_change_categoria_puede_acceder(self):
        """
        Escenario RBAC: Usuario no administrador pero con permiso directo puede acceder al formulario
        """
        self.client.force_login(self.direct_perm_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lácteos')

    def test_edicion_exitosa_categoria_por_administrador(self):
        """
        Escenario: Administrador edita formulario y categoría se actualiza exitosamente
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})

        payload = {
            'nombre': 'Lácteos y Quesos',
            'descripcion': 'Quesos frescos, madurados y leches pasteurizadas',
            'activo': 'on',
        }

        response = self.client.post(url, payload, follow=True)

        self.assertRedirects(response, reverse('inventario:lista_categorias'))

        # Verificar en base de datos
        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.nombre, 'Lácteos y Quesos')
        self.assertEqual(self.categoria.slug, 'lacteos-y-quesos')
        self.assertEqual(self.categoria.descripcion, 'Quesos frescos, madurados y leches pasteurizadas')
        self.assertTrue(self.categoria.activo)

        # Mensaje de confirmación flash
        messages = list(response.context['messages'])
        self.assertTrue(any('actualizada exitosamente' in m.message.lower() or 'actualizada' in m.message.lower() for m in messages))

    def test_formulario_edicion_rechaza_nombre_duplicado_con_error_accesible(self):
        """
        Escenario: Intento de renombrar a otra categoría existente muestra error accesible
        """
        Categoria.objects.create(nombre='Bebidas', slug='bebidas')

        self.client.force_login(self.admin_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})

        response = self.client.post(url, {'nombre': 'bebidas', 'descripcion': 'Duplicado'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'La categoría ya se encuentra registrada')
        # Aserciones NFR de accesibilidad
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'aria-invalid="true"')

    def test_edicion_categoria_inexistente_retorna_404(self):
        """
        Escenario: Solicitud con identificador inexistente retorna HTTP 404 Not Found
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': 999999})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nfr_accesibilidad_formulario_edicion(self):
        """
        Escenario NFR: Formulario de edición contiene labels vinculados a inputs y datos precargados
        """
        self.client.force_login(self.admin_user)
        url = reverse('inventario:editar_categoria', kwargs={'pk': self.categoria.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        self.assertIn('for="id_nombre"', content)
        self.assertIn('for="id_descripcion"', content)
        self.assertIn('for="id_activo"', content)
        self.assertIn('value="Lácteos"', content)
