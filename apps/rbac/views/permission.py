from rest_framework.viewsets import ModelViewSet

from rbac.models import Permission
from rbac.serializers import PermissionSerializer


class PermissionViewSet(ModelViewSet):
    """权限点的 CRUD 接口."""

    queryset = Permission.objects.all().order_by('-id')
    serializer_class = PermissionSerializer
