from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from rbac.models import Permission, Role, RolePermission, UserRole

User = get_user_model()


class ArticleDemoPermissionTests(APITestCase):
    """验证 ArticleDemoView 的 RBAC 保护."""

    url = "/api/demo/articles/"

    @classmethod
    def setUpTestData(cls):
        # 权限点
        cls.p_read = Permission.objects.get_or_create(
            code="article:read", defaults={"name": "读取文章"}
        )[0]
        cls.p_create = Permission.objects.get_or_create(
            code="article:create", defaults={"name": "创建文章"}
        )[0]

        # 角色 editor, 绑定两个权限
        cls.role_editor = Role.objects.create(name="编辑", code="editor")
        RolePermission.objects.create(role=cls.role_editor, permission=cls.p_read)
        RolePermission.objects.create(role=cls.role_editor, permission=cls.p_create)

        # 有权限的用户
        cls.alice = User.objects.create_user(
            username="alice", password="alice12345", email="alice@example.com"
        )
        UserRole.objects.create(user=cls.alice, role=cls.role_editor)

        # 无权限的用户
        cls.bob = User.objects.create_user(
            username="bob", password="bob12345", email="bob@example.com"
        )

    def _login(self, username, password):
        resp = self.client.post(
            "/api/users/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data["access"]

    def test_no_token_returns_401(self):
        """未登录访问 -> 401."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_role_gets_403(self):
        """无权限用户 -> 403."""
        token = self._login("bob", "bob12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_role_gets_200(self):
        """有权限用户 -> 200."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_superuser_bypasses(self):
        """超级管理员直接放行."""
        User.objects.create_superuser(
            username="root", password="root12345", email="root@example.com"
        )
        token = self._login("root", "root12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
