from django.contrib import admin

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

    list_display = (
        "id",
        "username",
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "phone", "email")
    ordering = ("-id",)
    readonly_fields = ("last_login", "date_joined")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料 admin (独立入口, 方便按昵称/性别筛选)."""

    list_display = ("id", "user", "nickname", "gender", "location", "updated_at")
    list_filter = ("gender",)
    search_fields = ("user__username", "nickname", "location")
    ordering = ("-id",)
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
