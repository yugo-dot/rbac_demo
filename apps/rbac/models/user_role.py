from django.conf import settings
from django.db import models

from .role import Role


class UserRole(models.Model):
    """用户-角色 关联"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户'
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'rbac_user_role'
        unique_together = ('user', 'role')
        verbose_name = '用户角色关联'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username} - {self.role.name}'
