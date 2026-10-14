from rest_framework.routers import DefaultRouter

from rbac.views import (
    AuditLogViewSet,
    PermissionViewSet,
    PolicyViewSet,
    RoleViewSet,
    UserRoleViewSet,
)

router = DefaultRouter()
router.register("users", UserRoleViewSet, basename="user-role")
router.register("roles", RoleViewSet, basename="role")
router.register("permissions", PermissionViewSet, basename="permission")
router.register("policies", PolicyViewSet, basename="policy")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = router.urls
