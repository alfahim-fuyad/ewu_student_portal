from django.contrib import admin
from attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date', 'enrollment__course')
    search_fields = ('enrollment__student__student_id', 'enrollment__course__course_code')
    autocomplete_fields = ('enrollment',)
    date_hierarchy = 'date'
