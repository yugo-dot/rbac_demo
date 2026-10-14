from django.contrib import admin

from .models import AuditLog, Permission, Role, RolePermission, UserRole


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色 admin.

    code / is_builtin 只读: 防止从 admin 绕过 API 层的保护.
    内置角色不可删: 与 ViewSet.perform_destroy 的保护对齐.
    """

    list_display = ("id", "name", "code", "is_builtin", "description", "created_at")
    list_filter = ("is_builtin",)
    search_fields = ("name", "code", "description")
    ordering = ("-id",)
    readonly_fields = ("code", "is_builtin", "created_at")

    def has_delete_permission(self, request, obj=None):
        """内置角色不可删 (超管也不行)."""
        if obj is not None and obj.is_builtin:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """权限点 admin.

    code / is_builtin 只读, 内置权限不可删, 理由同 RoleAdmin.
    """

    list_display = ("id", "name", "code", "is_builtin", "description", "created_at")
    list_filter = ("is_builtin",)
    search_fields = ("name", "code", "description")
    ordering = ("-id",)
    readonly_fields = ("code", "is_builtin", "created_at")

    def has_delete_permission(self, request, obj=None):
        """内置权限不可删 (超管也不行)."""
        if obj is not None and obj.is_builtin:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """用户-角色关联 admin (纯关联, 正常增删)."""

    list_display = ("id", "user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "role__name", "role__code")
    ordering = ("-id",)
    autocomplete_fields = ("user", "role")
    readonly_fields = ("created_at",)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """角色-权限关联 admin (纯关联, 正常增删)."""

    list_display = ("id", "role", "permission", "created_at")
    list_filter = ("role",)
    search_fields = ("role__name", "role__code", "permission__code")
    ordering = ("-id",)
    autocomplete_fields = ("role", "permission")
    readonly_fields = ("created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """审计日志 admin (全只读).

    审计日志的核心价值是不可篡改, admin 里不允许增 / 改 / 删.
    查询能力保留: 按动作 / 目标类型 / 操作人筛选, 按关键字搜索.
    """

    list_display = (
        "id",
        "created_at",
        "operator",
        "action",
        "target_type",
        "target_id",
        "target_repr",
        "ip",
    )
    list_filter = ("action", "target_type")
    search_fields = ("operator__username", "target_repr", "target_type")
    ordering = ("-id",)
    readonly_fields = (
        "operator",
        "action",
        "target_type",
        "target_id",
        "target_repr",
        "detail",
        "ip",
        "created_at",
    )

    def has_add_permission(self, request):
        """审计日志不允许手动新增."""
        return False

    def has_change_permission(self, request, obj=None):
        """审计日志不允许修改."""
        return False

    def has_delete_permission(self, request, obj=None):
        """审计日志不允许删除."""
        return False
