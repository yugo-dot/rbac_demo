from django.db import models

from .permission import Permission
from .role import Role


class RolePermission(models.Model):
    """角色-权限 关联"""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, verbose_name='权限'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'rbac_role_permission'
        unique_together = ('role', 'permission')
        verbose_name = '角色权限关联'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.role.name} - {self.permission.code}'
