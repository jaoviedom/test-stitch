from django.db import models


class AccessControl(models.Model):
    """
    Modelo para registrar permisos personalizados del subsistema de autenticación (HU-002)
    """
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('manage_access', 'Puede gestionar roles y permisos de usuarios'),
        ]
