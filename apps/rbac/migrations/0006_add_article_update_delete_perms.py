from django.db import migrations

# 补 article:update / article:delete 两个权限点
NEW_PERMISSIONS = [
    ("更新文章", "article:update", "更新文章"),
    ("删除文章", "article:delete", "删除文章"),
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
        ("rbac", "0005_add_casbin_rule"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
