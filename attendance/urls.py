from django.urls import path
from attendance.views import (
    AttendanceListView,
    TakeAttendanceView,
    attendance_report,
)

urlpatterns = [
    path('', AttendanceListView.as_view(), name='list'),
    path('take/<int:course_id>/', TakeAttendanceView.as_view(), name='take'),
    path('report/', attendance_report, name='report'),
]
