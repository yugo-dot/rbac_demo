from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from rbac.permissions import HasPerm


class ArticleDemoView(APIView):
    """示例接口: 用 RBAC 保护.

    GET  -> 需要 article:read
    POST -> 需要 article:create
    """

    permission_classes = [HasPerm]
    required_perms = {
        'GET': ['article:read'],
        'POST': ['article:create'],
    }

    @extend_schema(
        summary='读取文章 (需要 article:read)',
        responses={
            200: OpenApiResponse(description='{msg: ...}'),
            403: OpenApiResponse(description='无权限'),
        },
    )
    def get(self, request):
        return Response({'msg': '读取文章成功 (拥有 article:read)'})

    @extend_schema(
        summary='创建文章 (需要 article:create)',
        responses={
            200: OpenApiResponse(description='{msg: ...}'),
            403: OpenApiResponse(description='无权限'),
        },
    )
    def post(self, request):
        return Response({'msg': '创建文章成功 (拥有 article:create)'})
