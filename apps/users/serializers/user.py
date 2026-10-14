from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class MeSerializer(serializers.ModelSerializer):
    """当前登录用户信息, 含 Profile 字段与权限编码."""

    nickname = serializers.CharField(source='profile.nickname', read_only=True)
    avatar = serializers.URLField(source='profile.avatar', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'phone', 'email',
            'nickname', 'avatar',
            'is_superuser',
            'permissions',
        ]

    def get_permissions(self, obj):
        # 排序, 保证返回稳定
        return sorted(obj.get_permission_codes())
