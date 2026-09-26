from django.contrib import admin
from academics.models import Department, Course, Semester, Enrollment


class CourseInline(admin.TabularInline):
    model = Course
    extra = 0


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'head', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('term', 'year', 'is_current', 'start_date', 'end_date')
    list_filter = ('term', 'is_current', 'year')
    search_fields = ('term', 'year')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'department', 'semester', 'section', 'credits', 'instructor')
    list_filter = ('department', 'semester', 'is_active')
    search_fields = ('course_code', 'title')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'status', 'enrolled_at')
    list_filter = ('status', 'semester', 'course__department')
    search_fields = (
        'student__student_id',
        'student__user__username',
        'course__course_code',
    )
