from django.db import migrations, models


# 需要标记为内置的权限编码 (与 0003_seed_permissions 一致)
BUILTIN_PERMISSION_CODES = [
    'rbac:role:read', 'rbac:role:manage',
    'rbac:permission:read', 'rbac:permission:manage',
    'rbac:user_role:read', 'rbac:user_role:manage',
    'article:read', 'article:create',
]


def mark_builtin(apps, schema_editor):
    """把种子权限点标为内置."""
    Permission = apps.get_model('rbac', 'Permission')
    Permission.objects.filter(code__in=BUILTIN_PERMISSION_CODES).update(is_builtin=True)


def unmark_builtin(apps, schema_editor):
    """反向: 取消内置标记."""
    Permission = apps.get_model('rbac', 'Permission')
    Permission.objects.filter(code__in=BUILTIN_PERMISSION_CODES).update(is_builtin=False)


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0003_seed_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='is_builtin',
            field=models.BooleanField(default=False, verbose_name='是否内置'),
        ),
        migrations.AddField(
            model_name='role',
            name='is_builtin',
            field=models.BooleanField(default=False, verbose_name='是否内置'),
        ),
        migrations.RunPython(mark_builtin, unmark_builtin),
    ]
