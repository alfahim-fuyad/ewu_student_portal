"""Accounts app URL routes."""
from django.urls import path
from django.contrib.auth import views as auth_views
from accounts.views import (
    login_view,
    logout_view,
    register_view,
    dashboard,
    ProfileView,
    ChangePasswordView,
    forgot_password,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
