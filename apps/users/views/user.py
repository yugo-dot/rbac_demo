from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers import MeSerializer


class MeView(RetrieveAPIView):
    """当前登录用户信息, GET /api/users/me/."""

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="当前登录用户信息",
        description="返回当前用户的资料 + 权限编码列表.",
        responses={200: MeSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        # 永远返回当前请求用户
        return self.request.user
