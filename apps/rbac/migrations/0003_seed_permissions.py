from django.db import migrations


# 预置权限点: (name, code, description)
INITIAL_PERMISSIONS = [
    ('读取角色', 'rbac:role:read', '查看角色列表/详情/角色权限'),
    ('管理角色', 'rbac:role:manage', '增删改角色及分配角色权限'),
    ('读取权限点', 'rbac:permission:read', '查看权限点列表/详情'),
    ('管理权限点', 'rbac:permission:manage', '增删改权限点'),
    ('读取用户角色', 'rbac:user_role:read', '查看用户简表及用户的角色'),
    ('管理用户角色', 'rbac:user_role:manage', '给用户分配/移除角色'),
    ('读取文章', 'article:read', '读取文章示例接口'),
    ('创建文章', 'article:create', '创建文章示例接口'),
]


def create_permissions(apps, schema_editor):
    """正向: 预置权限点, 已存在则跳过 (幂等)."""
    Permission = apps.get_model('rbac', 'Permission')
    for name, code, description in INITIAL_PERMISSIONS:
        Permission.objects.get_or_create(
            code=code,
            defaults={'name': name, 'description': description},
        )


def remove_permissions(apps, schema_editor):
    """反向: 删除本次预置的权限点."""
    Permission = apps.get_model('rbac', 'Permission')
    codes = [code for _, code, _ in INITIAL_PERMISSIONS]
    Permission.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
