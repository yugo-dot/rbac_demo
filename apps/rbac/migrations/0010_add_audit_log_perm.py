from django.db import migrations

# 审计日志查看权限点
NEW_PERMISSIONS = [
    ("查看审计日志", "rbac:audit_log:read", "查看 RBAC 管理操作日志"),
]


def create_permissions(apps, schema_editor):
    """正向: 补权限点, 已存在则跳过 (幂等). 同时标记为内置."""
    Permission = apps.get_model("rbac", "Permission")
    for name, code, description in NEW_PERMISSIONS:
        obj, _ = Permission.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": description},
        )
        if not obj.is_builtin:
            obj.is_builtin = True
            obj.save(update_fields=["is_builtin"])


def remove_permissions(apps, schema_editor):
    """反向: 删除本次补的权限点."""
    Permission = apps.get_model("rbac", "Permission")
    codes = [code for _, code, _ in NEW_PERMISSIONS]
    Permission.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0009_add_audit_log"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
