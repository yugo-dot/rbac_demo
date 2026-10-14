from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """审计日志: 记录 RBAC 管理面的写操作 (以及开关开启时的读操作)."""

    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_ASSIGN = "assign"
    ACTION_REMOVE = "remove"
    ACTION_READ = "read"
    ACTION_CHOICES = (
        (ACTION_CREATE, "创建"),
        (ACTION_UPDATE, "更新"),
        (ACTION_DELETE, "删除"),
        (ACTION_ASSIGN, "分配"),
        (ACTION_REMOVE, "移除"),
        (ACTION_READ, "读取"),
    )

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="操作人",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="动作")
    target_type = models.CharField(max_length=50, verbose_name="目标类型")
    target_id = models.IntegerField(null=True, blank=True, verbose_name="目标 ID")
    target_repr = models.CharField(max_length=200, blank=True, verbose_name="目标描述")
    detail = models.JSONField(null=True, blank=True, verbose_name="变更详情")
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="操作 IP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "audit_log"
        verbose_name = "审计日志"
        verbose_name_plural = verbose_name
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["operator", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.operator} {self.action} {self.target_type}#{self.target_id}"
