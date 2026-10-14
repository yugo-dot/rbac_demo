from django.urls import path

from articles.views import ArticleDemoView

urlpatterns = [
    path("articles/", ArticleDemoView.as_view(), name="article-demo"),
]
