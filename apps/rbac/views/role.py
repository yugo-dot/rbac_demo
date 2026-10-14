from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from rbac.cache import invalidate_role_perms
from rbac.models import Permission, Role, RolePermission
from rbac.serializers import (
    RolePermissionInputSerializer,
    RolePermissionSerializer,
    RoleSerializer,
)


class RoleViewSet(ModelViewSet):
    """角色的 CRUD 接口 + 角色权限分配."""

    queryset = Role.objects.all().order_by('-id')
    serializer_class = RoleSerializer

    # 过滤 / 搜索 / 排序
    filterset_fields = ['code', 'name']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['id', 'code', 'name', 'created_at']

    @extend_schema(
        methods=['GET'],
        summary='列出某角色的权限',
        responses={200: RolePermissionSerializer(many=True)},
    )
    @extend_schema(
        methods=['POST'],
        summary='给角色分配权限',
        request=RolePermissionInputSerializer,
        responses={
            201: RolePermissionSerializer,
            200: OpenApiResponse(description='已存在, 幂等返回'),
            404: OpenApiResponse(description='角色或权限不存在'),
        },
    )
    @action(detail=True, methods=['get', 'post'], url_path='permissions')
    def permissions(self, request, pk=None):
        """GET  列出某角色的权限.
        POST 给某角色加权限 (body: {"permission_id": 1}).
        """
        role = get_object_or_404(Role, pk=pk)

        if request.method == 'GET':
            qs = RolePermission.objects.filter(role=role).select_related('permission')
            return Response(RolePermissionSerializer(qs, many=True).data)

        # POST
        input_ser = RolePermissionInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        permission = get_object_or_404(
            Permission, pk=input_ser.validated_data['permission_id']
        )

        obj, created = RolePermission.objects.get_or_create(
            role=role, permission=permission
        )
        # 清该角色下所有用户的权限缓存
        invalidate_role_perms(role.id)
        return Response(
            RolePermissionSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary='移除角色的某个权限',
        parameters=[
            OpenApiParameter('pk', int, OpenApiParameter.PATH, description='角色 id'),
            OpenApiParameter('permission_id', int, OpenApiParameter.PATH, description='权限 id'),
        ],
        responses={
            204: OpenApiResponse(description='删除成功'),
            404: OpenApiResponse(description='关联不存在'),
        },
    )
    @action(
        detail=True,
        methods=['delete'],
        url_path=r'permissions/(?P<permission_id>\d+)',
    )
    def remove_permission(self, request, pk=None, permission_id=None):
        """DELETE /api/rbac/roles/{pk}/permissions/{permission_id}/ 移除某角色的某权限."""
        role = get_object_or_404(Role, pk=pk)
        obj = get_object_or_404(
            RolePermission, role=role, permission_id=permission_id
        )
        obj.delete()
        # 清该角色下所有用户的权限缓存
        invalidate_role_perms(role.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
