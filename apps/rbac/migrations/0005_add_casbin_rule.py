from django.db import migrations, models


def create_casbin_rule_if_missing(apps, schema_editor):
    """建 casbin_rule 表 (若不存在).

    这张表原本由 casbin_adapter app 的迁移建, 但那个 app 因为会在
    AppConfig.ready() 里访问 DB 被我们从 INSTALLED_APPS 移除了.
    为让全新环境能完整复现, 把建表搬到这里.

    用 schema_editor.create_model() 而不是原生 SQL, 让 Django 根据
    当前数据库类型 (MySQL / SQLite) 生成正确的 DDL.

    开发库 (MySQL) 表已存在, 检测到就跳过 (幂等).
    """
    table_name = "casbin_rule"
    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name in existing_tables:
        return

    # 用历史模型 (迁移状态里的 CasbinRule) 来建表
    CasbinRule = apps.get_model("rbac", "CasbinRule")
    schema_editor.create_model(CasbinRule)


def drop_casbin_rule(apps, schema_editor):
    """反向: 删表 (谨慎)."""
    CasbinRule = apps.get_model("rbac", "CasbinRule")
    schema_editor.delete_model(CasbinRule)


class Migration(migrations.Migration):

    # MySQL 不支持事务里跑 DDL, 关闭本迁移的事务
    atomic = False

    dependencies = [
        ("rbac", "0004_add_is_builtin"),
    ]

    operations = [
        # 先在迁移状态里注册一个 CasbinRule 模型 (不真正建表)
        migrations.CreateModel(
            name="CasbinRule",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("ptype", models.CharField(max_length=255)),
                ("v0", models.CharField(max_length=255)),
                ("v1", models.CharField(max_length=255)),
                ("v2", models.CharField(max_length=255)),
                ("v3", models.CharField(max_length=255)),
                ("v4", models.CharField(max_length=255)),
                ("v5", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "casbin_rule",
                "managed": False,
            },
        ),
        migrations.RunPython(create_casbin_rule_if_missing, drop_casbin_rule),
    ]
