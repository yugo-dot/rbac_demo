import contextlib

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
)


class LoginView(APIView):
    """登录视图, 支持用户名 / 手机号 / 邮箱 三选一."""

    # 登录接口本身不需要认证
    permission_classes = [AllowAny]

    @extend_schema(
        summary="登录",
        description="支持 username / phone / email 三选一 + password.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="登录成功, 返回 access / refresh / user"),
            400: OpenApiResponse(description="参数错误 / 账号或密码错误"),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # to_representation 里已经把 token 和用户信息组装好
        data = serializer.to_representation(serializer.validated_data["user"])
        return Response(data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """注册视图, 注册成功直接返回 token (注册即登录)."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="注册",
        description="注册成功后直接返回 access / refresh / user.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="注册成功, 返回 access / refresh / user"),
            400: OpenApiResponse(description="参数错误 / 用户名或邮箱/手机号已存在"),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = serializer.to_representation(user)
        return Response(data, status=status.HTTP_201_CREATED)


class ChangePasswordView(APIView):
    """改密视图, 成功后强制重登 (拉黑该用户所有 refresh token)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="修改密码",
        description="修改成功后, 该用户所有 refresh token 会被拉黑, 需重新登录.",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="修改成功"),
            400: OpenApiResponse(description="旧密码错误 / 新密码不符合要求"),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 强制重登: 拉黑该用户所有未失效的 refresh token
        # OutstandingToken 由 blacklist app 在签发 token 时自动写入
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        for token in OutstandingToken.objects.filter(user=user):
            # 已过期或已拉黑时 blacklist() 会抛 TokenError, 忽略即可
            with contextlib.suppress(TokenError):
                RefreshToken(token.token).blacklist()

        return Response(
            {"msg": "密码修改成功, 请重新登录"},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """登出视图, 把传入的 refresh token 拉黑."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="登出",
        description="把请求体里的 refresh 拉黑, 后续用该 refresh 换 access 会被拒.",
        request=None,
        responses={
            200: OpenApiResponse(description="登出成功"),
            400: OpenApiResponse(description="refresh 缺失 / 无效"),
        },
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "缺少 refresh 参数"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"detail": "refresh 无效或已失效"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"msg": "登出成功"}, status=status.HTTP_200_OK)
