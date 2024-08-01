from django.urls import path
from .views import (
    EngineDetailView,
    EngineListCreateView,
    UserChatsListView,
    UserChatsDetailView,
    ChatsMessagesListView,
    AssistsDetailView,
    AssistsListCreateView,
    GenerateChatLinkView,
    EngineCategoryListCreateView,
    EngineCategoryDetailView
 )

urlpatterns = [
    path('engines/', EngineListCreateView.as_view(), name='engine_list'),
    path('engines/<int:id>/', EngineDetailView.as_view(), name='engine_detail'),
    path('engines/categories/', EngineCategoryListCreateView.as_view(), name='engine_detail'),
    path('engines/categories/<int:id>/', EngineCategoryDetailView.as_view(), name='engine_detail'),
    path('chats/', UserChatsListView.as_view(), name='chat_list'),
    path('chats/<slug:slug>/', UserChatsDetailView.as_view(), name='chat_detail'),
    path('chats/<int:id>/generate-link/', GenerateChatLinkView.as_view(), name='chat_link'),
    path('chats/<int:id>/messages/', ChatsMessagesListView.as_view(), name='chat_detail'),
    path('assists/', AssistsListCreateView.as_view(), name='assist_list'),
    path('assists/<int:id>/', AssistsDetailView.as_view(), name='assist_detail'),
]
