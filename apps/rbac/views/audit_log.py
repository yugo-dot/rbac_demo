from rest_framework.viewsets import ReadOnlyModelViewSet

from rbac.models import AuditLog
from rbac.permissions import HasPerm
from rbac.serializers import AuditLogSerializer


class AuditLogViewSet(ReadOnlyModelViewSet):
    """审计日志查询接口 (只读), 挂在 /api/rbac/audit-logs/ 下.

    - list: 日志列表 (分页 + 过滤 + 搜索 + 排序)
    - retrieve: 单条详情
    - 不支持 create / update / delete (日志一旦写入不可改)
    """

    queryset = AuditLog.objects.select_related("operator").all()
    serializer_class = AuditLogSerializer

    permission_classes = [HasPerm]
    required_perms = {
        "GET": ["rbac:audit_log:read"],
    }

    # 过滤 / 搜索 / 排序
    filterset_fields = ["action", "target_type", "operator", "target_id"]
    search_fields = ["target_repr", "target_type"]
    ordering_fields = ["id", "created_at"]
