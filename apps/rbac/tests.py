from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from rbac.models import Permission, Role, RolePermission, UserRole

User = get_user_model()


class RolePermissionAssignmentTests(APITestCase):
    """验证 用户-角色 / 角色-权限 分配接口."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username='alice', password='alice12345', email='alice@example.com'
        )
        cls.bob = User.objects.create_user(
            username='bob', password='bob12345', email='bob@example.com'
        )
        cls.role_editor = Role.objects.create(name='编辑', code='editor')
        cls.perm_read = Permission.objects.create(name='读取文章', code='article:read')

    def _login(self, username, password):
        resp = self.client.post(
            '/api/users/login/',
            {'username': username, 'password': password},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data['access']

    def setUp(self):
        # 每个测试前用 alice 登录
        token = self._login('alice', 'alice12345')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # --- 用户-角色 ---

    def test_assign_role_to_user(self):
        url = f'/api/rbac/users/{self.bob.id}/roles/'
        resp = self.client.post(url, {'role_id': self.role_editor.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserRole.objects.filter(user=self.bob, role=self.role_editor).exists()
        )

    def test_assign_role_is_idempotent(self):
        url = f'/api/rbac/users/{self.bob.id}/roles/'
        self.client.post(url, {'role_id': self.role_editor.id}, format='json')
        resp = self.client.post(url, {'role_id': self.role_editor.id}, format='json')
        # 第二次应返回 200, 不报错
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_user_roles(self):
        UserRole.objects.create(user=self.bob, role=self.role_editor)
        url = f'/api/rbac/users/{self.bob.id}/roles/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['role_code'], 'editor')

    def test_remove_role_from_user(self):
        UserRole.objects.create(user=self.bob, role=self.role_editor)
        url = f'/api/rbac/users/{self.bob.id}/roles/{self.role_editor.id}/'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            UserRole.objects.filter(user=self.bob, role=self.role_editor).exists()
        )

    def test_remove_nonexistent_role_returns_404(self):
        url = f'/api/rbac/users/{self.bob.id}/roles/{self.role_editor.id}/'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # --- 角色-权限 ---

    def test_assign_permission_to_role(self):
        url = f'/api/rbac/roles/{self.role_editor.id}/permissions/'
        resp = self.client.post(url, {'permission_id': self.perm_read.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            RolePermission.objects.filter(
                role=self.role_editor, permission=self.perm_read
            ).exists()
        )

    def test_remove_permission_from_role(self):
        RolePermission.objects.create(role=self.role_editor, permission=self.perm_read)
        url = (
            f'/api/rbac/roles/{self.role_editor.id}'
            f'/permissions/{self.perm_read.id}/'
        )
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            RolePermission.objects.filter(
                role=self.role_editor, permission=self.perm_read
            ).exists()
        )

    def test_unauthenticated_returns_401(self):
        self.client.credentials()  # 清掉 token
        url = f'/api/rbac/users/{self.bob.id}/roles/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionListFeatureTests(APITestCase):
    """验证 Permission 列表的分页 / 过滤 / 搜索 / 排序."""

    url = '/api/rbac/permissions/'

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username='alice', password='alice12345', email='alice@example.com'
        )
        # 建 25 条权限, 其中 3 条含 "文章"
        for i in range(1, 23):
            Permission.objects.create(name=f'演示 {i}', code=f'demo:{i:02d}')
        Permission.objects.create(name='读文章', code='article:read')
        Permission.objects.create(name='写文章', code='article:write')
        Permission.objects.create(name='删文章', code='article:delete')

    def setUp(self):
        token = self.client.post(
            '/api/users/login/',
            {'username': 'alice', 'password': 'alice12345'},
            format='json',
        ).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_pagination_default_page_size(self):
        """默认每页 20 条."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 25)
        self.assertEqual(len(resp.data['results']), 20)

    def test_pagination_second_page(self):
        """第 2 页剩 5 条."""
        resp = self.client.get(self.url, {'page': 2})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 5)

    def test_filter_by_code(self):
        """精确过滤 code=article:read."""
        resp = self.client.get(self.url, {'code': 'article:read'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['code'], 'article:read')

    def test_search(self):
        """搜索 name 含 '文章'."""
        resp = self.client.get(self.url, {'search': '文章'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 3)

    def test_ordering(self):
        """按 code 倒序, 第一条应是 demo:22."""
        resp = self.client.get(self.url, {'ordering': '-code'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['results'][0]['code'], 'demo:22')
