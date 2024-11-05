from django.urls import path
from .views import OfficeListView, FormListView

urlpatterns = [
    path('offices/', OfficeListView.as_view(), name='office_list'),
    path('forms/', FormListView.as_view(), name='form_list'),
    path('fields/', FormListView.as_view(), name='form_list'),
    path('inventions/', OfficeListView.as_view(), name='invention_list'),
]