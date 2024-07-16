from django.urls import path
from .views import EngineDetailView, EngineListCreateView

urlpatterns = [
    path('engines/', EngineListCreateView.as_view(), name='engine_list'),
    path('engines/<int:id>/', EngineDetailView.as_view(), name='engine_detail'),
]
