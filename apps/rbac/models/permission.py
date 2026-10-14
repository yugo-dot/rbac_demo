from django.db import models


class Permission(models.Model):
    """权限点"""

    name = models.CharField(max_length=50, verbose_name='权限名')
    code = models.CharField(max_length=100, unique=True, verbose_name='权限编码')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'rbac_permission'
        verbose_name = '权限'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code

