from django.db import migrations


def derive_module(code: str) -> str:
    """与 Permission.derive_module 同规则: 取最后一个 ":" 之前的部分."""
    if ":" not in code:
        return code
    return code.rsplit(":", 1)[0]


def backfill_module(apps, schema_editor):
    """给现有权限点回填 module."""
    Permission = apps.get_model("rbac", "Permission")
    for perm in Permission.objects.all():
        perm.module = derive_module(perm.code)
        perm.save(update_fields=["module"])


def clear_module(apps, schema_editor):
    """回滚: 把 module 清空."""
    Permission = apps.get_model("rbac", "Permission")
    Permission.objects.update(module="")


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0011_add_permission_module"),
    ]

    operations = [
        migrations.RunPython(backfill_module, clear_module),
    ]
