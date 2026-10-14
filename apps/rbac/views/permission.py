from rest_framework.viewsets import ModelViewSet

from rbac.models import Permission
from rbac.permissions import HasPerm
from rbac.serializers import PermissionSerializer


class PermissionViewSet(ModelViewSet):
    """权限点的 CRUD 接口."""

    queryset = Permission.objects.all().order_by('-id')
    serializer_class = PermissionSerializer

    permission_classes = [HasPerm]
    required_perms = {
        'GET': ['rbac:permission:read'],
        'POST': ['rbac:permission:manage'],
        'PUT': ['rbac:permission:manage'],
        'PATCH': ['rbac:permission:manage'],
        'DELETE': ['rbac:permission:manage'],
    }

    # 过滤 / 搜索 / 排序
    filterset_fields = ['code', 'name']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['id', 'code', 'name', 'created_at']

