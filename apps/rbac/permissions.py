from rest_framework.permissions import BasePermission


class HasPerm(BasePermission):
    """基于权限编码的访问控制.

    用法 (视图里):
        permission_classes = [HasPerm]
        required_perms = ['article:create']                 # 单一方法
        required_perms = {'GET': ['article:read'],          # 按 HTTP 方法区分
                          'POST': ['article:create']}

    规则:
    - 未登录 -> 拒绝
    - is_superuser -> 放行
    - 否则检查 user.get_permission_codes() 是否包含所需权限
    """

    def has_permission(self, request, view):
        user = request.user

        # 未登录, 拒绝
        if not user or not user.is_authenticated:
            return False

        # 超级管理员直接放行
        if user.is_superuser:
            return True

        # 从视图取所需权限
        required = getattr(view, "required_perms", None)
        if not required:
            # 视图没声明, 视为不需要权限 (只要登录就行)
            return True

        # 兼容 list 和 dict 两种写法
        codes = required.get(request.method, []) if isinstance(required, dict) else required

        # 视图没声明当前方法需要的权限 -> 放行
        if not codes:
            return True

        # 用集合判断, 要求所需权限全部满足
        user_perms = user.get_permission_codes()
        return all(code in user_perms for code in codes)


class HasAbacPerm(BasePermission):
    """基于 Casbin 的 ABAC 对象级权限.

    跟 HasPerm 的区别:
    - HasPerm:  接口级, "能不能调这个 URL"
    - HasAbacPerm: 对象级, "能不能操作这一条数据"

    用法 (视图里):
        permission_classes = [IsAuthenticated, HasAbacPerm]
        abac_resource = "article"           # 资源类型, 与 casbin_model 的 p.obj 对应

    判定流程:
    1. 组装主体属性 (sub): 从 user 取 id / username / role / is_superuser
    2. 根据视图的 action 映射 HTTP 方法到 act (read/create/update/delete)
    3. 普通列表请求 (has_permission): 不传 obj 属性, 交给视图的 get_queryset 过滤
    4. 对象级请求 (has_object_permission): 取 obj.to_abac_obj() 后判定

    注意:
    - 列表接口必须自己在 get_queryset 里按 ABAC 规则过滤, 否则会泄露数据
    - has_permission 这里不做数据过滤, 只保证用户已登录
    """

    # HTTP 方法 -> 动作
    METHOD_TO_ACT = {
        "GET": "read",
        "HEAD": "read",
        "OPTIONS": "read",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }

    def has_permission(self, request, view):
        """列表/创建入口: 只保证登录, 数据过滤由 get_queryset 负责."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """对象级: 调 Casbin 判定能否操作这一条数据."""
        from rbac.abac import build_sub, enforce

        user = request.user
        if user.is_superuser:
            return True

        act = self.METHOD_TO_ACT.get(request.method)
        if not act:
            return False

        sub = build_sub(user)
        # 对象需要提供 to_abac_obj() 方法返回属性 dict
        obj_attrs = (
            obj.to_abac_obj()
            if hasattr(obj, "to_abac_obj")
            else {
                "obj_type": getattr(view, "abac_resource", ""),
            }
        )
        return enforce(sub, obj_attrs, act)
