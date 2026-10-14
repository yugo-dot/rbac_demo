from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from rbac.audit import log_action
from rbac.cache import invalidate_user_perms
from rbac.models import AuditLog, Role, UserRole
from rbac.permissions import HasPerm
from rbac.serializers import (
    UserRoleInputSerializer,
    UserRoleSerializer,
)

User = get_user_model()


class UserRoleViewSet(ViewSet):
    """用户 - 角色 分配接口, 挂在 /api/rbac/users/ 下."""

    permission_classes = [HasPerm]
    required_perms = {
        "GET": ["rbac:user_role:read"],
        "POST": ["rbac:user_role:manage"],
        "DELETE": ["rbac:user_role:manage"],
    }

    @extend_schema(
        summary="用户列表 (简化版)",
        description="只返回 id / username, 不分页.",
        responses={200: OpenApiResponse(description="[{id, username}, ...]")},
    )
    def list(self, request):
        """GET /api/rbac/users/ 列出所有用户 (简化版, 只返回 id / username)."""
        qs = User.objects.all().order_by("-id")
        data = [{"id": u.id, "username": u.username} for u in qs]
        return Response(data)

    @extend_schema(
        methods=["GET"],
        summary="列出某用户的角色",
        responses={200: UserRoleSerializer(many=True)},
    )
    @extend_schema(
        methods=["POST"],
        summary="给用户分配角色",
        request=UserRoleInputSerializer,
        responses={
            201: UserRoleSerializer,
            200: OpenApiResponse(description="已存在, 幂等返回"),
            404: OpenApiResponse(description="用户或角色不存在"),
        },
    )
    @action(detail=True, methods=["get", "post"], url_path="roles")
    def roles(self, request, pk=None):
        """GET  列出某用户的角色.
        POST 给某用户加角色 (body: {"role_id": 1}).
        """
        user = get_object_or_404(User, pk=pk)

        if request.method == "GET":
            qs = UserRole.objects.filter(user=user).select_related("role")
            return Response(UserRoleSerializer(qs, many=True).data)

        # POST
        input_ser = UserRoleInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        role = get_object_or_404(Role, pk=input_ser.validated_data["role_id"])

        obj, created = UserRole.objects.get_or_create(user=user, role=role)
        # 清该用户的权限缓存
        invalidate_user_perms(user.id)
        # 审计: 只在新分配时记
        if created:
            log_action(
                request,
                AuditLog.ACTION_ASSIGN,
                "user_role",
                target_id=user.id,
                target_repr=f"用户 {user.username}",
                detail={"role": role.code},
            )
        return Response(
            UserRoleSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="移除用户的某个角色",
        parameters=[
            OpenApiParameter("pk", int, OpenApiParameter.PATH, description="用户 id"),
            OpenApiParameter("role_id", int, OpenApiParameter.PATH, description="角色 id"),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            404: OpenApiResponse(description="关联不存在"),
        },
    )
    @action(detail=True, methods=["delete"], url_path=r"roles/(?P<role_id>\d+)")
    def remove_role(self, request, pk=None, role_id=None):
        """DELETE /api/rbac/users/{pk}/roles/{role_id}/ 移除某用户的某角色."""
        user = get_object_or_404(User, pk=pk)
        obj = get_object_or_404(UserRole, user=user, role_id=role_id)
        role_code = obj.role.code
        obj.delete()
        # 清该用户的权限缓存
        invalidate_user_perms(user.id)
        # 审计
        log_action(
            request,
            AuditLog.ACTION_REMOVE,
            "user_role",
            target_id=user.id,
            target_repr=f"用户 {user.username}",
            detail={"role": role_code},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
