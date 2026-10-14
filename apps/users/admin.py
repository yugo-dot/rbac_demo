from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from unfold.widgets import UnfoldBooleanSwitchWidget

from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """用户资料内联到 User 编辑页, 一个用户只有一份."""

    model = UserProfile
    can_delete = False
    verbose_name = "用户资料"
    verbose_name_plural = verbose_name


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """用户 admin.

    在 Django 自带 UserAdmin 的基础上补 phone / email 的展示与筛选.
    这里直接继承 admin.ModelAdmin, 不继承 django.contrib.auth.admin.UserAdmin,
    避免密码字段的特殊表单逻辑干扰 (本项目认证走 JWT, 不走 admin 登录).
    """

    inlines = [UserProfileInline]

    # 布尔字段统一渲染成开关控件 (unfold 的 UnfoldBooleanSwitchWidget)
    formfield_overrides = {
        models.BooleanField: {"widget": UnfoldBooleanSwitchWidget},
    }

    # 本项目认证走 JWT, 不走 admin 登录; Django 自带的密码 / 组 / 用户权限 三个
    # 字段在这里没用, 从表单里去掉, 避免误导和占空间
    exclude = ("password", "groups", "user_permissions")

    # 详情页字段分组 (避免一列到底)
    fieldsets = (
        ("账号信息", {"fields": ("username", "email", "phone")}),
        ("权限状态", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("时间信息", {"fields": ("last_login", "date_joined")}),
    )

    list_display = (
        "id",
        "username",
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "row_actions",
    )
    # 列表页可直接改这三个开关 (simpleui 渲染成开关控件)
    # 注意: list_editable 的字段必须同时在 list_display 里
    list_editable = ("is_active", "is_staff", "is_superuser")
    list_filter = ("is_active", "is_staff", "is_superuser")

    # 把这三个 filter 从右侧挪到顶部 (unfold 的 list_filter_options)
    list_filter_options = {
        "is_active": {"horizontal": True},
        "is_staff": {"horizontal": True},
        "is_superuser": {"horizontal": True},
    }
    search_fields = ("username", "phone", "email")
    ordering = ("-id",)
    readonly_fields = ("last_login", "date_joined")

    @admin.display(description="操作")
    def row_actions(self, obj):
        """列表行操作: 编辑 / 删除."""
        edit_url = reverse("admin:users_user_change", args=[obj.pk])
        delete_url = reverse("admin:users_user_delete", args=[obj.pk])
        # 用 unfold 的按钮样式类 (抄自 unfold/templates/admin/actions.html)
        btn = (
            "cursor-pointer inline-flex font-medium items-center justify-center "
            "px-3 py-1 rounded-default text-sm whitespace-nowrap mr-2"
        )
        return mark_safe(
            f'<a class="{btn} bg-primary-900 text-white" href="{edit_url}">编辑</a>'
            f'<a class="{btn} bg-red-600 text-white" href="{delete_url}">删除</a>'
        )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料 admin (独立入口, 方便按昵称/性别筛选)."""

    list_display = ("id", "user", "nickname", "gender", "location", "updated_at")
    list_filter = ("gender",)
    search_fields = ("user__username", "nickname", "location")
    ordering = ("-id",)
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
