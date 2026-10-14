from django.db import models


class Permission(models.Model):
    """权限点"""

    name = models.CharField(max_length=50, verbose_name="权限名")
    code = models.CharField(max_length=100, unique=True, verbose_name="权限编码")
    module = models.CharField(max_length=50, blank=True, verbose_name="所属模块")
    description = models.CharField(max_length=200, blank=True, verbose_name="描述")
    is_builtin = models.BooleanField(default=False, verbose_name="是否内置")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "rbac_permission"
        verbose_name = "权限"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code

    @staticmethod
    def derive_module(code: str) -> str:
        """从权限编码推导 module: 取最后一个 ":" 之前的部分.

        例:
        - article:read          -> article
        - rbac:role:read        -> rbac:role
        - rbac:audit_log:read   -> rbac:audit_log
        """
        if ":" not in code:
            return code
        return code.rsplit(":", 1)[0]

    def save(self, *args, **kwargs):
        """未显式填 module 时, 自动从 code 推导 (允许手动覆盖)."""
        if not self.module:
            self.module = self.derive_module(self.code)
        super().save(*args, **kwargs)
