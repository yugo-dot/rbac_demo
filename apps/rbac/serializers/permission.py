from rest_framework import serializers

from rbac.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器."""

    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']
