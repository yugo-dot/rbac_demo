from django.db import migrations

# 策略管理权限点
NEW_PERMISSIONS = [
    ("读取策略", "rbac:policy:read", "查看 Casbin 策略列表"),
    ("管理策略", "rbac:policy:manage", "增删 Casbin 策略"),
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
        ("rbac", "0007_seed_casbin_policies"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
