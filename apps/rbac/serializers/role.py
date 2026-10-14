from rest_framework import serializers

from rbac.models import Role


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器."""

    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']
