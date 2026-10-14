from django.contrib.auth import get_user_model
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
        account = attrs.get('username') or attrs.get('phone') or attrs.get('email')
        password = attrs.get('password')

        if not account:
            raise serializers.ValidationError('请提供 username / phone / email 之一')

        if attrs.get('username'):
            user = User.objects.filter(username=attrs['username']).first()
        elif attrs.get('phone'):
            user = User.objects.filter(phone=attrs['phone']).first()
        else:
            user = User.objects.filter(email=attrs['email']).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError('账号或密码错误')

        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用')

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        return validated_data['user']

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        # 从 Profile 取展示类信息
        profile = getattr(instance, 'profile', None)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': instance.id,
                'username': instance.username,
                'nickname': profile.nickname if profile else '',
                'phone': instance.phone,
                'email': instance.email,
            },
        }
