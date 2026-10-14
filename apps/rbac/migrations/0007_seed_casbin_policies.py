from django.db import migrations

# 预置 ABAC 策略: (sub_rule, obj, act)
# 这些是新环境开箱即用的默认策略, 管理员之后可通过策略管理接口调整.
INITIAL_POLICIES = [
    # 作者对自己的文章: 读 / 改 / 删
    ("r.sub.id == r.obj.author_id", "article", "read"),
    ("r.sub.id == r.obj.author_id", "article", "update"),
    ("r.sub.id == r.obj.author_id", "article", "delete"),
    # 已发布的文章: 所有人可读
    ('r.obj.status == "published"', "article", "read"),
    # 主编角色: 可读所有文章
    ('r.sub.role == "chief_editor"', "article", "read"),
]

# 写入 casbin_rule 时 ptype 固定为 "p", 最多 6 个 v 位
PTYPE = "p"
V_COLUMNS = ["v0", "v1", "v2", "v3", "v4", "v5"]


def _pad(values: list, length: int) -> list:
    """把值列表补齐到指定长度, 空位用空串."""
    return list(values) + [""] * (length - len(values))


def seed_policies(apps, schema_editor):
    """正向: 预置策略, 已存在则跳过 (幂等)."""
    with schema_editor.connection.cursor() as cursor:
        for sub_rule, obj, act in INITIAL_POLICIES:
            cursor.execute(
                f"SELECT 1 FROM casbin_rule WHERE ptype=%s AND v0=%s AND v1=%s AND v2=%s",
                [PTYPE, sub_rule, obj, act],
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                f"INSERT INTO casbin_rule (ptype, {', '.join(V_COLUMNS)}) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [PTYPE, *_pad([sub_rule, obj, act], len(V_COLUMNS))],
            )


def remove_policies(apps, schema_editor):
    """反向: 删除本次预置的策略."""
    with schema_editor.connection.cursor() as cursor:
        for sub_rule, obj, act in INITIAL_POLICIES:
            cursor.execute(
                "DELETE FROM casbin_rule WHERE ptype=%s AND v0=%s AND v1=%s AND v2=%s",
                [PTYPE, sub_rule, obj, act],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0006_add_article_update_delete_perms"),
    ]

    operations = [
        migrations.RunPython(seed_policies, remove_policies),
    ]
