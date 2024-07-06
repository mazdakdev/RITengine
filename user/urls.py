
from django.contrib import admin
from django.urls import path, include
from .views import *
from dj_rest_auth.views import LoginView

urlpatterns = [
    path('register/', CustomRegisterView.as_view(), name='rest_register'),
    path('login/', CustomLoginView.as_view(), name='rest_login'),
    path('github/', GitHubLogin.as_view(), name='github_login'),
    path('verify-otp/', VerifyOTP.as_view(), name='verify_otp'),
    path('me/', Profile.as_view(), name='profile'),
    path('change-username/', ChangeUsername.as_view(), name='change_username'),
    path('accounts/', include('allauth.urls')),
]
