
from django.contrib import admin
from django.urls import path, include
from .views import *
from dj_rest_auth.jwt_auth import get_refresh_view
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path('register/', CustomRegisterView.as_view(), name='rest_register'),
    path('register/complete/', CompleteRegistrationView.as_view(), name='register_complete'),
    path('login/', CustomLoginView.as_view(), name='rest_login'),
    path('login/complete/', CompleteLoginView.as_view(), name='login_complete'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
    path('github/', GitHubLoginView.as_view(), name='github_login'),
    path("me/", CustomUserDetailsView.as_view(), name="user_details"),
    path("password/change/", PasswordChangeView.as_view(), name='rest_password_change'),
    path("password/reset/", PasswordResetView.as_view(), name='rest_password_reset'),
    path('accounts/', include('allauth.urls')),
    path('2fa/enable/', Enable2FAView.as_view(), name="two_fa_enable"),
    path('2fa/verify/', Verify2FASetupView.as_view(), name="two_fa_verify"),
    path('2fa/request/', Request2FAView.as_view(), name="two_fa_request"),
]