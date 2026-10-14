from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from rbac.audit import log_action
from rbac.models import AuditLog, Permission
from rbac.permissions import HasPerm
from rbac.serializers import PermissionSerializer


class PermissionViewSet(ModelViewSet):
    """权限点的 CRUD 接口."""

    queryset = Permission.objects.all().order_by("-id")
    serializer_class = PermissionSerializer

    permission_classes = [HasPerm]
    required_perms = {
        "GET": ["rbac:permission:read"],
        "POST": ["rbac:permission:manage"],
        "PUT": ["rbac:permission:manage"],
        "PATCH": ["rbac:permission:manage"],
        "DELETE": ["rbac:permission:manage"],
    }

    # 过滤 / 搜索 / 排序
    filterset_fields = ["code", "name"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["id", "code", "name", "created_at"]

    def perform_create(self, serializer):
        """创建权限 + 审计."""
        instance = serializer.save()
        log_action(
            self.request,
            AuditLog.ACTION_CREATE,
            "permission",
            target_id=instance.id,
            target_repr=f"权限 {instance.code}",
            detail={"name": instance.name, "code": instance.code},
        )

    def perform_update(self, serializer):
        """内置权限: 禁止修改 code. 成功则记审计."""
        instance = serializer.instance
        if instance.is_builtin and "code" in serializer.validated_data:
            if serializer.validated_data["code"] != instance.code:
                raise PermissionDenied("内置权限的 code 不可修改")

        before = {
            "name": instance.name,
            "code": instance.code,
            "description": instance.description,
        }
        updated = serializer.save()
        after = {
            "name": updated.name,
            "code": updated.code,
            "description": updated.description,
        }
        log_action(
            self.request,
            AuditLog.ACTION_UPDATE,
            "permission",
            target_id=updated.id,
            target_repr=f"权限 {updated.code}",
            detail={"before": before, "after": after},
        )

    def perform_destroy(self, instance):
        """内置权限: 禁止删除. 成功则记审计."""
        if instance.is_builtin:
            raise PermissionDenied("内置权限不可删除")
        perm_id = instance.id
        perm_code = instance.code
        instance.delete()
        log_action(
            self.request,
            AuditLog.ACTION_DELETE,
            "permission",
            target_id=perm_id,
            target_repr=f"权限 {perm_code}",
        )
