from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from rbac.models import Permission, Role, RolePermission, UserRole

User = get_user_model()


class MeViewTests(APITestCase):
    """验证 GET /api/users/me/."""

    url = "/api/users/me/"

    @classmethod
    def setUpTestData(cls):
        p_read = Permission.objects.get_or_create(
            code="article:read", defaults={"name": "读取文章"}
        )[0]
        p_create = Permission.objects.get_or_create(
            code="article:create", defaults={"name": "创建文章"}
        )[0]

        role_editor = Role.objects.create(name="编辑", code="editor")
        RolePermission.objects.create(role=role_editor, permission=p_read)
        RolePermission.objects.create(role=role_editor, permission=p_create)

        cls.alice = User.objects.create_user(
            username="alice",
            password="alice12345",
            email="alice@example.com",
            phone="13800000001",
        )
        UserRole.objects.create(user=cls.alice, role=role_editor)
        # 填个昵称
        cls.alice.profile.nickname = "爱丽丝"
        cls.alice.profile.save()

    def _login(self, username, password):
        resp = self.client.post(
            "/api/users/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data["access"]

    def test_no_token_returns_401(self):
        """未登录 -> 401."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile_and_permissions(self):
        """已登录 -> 200, 返回 profile 字段 + 权限列表."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(data["username"], "alice")
        self.assertEqual(data["nickname"], "爱丽丝")
        self.assertEqual(data["phone"], "13800000001")
        self.assertEqual(sorted(data["permissions"]), ["article:create", "article:read"])
