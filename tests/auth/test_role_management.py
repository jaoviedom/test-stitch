from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from unittest.mock import patch


class RoleManagementUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de servicio de gestión de roles y permisos (HU-002)
    """

    def setUp(self):
        # Crear grupos oficiales
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')

        # Crear permiso oficial manage_access y permisos de inventario
        ct_user = ContentType.objects.get_for_model(User)
        self.perm_manage_access, _ = Permission.objects.get_or_create(
            codename='manage_access',
            content_type=ct_user,
            defaults={'name': 'Puede gestionar roles y permisos de usuarios'}
        )
        self.perm_view_cat, _ = Permission.objects.get_or_create(
            codename='view_categoria',
            content_type=ct_user,
            defaults={'name': 'Puede ver categorías'}
        )
        self.perm_add_cat, _ = Permission.objects.get_or_create(
            codename='add_categoria',
            content_type=ct_user,
            defaults={'name': 'Puede agregar categorías'}
        )

        # Asignar permisos a vendedor y admin
        self.grupo_vendedor.permissions.add(self.perm_view_cat)
        self.grupo_admin.permissions.add(self.perm_manage_access, self.perm_view_cat, self.perm_add_cat)

        # Usuarios de prueba
        self.admin_user = User.objects.create_user(username='admin', email='admin@teckstore.co', password='Password123!')
        self.admin_user.groups.add(self.grupo_admin)

        self.maria = User.objects.create_user(username='maria', email='maria@teckstore.co', password='Password123!')
        self.maria.groups.add(self.grupo_usuario)

        self.pedro = User.objects.create_user(username='pedro', email='pedro@teckstore.co', password='Password123!')
        self.pedro.groups.add(self.grupo_vendedor)

    def test_asignar_multiples_roles_a_usuario_por_administrador(self):
        """
        Escenario: Administrador asigna simultáneamente roles 'usuario' y 'vendedor' a María
        """
        from authentication.services import UpdateUserAccessService

        updated_user = UpdateUserAccessService.execute(
            target_user=self.maria,
            role_names=['usuario', 'vendedor'],
            requested_by=self.admin_user,
        )

        roles = set(updated_user.groups.values_list('name', flat=True))
        self.assertEqual(roles, {'usuario', 'vendedor'})

        # María ahora hereda los permisos del rol vendedor
        self.assertTrue(updated_user.has_perm('auth.view_categoria'))

    def test_otorgar_permiso_granular_directo_a_usuario(self):
        """
        Escenario: Administrador otorga permiso directo 'add_categoria' a un vendedor
        """
        from authentication.services import UpdateUserAccessService

        updated_user = UpdateUserAccessService.execute(
            target_user=self.maria,
            role_names=['vendedor'],
            permission_codenames=['auth.add_categoria'],
            requested_by=self.admin_user,
        )

        self.assertTrue(updated_user.has_perm('auth.add_categoria'))
        self.assertTrue(updated_user.user_permissions.filter(codename='add_categoria').exists())

    def test_revocar_rol_asignado_a_usuario(self):
        """
        Escenario: Revocación de un rol asignado (quitar vendedor y dejar únicamente usuario)
        """
        from authentication.services import UpdateUserAccessService

        # Carlos posee usuario y vendedor
        carlos = User.objects.create_user(username='carlos', email='carlos@teckstore.co', password='Password123!')
        carlos.groups.set([self.grupo_usuario, self.grupo_vendedor])

        updated_user = UpdateUserAccessService.execute(
            target_user=carlos,
            role_names=['usuario'],
            requested_by=self.admin_user,
        )

        roles = list(updated_user.groups.values_list('name', flat=True))
        self.assertEqual(roles, ['usuario'])
        self.assertFalse(updated_user.has_perm('auth.view_categoria'))

    def test_servicio_falla_si_solicitante_carece_de_permiso_manage_access(self):
        """
        Escenario NFR: Rechazo con PermissionDenied si el solicitante no tiene permiso de gestión
        """
        from authentication.services import UpdateUserAccessService

        with self.assertRaises(PermissionDenied):
            UpdateUserAccessService.execute(
                target_user=self.maria,
                role_names=['administrador'],
                requested_by=self.pedro,  # Pedro es vendedor, no tiene manage_access
            )

    def test_servicio_actualizacion_es_atomico_ante_fallos(self):
        """
        Escenario NFR: Atomicidad de la transacción - Rollback completo si ocurre un error
        """
        from authentication.services import UpdateUserAccessService

        roles_iniciales = list(self.maria.groups.values_list('name', flat=True))

        with patch.object(type(self.maria.user_permissions), 'set', side_effect=RuntimeError('Database simulation error')):
            with self.assertRaises(RuntimeError):
                UpdateUserAccessService.execute(
                    target_user=self.maria,
                    role_names=['usuario', 'vendedor'],
                    permission_codenames=['auth.add_categoria'],
                    requested_by=self.admin_user,
                )

        # El estado de los roles debe permanecer inalterado tras el rollback
        self.maria.refresh_from_db()
        self.assertEqual(list(self.maria.groups.values_list('name', flat=True)), roles_iniciales)


class RoleManagementIntegrationAndViewsTests(TestCase):
    """
    Pruebas de integración HTTP y vistas para HU-002
    """

    def setUp(self):
        self.client = Client()

        # Crear grupos
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')

        ct_user = ContentType.objects.get_for_model(User)
        self.perm_manage_access, _ = Permission.objects.get_or_create(
            codename='manage_access',
            content_type=ct_user,
            defaults={'name': 'Puede gestionar roles y permisos de usuarios'}
        )
        self.grupo_admin.permissions.add(self.perm_manage_access)

        # Admin
        self.admin_user = User.objects.create_user(username='superadmin', email='superadmin@teckstore.co', password='Password123!')
        self.admin_user.groups.add(self.grupo_admin)

        # Usuario normal
        self.normal_user = User.objects.create_user(username='regular', email='regular@teckstore.co', password='Password123!')
        self.normal_user.groups.add(self.grupo_usuario)

    def test_administrador_accede_a_lista_usuarios_y_visualiza_tabla_con_badges(self):
        """
        Escenario: Administrador autorizado accede a /auth/usuarios/ (HTTP 200 OK)
        """
        self.client.force_login(self.admin_user)
        url = reverse('authentication:user_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Usuarios')
        self.assertContains(response, 'regular@teckstore.co')
        self.assertContains(response, 'usuario')

    def test_administrador_accede_a_formulario_de_edicion_de_accesos_get(self):
        """
        Escenario: Administrador accede a /auth/usuarios/<id>/accesos/ (HTTP 200 OK)
        """
        self.client.force_login(self.admin_user)
        url = reverse('authentication:user_manage_access', kwargs={'user_id': self.normal_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestionar Roles y Permisos')
        self.assertContains(response, 'regular')

    def test_administrador_actualiza_roles_via_post_y_redirige(self):
        """
        Escenario: Administrador actualiza roles de un usuario con POST y redirige con mensaje
        """
        self.client.force_login(self.admin_user)
        url = reverse('authentication:user_manage_access', kwargs={'user_id': self.normal_user.id})
        data = {
            'roles': [self.grupo_usuario.id, self.grupo_vendedor.id],
        }

        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse('authentication:user_list'))

        # Verificación en BD
        self.normal_user.refresh_from_db()
        roles = set(self.normal_user.groups.values_list('name', flat=True))
        self.assertEqual(roles, {'usuario', 'vendedor'})

    def test_usuario_sin_permiso_manage_access_recibe_403_forbidden(self):
        """
        Escenario NFR de Seguridad: Usuario con rol regular recibe HTTP 403 Forbidden
        """
        self.client.force_login(self.normal_user)

        url_list = reverse('authentication:user_list')
        response_list = self.client.get(url_list)
        self.assertEqual(response_list.status_code, 403)

        url_edit = reverse('authentication:user_manage_access', kwargs={'user_id': self.normal_user.id})
        response_edit = self.client.get(url_edit)
        self.assertEqual(response_edit.status_code, 403)

    def test_visitante_anonimo_es_redirigido_a_login(self):
        """
        Escenario NFR: Visitante no autenticado es redirigido a login
        """
        url_list = reverse('authentication:user_list')
        response = self.client.get(url_list)
        self.assertEqual(response.status_code, 302)
        location = response.headers.get('Location', '')
        self.assertTrue('/login/' in location or '/register/' in location)
