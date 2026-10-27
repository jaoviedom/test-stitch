from django.db import transaction
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import PermissionDenied


class RegisterUserService:
    """
    Capa de servicio de dominio para el registro de nuevos usuarios en TeckStore (HU-001).
    Garantiza la atomicidad de la transacción y la asignación exclusiva del rol 'usuario'.
    """

    @staticmethod
    @transaction.atomic
    def execute(first_name: str, username: str, email: str, password: str) -> User:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
        )

        grupo_usuario, _ = Group.objects.get_or_create(name='usuario')
        user.groups.set([grupo_usuario])

        return user


class UpdateUserAccessService:
    """
    Capa de servicio de dominio para la gestión y actualización de roles y permisos (HU-002).
    Permite asignar o revocar múltiples roles simultáneos y permisos granulares directos.
    Protegido con @transaction.atomic y control de autorización.
    """

    @staticmethod
    @transaction.atomic
    def execute(
        target_user: User,
        role_names: list[str],
        permission_codenames: list[str] = None,
        requested_by: User = None,
    ) -> User:
        # Validación de autorización si se provee el usuario solicitante
        if requested_by is not None:
            has_manage = (
                requested_by.is_superuser
                or requested_by.has_perm('authentication.manage_access')
                or requested_by.has_perm('auth.manage_access')
            )
            if not has_manage:
                raise PermissionDenied("No posee el permiso requerido 'authentication.manage_access' para modificar accesos.")

        # Sincronización de Grupos / Roles
        groups = []
        for name in role_names:
            group, _ = Group.objects.get_or_create(name=name)
            groups.append(group)
        target_user.groups.set(groups)

        # Sincronización de Permisos directos opcionales
        if permission_codenames is not None:
            codenames = [p.split('.')[-1] for p in permission_codenames]
            permissions = list(Permission.objects.filter(codename__in=codenames))
            target_user.user_permissions.set(permissions)

        return target_user


class AuthenticateUserService:
    """
    Capa de servicio de dominio para autenticación dual de usuarios en TeckStore (HU-003).
    Permite autenticarse indistintamente con username o email de forma insensible a mayúsculas/minúsculas.
    """

    @staticmethod
    def execute(identifier: str, password: str, request=None) -> User | None:
        from django.db.models import Q
        from django.contrib.auth import authenticate

        if not identifier or not password:
            return None

        clean_identifier = identifier.strip()

        # Buscar usuario por username o email de forma insensible a mayúsculas
        user_candidate = User.objects.filter(
            Q(username__iexact=clean_identifier) | Q(email__iexact=clean_identifier)
        ).first()

        if user_candidate is None:
            return None

        # Autenticar utilizando el username real del modelo
        return authenticate(request=request, username=user_candidate.username, password=password)


class UpdateUserProfileService:
    """
    Capa de servicio de dominio para actualizar los datos personales del usuario (HU-004).
    Garantiza la inmutabilidad estricta de roles y permisos y se ejecuta bajo @transaction.atomic.
    """

    @staticmethod
    @transaction.atomic
    def execute(user: User, first_name: str, email: str, last_name: str = "") -> User:
        user.first_name = first_name.strip()
        user.email = email.strip()
        if last_name:
            user.last_name = last_name.strip()
        user.save(update_fields=['first_name', 'last_name', 'email'])
        return user


class UpdateUserPasswordService:
    """
    Capa de servicio de dominio para el cambio seguro de contraseñas de usuario (HU-004).
    Valida la contraseña actual, aplica validadores de complejidad y cifra con hash seguro bajo @transaction.atomic.
    """

    @staticmethod
    @transaction.atomic
    def execute(user: User, current_password: str, new_password: str) -> None:
        from django.core.exceptions import ValidationError
        from django.contrib.auth.password_validation import validate_password

        if not user.check_password(current_password):
            raise ValidationError("La contraseña actual ingresada es incorrecta.")

        validate_password(new_password, user=user)
        user.set_password(new_password)
        user.save(update_fields=['password'])


