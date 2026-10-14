from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rbac.audit import log_action
from rbac.cache import invalidate_role_perms
from rbac.models import AuditLog, Permission, Role, RolePermission
from rbac.permissions import HasPerm
from rbac.serializers import (
    RolePermissionInputSerializer,
    RolePermissionSerializer,
    RoleSerializer,
)


class RoleViewSet(ModelViewSet):
    """角色的 CRUD 接口 + 角色权限分配."""

    queryset = Role.objects.all().order_by("-id")
    serializer_class = RoleSerializer

    permission_classes = [HasPerm]
    required_perms = {
        "GET": ["rbac:role:read"],
        "POST": ["rbac:role:manage"],
        "PUT": ["rbac:role:manage"],
        "PATCH": ["rbac:role:manage"],
        "DELETE": ["rbac:role:manage"],
    }

    # 过滤 / 搜索 / 排序
    filterset_fields = ["code", "name"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["id", "code", "name", "created_at"]

    def perform_create(self, serializer):
        """创建角色 + 审计."""
        instance = serializer.save()
        log_action(
            self.request,
            AuditLog.ACTION_CREATE,
            "role",
            target_id=instance.id,
            target_repr=f"角色 {instance.code}",
            detail={"name": instance.name, "code": instance.code},
        )

    def perform_update(self, serializer):
        """内置角色: 禁止修改 code. 成功则记审计."""
        instance = serializer.instance
        if instance.is_builtin and "code" in serializer.validated_data:
            if serializer.validated_data["code"] != instance.code:
                raise PermissionDenied("内置角色的 code 不可修改")

        before = {"name": instance.name, "code": instance.code, "description": instance.description}
        updated = serializer.save()
        after = {"name": updated.name, "code": updated.code, "description": updated.description}
        log_action(
            self.request,
            AuditLog.ACTION_UPDATE,
            "role",
            target_id=updated.id,
            target_repr=f"角色 {updated.code}",
            detail={"before": before, "after": after},
        )

    def perform_destroy(self, instance):
        """内置角色: 禁止删除. 成功则记审计."""
        if instance.is_builtin:
            raise PermissionDenied("内置角色不可删除")
        role_id = instance.id
        role_code = instance.code
        instance.delete()
        log_action(
            self.request,
            AuditLog.ACTION_DELETE,
            "role",
            target_id=role_id,
            target_repr=f"角色 {role_code}",
        )

    @extend_schema(
        methods=["GET"],
        summary="列出某角色的权限",
        responses={200: RolePermissionSerializer(many=True)},
    )
    @extend_schema(
        methods=["POST"],
        summary="给角色分配权限",
        request=RolePermissionInputSerializer,
        responses={
            201: RolePermissionSerializer,
            200: OpenApiResponse(description="已存在, 幂等返回"),
            404: OpenApiResponse(description="角色或权限不存在"),
        },
    )
    @action(detail=True, methods=["get", "post"], url_path="permissions")
    def permissions(self, request, pk=None):
        """GET  列出某角色的权限.
        POST 给某角色加权限 (body: {"permission_id": 1}).
        """
        role = get_object_or_404(Role, pk=pk)

        if request.method == "GET":
            qs = RolePermission.objects.filter(role=role).select_related("permission")
            return Response(RolePermissionSerializer(qs, many=True).data)

        # POST
        input_ser = RolePermissionInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        permission = get_object_or_404(Permission, pk=input_ser.validated_data["permission_id"])

        obj, created = RolePermission.objects.get_or_create(role=role, permission=permission)
        # 清该角色下所有用户的权限缓存
        invalidate_role_perms(role.id)
        # 审计: 只在新分配时记 (已存在时幂等, 不记)
        if created:
            log_action(
                request,
                AuditLog.ACTION_ASSIGN,
                "role_permission",
                target_id=role.id,
                target_repr=f"角色 {role.code}",
                detail={"permission": permission.code},
            )
        return Response(
            RolePermissionSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="移除角色的某个权限",
        parameters=[
            OpenApiParameter("pk", int, OpenApiParameter.PATH, description="角色 id"),
            OpenApiParameter("permission_id", int, OpenApiParameter.PATH, description="权限 id"),
        ],
        responses={
            204: OpenApiResponse(description="删除成功"),
            404: OpenApiResponse(description="关联不存在"),
        },
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"permissions/(?P<permission_id>\d+)",
    )
    def remove_permission(self, request, pk=None, permission_id=None):
        """DELETE /api/rbac/roles/{pk}/permissions/{permission_id}/ 移除某角色的某权限."""
        role = get_object_or_404(Role, pk=pk)
        obj = get_object_or_404(RolePermission, role=role, permission_id=permission_id)
        permission_code = obj.permission.code
        obj.delete()
        # 清该角色下所有用户的权限缓存
        invalidate_role_perms(role.id)
        # 审计
        log_action(
            request,
            AuditLog.ACTION_REMOVE,
            "role_permission",
            target_id=role.id,
            target_repr=f"角色 {role.code}",
            detail={"permission": permission_code},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
