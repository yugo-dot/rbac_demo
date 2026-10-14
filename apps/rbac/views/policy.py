from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from rbac.abac import add_policy, list_policies_with_id, remove_policy_by_id
from rbac.permissions import HasPerm
from rbac.serializers import PolicySerializer


class PolicyViewSet(ViewSet):
    """Casbin 策略管理接口, 挂在 /api/rbac/policies/ 下.

    策略不是 Django 模型, 是 casbin_rule 表里的行, 所以手写 list / create / destroy.
    """

    permission_classes = [HasPerm]
    required_perms = {
        "GET": ["rbac:policy:read"],
        "POST": ["rbac:policy:manage"],
        "DELETE": ["rbac:policy:manage"],
    }

    @extend_schema(
        summary="列出所有策略",
        responses={200: PolicySerializer(many=True)},
    )
    def list(self, request):
        policies = list_policies_with_id()
        return Response(PolicySerializer(policies, many=True).data)

    @extend_schema(
        summary="添加策略",
        request=PolicySerializer,
        responses={
            201: PolicySerializer,
            200: OpenApiResponse(description="已存在, 幂等返回"),
            400: OpenApiResponse(description="参数错误"),
        },
    )
    def create(self, request):
        serializer = PolicySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        created = add_policy(data["sub_rule"], data["obj"], data["act"])
        # 返回新策略 (带 id)
        policies = list_policies_with_id()
        obj = next(
            (
                p
                for p in policies
                if p["sub_rule"] == data["sub_rule"]
                and p["obj"] == data["obj"]
                and p["act"] == data["act"]
            ),
            None,
        )
        return Response(
            PolicySerializer(obj).data if obj else serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="删除策略",
        responses={
            204: OpenApiResponse(description="删除成功"),
            404: OpenApiResponse(description="策略不存在"),
        },
    )
    def destroy(self, request, pk=None):
        deleted = remove_policy_by_id(int(pk))
        if not deleted:
            return Response({"detail": "策略不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
