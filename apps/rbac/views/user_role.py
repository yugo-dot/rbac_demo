from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from rbac.models import Role, UserRole
from rbac.serializers import (
    UserRoleInputSerializer,
    UserRoleSerializer,
)

User = get_user_model()


class UserRoleViewSet(ViewSet):
    """用户 - 角色 分配接口, 挂在 /api/rbac/users/ 下."""

    def list(self, request):
        """GET /api/rbac/users/ 列出所有用户 (简化版, 只返回 id / username)."""
        qs = User.objects.all().order_by('-id')
        data = [{'id': u.id, 'username': u.username} for u in qs]
        return Response(data)

    @action(detail=True, methods=['get', 'post'], url_path='roles')
    def roles(self, request, pk=None):
        """GET  列出某用户的角色.
        POST 给某用户加角色 (body: {"role_id": 1}).
        """
        user = get_object_or_404(User, pk=pk)

        if request.method == 'GET':
            qs = UserRole.objects.filter(user=user).select_related('role')
            return Response(UserRoleSerializer(qs, many=True).data)

        # POST
        input_ser = UserRoleInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        role = get_object_or_404(Role, pk=input_ser.validated_data['role_id'])

        obj, created = UserRole.objects.get_or_create(user=user, role=role)
        return Response(
            UserRoleSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['delete'], url_path=r'roles/(?P<role_id>\d+)')
    def remove_role(self, request, pk=None, role_id=None):
        """DELETE /api/rbac/users/{pk}/roles/{role_id}/ 移除某用户的某角色."""
        user = get_object_or_404(User, pk=pk)
        obj = get_object_or_404(UserRole, user=user, role_id=role_id)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
