from rest_framework import serializers

from rbac.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """审计日志序列化器 (只读)."""

    operator_name = serializers.CharField(source="operator.username", read_only=True, default="")

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "operator",
            "operator_name",
            "action",
            "target_type",
            "target_id",
            "target_repr",
            "detail",
            "ip",
            "created_at",
        ]
        read_only_fields = fields
