from rest_framework.viewsets import ModelViewSet

from rbac.models import Permission
from rbac.serializers import PermissionSerializer


class PermissionViewSet(ModelViewSet):
    """权限点的 CRUD 接口."""

    queryset = Permission.objects.all().order_by('-id')
    serializer_class = PermissionSerializer

    # 过滤 / 搜索 / 排序
    filterset_fields = ['code', 'name']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['id', 'code', 'name', 'created_at']
