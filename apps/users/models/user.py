from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import models


class User(AbstractUser):
    """自定义用户模型, 继承 Django 自带的 AbstractUser.

    登录支持三种凭证: username / phone / email.
    phone 和 email 允许为空, 但一旦填写则必须唯一.

    展示类字段 (nickname / avatar 等) 已挪到 UserProfile.
    """

    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name="手机号"
    )
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="邮箱")

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def get_permission_codes(self) -> set:
        """获取该用户拥有的所有权限编码集合 (带 Redis 缓存).

        查询路径: User -> UserRole -> Role -> RolePermission -> Permission
        缓存 key: user:perms:{user_id}, TTL 300 秒.
        缓存失效: 分配 / 移除角色或权限时主动清, TTL 兜底.
        """
        # 延迟导入, 避免 users 与 rbac 之间潜在的循环导入
        from rbac.cache import PERM_CACHE_TTL, perm_cache_key
        from rbac.models import Permission

        key = perm_cache_key(self.id)
        cached = cache.get(key)
        if cached is not None:
            return set(cached)

        codes = list(
            Permission.objects.filter(rolepermission__role__userrole__user=self)
            .values_list("code", flat=True)
            .distinct()
        )
        cache.set(key, codes, PERM_CACHE_TTL)
        return set(codes)
