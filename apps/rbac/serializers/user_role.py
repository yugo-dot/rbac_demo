from rest_framework import serializers

from rbac.models import UserRole


class UserRoleSerializer(serializers.ModelSerializer):
    """用户角色关联, 用于列表返回."""

    role_name = serializers.CharField(source="role.name", read_only=True)
    role_code = serializers.CharField(source="role.code", read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "user_id", "role_id", "role_name", "role_code", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserRoleInputSerializer(serializers.Serializer):
    """给用户分配角色的输入参数."""

    role_id = serializers.IntegerField()
