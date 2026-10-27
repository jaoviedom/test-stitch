from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import DatabaseError


class UserProfileServiceUnitTests(TestCase):
    """
    Pruebas unitarias para la capa de servicios de dominio de Perfil de Usuario (HU-004).
    """

    def setUp(self):
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')

        self.user = User.objects.create_user(
            username='joseoviedo',
            email='jose@tienda.co',
            password='Password123!',
            first_name='Jose',
        )
        self.user.groups.set([self.grupo_usuario, self.grupo_vendedor])

    def test_update_user_profile_service_success(self):
        """
        Escenario: Actualización exitosa de first_name y email bajo transacción atómica.
        """
        from authentication.services import UpdateUserProfileService

        updated_user = UpdateUserProfileService.execute(
            user=self.user,
            first_name='Jose Alonso',
            email='jose.alonso@tienda.co',
        )

        self.assertEqual(updated_user.first_name, 'Jose Alonso')
        self.assertEqual(updated_user.email, 'jose.alonso@tienda.co')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jose Alonso')
        self.assertEqual(self.user.email, 'jose.alonso@tienda.co')

    def test_update_user_profile_service_immutability_of_roles(self):
        """
        Escenario: Inmutabilidad de roles. El servicio de perfil no permite modificar grupos ni permisos.
        """
        from authentication.services import UpdateUserProfileService

        initial_groups = list(self.user.groups.values_list('name', flat=True))

        UpdateUserProfileService.execute(
            user=self.user,
            first_name='Jose Alonso',
            email='jose.alonso@tienda.co',
        )

        self.user.refresh_from_db()
        current_groups = list(self.user.groups.values_list('name', flat=True))
        self.assertEqual(current_groups, initial_groups)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_update_user_profile_service_atomic_rollback(self):
        """
        Escenario: Atomicidad estricta y rollback en caso de fallo inesperado de BD.
        """
        from authentication.services import UpdateUserProfileService

        with patch.object(User, 'save', side_effect=DatabaseError("Error de base de datos")):
            with self.assertRaises(DatabaseError):
                UpdateUserProfileService.execute(
                    user=self.user,
                    first_name='Nuevo Nombre',
                    email='nuevo@tienda.co',
                )

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jose')
        self.assertEqual(self.user.email, 'jose@tienda.co')

    def test_update_user_password_service_success(self):
        """
        Escenario: Cambio de contraseña exitoso validando contraseña actual con hash seguro.
        """
        from authentication.services import UpdateUserPasswordService

        UpdateUserPasswordService.execute(
            user=self.user,
            current_password='Password123!',
            new_password='NuevaPassword456!',
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NuevaPassword456!'))
        self.assertFalse(self.user.check_password('Password123!'))

    def test_update_user_password_service_fails_when_current_password_invalid(self):
        """
        Escenario: Rechazo de cambio de contraseña cuando la contraseña actual es errónea.
        """
        from authentication.services import UpdateUserPasswordService

        with self.assertRaises(ValidationError):
            UpdateUserPasswordService.execute(
                user=self.user,
                current_password='ClaveIncorrecta!',
                new_password='NuevaPassword456!',
            )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Password123!'))


class UserProfileViewsIntegrationTests(TestCase):
    """
    Pruebas de integración HTTP y controladores de vista para el Perfil de Usuario (HU-004).
    """

    def setUp(self):
        self.client = Client()
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.grupo_vendedor, _ = Group.objects.get_or_create(name='vendedor')
        self.grupo_admin, _ = Group.objects.get_or_create(name='administrador')

        self.user = User.objects.create_user(
            username='joseoviedo',
            email='jose@tienda.co',
            password='Password123!',
            first_name='Jose',
        )
        self.user.groups.set([self.grupo_usuario, self.grupo_vendedor])

        self.other_user = User.objects.create_user(
            username='carlosr',
            email='carlos@tienda.co',
            password='Password123!',
            first_name='Carlos',
        )

    def test_anonymous_user_redirected_to_login(self):
        """
        Escenario NFR: Visitante no autenticado es redirigido a login con código 302 y next.
        """
        url = reverse('authentication:profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('authentication:login'), response.url)
        self.assertIn('next=', response.url)

    def test_access_profile_allowed_for_authenticated_user_with_roles_readonly(self):
        """
        Escenario: Acceso permitido para cualquier rol autenticado y visualización de roles en solo lectura.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jose')
        self.assertContains(response, 'jose@tienda.co')
        self.assertContains(response, 'usuario')
        self.assertContains(response, 'vendedor')
        # Verificar que no es un formulario editable de roles
        self.assertNotContains(response, 'name="roles"')

    def test_update_profile_personal_info_success(self):
        """
        Escenario: Actualización exitosa de nombre y email mediante POST.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        post_data = {
            'action': 'update_profile',
            'first_name': 'Jose Alonso',
            'email': 'jose.alonso@tienda.co',
        }
        response = self.client.post(url, data=post_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jose Alonso')
        self.assertEqual(self.user.email, 'jose.alonso@tienda.co')

        # Comprobar mensaje de confirmación exitosa
        messages = list(response.context['messages'])
        self.assertTrue(any("actualizado" in str(m).lower() or "éxito" in str(m).lower() for m in messages))

    def test_update_profile_fails_when_fields_empty(self):
        """
        Escenario: Validación de campos obligatorios vacíos y renderizado de atributos de accesibilidad WCAG.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        post_data = {
            'action': 'update_profile',
            'first_name': '',
            'email': '',
        }
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jose')

        content = response.content.decode('utf-8')
        self.assertTrue('role="alert"' in content or 'aria-invalid="true"' in content)

    def test_update_profile_fails_when_email_already_registered_by_other_user(self):
        """
        Escenario: Rechazo de actualización cuando el correo pertenece a otra cuenta.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        post_data = {
            'action': 'update_profile',
            'first_name': 'Jose Alonso',
            'email': 'carlos@tienda.co',  # Correo de other_user
        }
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'jose@tienda.co')

        content = response.content.decode('utf-8')
        self.assertIn('role="alert"', content)

    def test_update_password_success_and_preserves_session(self):
        """
        Escenario: Cambio de contraseña exitoso validando clave actual y preservando sesión activa.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        post_data = {
            'action': 'change_password',
            'current_password': 'Password123!',
            'new_password1': 'NuevaPassword456!',
            'new_password2': 'NuevaPassword456!',
        }
        response = self.client.post(url, data=post_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NuevaPassword456!'))

        # Sesión preservada (update_session_auth_hash)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_update_password_fails_when_current_password_incorrect(self):
        """
        Escenario: Rechazo cuando la contraseña actual es errónea.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        post_data = {
            'action': 'change_password',
            'current_password': 'ClaveEquivocada!',
            'new_password1': 'NuevaPassword456!',
            'new_password2': 'NuevaPassword456!',
        }
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Password123!'))

        content = response.content.decode('utf-8')
        self.assertIn('role="alert"', content)

    def test_update_password_fails_when_new_passwords_do_not_match(self):
        """
        Escenario: Rechazo cuando la confirmación de contraseña no coincide.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        post_data = {
            'action': 'change_password',
            'current_password': 'Password123!',
            'new_password1': 'NuevaPassword456!',
            'new_password2': 'OtraPassword789!',
        }
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Password123!'))

        content = response.content.decode('utf-8')
        self.assertTrue('role="alert"' in content or 'aria-invalid="true"' in content)

    def test_profile_post_rbac_privilege_escalation_is_prevented(self):
        """
        Escenario RBAC: Parámetros maliciosos inyectados para alterar roles o flags son ignorados.
        """
        self.client.force_login(self.user)
        url = reverse('authentication:profile')

        malicious_data = {
            'action': 'update_profile',
            'first_name': 'Jose Alonso',
            'email': 'jose.alonso@tienda.co',
            'is_staff': True,
            'is_superuser': True,
            'groups': [self.grupo_admin.id],
            'roles': ['administrador'],
        }
        response = self.client.post(url, data=malicious_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertNotIn(self.grupo_admin, self.user.groups.all())
