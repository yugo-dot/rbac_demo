from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import LoginSerializer


class LoginView(APIView):
    """登录视图, 支持用户名 / 手机号 / 邮箱 三选一."""

    # 登录接口本身不需要认证
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # to_representation 里已经把 token 和用户信息组装好
        data = serializer.to_representation(serializer.validated_data['user'])
        return Response(data, status=status.HTTP_200_OK)
