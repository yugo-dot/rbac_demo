"""UserAdmin 冒烟测试: 页面能打开, 关键元素存在."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserAdminSmokeTests(TestCase):
    """User admin 页面冒烟测试."""

    @classmethod
    def setUpTestData(cls):
        # 超管 (能进 admin)
        cls.superuser = User.objects.create_superuser(
            username="root", password="root12345", email="root@example.com"
        )
        # 普通用户 (不能进 admin)
        cls.normal = User.objects.create_user(
            username="alice", password="alice12345", email="alice@example.com"
        )

    def _login_superuser(self):
        self.client.force_login(self.superuser)

    def test_anonymous_redirected_to_login(self):
        """未登录访问 admin -> 重定向到登录页."""
        resp = self.client.get(reverse("admin:users_user_changelist"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_normal_user_cannot_access(self):
        """普通用户 (非 staff) 访问 admin -> 重定向."""
        self.client.force_login(self.normal)
        resp = self.client.get(reverse("admin:users_user_changelist"))
        self.assertEqual(resp.status_code, 302)

    def test_changelist_renders(self):
        """超管访问用户列表 -> 200."""
        self._login_superuser()
        resp = self.client.get(reverse("admin:users_user_changelist"))
        self.assertEqual(resp.status_code, 200)

    def test_changelist_has_action_buttons(self):
        """列表页含操作列的编辑 / 删除按钮."""
        self._login_superuser()
        resp = self.client.get(reverse("admin:users_user_changelist"))
        html = resp.content.decode()
        self.assertIn("编辑", html)
        self.assertIn("删除", html)
        # 按钮链接指向 change / delete
        self.assertIn(reverse("admin:users_user_change", args=[self.normal.pk]), html)

    def test_change_form_renders_with_fieldsets(self):
        """编辑页 200, 含三个字段分组标题."""
        self._login_superuser()
        resp = self.client.get(reverse("admin:users_user_change", args=[self.normal.pk]))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("账号信息", html)
        self.assertIn("权限状态", html)
        self.assertIn("时间信息", html)

    def test_change_form_excludes_unused_fields(self):
        """编辑页不含 密码 / 组 / 用户权限 三个字段 (已被 exclude)."""
        self._login_superuser()
        resp = self.client.get(reverse("admin:users_user_change", args=[self.normal.pk]))
        html = resp.content.decode()
        # 查具体字段的 form input name, 避免误伤页面里的其它文案
        self.assertNotIn('name="password"', html)
        self.assertNotIn('name="groups"', html)
        self.assertNotIn('name="user_permissions"', html)
