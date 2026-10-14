from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

admin.site.site_header = "RBAC 管理后台"
admin.site.site_title = "RBAC 管理后台"
admin.site.index_title = "欢迎使用 RBAC 管理后台"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/rbac/", include("rbac.urls")),
    path("api/demo/", include("articles.urls")),
    # OpenAPI schema + Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
