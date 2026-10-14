from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型, 继承 Django 自带的 AbstractUser.

    登录支持三种凭证: username / phone / email.
    phone 和 email 允许为空, 但一旦填写则必须唯一.
    """

    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name='手机号'
    )
    email = models.EmailField(
        unique=True, null=True, blank=True, verbose_name='邮箱'
    )
    avatar = models.URLField(max_length=500, blank=True, verbose_name='头像地址')

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def get_permission_codes(self) -> set:
        """获取该用户拥有的所有权限编码集合.

        查询路径: User -> UserRole -> Role -> RolePermission -> Permission
        返回形如 {'article:create', 'user:delete'} 的集合.
        """
        # 延迟导入, 避免 users 与 rbac 之间潜在的循环导入
        from rbac.models import Permission

        codes = Permission.objects.filter(
            rolepermission__role__userrole__user=self
        ).values_list('code', flat=True).distinct()
        return set(codes)