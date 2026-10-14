from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """登录序列化器, 支持用户名 / 手机号 / 邮箱 三选一."""

    username = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        account = attrs.get("username") or attrs.get("phone") or attrs.get("email")
        password = attrs.get("password")

        if not account:
            raise serializers.ValidationError("请提供 username / phone / email 之一")

        if attrs.get("username"):
            user = User.objects.filter(username=attrs["username"]).first()
        elif attrs.get("phone"):
            user = User.objects.filter(phone=attrs["phone"]).first()
        else:
            user = User.objects.filter(email=attrs["email"]).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("账号或密码错误")

        if not user.is_active:
            raise serializers.ValidationError("账号已被禁用")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        return validated_data["user"]

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        # 从 Profile 取展示类信息
        profile = getattr(instance, "profile", None)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": instance.id,
                "username": instance.username,
                "nickname": profile.nickname if profile else "",
                "phone": instance.phone,
                "email": instance.email,
            },
        }


class RegisterSerializer(serializers.Serializer):
    """注册序列化器, 成功后直接返回 token (注册即登录)."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def validate_email(self, value):
        # 空串按 None 处理, 避免踩 unique 冲突
        if not value:
            return None
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("邮箱已被注册")
        return value

    def validate_phone(self, value):
        if not value:
            return None
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("手机号已被注册")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("两次输入的密码不一致")
        # 走 Django 内置密码强度校验
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        profile = getattr(instance, "profile", None)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": instance.id,
                "username": instance.username,
                "nickname": profile.nickname if profile else "",
                "phone": instance.phone,
                "email": instance.email,
            },
        }


class ChangePasswordSerializer(serializers.Serializer):
    """改密序列化器, 成功后调用方负责拉黑用户所有 refresh token."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码不正确")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError("两次输入的新密码不一致")
        validate_password(attrs["new_password"], self.context["request"].user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
