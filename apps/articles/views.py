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

    def get(self, request):
        return Response({'msg': '读取文章成功 (拥有 article:read)'})

    def post(self, request):
        return Response({'msg': '创建文章成功 (拥有 article:create)'})
