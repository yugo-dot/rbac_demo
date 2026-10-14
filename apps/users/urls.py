from django.urls import path

from users.views import LoginView, MeView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
]
