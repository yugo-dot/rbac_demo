"""审计日志工具.

设计:
- 记录 RBAC 管理面的写操作 (create / update / delete / assign / remove)
- 读操作默认不记, 由 settings.AUDIT_LOG_READ_OPERATIONS 开关控制
- operator 允许为 None (匿名操作也留痕)
- target_repr 存可读描述, 即使目标对象被删也能看懂日志
- detail 用 JSON 存变更详情 (before / after)
"""

from django.conf import settings

from rbac.models import AuditLog


def get_client_ip(request) -> str | None:
    """从 request 里取客户端 IP.

    优先取 X-Forwarded-For (经过反向代理时), 否则取 REMOTE_ADDR.
    """
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # X-Forwarded-For 可能是 "client, proxy1, proxy2", 取第一个
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(
    request,
    action: str,
    target_type: str,
    target_id: int | None = None,
    target_repr: str = "",
    detail: dict | None = None,
) -> AuditLog | None:
    """记录一条审计日志.

    参数:
    - request: DRF request (用于取 operator 和 ip); None 时只记 operator=None
    - action: create / update / delete / assign / remove / read
    - target_type: 资源类型 (role / permission / user_role / policy)
    - target_id: 目标 ID (可选)
    - target_repr: 目标可读描述 (可选)
    - detail: 变更详情 (可选, JSON)

    返回创建的 AuditLog, 或者 None (读操作未开启开关时).
    """
    # 读操作: 未开启开关则跳过
    if action == AuditLog.ACTION_READ and not getattr(settings, "AUDIT_LOG_READ_OPERATIONS", False):
        return None

    # 组装 operator: 未登录时为 None
    operator = None
    if request is not None and getattr(request, "user", None) is not None:
        if request.user.is_authenticated:
            operator = request.user

    return AuditLog.objects.create(
        operator=operator,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_repr=target_repr,
        detail=detail,
        ip=get_client_ip(request),
    )
