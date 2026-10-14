from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "用户管理"

    def ready(self):
        # 注册 signal, 保证 User 创建后自动创建 UserProfile
        from . import signals  # noqa: F401
