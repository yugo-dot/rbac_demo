from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import LoginSerializer


class LoginView(APIView):
    """登录视图, 支持用户名 / 手机号 / 邮箱 三选一."""

    # 登录接口本身不需要认证
    permission_classes = [AllowAny]

    @extend_schema(
        summary='登录',
        description='支持 username / phone / email 三选一 + password.',
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='登录成功, 返回 access / refresh / user'),
            400: OpenApiResponse(description='参数错误 / 账号或密码错误'),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # to_representation 里已经把 token 和用户信息组装好
        data = serializer.to_representation(serializer.validated_data['user'])
        return Response(data, status=status.HTTP_200_OK)
