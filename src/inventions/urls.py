from django.urls import path
from .views import OfficeListView, FormListView, FieldListView, FormDetailView

urlpatterns = [
    path('offices/', OfficeListView.as_view(), name='office_list'),
    path('forms/', FormListView.as_view(), name='form_list'),
    path('forms/<slug:slug>/', FormDetailView.as_view(), name='form_details_list'),
    path('fields/', FieldListView.as_view(), name='field_list'),
    path('inventions/', OfficeListView.as_view(), name='invention_list'),
]