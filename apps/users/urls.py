from django.urls import path
from .views import SignUpView, LogoutView, LoginView

urlpatterns = [
    path("login/", LoginView.as_view(), name="user-login"),  # Alternative login route
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
