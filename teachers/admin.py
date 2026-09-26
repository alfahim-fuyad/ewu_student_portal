from django.contrib import admin
from teachers.models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'user', 'department', 'designation', 'is_active')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('teacher_id', 'user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user', 'department')
