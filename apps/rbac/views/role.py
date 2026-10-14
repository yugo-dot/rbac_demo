from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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
        return Response(
            RolePermissionSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
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
        return Response(status=status.HTTP_204_NO_CONTENT)
