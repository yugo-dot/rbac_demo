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


class RegisterTests(APITestCase):
    """验证 POST /api/users/register/."""

    url = "/api/users/register/"

    def test_register_success_returns_201_and_tokens(self):
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "password": "StrongPass!2024",
                "password2": "StrongPass!2024",
                "email": "new@example.com",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["username"], "newuser")

    def test_register_duplicate_username_returns_400(self):
        User.objects.create_user(username="dup", password="x12345678", email="dup@example.com")
        resp = self.client.post(
            self.url,
            {
                "username": "dup",
                "password": "StrongPass!2024",
                "password2": "StrongPass!2024",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "username": "mismatch",
                "password": "StrongPass!2024",
                "password2": "OtherPass!2024",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_returns_400(self):
        resp = self.client.post(
            self.url,
            {"username": "weak", "password": "123", "password2": "123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordTests(APITestCase):
    """验证 POST /api/users/change-password/."""

    url = "/api/users/change-password/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="OldPass!2024", email="alice@example.com"
        )
        resp = self.client.post(
            "/api/users/login/",
            {"username": "alice", "password": "OldPass!2024"},
            format="json",
        )
        self.access = resp.data["access"]
        self.refresh = resp.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

    def test_change_password_success_returns_200(self):
        resp = self.client.post(
            self.url,
            {
                "old_password": "OldPass!2024",
                "new_password": "NewPass!2024",
                "new_password2": "NewPass!2024",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass!2024"))

    def test_change_password_wrong_old_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "old_password": "WrongOld!2024",
                "new_password": "NewPass!2024",
                "new_password2": "NewPass!2024",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch_returns_400(self):
        resp = self.client.post(
            self.url,
            {
                "old_password": "OldPass!2024",
                "new_password": "NewPass!2024",
                "new_password2": "OtherPass!2024",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_change_password_returns_401(self):
        self.client.credentials()
        resp = self.client.post(
            self.url,
            {
                "old_password": "OldPass!2024",
                "new_password": "NewPass!2024",
                "new_password2": "NewPass!2024",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_blacklists_old_refresh(self):
        """改密后旧 refresh 应失效 (被拉黑)."""
        old_refresh = self.refresh
        self.client.post(
            self.url,
            {
                "old_password": "OldPass!2024",
                "new_password": "NewPass!2024",
                "new_password2": "NewPass!2024",
            },
            format="json",
        )
        # 用旧 refresh 换 access, 应失败 (401)
        self.client.credentials()
        resp = self.client.post(
            "/api/users/token/refresh/",
            {"refresh": old_refresh},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    """验证 POST /api/users/logout/."""

    url = "/api/users/logout/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="bob", password="BobPass!2024", email="bob@example.com"
        )
        resp = self.client.post(
            "/api/users/login/",
            {"username": "bob", "password": "BobPass!2024"},
            format="json",
        )
        self.access = resp.data["access"]
        self.refresh = resp.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

    def test_logout_success_returns_200(self):
        resp = self.client.post(self.url, {"refresh": self.refresh}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh(self):
        """登出后旧 refresh 换 access 应失败."""
        self.client.post(self.url, {"refresh": self.refresh}, format="json")
        self.client.credentials()
        resp = self.client.post(
            "/api/users/token/refresh/",
            {"refresh": self.refresh},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_refresh_returns_400(self):
        resp = self.client.post(self.url, {"refresh": "not.a.valid.token"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTests(APITestCase):
    """验证 POST /api/users/token/refresh/."""

    url = "/api/users/token/refresh/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="carol", password="CarolPass!2024", email="carol@example.com"
        )
        resp = self.client.post(
            "/api/users/login/",
            {"username": "carol", "password": "CarolPass!2024"},
            format="json",
        )
        self.refresh = resp.data["refresh"]

    def test_refresh_returns_new_access(self):
        resp = self.client.post(self.url, {"refresh": self.refresh}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        # ROTATE_REFRESH_TOKENS=True, 应返回新 refresh
        self.assertIn("refresh", resp.data)

    def test_old_refresh_blacklisted_after_rotation(self):
        """轮换后旧 refresh 应被拉黑."""
        self.client.post(self.url, {"refresh": self.refresh}, format="json")
        resp = self.client.post(self.url, {"refresh": self.refresh}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
