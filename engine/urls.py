from django.urls import path
from .views import EngineDetailView, EngineListCreateView, UserChatsListView, UserChatsDetailView, ChatsMessagesListView

urlpatterns = [
    path('engines/', EngineListCreateView.as_view(), name='engine_list'),
    path('engines/<int:id>/', EngineDetailView.as_view(), name='engine_detail'),
    path('chats/', UserChatsListView.as_view(), name='chat_list'),
    path('chats/<int:id>/', UserChatsDetailView.as_view(), name='chat_detail'),
    path('chats/<int:id>/messages/', ChatsMessagesListView.as_view(), name='chat_detail'),
]
