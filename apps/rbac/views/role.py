from rest_framework.viewsets import ModelViewSet

from rbac.models import Role
from rbac.serializers import RoleSerializer


class RoleViewSet(ModelViewSet):
    """角色的 CRUD 接口.

    list / create / retrieve / update / partial_update / destroy
    由 ModelViewSet 自动提供.
    """

    queryset = Role.objects.all().order_by('-id')
    serializer_class = RoleSerializer
