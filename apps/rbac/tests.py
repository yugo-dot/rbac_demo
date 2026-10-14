from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from rbac.models import AuditLog, Permission, Role, RolePermission, UserRole

User = get_user_model()


class RolePermissionAssignmentTests(APITestCase):
    """验证 用户-角色 / 角色-权限 分配接口."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice", password="alice12345", email="alice@example.com"
        )
        cls.bob = User.objects.create_user(
            username="bob", password="bob12345", email="bob@example.com"
        )
        cls.role_editor = Role.objects.create(name="编辑", code="editor")
        cls.perm_read = Permission.objects.get_or_create(
            code="article:read", defaults={"name": "读取文章"}
        )[0]

        # alice 加一个管理员角色, 绑全部 rbac:* 权限 (种子数据已建)
        cls.role_admin = Role.objects.create(name="管理员", code="admin")
        admin_perm_codes = [
            "rbac:role:read",
            "rbac:role:manage",
            "rbac:permission:read",
            "rbac:permission:manage",
            "rbac:user_role:read",
            "rbac:user_role:manage",
        ]
        for code in admin_perm_codes:
            perm = Permission.objects.get(code=code)
            RolePermission.objects.create(role=cls.role_admin, permission=perm)
        UserRole.objects.create(user=cls.alice, role=cls.role_admin)

    def _login(self, username, password):
        resp = self.client.post(
            "/api/users/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data["access"]

    def setUp(self):
        # 每个测试前用 alice 登录
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # --- 用户-角色 ---

    def test_assign_role_to_user(self):
        url = f"/api/rbac/users/{self.bob.id}/roles/"
        resp = self.client.post(url, {"role_id": self.role_editor.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserRole.objects.filter(user=self.bob, role=self.role_editor).exists())

    def test_assign_role_is_idempotent(self):
        url = f"/api/rbac/users/{self.bob.id}/roles/"
        self.client.post(url, {"role_id": self.role_editor.id}, format="json")
        resp = self.client.post(url, {"role_id": self.role_editor.id}, format="json")
        # 第二次应返回 200, 不报错
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_user_roles(self):
        UserRole.objects.create(user=self.bob, role=self.role_editor)
        url = f"/api/rbac/users/{self.bob.id}/roles/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["role_code"], "editor")

    def test_remove_role_from_user(self):
        UserRole.objects.create(user=self.bob, role=self.role_editor)
        url = f"/api/rbac/users/{self.bob.id}/roles/{self.role_editor.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserRole.objects.filter(user=self.bob, role=self.role_editor).exists())

    def test_remove_nonexistent_role_returns_404(self):
        url = f"/api/rbac/users/{self.bob.id}/roles/{self.role_editor.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # --- 角色-权限 ---

    def test_assign_permission_to_role(self):
        url = f"/api/rbac/roles/{self.role_editor.id}/permissions/"
        resp = self.client.post(url, {"permission_id": self.perm_read.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            RolePermission.objects.filter(role=self.role_editor, permission=self.perm_read).exists()
        )

    def test_remove_permission_from_role(self):
        RolePermission.objects.create(role=self.role_editor, permission=self.perm_read)
        url = f"/api/rbac/roles/{self.role_editor.id}/permissions/{self.perm_read.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            RolePermission.objects.filter(role=self.role_editor, permission=self.perm_read).exists()
        )

    def test_unauthenticated_returns_401(self):
        self.client.credentials()  # 清掉 token
        url = f"/api/rbac/users/{self.bob.id}/roles/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionListFeatureTests(APITestCase):
    """验证 Permission 列表的分页 / 过滤 / 搜索 / 排序."""

    url = "/api/rbac/permissions/"

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice", password="alice12345", email="alice@example.com"
        )
        # 建 25 条权限, 其中 3 条含 "文章"
        for i in range(1, 23):
            Permission.objects.create(name=f"演示 {i}", code=f"demo:{i:02d}")
        Permission.objects.get_or_create(code="article:read", defaults={"name": "读文章"})
        Permission.objects.create(name="写文章", code="article:write")
        Permission.objects.get_or_create(code="article:delete", defaults={"name": "删文章"})

        # alice 加管理员角色, 绑全部 rbac:* 权限
        role_admin = Role.objects.create(name="管理员", code="admin")
        for code in [
            "rbac:role:read",
            "rbac:role:manage",
            "rbac:permission:read",
            "rbac:permission:manage",
            "rbac:user_role:read",
            "rbac:user_role:manage",
        ]:
            RolePermission.objects.create(
                role=role_admin, permission=Permission.objects.get(code=code)
            )
        UserRole.objects.create(user=cls.alice, role=role_admin)

    def setUp(self):
        token = self.client.post(
            "/api/users/login/",
            {"username": "alice", "password": "alice12345"},
            format="json",
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_pagination_default_page_size(self):
        """默认每页 20 条 (总数动态取, 不写死, 避免受种子数据影响)."""
        total = Permission.objects.count()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], total)
        self.assertEqual(len(resp.data["results"]), min(20, total))

    def test_pagination_second_page(self):
        """第 2 页应有 total - 20 条."""
        total = Permission.objects.count()
        resp = self.client.get(self.url, {"page": 2})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), max(0, total - 20))

    def test_filter_by_code(self):
        """精确过滤 code=article:read."""
        resp = self.client.get(self.url, {"code": "article:read"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["code"], "article:read")

    def test_search(self):
        """搜索 name 含 '文章', 数量动态取."""
        expected = Permission.objects.filter(name__icontains="文章").count()
        resp = self.client.get(self.url, {"search": "文章"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], expected)

    def test_ordering(self):
        """按 code 倒序: 返回结果应严格递减."""
        resp = self.client.get(self.url, {"ordering": "-code"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = [r["code"] for r in resp.data["results"]]
        self.assertEqual(codes, sorted(codes, reverse=True))


class BuiltinProtectionTests(APITestCase):
    """验证内置角色/权限的保护 (禁止改 code, 禁止删)."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice", password="alice12345", email="alice@example.com"
        )
        # alice 给全部 rbac:* 权限
        role_admin = Role.objects.create(name="管理员", code="admin")
        for code in [
            "rbac:role:read",
            "rbac:role:manage",
            "rbac:permission:read",
            "rbac:permission:manage",
            "rbac:user_role:read",
            "rbac:user_role:manage",
        ]:
            RolePermission.objects.create(
                role=role_admin, permission=Permission.objects.get(code=code)
            )
        UserRole.objects.create(user=cls.alice, role=role_admin)

        # 内置权限 (种子数据里就有)
        cls.builtin_perm = Permission.objects.get(code="article:read")
        # 非内置权限
        cls.custom_perm = Permission.objects.create(name="自定义权限", code="custom:read")

    def setUp(self):
        resp = self.client.post(
            "/api/users/login/",
            {"username": "alice", "password": "alice12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    # --- 权限点 ---

    def test_delete_builtin_permission_returns_403(self):
        url = f"/api/rbac/permissions/{self.builtin_perm.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Permission.objects.filter(id=self.builtin_perm.id).exists())

    def test_change_builtin_permission_code_returns_403(self):
        url = f"/api/rbac/permissions/{self.builtin_perm.id}/"
        resp = self.client.patch(url, {"code": "article:read2"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_builtin_permission_name_returns_200(self):
        url = f"/api/rbac/permissions/{self.builtin_perm.id}/"
        resp = self.client.patch(url, {"name": "新名字"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_custom_permission_returns_204(self):
        url = f"/api/rbac/permissions/{self.custom_perm.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # --- 角色 ---

    def test_delete_builtin_role_returns_403(self):
        role = Role.objects.create(name="内置角色", code="builtin_role", is_builtin=True)
        url = f"/api/rbac/roles/{role.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Role.objects.filter(id=role.id).exists())

    def test_change_builtin_role_code_returns_403(self):
        role = Role.objects.create(name="内置角色", code="builtin_role", is_builtin=True)
        url = f"/api/rbac/roles/{role.id}/"
        resp = self.client.patch(url, {"code": "builtin_role2"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_builtin_role_name_returns_200(self):
        role = Role.objects.create(name="内置角色", code="builtin_role", is_builtin=True)
        url = f"/api/rbac/roles/{role.id}/"
        resp = self.client.patch(url, {"name": "新名字"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_custom_role_returns_204(self):
        role = Role.objects.create(name="自定义角色", code="custom_role")
        url = f"/api/rbac/roles/{role.id}/"
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class PolicyManagementTests(APITestCase):
    """验证 /api/rbac/policies/ 策略管理接口."""

    url = "/api/rbac/policies/"

    @classmethod
    def setUpTestData(cls):
        # 两个用户: admin 有策略管理权限, viewer 只有读权限
        cls.policy_read = Permission.objects.get(code="rbac:policy:read")
        cls.policy_manage = Permission.objects.get(code="rbac:policy:manage")

        role_admin = Role.objects.create(name="策略管理员", code="policy_admin")
        RolePermission.objects.create(role=role_admin, permission=cls.policy_read)
        RolePermission.objects.create(role=role_admin, permission=cls.policy_manage)

        role_viewer = Role.objects.create(name="策略查看", code="policy_viewer")
        RolePermission.objects.create(role=role_viewer, permission=cls.policy_read)

        cls.admin = User.objects.create_user(
            username="policy_admin", password="admin12345", email="pa@example.com"
        )
        UserRole.objects.create(user=cls.admin, role=role_admin)

        cls.viewer = User.objects.create_user(
            username="policy_viewer", password="viewer12345", email="pv@example.com"
        )
        UserRole.objects.create(user=cls.viewer, role=role_viewer)

    def _login(self, username, password):
        resp = self.client.post(
            "/api/users/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data["access"]

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_can_list(self):
        """有 rbac:policy:read 的用户能看策略列表."""
        token = self._login("policy_viewer", "viewer12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # 种子数据里有 5 条策略
        self.assertEqual(len(resp.data), 5)

    def test_viewer_cannot_create(self):
        """只有 read 权限的用户加策略 -> 403."""
        token = self._login("policy_viewer", "viewer12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.post(
            self.url,
            {"sub_rule": "r.sub.id == 999", "obj": "article", "act": "read"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_policy(self):
        """有 manage 权限的用户加策略 -> 201, 列表变 6 条."""
        token = self._login("policy_admin", "admin12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.post(
            self.url,
            {"sub_rule": "r.sub.id == 999", "obj": "article", "act": "read"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["sub_rule"], "r.sub.id == 999")

        list_resp = self.client.get(self.url)
        self.assertEqual(len(list_resp.data), 6)

    def test_admin_add_duplicate_returns_200(self):
        """重复加同一策略 -> 200 (幂等), 列表不变."""
        token = self._login("policy_admin", "admin12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        data = {"sub_rule": "r.sub.id == 999", "obj": "article", "act": "read"}
        self.client.post(self.url, data, format="json")
        resp = self.client.post(self.url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        list_resp = self.client.get(self.url)
        self.assertEqual(len(list_resp.data), 6)

    def test_admin_can_delete_policy(self):
        """删策略 -> 204, 列表变 4 条."""
        token = self._login("policy_admin", "admin12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 先加一条, 再删
        create_resp = self.client.post(
            self.url,
            {"sub_rule": "r.sub.id == 999", "obj": "article", "act": "read"},
            format="json",
        )
        policy_id = create_resp.data["id"]
        resp = self.client.delete(f"{self.url}{policy_id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        list_resp = self.client.get(self.url)
        self.assertEqual(len(list_resp.data), 5)

    def test_delete_nonexistent_returns_404(self):
        token = self._login("policy_admin", "admin12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.delete(f"{self.url}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class AuditLogTests(APITestCase):
    """验证审计日志的写入和查询."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice",
            password="alice12345",
            email="alice_audit@example.com",
        )
        # alice 拿到 RBAC 管理 + 审计查看的全部权限
        role_admin = Role.objects.create(name="审计管理员", code="audit_admin")
        for code in [
            "rbac:role:read",
            "rbac:role:manage",
            "rbac:permission:read",
            "rbac:permission:manage",
            "rbac:user_role:read",
            "rbac:user_role:manage",
            "rbac:audit_log:read",
        ]:
            perm = Permission.objects.get(code=code)
            RolePermission.objects.create(role=role_admin, permission=perm)
        UserRole.objects.create(user=cls.alice, role=role_admin)

    def setUp(self):
        resp = self.client.post(
            "/api/users/login/",
            {"username": "alice", "password": "alice12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        # 每个测试前清空审计日志, 避免串扰
        AuditLog.objects.all().delete()

    def _logs(self, **filters):
        return AuditLog.objects.filter(**filters)

    # --- 记录写入 ---

    def test_create_role_logs(self):
        """创建角色 -> 一条 create 日志."""
        resp = self.client.post(
            "/api/rbac/roles/",
            {"name": "测试角色", "code": "test_role"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        logs = self._logs(action="create", target_type="role")
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.operator, self.alice)
        self.assertEqual(log.target_id, resp.data["id"])
        self.assertIn("test_role", log.target_repr)

    def test_update_role_logs_with_before_after(self):
        """更新角色 -> 一条 update 日志, 含 before / after."""
        role = Role.objects.create(name="旧名字", code="update_role")
        resp = self.client.patch(
            f"/api/rbac/roles/{role.id}/",
            {"name": "新名字"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        log = self._logs(action="update", target_type="role").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.detail["before"]["name"], "旧名字")
        self.assertEqual(log.detail["after"]["name"], "新名字")

    def test_delete_role_logs(self):
        """删除角色 -> 一条 delete 日志."""
        role = Role.objects.create(name="待删", code="del_role")
        resp = self.client.delete(f"/api/rbac/roles/{role.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        logs = self._logs(action="delete", target_type="role")
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().target_id, role.id)

    def test_assign_user_role_logs(self):
        """分配用户角色 -> 一条 assign 日志."""
        target_user = User.objects.create_user(
            username="bob", password="bob12345", email="bob_audit@example.com"
        )
        role = Role.objects.create(name="编辑器", code="editor_log")
        resp = self.client.post(
            f"/api/rbac/users/{target_user.id}/roles/",
            {"role_id": role.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        log = self._logs(action="assign", target_type="user_role").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.target_id, target_user.id)
        self.assertEqual(log.detail["role"], "editor_log")

    def test_remove_user_role_logs(self):
        """移除用户角色 -> 一条 remove 日志."""
        target_user = User.objects.create_user(
            username="carol", password="carol12345", email="carol_audit@example.com"
        )
        role = Role.objects.create(name="临时的", code="tmp_role")
        UserRole.objects.create(user=target_user, role=role)
        resp = self.client.delete(f"/api/rbac/users/{target_user.id}/roles/{role.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        log = self._logs(action="remove", target_type="user_role").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.detail["role"], "tmp_role")

    def test_assign_same_role_twice_logs_once(self):
        """重复分配同一角色 (幂等) -> 只记一次 assign."""
        target_user = User.objects.create_user(
            username="dan", password="dan12345", email="dan_audit@example.com"
        )
        role = Role.objects.create(name="幂等", code="idem_role")
        self.client.post(
            f"/api/rbac/users/{target_user.id}/roles/",
            {"role_id": role.id},
            format="json",
        )
        self.client.post(
            f"/api/rbac/users/{target_user.id}/roles/",
            {"role_id": role.id},
            format="json",
        )
        logs = self._logs(action="assign", target_type="user_role")
        self.assertEqual(logs.count(), 1)

    # --- 查询接口 ---

    def test_list_audit_logs(self):
        """有权限的用户能查审计日志列表."""
        self.client.post(
            "/api/rbac/roles/",
            {"name": "查日志测试", "code": "read_logs_role"},
            format="json",
        )
        resp = self.client.get("/api/rbac/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["count"], 1)

    def test_unauthenticated_cannot_list_logs(self):
        """未登录 -> 401."""
        self.client.credentials()
        resp = self.client.get("/api/rbac/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_perm_cannot_list_logs(self):
        """无 rbac:audit_log:read 权限 -> 403."""
        User.objects.create_user(
            username="nobody", password="no123456", email="nobody_audit@example.com"
        )
        resp = self.client.post(
            "/api/users/login/",
            {"username": "nobody", "password": "no123456"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        resp = self.client.get("/api/rbac/audit-logs/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_action(self):
        """按 action 过滤."""
        self.client.post(
            "/api/rbac/roles/",
            {"name": "过滤测试", "code": "filter_role"},
            format="json",
        )
        resp = self.client.get("/api/rbac/audit-logs/", {"action": "create"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data["results"]:
            self.assertEqual(item["action"], "create")
