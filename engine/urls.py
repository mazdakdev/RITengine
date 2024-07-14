from .views import StreamGeneratorView
from django.urls import path

urlpatterns = [
    path("generate-stream/", StreamGeneratorView.as_view(), name="generate_stream"),
]