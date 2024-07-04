from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from .serializers import CustomRegisterSerializer, CustomLoginSerializer
from dj_rest_auth.views import LoginView

class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "https://127.0.0.1:3000/oath/callback/github"
    client_class = OAuth2Client

class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer

class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer