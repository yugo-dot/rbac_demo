from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.serializers import MeSerializer, MeUpdateSerializer


class MeView(RetrieveUpdateAPIView):
    """当前登录用户信息 / 修改资料.

    - GET   /api/users/me/  读 (返回资料 + 权限编码)
    - PATCH /api/users/me/  改 (只改 UserProfile 展示字段)
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # 读用 MeSerializer, 写用 MeUpdateSerializer
        if self.request.method in ("PUT", "PATCH"):
            return MeUpdateSerializer
        return MeSerializer

    def get_object(self):
        # 永远返回当前请求用户
        return self.request.user

    @extend_schema(
        summary="当前登录用户信息",
        description="返回当前用户的资料 + 权限编码列表.",
        responses={200: MeSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="修改当前用户资料",
        description="只允许改 UserProfile 的展示字段 (nickname / avatar / bio / gender / birthday / location).",
        request=MeUpdateSerializer,
        responses={200: MeSerializer},
    )
    def patch(self, request, *args, **kwargs):
        """写入用 MeUpdateSerializer, 响应统一用 MeSerializer 返回完整资源."""
        instance = self.get_object()
        write_serializer = self.get_serializer(instance, data=request.data, partial=True)
        write_serializer.is_valid(raise_exception=True)
        write_serializer.save()
        return Response(MeSerializer(instance).data)
