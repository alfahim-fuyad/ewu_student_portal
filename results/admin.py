from django.contrib import admin
from results.models import Result


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'marks', 'grade_letter', 'grade_point', 'is_published')
    list_filter = ('is_published', 'grade_letter')
    search_fields = (
        'enrollment__student__student_id',
        'enrollment__course__course_code',
    )
    autocomplete_fields = ('enrollment',)
