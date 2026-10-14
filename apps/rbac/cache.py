"""RBAC 缓存工具.

约定:
- 用户权限缓存 key: user:perms:{user_id}, value 为权限码列表, TTL 300 秒
- 变动 (分配 / 移除角色权限) 时主动清缓存, 同时保留 TTL 作为兜底
"""

from django.core.cache import cache

from rbac.models import UserRole

# 缓存 key 前缀与 TTL
PERM_CACHE_PREFIX = 'user:perms:'
PERM_CACHE_TTL = 300


def perm_cache_key(user_id: int) -> str:
    """生成用户权限缓存的 key."""
    return f'{PERM_CACHE_PREFIX}{user_id}'


def invalidate_user_perms(user_id: int) -> None:
    """清除单个用户的权限缓存."""
    cache.delete(perm_cache_key(user_id))


def invalidate_role_perms(role_id: int) -> None:
    """清除某角色下所有用户的权限缓存."""
    user_ids = (
        UserRole.objects
        .filter(role_id=role_id)
        .values_list('user_id', flat=True)
        .distinct()
    )
    keys = [perm_cache_key(uid) for uid in user_ids]
    if keys:
        cache.delete_many(keys)
