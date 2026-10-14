from rest_framework import serializers

from rbac.models import RolePermission


class RolePermissionSerializer(serializers.ModelSerializer):
    """角色权限关联, 用于列表返回."""

    permission_name = serializers.CharField(source="permission.name", read_only=True)
    permission_code = serializers.CharField(source="permission.code", read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "role_id",
            "permission_id",
            "permission_name",
            "permission_code",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RolePermissionInputSerializer(serializers.Serializer):
    """给角色分配权限的输入参数."""

    permission_id = serializers.IntegerField()
