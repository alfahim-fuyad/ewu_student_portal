from django.urls import path
from notices.views import (
    NoticeListView,
    NoticeDetailView,
    NoticeCreateView,
    NoticeUpdateView,
    NoticeDeleteView,
)

urlpatterns = [
    path('', NoticeListView.as_view(), name='list'),
    path('add/', NoticeCreateView.as_view(), name='add'),
    path('<int:pk>/', NoticeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', NoticeUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', NoticeDeleteView.as_view(), name='delete'),
]
