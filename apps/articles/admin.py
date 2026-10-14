from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """文章 admin.

    仅超管运维用; 业务侧的 ABAC 数据级权限走 API, 不走 admin.
    """

    list_display = (
        "id",
        "title",
        "author",
        "status",
        "visibility",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "visibility")
    search_fields = ("title", "body", "author__username")
    ordering = ("-id",)
    autocomplete_fields = ("author",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
