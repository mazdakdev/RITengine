from django.urls import path, include
from dj_rest_auth.jwt_auth import get_refresh_view
from rest_framework_simplejwt.views import TokenVerifyView
from .views import (
    CompletePasswordResetView, CustomRegisterView, CompleteRegistrationView, CustomLoginView,
    CompleteLoginView, GitHubLoginView, UserDetailsView,
    PasswordChangeView, PasswordResetView, Enable2FAView,
    Verify2FASetupView, Request2FAView, UsernameChangeView,
    EmailChangeView, CompleteEmailChangeView, PhoneChangeView,
    CompletePhoneChangeView, Disable2FAView, CompleteDisable2FAView,
    CompletePasswordChangeView, UserSearchView, CompletePasswordResetSerializer,
    Change2FAMethodView
)

urlpatterns = [
    path('register/', CustomRegisterView.as_view(), name='rest_register'),
    path('register/complete/', CompleteRegistrationView.as_view(), name='register_complete'),
    path('login/', CustomLoginView.as_view(), name='rest_login'),
    path('login/complete/', CompleteLoginView.as_view(), name='login_complete'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
    path('github/', GitHubLoginView.as_view(), name='github_login'),
    path("me/", UserDetailsView.as_view(), name="user_details"),
    path("password/change/", PasswordChangeView.as_view(), name='password_change'),
    path("password/change/complete/", CompletePasswordChangeView.as_view(), name='password_change_complete'),
    path("password/reset/", PasswordResetView.as_view(), name='password_reset'),
    path("password/reset/complete/", CompletePasswordResetView.as_view(), name='password_reset_complete'),
    path('accounts/', include('allauth.urls')),
    path('2fa/enable/', Enable2FAView.as_view(), name="two_fa_enable"),
    path('2fa/disable/', Disable2FAView.as_view(), name="two_fa_disable"),
    path('2fa/change/', Change2FAMethodView.as_view(), name="two_fa_change"),
    path('2fa/disable/complete/', CompleteDisable2FAView.as_view(), name="two_fa_disable_complete"),
    path('2fa/enable/complete/', Verify2FASetupView.as_view(), name="two_fa_verify"),
    path('2fa/request/', Request2FAView.as_view(), name="two_fa_request"),
    path("me/change-username/", UsernameChangeView.as_view(), name="username_change"),
    path("me/change-email/", EmailChangeView.as_view(), name="email_change"),
    path("me/change-email/complete/", CompleteEmailChangeView.as_view(), name="email_change_complete"),
    path('me/change-phone/', PhoneChangeView.as_view(), name="phone_change"),
    path('me/change-phone/complete/', CompletePhoneChangeView.as_view(), name="phone_change_complete"),
    path('users/', UserSearchView.as_view(), name="user_search_view"),
]
