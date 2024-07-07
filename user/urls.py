
from django.contrib import admin
from django.urls import path, include
from .views import *
from dj_rest_auth.views import LoginView, PasswordChangeView

urlpatterns = [
    path('register/', CustomRegisterView.as_view(), name='rest_register'),
    path('login/', CustomLoginView.as_view(), name='rest_login'),
    path('github/', GitHubLoginView.as_view(), name='github_login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path("me/", CustomUserDetailsView.as_view(), name="user_details"),
    path("passowrd/change", PasswordChangeView.as_view(), name='rest_password_change'),
    path('accounts/', include('allauth.urls')),
]
