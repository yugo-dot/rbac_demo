from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import UserProfile

User = get_user_model()


class MeSerializer(serializers.ModelSerializer):
    """当前登录用户信息, 含 Profile 字段与权限编码."""

    nickname = serializers.CharField(source="profile.nickname", read_only=True)
    avatar = serializers.URLField(source="profile.avatar", read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "phone",
            "email",
            "nickname",
            "avatar",
            "is_superuser",
            "permissions",
        ]

    def get_permissions(self, obj) -> list:
        # 排序, 保证返回稳定
        return sorted(obj.get_permission_codes())


class MeUpdateSerializer(serializers.ModelSerializer):
    """当前用户资料修改 (PATCH /api/users/me/), 只放可写字段.

    可写: UserProfile 的展示类字段 (nickname / avatar / bio / gender / birthday / location).
    不可写: username / phone / email / is_superuser / permissions (走各自的专用接口或禁止改).
    """

    nickname = serializers.CharField(
        source="profile.nickname", required=False, allow_blank=True, max_length=50
    )
    avatar = serializers.URLField(
        source="profile.avatar", required=False, allow_blank=True, max_length=500
    )
    bio = serializers.CharField(
        source="profile.bio", required=False, allow_blank=True, max_length=200
    )
    gender = serializers.ChoiceField(
        source="profile.gender", required=False, choices=UserProfile.GENDER_CHOICES
    )
    birthday = serializers.DateField(source="profile.birthday", required=False, allow_null=True)
    location = serializers.CharField(
        source="profile.location", required=False, allow_blank=True, max_length=100
    )

    class Meta:
        model = User
        fields = ["nickname", "avatar", "bio", "gender", "birthday", "location"]

    def update(self, instance, validated_data):
        """把嵌套的 profile 字段拆出来, 写到 UserProfile 上."""
        profile_data = validated_data.pop("profile", {})
        for attr, value in profile_data.items():
            setattr(instance.profile, attr, value)
        instance.profile.save()
        return instance
