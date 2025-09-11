from django.urls import path
from .views import RegisterView, ProfileView, LogoutView

urlpatterns = [
    path("users/register/", RegisterView.as_view(), name="register"),
    path("signup/", RegisterView.as_view(), name="signup"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
