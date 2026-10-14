from django.db import migrations

# 旧策略: 已发布文章所有人可读
OLD_RULE = 'r.obj.status == "published"'
# 新策略: 已发布且公开的文章, 所有人可读
NEW_RULE = 'r.obj.status == "published" and r.obj.visibility == "public"'

PTYPE = "p"


def update_policy(apps, schema_editor):
    """正向: 把旧的公开读策略替换为带 visibility 条件的新策略."""
    with schema_editor.connection.cursor() as cursor:
        # 删除旧策略
        cursor.execute(
            "DELETE FROM casbin_rule WHERE ptype=%s AND v0=%s AND v1=%s AND v2=%s",
            [PTYPE, OLD_RULE, "article", "read"],
        )
        # 幂等: 已存在新策略则跳过
        cursor.execute(
            "SELECT 1 FROM casbin_rule WHERE ptype=%s AND v0=%s AND v1=%s AND v2=%s",
            [PTYPE, NEW_RULE, "article", "read"],
        )
        if cursor.fetchone():
            return
        cursor.execute(
            "INSERT INTO casbin_rule (ptype, v0, v1, v2, v3, v4, v5) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [PTYPE, NEW_RULE, "article", "read", "", "", ""],
        )


def revert_policy(apps, schema_editor):
    """反向: 恢复旧的公开读策略."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM casbin_rule WHERE ptype=%s AND v0=%s AND v1=%s AND v2=%s",
            [PTYPE, NEW_RULE, "article", "read"],
        )
        cursor.execute(
            "INSERT INTO casbin_rule (ptype, v0, v1, v2, v3, v4, v5) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [PTYPE, OLD_RULE, "article", "read", "", "", ""],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0012_backfill_permission_module"),
    ]

    operations = [
        migrations.RunPython(update_policy, revert_policy),
    ]
