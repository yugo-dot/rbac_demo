from django.db import models


class CasbinRule(models.Model):
    """Casbin 策略表映射 (managed=False).

    这张表由 rbac/0005 迁移用 schema_editor.create_model() 建,
    这里只做"模型声明", 让 Django 迁移系统知道它还在, 不要删.
    managed=False: 表的生命周期不归 Django 管 (增删改表结构时 Django 不介入).
    """

    ptype = models.CharField(max_length=255)
    v0 = models.CharField(max_length=255)
    v1 = models.CharField(max_length=255)
    v2 = models.CharField(max_length=255)
    v3 = models.CharField(max_length=255)
    v4 = models.CharField(max_length=255)
    v5 = models.CharField(max_length=255)

    class Meta:
        db_table = "casbin_rule"
        managed = False

    def __str__(self):
        return f"{self.ptype} {self.v0} {self.v1} {self.v2}"
