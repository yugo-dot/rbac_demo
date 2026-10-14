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
        required = getattr(view, 'required_perms', None)
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
