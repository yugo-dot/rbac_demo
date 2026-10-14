from django.conf import settings
from django.db import models


class Article(models.Model):
    """文章模型, 用于演示 ABAC 数据级权限."""

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "草稿"),
        (STATUS_PUBLISHED, "已发布"),
        (STATUS_ARCHIVED, "已归档"),
    )

    VISIBILITY_PRIVATE = "private"
    VISIBILITY_TEAM = "team"
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_CHOICES = (
        (VISIBILITY_PRIVATE, "仅自己"),
        (VISIBILITY_TEAM, "团队可见"),
        (VISIBILITY_PUBLIC, "公开"),
    )

    title = models.CharField(max_length=200, verbose_name="标题")
    body = models.TextField(blank=True, verbose_name="正文")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="作者",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name="状态",
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PRIVATE,
        verbose_name="可见性",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "article"
        verbose_name = "文章"
        verbose_name_plural = verbose_name
        ordering = ["-id"]

    def __str__(self):
        return self.title

    def to_abac_obj(self) -> dict:
        """转成 Casbin 需要的对象属性 dict."""
        return {
            "obj_type": "article",
            "id": self.id,
            "author_id": self.author_id,
            "status": self.status,
            "visibility": self.visibility,
        }
