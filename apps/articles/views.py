from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from articles.models import Article
from articles.serializers import ArticleSerializer
from rbac.abac import build_sub, enforce
from rbac.permissions import HasAbacPerm, HasPerm


@extend_schema_view(
    list=extend_schema(summary="文章列表 (只返回当前用户可见的)"),
    retrieve=extend_schema(summary="文章详情"),
    create=extend_schema(summary="创建文章"),
    update=extend_schema(summary="更新文章"),
    partial_update=extend_schema(summary="部分更新"),
    destroy=extend_schema(summary="删除文章"),
)
class ArticleViewSet(ModelViewSet):
    """文章 CRUD, 两层权限:

    - HasPerm:     接口级 (需要 article:read / article:create ...)
    - HasAbacPerm: 对象级 (具体到某一条文章, 由 Casbin 判定)
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, HasPerm, HasAbacPerm]
    abac_resource = "article"

    required_perms = {
        "GET": ["article:read"],
        "POST": ["article:create"],
        "PUT": ["article:update"],
        "PATCH": ["article:update"],
        "DELETE": ["article:delete"],
    }

    def get_queryset(self):
        """列表/详情查询集: 按 ABAC 规则过滤.

        普通用户只能看自己写的 + 已发布的, 超管看全部.
        """
        qs = Article.objects.select_related("author").all()
        user = self.request.user
        if user.is_superuser:
            return qs

        sub = build_sub(user)
        visible_ids = [a.id for a in qs if enforce(sub, a.to_abac_obj(), "read")]
        return qs.filter(id__in=visible_ids)

    def perform_create(self, serializer):
        """创建时作者固定为当前用户."""
        serializer.save(author=self.request.user)
