from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from unittest.mock import patch


class UserRegistrationUnitAndServiceTests(TestCase):
    """
    Pruebas unitarias para la capa de dominio y servicio de registro (HU-001)
    """

    def setUp(self):
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')

    def test_servicio_registro_crea_usuario_con_rol_usuario_exitosamente(self):
        """
        Escenario: Registro exitoso crea cuenta y asigna exclusivamente el rol 'usuario'
        """
        from authentication.services import RegisterUserService

        user = RegisterUserService.execute(
            first_name='Juan Pérez',
            username='juanperez',
            email='juan@tienda.co',
            password='Password123!',
        )

        self.assertIsNotNone(user.pk)
        self.assertEqual(user.username, 'juanperez')
        self.assertEqual(user.first_name, 'Juan Pérez')
        self.assertEqual(user.email, 'juan@tienda.co')
        self.assertTrue(user.check_password('Password123!'))

        # Debe tener asignado única y exclusivamente el rol "usuario"
        roles = list(user.groups.values_list('name', flat=True))
        self.assertEqual(roles, ['usuario'])

    def test_servicio_registro_es_atomico_ante_fallos_en_asignacion_de_rol(self):
        """
        Escenario NFR: Atomicidad en el registro - Rollback completo si falla la asignación del rol
        """
        from authentication.services import RegisterUserService

        initial_user_count = User.objects.count()

        with patch.object(Group.objects, 'get_or_create', side_effect=RuntimeError('Database simulation error')):
            with self.assertRaises(RuntimeError):
                RegisterUserService.execute(
                    first_name='Error User',
                    username='erroruser',
                    email='error@tienda.co',
                    password='Password123!',
                )

        # La transacción debe revertirse: ningún registro huérfano
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertFalse(User.objects.filter(username='erroruser').exists())


class UserRegistrationIntegrationAndViewsTests(TestCase):
    """
    Pruebas de integración HTTP y vistas para HU-001
    """

    def setUp(self):
        self.client = Client()
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')

    def test_pagina_registro_get_retorna_200_ok(self):
        """
        Verifica que la ruta GET de registro carga la plantilla correctamente
        """
        url = reverse('authentication:register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Cuenta')
        self.assertContains(response, 'TeckStore')

    def test_registro_exitoso_post_crea_usuario_asigna_rol_y_redirige_a_dashboard(self):
        """
        Escenario: Envío de formulario válido crea cuenta, asigna rol 'usuario', inicia sesión y redirige
        """
        url = reverse('authentication:register')
        data = {
            'first_name': 'Juan Pérez',
            'username': 'juanperez',
            'email': 'juan@tienda.co',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'terms': True,
        }

        response = self.client.post(url, data=data)

        # Redirección esperada a dashboard
        self.assertRedirects(response, reverse('dashboard'))

        # Verificación en BD
        user = User.objects.get(username='juanperez')
        self.assertEqual(user.email, 'juan@tienda.co')
        self.assertEqual(list(user.groups.values_list('name', flat=True)), ['usuario'])

        # Sesión automáticamente autenticada
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registro_falla_por_duplicidad_de_username_o_email(self):
        """
        Escenario: Intento de registro con username o email previamente existente
        Aserción NFR: Atributo role="alert" para lectores de pantalla
        """
        User.objects.create_user(username='juanperez', email='juan@tienda.co', password='Password123!')

        url = reverse('authentication:register')
        data = {
            'first_name': 'Otro Juan',
            'username': 'juanperez',
            'email': 'juan@tienda.co',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'terms': True,
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)

        # Comprobación de no duplicación
        self.assertEqual(User.objects.filter(username='juanperez').count(), 1)

        # NFR Accesibilidad: role="alert" presente en los errores
        content = response.content.decode('utf-8')
        self.assertIn('role="alert"', content)

    def test_registro_falla_si_passwords_no_coinciden(self):
        """
        Escenario: Validación de contraseñas distintas con atributos de accesibilidad
        """
        url = reverse('authentication:register')
        data = {
            'first_name': 'Carlos',
            'username': 'carlos123',
            'email': 'carlos@tienda.co',
            'password1': 'Password123!',
            'password2': 'PasswordDistinto999!',
            'terms': True,
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='carlos123').exists())

        content = response.content.decode('utf-8')
        self.assertIn('role="alert"', content)

    def test_registro_falla_con_campos_obligatorios_vacios(self):
        """
        Escenario: Envío de formulario vacío es rechazado
        """
        url = reverse('authentication:register')
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

        content = response.content.decode('utf-8')
        self.assertIn('role="alert"', content)


class UserRoleAccessRestrictionsTests(TestCase):
    """
    Pruebas de autorización RBAC para el rol base 'usuario' (HU-001)
    """

    def setUp(self):
        self.client = Client()
        self.grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        self.user = User.objects.create_user(username='nuevousuario', email='nuevo@tienda.co', password='Password123!')
        self.user.groups.add(self.grupo_usuario)

    def test_usuario_con_rol_base_recibe_403_forbidden_en_categorias(self):
        """
        Escenario NFR de Seguridad: Usuario recién registrado con rol 'usuario'
        recibe HTTP 403 Forbidden al intentar acceder al módulo de categorías
        """
        self.client.force_login(self.user)
        url = reverse('inventario:lista_categorias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
