from django.db.models import Q
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

        优化思路 (DB 粗筛 + Casbin 精筛):
        - 作者本人 / 已发布且公开: 策略上必然可见, 直接放行, 不跑 enforce
        - 其余行: 才逐行 enforce
        注意: 粗筛条件是策略的"软编码", 策略变更时需同步改这里.
        """
        qs = Article.objects.select_related("author").all()
        user = self.request.user
        if user.is_superuser:
            return qs

        # 粗筛: 这两类命中策略里的宽松条件, 无需 enforce
        coarse_ids = set(
            qs.filter(
                Q(author=user)
                | Q(status=Article.STATUS_PUBLISHED, visibility=Article.VISIBILITY_PUBLIC)
            ).values_list("id", flat=True)
        )

        # 剩余行 (非作者本人 且 非已发布公开) 才跑 enforce
        sub = build_sub(user)
        rest = qs.exclude(id__in=coarse_ids)
        extra_ids = {a.id for a in rest if enforce(sub, a.to_abac_obj(), "read")}

        return qs.filter(id__in=coarse_ids | extra_ids)

    def perform_create(self, serializer):
        """创建时作者固定为当前用户."""
        serializer.save(author=self.request.user)
