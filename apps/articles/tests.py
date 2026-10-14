from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from articles.models import Article
from rbac.abac import add_policy, remove_policy
from rbac.models import Permission, Role, RolePermission, UserRole

User = get_user_model()


class ArticleABACTests(APITestCase):
    """验证 ArticleViewSet 的两层权限: HasPerm (接口) + HasAbacPerm (对象)."""

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
        cls.p_update = Permission.objects.get_or_create(
            code="article:update", defaults={"name": "更新文章"}
        )[0]
        cls.p_delete = Permission.objects.get_or_create(
            code="article:delete", defaults={"name": "删除文章"}
        )[0]

        # 角色 editor, 绑全部 article:* 权限
        cls.role_editor = Role.objects.create(name="编辑", code="editor")
        for p in [cls.p_read, cls.p_create, cls.p_update, cls.p_delete]:
            RolePermission.objects.create(role=cls.role_editor, permission=p)

        # alice: 编辑, 写文章
        cls.alice = User.objects.create_user(
            username="alice", password="alice12345", email="alice@example.com"
        )
        UserRole.objects.create(user=cls.alice, role=cls.role_editor)

        # bob: 编辑, 也写文章
        cls.bob = User.objects.create_user(
            username="bob", password="bob12345", email="bob@example.com"
        )
        UserRole.objects.create(user=cls.bob, role=cls.role_editor)

        # carol: 无角色
        cls.carol = User.objects.create_user(
            username="carol", password="carol12345", email="carol@example.com"
        )

        # alice 的私密文章
        cls.alice_article = Article.objects.create(
            title="Alice 的私密文章",
            author=cls.alice,
            status=Article.STATUS_DRAFT,
            visibility=Article.VISIBILITY_PRIVATE,
        )

        # bob 的文章
        cls.bob_article = Article.objects.create(
            title="Bob 的文章",
            author=cls.bob,
            status=Article.STATUS_DRAFT,
            visibility=Article.VISIBILITY_PRIVATE,
        )

    def setUp(self):
        """每条 ABAC 策略测试前加一条规则: 作者能读自己的文章.

        测试完在 tearDown 里清掉, 避免影响其他测试.
        """
        add_policy("r.sub.id == r.obj.author_id", "article", "read")
        add_policy("r.sub.id == r.obj.author_id", "article", "update")
        add_policy("r.sub.id == r.obj.author_id", "article", "delete")

    def tearDown(self):
        remove_policy("r.sub.id == r.obj.author_id", "article", "read")
        remove_policy("r.sub.id == r.obj.author_id", "article", "update")
        remove_policy("r.sub.id == r.obj.author_id", "article", "delete")

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

    def test_user_without_perm_gets_403(self):
        """无 article:read 权限 -> 接口级被 HasPerm 拦下 -> 403."""
        token = self._login("carol", "carol12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_alice_sees_only_own_article(self):
        """alice 有 article:read + ABAC 'author 可读', 只能看到自己的文章."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in resp.data["results"]]
        self.assertIn(self.alice_article.id, ids)
        self.assertNotIn(self.bob_article.id, ids)

    def test_alice_can_read_own_detail(self):
        """alice 能访问自己文章的详情."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(f"{self.url}{self.alice_article.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_alice_cannot_read_bob_detail(self):
        """alice 不能访问 bob 的文章详情 -> 404 (查询集已过滤)."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(f"{self.url}{self.bob_article.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_alice_can_delete_own_article(self):
        """alice 能删自己的文章."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.delete(f"{self.url}{self.alice_article.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=self.alice_article.id).exists())

    def test_alice_cannot_delete_bob_article(self):
        """alice 不能删 bob 的文章 -> 404."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.delete(f"{self.url}{self.bob_article.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Article.objects.filter(id=self.bob_article.id).exists())

    def test_create_sets_author_to_current_user(self):
        """创建文章时 author 强制为当前用户."""
        token = self._login("alice", "alice12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.post(
            self.url,
            {"title": "新文章", "body": "内容"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(id=resp.data["id"])
        self.assertEqual(article.author_id, self.alice.id)

    def test_superuser_sees_all(self):
        """超管看全部文章."""
        User.objects.create_superuser(
            username="root", password="root12345", email="root@example.com"
        )
        token = self._login("root", "root12345")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in resp.data["results"]]
        self.assertIn(self.alice_article.id, ids)
        self.assertIn(self.bob_article.id, ids)
