"""Casbin ABAC 封装.

设计:
- 策略存 MySQL (casbin_rule 表, 建表迁移在 rbac/migrations/0005)
- 自己实现 Adapter (绕开 casbin_adapter 的 model, 避免它绑定到已移除的 app)
- enforcer 用 lru_cache 缓存, 避免每次请求重新加载策略
- 策略变更 (add/remove) 后需主动 clear_enforcer_cache()

请求三元组:
- sub: dict, 主体属性 {id, username, role, is_superuser, perms}
- obj: dict, 对象属性 {obj_type, author_id, status, visibility, ...}
- act: str, 动作 read / create / update / delete

策略三元组 (p):
- sub_rule: 主体条件表达式, 引用 r.sub.xxx
- obj: 资源类型字符串, 如 "article"
- act: 动作字符串, 或 "*" 通配
"""

from functools import lru_cache

import casbin
from django.conf import settings
from django.db import connection


class CasbinRuleAdapter(casbin.persist.Adapter):
    """把策略读写到 casbin_rule 表 (不依赖 casbin_adapter 的 Django model)."""

    def load_policy(self, model):
        with connection.cursor() as cursor:
            cursor.execute("SELECT ptype, v0, v1, v2, v3, v4, v5 FROM casbin_rule")
            rows = cursor.fetchall()
        for row in rows:
            ptype = row[0]
            rule = [v for v in row[1:] if v]
            if ptype == "p":
                model.add_policy("p", "p", rule)

    def save_policy(self, model):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM casbin_rule")
            for ptype in ("p", "g"):
                for rule in model.model[ptype].policy:
                    cursor.execute(
                        "INSERT INTO casbin_rule (ptype, v0, v1, v2, v3, v4, v5) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        [ptype] + list(rule) + [""] * (6 - len(rule)),
                    )

    def add_policy(self, sec, ptype, rule):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO casbin_rule (ptype, v0, v1, v2, v3, v4, v5) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [ptype] + list(rule) + [""] * (6 - len(rule)),
            )

    def remove_policy(self, sec, ptype, rule):
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM casbin_rule WHERE ptype=%s AND v0=%s AND v1=%s AND v2=%s",
                [ptype] + list(rule)[:3],
            )
        return True

    def remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        # 本封装暂不用
        return True


@lru_cache(maxsize=1)
def get_enforcer() -> casbin.Enforcer:
    """获取 Casbin enforcer (单例, 带缓存)."""
    adapter = CasbinRuleAdapter()
    return casbin.Enforcer(settings.CASBIN_MODEL, adapter)


def clear_enforcer_cache() -> None:
    """清除 enforcer 缓存, 强制下次重新加载策略."""
    get_enforcer.cache_clear()


def enforce(sub: dict, obj: dict, act: str) -> bool:
    """执行一次 ABAC 判定."""
    return get_enforcer().enforce(sub, obj, act)


def add_policy(sub_rule: str, obj: str, act: str) -> bool:
    """添加策略, 返回是否新增 (False 表示已存在)."""
    ok = get_enforcer().add_policy(sub_rule, obj, act)
    clear_enforcer_cache()
    return ok


def remove_policy(sub_rule: str, obj: str, act: str) -> bool:
    """移除策略, 返回是否删除成功."""
    ok = get_enforcer().remove_policy(sub_rule, obj, act)
    clear_enforcer_cache()
    return ok


def list_policies() -> list[list[str]]:
    """列出所有策略."""
    return get_enforcer().get_policy()
