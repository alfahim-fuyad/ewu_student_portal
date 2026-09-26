"""Admin registration for students app."""
from django.contrib import admin
from students.models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'department', 'program', 'current_semester', 'is_active')
    list_filter = ('department', 'program', 'is_active', 'current_semester')
    search_fields = ('student_id', 'user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user', 'department', 'current_semester')
    readonly_fields = ('id',)
