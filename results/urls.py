from django.urls import path
from results.views import (
    ResultListView,
    ResultCreateView,
    ResultUpdateView,
    TranscriptView,
)

urlpatterns = [
    path('', ResultListView.as_view(), name='list'),
    path('add/', ResultCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', ResultUpdateView.as_view(), name='edit'),
    path('transcript/', TranscriptView.as_view(), name='transcript'),
]
