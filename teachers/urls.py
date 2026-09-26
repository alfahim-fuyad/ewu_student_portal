from django.urls import path
from teachers.views import (
    TeacherListView,
    TeacherDetailView,
    TeacherCreateView,
    TeacherUpdateView,
    TeacherDeleteView,
)

urlpatterns = [
    path('', TeacherListView.as_view(), name='list'),
    path('add/', TeacherCreateView.as_view(), name='add'),
    path('<int:pk>/', TeacherDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', TeacherUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', TeacherDeleteView.as_view(), name='delete'),
]
