from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers import MeSerializer


class MeView(RetrieveAPIView):
    """当前登录用户信息, GET /api/users/me/."""

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # 永远返回当前请求用户
        return self.request.user
