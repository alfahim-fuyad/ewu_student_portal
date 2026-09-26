from django.urls import path
from fees.views import (
    FeeListView,
    FeeCreateView,
    PaymentView,
    PaymentHistoryView,
)

urlpatterns = [
    path('', FeeListView.as_view(), name='list'),
    path('add/', FeeCreateView.as_view(), name='add'),
    path('<int:pk>/payment/', PaymentView.as_view(), name='payment'),
    path('history/', PaymentHistoryView.as_view(), name='history'),
]
