from django.db import models


class Role(models.Model):
    """角色"""

    name = models.CharField(max_length=50, unique=True, verbose_name='角色名')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'rbac_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
