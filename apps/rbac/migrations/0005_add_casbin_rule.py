from django.db import migrations


def create_casbin_rule_if_missing(apps, schema_editor):
    """建 casbin_rule 表 (若不存在).

    这张表原本由 casbin_adapter app 的迁移建, 但那个 app 因为会在
    AppConfig.ready() 里访问 DB 被我们从 INSTALLED_APPS 移除了.
    为让全新环境能完整复现, 把建表搬到这里.
    开发库表已存在, 检测到就跳过 (幂等).
    """
    table_name = "casbin_rule"
    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name in existing_tables:
        return

    schema_editor.execute(
        """
        CREATE TABLE casbin_rule (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            ptype VARCHAR(255) NOT NULL,
            v0 VARCHAR(255) NOT NULL,
            v1 VARCHAR(255) NOT NULL,
            v2 VARCHAR(255) NOT NULL,
            v3 VARCHAR(255) NOT NULL,
            v4 VARCHAR(255) NOT NULL,
            v5 VARCHAR(255) NOT NULL
        )
        """
    )


def drop_casbin_rule(apps, schema_editor):
    """反向: 删表 (谨慎)."""
    schema_editor.execute("DROP TABLE IF EXISTS casbin_rule")


class Migration(migrations.Migration):

    # MySQL 不支持事务里跑 DDL, 关闭本迁移的事务
    atomic = False

    dependencies = [
        ("rbac", "0004_add_is_builtin"),
    ]

    operations = [
        migrations.RunPython(create_casbin_rule_if_missing, drop_casbin_rule),
    ]
