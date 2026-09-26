"""URL routes for students app."""
from django.urls import path
from students.views import (
    StudentListView,
    StudentDetailView,
    StudentCreateView,
    StudentUpdateView,
    StudentDeleteView,
    my_profile,
)

urlpatterns = [
    path('', StudentListView.as_view(), name='list'),
    path('my/', my_profile, name='my_profile'),
    path('add/', StudentCreateView.as_view(), name='add'),
    path('<int:pk>/', StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', StudentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', StudentDeleteView.as_view(), name='delete'),
]
